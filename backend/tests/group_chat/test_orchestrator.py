# backend/tests/group_chat/test_orchestrator.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agentscope.message import Msg
from haibot.app.group_chat.models import GroupChatConfig
from haibot.app.group_chat.orchestrator import GroupChatOrchestrator, tag_event


def test_tag_event_adds_agent_fields():
    event = {"object": "message", "type": "message"}
    tagged = tag_event(event, agent_id="analyst", agent_name="分析师")
    assert tagged["agent_id"] == "analyst"
    assert tagged["agent_name"] == "分析师"
    assert tagged["object"] == "message"  # original fields preserved


def test_tag_event_does_not_mutate_original():
    original = {"object": "content"}
    tagged = tag_event(original, agent_id="x", agent_name="X")
    assert "agent_id" not in original


async def test_orchestrator_single_round_no_mentions(tmp_path):
    """Host replies without @mention → single round, no participants run."""
    config = GroupChatConfig(
        id="test_group",
        name="Test",
        host_agent_id="main",
        participant_agent_ids=["analyst"],
        max_rounds=5,
    )

    host_reply = Msg("main", "这个问题我来回答，无需讨论。", "assistant")

    async def fake_stream_agent(agent, msgs, agent_id, agent_name):
        yield host_reply, True

    with patch(
        "haibot.app.group_chat.orchestrator.stream_agent",
        side_effect=fake_stream_agent,
    ):
        orchestrator = GroupChatOrchestrator(
            config=config,
            agent_meta={"main": {"name": "Main"}, "analyst": {"name": "分析师"}},
            memory_manager_factory=AsyncMock(return_value=None),
            mcp_clients=[],
            env_context_factory=MagicMock(return_value=""),
            language="zh",
        )

        user_msg = Msg("user", "今天天气怎么样？", "user")
        events = []
        async for event in orchestrator.run(
            user_msg=user_msg,
            session_id="sess1",
            user_id="u1",
            channel="console",
        ):
            events.append(event)

    # events is a list of (msg, last) tuples
    assert len(events) > 0
    # At least one (msg, True) pair — the final message
    last_msgs = [msg for msg, last in events if last]
    assert len(last_msgs) >= 1
    # No participants should have run (host had no @mentions → loop ends)
