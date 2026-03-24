# -*- coding: utf-8 -*-
"""Streaming coordinator for group chat requests."""
from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, AsyncGenerator

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


class GroupChatCoordinator:
    """Route group requests to host or explicitly mentioned agents."""

    async def _stream_single_agent(
        self,
        request: Request,
        group_id: str,
        agent_id: str,
        payload: dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        manager = request.app.state.multi_agent_manager
        workspace = await manager.get_agent(agent_id)
        console_channel = await workspace.channel_manager.get_channel("console")
        if not isinstance(console_channel, ConsoleChannel):
            error = {"error": f"Console channel unavailable for {agent_id}"}
            yield f"data: {json.dumps(error)}\n\n"
            return

        async for chunk in console_channel.stream_one(payload):
            yield _decorate_chunk(chunk, group_id)

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

        payload = {
            "channel_id": "console",
            "sender_id": body.user_id,
            "content_parts": _normalize_content_parts(runtime, body.input),
            "meta": {
                "session_id": body.session_id,
                "user_id": body.user_id,
                "group_id": runtime.group_id,
                "group_chat_id": runtime.group_id,
                "chat_id": body.chat_id,
            },
        }

        if len(target_ids) == 1:
            async for chunk in self._stream_single_agent(
                request,
                runtime.group_id,
                target_ids[0],
                payload,
            ):
                collector.consume_sse_chunk(chunk)
                yield chunk
        else:
            queue: asyncio.Queue[str | None] = asyncio.Queue()
            remaining = len(target_ids)

            async def _producer(agent_id: str) -> None:
                nonlocal remaining
                try:
                    async for chunk in self._stream_single_agent(
                        request,
                        runtime.group_id,
                        agent_id,
                        payload,
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
