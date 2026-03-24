# -*- coding: utf-8 -*-
"""Tests for host group chat tool registration."""
from __future__ import annotations

import pytest

from haibot.agents.react_agent import HaiBotAgent


class _FakeToolkit:
    def __init__(self) -> None:
        self.registered = {}

    def register_tool_function(self, fn, namesake_strategy="skip") -> None:
        self.registered[fn.__name__] = fn


@pytest.mark.asyncio
async def test_register_group_chat_tools_registers_delegate_tool():
    async def callback(agent_id: str, task: str) -> str:
        return f"{agent_id}:{task}"

    toolkit = _FakeToolkit()
    agent = object.__new__(HaiBotAgent)
    agent._request_context = {  # pylint: disable=protected-access
        "group_chat_role": "host",
        "group_participant_agent_ids": ["writer"],
        "group_delegate_callback": callback,
        "group_chat_name": "Team",
    }

    HaiBotAgent._register_group_chat_tools(agent, toolkit)

    assert "delegate_to_agent" in toolkit.registered
    response = await toolkit.registered["delegate_to_agent"](
        "writer",
        "draft section 2",
    )
    assert response.content[0]["text"] == "writer:draft section 2"


def test_build_group_chat_prompt_for_host_mentions_delegate_tool():
    agent = object.__new__(HaiBotAgent)
    agent._request_context = {  # pylint: disable=protected-access
        "group_chat_role": "host",
        "group_chat_name": "Research Team",
        "group_participant_agent_ids": ["writer", "reviewer"],
    }

    prompt = HaiBotAgent._build_group_chat_prompt(agent)

    assert "delegate_to_agent" in prompt
    assert "`writer`" in prompt
    assert "Research Team" in prompt
