# -*- coding: utf-8 -*-
"""Streaming coordinator for group chat requests."""
from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, AsyncGenerator, Callable

from fastapi import Request
from agentscope_runtime.engine.schemas.agent_schemas import (
    FileContent,
    ImageContent,
    TextContent,
)

from ...config import GroupChatConfig
from ..channels.console.channel import ConsoleChannel
from .models import GroupChatStreamRequest
from .runtime import GroupChatRuntime
from .transcript import GroupTranscriptCollector, flatten_metadata

logger = logging.getLogger(__name__)

_MENTION_RE = re.compile(r"@([\w\-]+)")


def _build_group_file_url(group_id: str, filename: str) -> str:
    return f"/api/group-chats/{group_id}/files/{filename}"


def _host_session_id(group_id: str, chat_id: str, agent_id: str) -> str:
    return f"gc:{group_id}:{chat_id}:host:{agent_id}"


def _participant_session_id(
    group_id: str,
    chat_id: str,
    agent_id: str,
) -> str:
    return f"gc:{group_id}:{chat_id}:member:{agent_id}"


def _extract_text(request_input: list[dict[str, Any]]) -> str:
    if not request_input:
        return ""
    content = request_input[0].get("content") or []
    parts = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            parts.append(str(item.get("text") or ""))
    return "".join(parts)


def _find_mentions(text: str, valid_ids: set[str]) -> list[str]:
    if not text:
        return []
    mentions = _MENTION_RE.findall(text)
    return [mention for mention in mentions if mention in valid_ids]


def _resolve_group_media_ref(runtime: GroupChatRuntime, value: str) -> str:
    if not value:
        return value
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str(runtime.media_dir / value)


def _normalize_content_parts(
    runtime: GroupChatRuntime,
    request_input: list[dict[str, Any]],
) -> list[Any]:
    """Convert request input to console-native content parts."""
    if not request_input:
        return []
    content = request_input[0].get("content") or []
    normalized = []
    for item in content:
        if not isinstance(item, dict):
            continue
        part = dict(item)
        part_type = part.get("type")
        if part_type == "text":
            normalized.append(TextContent(text=str(part.get("text") or "")))
        elif part_type == "image":
            image_url = part.get("image_url")
            if isinstance(image_url, dict) and image_url.get("url"):
                normalized.append(
                    ImageContent(
                        image_url=_resolve_group_media_ref(
                            runtime,
                            str(image_url["url"]),
                        ),
                    ),
                )
        elif part_type == "file" and part.get("file_url"):
            normalized.append(
                FileContent(
                    file_url=_resolve_group_media_ref(
                        runtime,
                        str(part["file_url"]),
                    ),
                    filename=str(part.get("filename") or ""),
                ),
            )
    return normalized


def _decorate_chunk(chunk: str, group_id: str) -> str:
    """Inject flattened group metadata into SSE event JSON."""
    lines = []
    for line in chunk.splitlines():
        if not line.startswith("data: "):
            lines.append(line)
            continue

        raw = line[6:].strip()
        if not raw or raw == "[DONE]":
            lines.append(line)
            continue

        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            lines.append(line)
            continue

        if isinstance(event, dict):
            event["metadata"] = flatten_metadata(
                event.get("metadata"),
                group_id,
            )
            lines.append(f"data: {json.dumps(event, ensure_ascii=False)}")
        else:
            lines.append(line)

    return "\n".join(lines) + "\n\n"


class _ParticipantResultCollector:
    """Collect final assistant text from delegated participant stream."""

    def __init__(self) -> None:
        self._message_types: dict[str, str] = {}
        self._chunks: list[str] = []

    def consume(self, chunk: str) -> None:
        """Track message types and final text deltas."""
        for line in chunk.splitlines():
            if not line.startswith("data: "):
                continue
            raw = line[6:].strip()
            if not raw or raw == "[DONE]":
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue

            if (
                event.get("object") == "message"
                and event.get("status") == "in_progress"
                and event.get("id")
            ):
                self._message_types[str(event["id"])] = str(
                    event.get("type") or "",
                )
            elif (
                event.get("object") == "content"
                and event.get("type") == "text"
                and event.get("delta") is True
            ):
                msg_id = str(event.get("msg_id") or "")
                if self._message_types.get(msg_id) == "message":
                    self._chunks.append(str(event.get("text") or ""))

    def result_text(self) -> str:
        """Return collected assistant message text."""
        return "".join(self._chunks).strip()


