# -*- coding: utf-8 -*-
"""Tests for runtime message metadata conversion."""
from __future__ import annotations

from agentscope.message import Msg, TextBlock

from haibot.app.runner.utils import agentscope_msg_to_message


def test_agentscope_msg_to_message_flattens_metadata():
    msg = Msg(
        name="Alpha",
        role="assistant",
        content=[TextBlock(type="text", text="done")],
        metadata={"agent_id": "alpha", "agent_name": "Alpha"},
    )

    messages = agentscope_msg_to_message(msg)

    assert len(messages) == 1
    assert messages[0].metadata["agent_id"] == "alpha"
    assert messages[0].metadata["agent_name"] == "Alpha"
    assert messages[0].metadata["original_name"] == "Alpha"
