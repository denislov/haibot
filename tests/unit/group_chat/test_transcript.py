# -*- coding: utf-8 -*-
"""Tests for group chat transcript collection."""
from __future__ import annotations

from haibot.app.group_chat.transcript import GroupTranscriptCollector


def test_group_transcript_collector_collects_user_and_agent_messages():
    collector = GroupTranscriptCollector(
        "team",
        lambda group_id, name: f"/api/group-chats/{group_id}/files/{name}",
    )

    collector.add_user_message(
        [
            {
                "role": "user",
                "type": "message",
                "content": [
                    {"type": "text", "text": "hello"},
                    {"type": "image", "image_url": {"url": "image.png"}},
                    {"type": "file", "file_url": "doc.txt", "filename": "doc.txt"},
                ],
            },
        ],
    )
    collector.consume_sse_chunk(
        "\n".join(
            [
                'data: {"object":"message","status":"in_progress","id":"m1","type":"message","role":"assistant","metadata":{"agent_id":"alpha","agent_name":"Alpha"}}',
                'data: {"object":"content","status":"in_progress","msg_id":"m1","type":"text","delta":true,"text":"world"}',
                'data: {"object":"message","status":"completed","id":"m1","type":"message","role":"assistant","metadata":{"agent_id":"alpha","agent_name":"Alpha"}}',
                "",
            ],
        ),
    )

    messages = collector.finalize()

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"][1]["image_url"]["url"].endswith("/image.png")
    assert messages[0]["content"][2]["file_url"].endswith("/doc.txt")
    assert messages[1]["role"] == "assistant"
    assert messages[1]["metadata"]["group_id"] == "team"
    assert messages[1]["metadata"]["agent_id"] == "alpha"
    assert messages[1]["content"][0]["text"] == "world"
