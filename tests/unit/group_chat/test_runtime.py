# -*- coding: utf-8 -*-
"""Tests for group chat runtime storage."""
from __future__ import annotations

from pathlib import Path

import pytest

from haibot.app.group_chat.runtime import GroupChatRuntime
from haibot.app.runner.models import ChatSpec


@pytest.mark.asyncio
async def test_group_chat_runtime_persists_transcript(tmp_path: Path):
    runtime = GroupChatRuntime("team", tmp_path / "group")

    spec = ChatSpec(
        id="chat-1",
        name="Demo",
        session_id="sess-1",
        user_id="user-1",
        channel="console",
        meta={},
    )
    await runtime.create_chat(spec)
    await runtime.append_transcript_messages(
        "sess-1",
        "user-1",
        [
            {
                "id": "msg-1",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": "hello"}],
                "metadata": {"group_id": "team", "agent_id": "writer"},
            },
        ],
    )

    history = await runtime.get_history("chat-1")

    assert history["status"] == "idle"
    assert len(history["messages"]) == 1
    assert history["messages"][0]["metadata"]["group_id"] == "team"
    assert history["messages"][0]["metadata"]["agent_id"] == "writer"
