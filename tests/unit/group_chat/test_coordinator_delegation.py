# -*- coding: utf-8 -*-
"""Tests for group chat delegation callback."""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from haibot.app.group_chat.coordinator import GroupChatCoordinator
from haibot.app.group_chat.models import GroupChatStreamRequest
from haibot.config.config import GroupChatConfig


@pytest.mark.asyncio
async def test_delegate_callback_streams_participant_and_returns_text():
    coordinator = GroupChatCoordinator()
    runtime = SimpleNamespace(group_id="team", media_dir=Path("/tmp/team-media"))
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))
    group_config = GroupChatConfig(
        id="team",
        name="Team",
        host_agent_id="host",
        participant_agent_ids=["writer"],
        max_rounds=6,
    )
    body = GroupChatStreamRequest(
        chat_id="chat-1",
        session_id="public-session",
        user_id="user-1",
        input=[],
    )
    event_queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def fake_stream_single_agent(
        request,
        group_id,
        agent_id,
        payload,
        extra_metadata=None,
    ):
        assert agent_id == "writer"
        assert payload["meta"]["group_chat_role"] == "participant"
        assert payload["meta"]["delegated_by_agent_id"] == "host"
        yield (
            'data: {"object":"message","status":"in_progress","id":"m1",'
            '"type":"message","role":"assistant","metadata":{"agent_id":"writer"}}\n\n'
        )
        yield (
            'data: {"object":"content","status":"in_progress","msg_id":"m1",'
            '"type":"text","delta":true,"text":"delegated result"}\n\n'
        )
        yield (
            'data: {"object":"message","status":"completed","id":"m1",'
            '"type":"message","role":"assistant","metadata":{"agent_id":"writer"}}\n\n'
        )

    coordinator._stream_single_agent = fake_stream_single_agent  # type: ignore[method-assign]

    callback = coordinator._build_delegate_callback(
        request,
        runtime,
        group_config,
        body,
        event_queue,
    )
    result = await callback("writer", "Summarize the draft")

    assert result == "delegated result"
    queued = []
    while not event_queue.empty():
        queued.append(await event_queue.get())
    assert len(queued) == 3
    assert "delegated result" in queued[1]


@pytest.mark.asyncio
async def test_delegate_callback_rejects_unknown_participant():
    coordinator = GroupChatCoordinator()
    runtime = SimpleNamespace(group_id="team", media_dir=Path("/tmp/team-media"))
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))
    group_config = GroupChatConfig(
        id="team",
        name="Team",
        host_agent_id="host",
        participant_agent_ids=["writer"],
        max_rounds=6,
    )
    body = GroupChatStreamRequest(
        chat_id="chat-1",
        session_id="public-session",
        user_id="user-1",
        input=[],
    )
    event_queue: asyncio.Queue[str | None] = asyncio.Queue()

    callback = coordinator._build_delegate_callback(
        request,
        runtime,
        group_config,
        body,
        event_queue,
    )
    result = await callback("unknown", "task")

    assert "not a participant" in result
