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
    assert "delegate_to_agents" in toolkit.registered
    response = await toolkit.registered["delegate_to_agent"](
        "writer",
        "draft section 2",
    )
    assert response.content[0]["text"] == "writer:draft section 2"


@pytest.mark.asyncio
async def test_delegate_to_agents_runs_parallel_batch():
    async def callback(agent_id: str, task: str) -> str:
        return f"{agent_id}:{task}"

    toolkit = _FakeToolkit()
    agent = object.__new__(HaiBotAgent)
    agent._request_context = {  # pylint: disable=protected-access
        "group_chat_role": "host",
        "group_participant_agent_ids": ["writer", "reviewer"],
        "group_delegate_callback": callback,
        "group_chat_name": "Team",
    }

    HaiBotAgent._register_group_chat_tools(agent, toolkit)

    response = await toolkit.registered["delegate_to_agents"](
        '[{"agent_id":"writer","task":"draft"},{"agent_id":"reviewer","task":"review"}]',
    )
    text = response.content[0]["text"]
    assert "[writer]" in text
    assert "writer:draft" in text
    assert "[reviewer]" in text
    assert "reviewer:review" in text


def test_build_group_chat_prompt_for_host_mentions_delegate_tool():
    agent = object.__new__(HaiBotAgent)
    agent._request_context = {  # pylint: disable=protected-access
        "group_chat_role": "host",
        "group_chat_name": "Research Team",
        "group_participant_agent_ids": ["writer", "reviewer"],
        "group_user_request_text": "Prepare a launch brief.",
    }

    prompt = HaiBotAgent._build_group_chat_prompt(agent)

    assert "delegate_to_agent" in prompt
    assert "delegate_to_agents" in prompt
    assert "Reply directly when you already have enough information." in prompt
    assert "Prepare a launch brief." in prompt
    assert "`writer`" in prompt
    assert "Research Team" in prompt


def test_build_group_chat_prompt_for_delegated_participant_mentions_task():
    agent = object.__new__(HaiBotAgent)
    agent._request_context = {  # pylint: disable=protected-access
        "group_chat_role": "participant",
        "group_chat_name": "Research Team",
        "delegated_by_agent_id": "host",
        "delegated_task": "Review the risk section and list gaps.",
    }

    prompt = HaiBotAgent._build_group_chat_prompt(agent)

    assert "audience is the host" in prompt
    assert "Review the risk section and list gaps." in prompt
    assert "`host`" in prompt


def test_build_group_chat_prompt_for_direct_participant_mentions_user_request():
    agent = object.__new__(HaiBotAgent)
    agent._request_context = {  # pylint: disable=protected-access
        "group_chat_role": "participant_direct",
        "group_chat_name": "Research Team",
        "group_user_request_text": "Reviewer, what risks do you see?",
    }

    prompt = HaiBotAgent._build_group_chat_prompt(agent)

    assert "user addressed you directly" in prompt
    assert "Reviewer, what risks do you see?" in prompt
    assert "do not pretend to coordinate other agents" in prompt
