# -*- coding: utf-8 -*-
"""Tests for runner message conversion utilities."""
from __future__ import annotations

from agentscope.message import Msg
from agentscope_runtime.engine.schemas.agent_schemas import MessageType

from haibot.app.runner.utils import _abspath_from_url, agentscope_msg_to_message


def test_abspath_from_url_preserves_unix_paths() -> None:
    assert _abspath_from_url("file:///tmp/demo.png") == "/tmp/demo.png"


def test_abspath_from_url_normalizes_windows_drive_paths() -> None:
    assert _abspath_from_url("file:///C:/temp/demo.png") == "C:/temp/demo.png"
    assert _abspath_from_url("file://C:/temp/demo.png") == "C:/temp/demo.png"


def test_agentscope_msg_to_message_converts_rich_media_blocks() -> None:
    msg = Msg(
        name="Alpha",
        role="assistant",
        content=[
            {"type": "text", "text": "hello"},
            {
                "type": "image",
                "source": {"type": "url", "url": "file:///tmp/example.png"},
            },
            {
                "type": "audio",
                "source": {"type": "url", "url": "file:///tmp/example.wav"},
            },
            {
                "type": "video",
                "source": {"type": "url", "url": "file:///tmp/example.mp4"},
            },
        ],
    )

    messages = agentscope_msg_to_message(msg)

    assert len(messages) == 1
    assert messages[0].type == MessageType.MESSAGE
    assert messages[0].content[0].text == "hello"
    assert messages[0].content[1].image_url == "/tmp/example.png"
    assert messages[0].content[2].data == "/tmp/example.wav"
    assert messages[0].content[2].format == "wav"
    assert messages[0].content[3].video_url == "/tmp/example.mp4"


def test_agentscope_msg_to_message_converts_tool_result_output() -> None:
    msg = Msg(
        name="Friday",
        role="assistant",
        content=[
            {
                "type": "tool_result",
                "id": "call-1",
                "name": "run_codex_cli",
                "output": {
                    "status": "completed",
                    "output": "Codex transcript",
                },
            },
        ],
    )

    messages = agentscope_msg_to_message(msg)

    assert len(messages) == 1
    assert messages[0].type == MessageType.PLUGIN_CALL_OUTPUT
    payload = messages[0].content[0].data
    assert payload["call_id"] == "call-1"
    assert payload["name"] == "run_codex_cli"
    assert "Codex transcript" in payload["output"]
