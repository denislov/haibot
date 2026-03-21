# -*- coding: utf-8 -*-
"""Group Chat streaming endpoint.

Coordinates multiple agents in a host/participant group chat model.
- User message without @mention → routed to host agent.
- User message with @<agent_name_or_id> → routed directly to that participant.
- Host may @mention participants in its response → parallel dispatch.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import AsyncGenerator

from fastapi import APIRouter, Body, HTTPException, Request
from starlette.responses import StreamingResponse

from ...config import load_config, GroupChatConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/console/group-chat", tags=["group-chat"])

# Regex to capture @mentions: @agent_name or @agent_id
_MENTION_RE = re.compile(r"@([\w\-]+)")


def _find_mentions(text: str, valid_ids: set[str]) -> list[str]:
    """Extract valid @mentions from text.

    Returns list of agent_ids that appear as @mentions, in order.
    """
    if not text:
        return []
    mentions = _MENTION_RE.findall(text)
    return [m for m in mentions if m in valid_ids]


def _get_group_config(gc_id: str) -> GroupChatConfig:
    """Load a GroupChatConfig by ID from the global config.

    Raises HTTPException 404 if not found.
    """
    config = load_config()
    gc = config.group_chats.get(gc_id)
    if gc is None:
        raise HTTPException(
            status_code=404,
            detail=f"Group chat '{gc_id}' not found",
        )
    return gc


def _build_host_delegation_prompt(gc: GroupChatConfig) -> str:
    """Build a short system-prompt appendix informing the host about
    its available participants for delegation."""
    participant_ids = gc.participant_agent_ids
    if not participant_ids:
        return ""
    members = ", ".join(f"`{pid}`" for pid in participant_ids)
    return (
        "\n\n---\n"
        "## Group Chat Host Instructions\n"
        f"You are the host of group chat **{gc.name}**.\n"
        f"Available participants: {members}.\n"
        "When a task requires specialized help, delegate by writing "
        "`@<participant_id>: <instruction>` in your response. "
        "You may @mention multiple participants; they will work in parallel.\n"
        "---\n"
    )


async def _stream_single_agent(
    request: Request,
    agent_id: str,
    payload: dict,
) -> AsyncGenerator[str, None]:
    """Stream SSE events from a single agent's console channel.

    The runner injects agent_id/agent_name into each Msg's metadata,
    so the SSE events already carry agent attribution natively.
    """
    manager = request.app.state.multi_agent_manager
    try:
        workspace = await manager.get_agent(agent_id)
    except ValueError as exc:
        logger.error("Agent '%s' not found: %s", agent_id, exc)
        yield f"data: {json.dumps({'error': f'Agent {agent_id} not found'})}\n\n"
        return

    console_channel = await workspace.channel_manager.get_channel("console")
    if console_channel is None:
        yield f"data: {json.dumps({'error': f'Console channel not available for {agent_id}'})}\n\n"
        return

    async for sse_chunk in console_channel.stream_one(payload):
        yield sse_chunk


async def _stream_parallel_agents(
    request: Request,
    agent_ids: list[str],
    payload: dict,
) -> AsyncGenerator[str, None]:
    """Run multiple agents in parallel and merge their SSE streams."""
    merge_queue: asyncio.Queue[str | None] = asyncio.Queue()
    remaining = len(agent_ids)

    async def _producer(aid: str) -> None:
        nonlocal remaining
        try:
            async for chunk in _stream_single_agent(request, aid, payload):
                await merge_queue.put(chunk)
        except Exception as exc:
            logger.exception("Error streaming agent %s", aid)
            await merge_queue.put(
                f"data: {json.dumps({'error': str(exc), '_agent_id': aid})}\n\n"
            )
        finally:
            remaining -= 1
            if remaining <= 0:
                await merge_queue.put(None)  # sentinel

    # Launch all producers
    for aid in agent_ids:
        asyncio.create_task(_producer(aid))

    # Yield merged results
    while True:
        item = await merge_queue.get()
        if item is None:
            break
        yield item


@router.post(
    "/stream",
    status_code=200,
    summary="Stream group chat response",
    description="Send a message to a group chat. Routes to host or "
    "@mentioned participant(s). Returns SSE stream.",
)
async def post_group_chat_stream(
    request: Request,
    body: dict = Body(
        ...,
        description=(
            '{"group_chat_id": "...", "user_id": "...", '
            '"session_id": "...", "text": "..."}'
        ),
    ),
) -> StreamingResponse:
    """Main group chat endpoint.

    Routing logic:
    1. Parse user text for @mentions matching participant agent IDs.
    2. If mentions found → route to those participants (skip host).
    3. If no mentions → route to host agent.
    """
    gc_id = body.get("group_chat_id")
    if not gc_id:
        raise HTTPException(status_code=400, detail="group_chat_id required")

    gc = _get_group_config(gc_id)

    user_text = body.get("text", "")
    user_id = body.get("user_id", "default")
    session_id = body.get("session_id", "default")

    all_member_ids = set(gc.participant_agent_ids) | {gc.host_agent_id}
    mentions = _find_mentions(user_text, all_member_ids)

    # Build a native payload compatible with console channel
    from agentscope_runtime.engine.schemas.agent_schemas import (
        TextContent,
    )

    content_parts = [TextContent(text=user_text)]
    native_payload = {
        "channel_id": "console",
        "sender_id": user_id,
        "content_parts": content_parts,
        "meta": {
            "session_id": session_id,
            "user_id": user_id,
            "group_chat_id": gc_id,
        },
    }

    # Determine target agents
    if mentions:
        # Filter to only participant mentions (not the host)
        target_ids = [
            m for m in mentions if m in gc.participant_agent_ids
        ]
        if not target_ids:
            # If user @mentioned the host explicitly, route to host
            target_ids = [gc.host_agent_id]
    else:
        # Default: route to host
        target_ids = [gc.host_agent_id]

    if len(target_ids) == 1:
        gen = _stream_single_agent(request, target_ids[0], native_payload)
    else:
        gen = _stream_parallel_agents(request, target_ids, native_payload)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for chunk in gen:
                yield chunk
        except Exception as exc:
            logger.exception("Group chat stream error")
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