class GroupChatCoordinator:
    """Route group requests to host or explicitly mentioned agents."""

    async def _stream_single_agent(
        self,
        request: Request,
        group_id: str,
        agent_id: str,
        payload: dict[str, Any],
        extra_metadata: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        manager = request.app.state.multi_agent_manager
        workspace = await manager.get_agent(agent_id)
        console_channel = await workspace.channel_manager.get_channel("console")
        if not isinstance(console_channel, ConsoleChannel):
            error = {"error": f"Console channel unavailable for {agent_id}"}
            yield f"data: {json.dumps(error)}\n\n"
            return

        async for chunk in console_channel.stream_one(payload):
            decorated = _decorate_chunk(chunk, group_id)
            if extra_metadata:
                decorated = self._merge_static_metadata(
                    decorated,
                    extra_metadata,
                )
            yield decorated

    @staticmethod
    def _merge_static_metadata(
        chunk: str,
        extra_metadata: dict[str, Any],
    ) -> str:
        """Merge static metadata into each SSE event chunk."""
        lines = []
        for line in chunk.splitlines():
            if not line.startswith("data: "):
                lines.append(line)
                continue
            raw = line[6:].strip()
            if not raw or raw == "[DONE]":
                lines.append(line)
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                lines.append(line)
                continue

            if isinstance(event, dict):
                metadata = dict(event.get("metadata") or {})
                metadata.update(extra_metadata)
                event["metadata"] = metadata
                lines.append(f"data: {json.dumps(event, ensure_ascii=False)}")
            else:
                lines.append(line)
        return "\n".join(lines) + "\n\n"

    def _build_delegate_callback(
        self,
        request: Request,
        runtime: GroupChatRuntime,
        group_config: GroupChatConfig,
        body: GroupChatStreamRequest,
        event_queue: "asyncio.Queue[str | None]",
    ) -> Callable[[str, str], Any]:
        """Create host tool callback for delegating to a participant."""

        async def _delegate(agent_id: str, task: str) -> str:
            if agent_id not in group_config.participant_agent_ids:
                return (
                    f"Error: '{agent_id}' is not a participant in "
                    f"group chat '{group_config.id}'."
                )

            payload = {
                "channel_id": "console",
                "sender_id": body.user_id,
                "content_parts": [TextContent(text=task)],
                "meta": {
                    "session_id": _participant_session_id(
                        runtime.group_id,
                        body.chat_id,
                        agent_id,
                    ),
                    "user_id": body.user_id,
                    "group_id": runtime.group_id,
                    "group_chat_id": runtime.group_id,
                    "group_chat_name": group_config.name,
                    "group_chat_role": "participant",
                    "group_host_agent_id": group_config.host_agent_id,
                    "group_participant_agent_ids": list(
                        group_config.participant_agent_ids,
                    ),
                    "chat_id": body.chat_id,
                    "public_group_session_id": body.session_id,
                    "delegated_by_agent_id": group_config.host_agent_id,
                },
            }
            result_collector = _ParticipantResultCollector()
            extra_metadata = {
                "group_chat_role": "participant",
                "delegated_by_agent_id": group_config.host_agent_id,
            }

            async for chunk in self._stream_single_agent(
                request,
                runtime.group_id,
                agent_id,
                payload,
                extra_metadata=extra_metadata,
            ):
                result_collector.consume(chunk)
                await event_queue.put(chunk)

            result_text = result_collector.result_text()
            if result_text:
                return result_text
            return (
                f"Participant `{agent_id}` completed the delegated task "
                "without a final text message."
            )

        return _delegate

    async def stream_turn(
        self,
        request: Request,
        runtime: GroupChatRuntime,
        group_config: GroupChatConfig,
        body: GroupChatStreamRequest,
    ) -> AsyncGenerator[str, None]:
        """Run one public turn and persist transcript after completion."""
        collector = GroupTranscriptCollector(
            runtime.group_id,
            _build_group_file_url,
        )
        collector.add_user_message(body.input)

        request_text = _extract_text(body.input)
        all_member_ids = set(group_config.participant_agent_ids)
        all_member_ids.add(group_config.host_agent_id)
        mentions = _find_mentions(request_text, all_member_ids)

        if mentions:
            target_ids = [
                mention
                for mention in mentions
                if mention in group_config.participant_agent_ids
            ]
            if not target_ids:
                target_ids = [group_config.host_agent_id]
        else:
            target_ids = [group_config.host_agent_id]

        content_parts = _normalize_content_parts(runtime, body.input)

        if len(target_ids) == 1:
            target_agent_id = target_ids[0]
            if target_agent_id == group_config.host_agent_id:
                queue: asyncio.Queue[str | None] = asyncio.Queue()
                delegate_callback = self._build_delegate_callback(
                    request,
                    runtime,
                    group_config,
                    body,
                    queue,
                )
                payload = {
                    "channel_id": "console",
                    "sender_id": body.user_id,
                    "content_parts": content_parts,
                    "meta": {
                        "session_id": _host_session_id(
                            runtime.group_id,
                            body.chat_id,
                            target_agent_id,
                        ),
                        "user_id": body.user_id,
                        "group_id": runtime.group_id,
                        "group_chat_id": runtime.group_id,
                        "group_chat_name": group_config.name,
                        "group_chat_role": "host",
                        "group_host_agent_id": group_config.host_agent_id,
                        "group_participant_agent_ids": list(
                            group_config.participant_agent_ids,
                        ),
                        "group_delegate_callback": delegate_callback,
                        "chat_id": body.chat_id,
                        "public_group_session_id": body.session_id,
                    },
                }

                async def _host_producer() -> None:
                    try:
                        async for chunk in self._stream_single_agent(
                            request,
                            runtime.group_id,
                            target_agent_id,
                            payload,
                            extra_metadata={"group_chat_role": "host"},
                        ):
                            await queue.put(chunk)
                    except Exception:
                        logger.exception("Group chat host stream failed")
                        await queue.put(
                            "data: "
                            f"{json.dumps({'error': 'Host agent failed'})}\n\n"
                        )
                    finally:
                        await queue.put(None)

                asyncio.create_task(_host_producer())
                while True:
                    item = await queue.get()
                    if item is None:
                        break
                    collector.consume_sse_chunk(item)
                    yield item
            else:
                payload = {
                    "channel_id": "console",
                    "sender_id": body.user_id,
                    "content_parts": content_parts,
                    "meta": {
                        "session_id": _participant_session_id(
                            runtime.group_id,
                            body.chat_id,
                            target_agent_id,
                        ),
                        "user_id": body.user_id,
                        "group_id": runtime.group_id,
                        "group_chat_id": runtime.group_id,
                        "group_chat_name": group_config.name,
                        "group_chat_role": "participant",
                        "group_host_agent_id": group_config.host_agent_id,
                        "group_participant_agent_ids": list(
                            group_config.participant_agent_ids,
                        ),
                        "chat_id": body.chat_id,
                        "public_group_session_id": body.session_id,
                    },
                }
                async for chunk in self._stream_single_agent(
                    request,
                    runtime.group_id,
                    target_agent_id,
                    payload,
                    extra_metadata={"group_chat_role": "participant"},
                ):
                    collector.consume_sse_chunk(chunk)
                    yield chunk
        else:
            queue: asyncio.Queue[str | None] = asyncio.Queue()
            remaining = len(target_ids)

            async def _producer(agent_id: str) -> None:
                nonlocal remaining
                payload = {
                    "channel_id": "console",
                    "sender_id": body.user_id,
                    "content_parts": content_parts,
                    "meta": {
                        "session_id": _participant_session_id(
                            runtime.group_id,
                            body.chat_id,
                            agent_id,
                        ),
                        "user_id": body.user_id,
                        "group_id": runtime.group_id,
                        "group_chat_id": runtime.group_id,
                        "group_chat_name": group_config.name,
                        "group_chat_role": "participant",
                        "group_host_agent_id": group_config.host_agent_id,
                        "group_participant_agent_ids": list(
                            group_config.participant_agent_ids,
                        ),
                        "chat_id": body.chat_id,
                        "public_group_session_id": body.session_id,
                    },
                }
                try:
                    async for chunk in self._stream_single_agent(
                        request,
                        runtime.group_id,
                        agent_id,
                        payload,
                        extra_metadata={"group_chat_role": "participant"},
                    ):
                        await queue.put(chunk)
                except Exception:
                    logger.exception("Group chat agent stream failed")
                    await queue.put(
                        "data: "
                        f"{json.dumps({'error': f'Agent {agent_id} failed'})}\n\n"
                    )
                finally:
                    remaining -= 1
                    if remaining <= 0:
                        await queue.put(None)

            for agent_id in target_ids:
                asyncio.create_task(_producer(agent_id))

            while True:
                item = await queue.get()
                if item is None:
                    break
                collector.consume_sse_chunk(item)
                yield item

        messages = collector.finalize()
        if messages:
            await runtime.append_transcript_messages(
                body.session_id,
                body.user_id,
                messages,
            )
