# -*- coding: utf-8 -*-
"""Helpers for group chat transcript persistence."""
from __future__ import annotations

import json
import uuid
from typing import Any


def flatten_metadata(metadata: Any, group_id: str) -> dict[str, Any]:
    """Flatten runtime metadata and ensure group_id is present."""
    if not isinstance(metadata, dict):
        return {"group_id": group_id}

    flat: dict[str, Any] = {}
    nested = metadata.get("metadata")
    if isinstance(nested, dict):
        flat.update(nested)

    for key, value in metadata.items():
        if key != "metadata":
            flat[key] = value

    flat["group_id"] = group_id
    return flat


def _content_part_to_dict(
    part: Any,
    *,
    group_id: str,
    file_url_builder,
) -> dict[str, Any] | None:
    """Convert content part object or dict into JSON-safe dict."""
    if isinstance(part, dict):
        part_dict = dict(part)
    else:
        part_dict = {}
        for key in (
            "type",
            "text",
            "image_url",
            "file_url",
            "filename",
            "data",
            "format",
        ):
            value = getattr(part, key, None)
            if value is not None:
                part_dict[key] = value

    part_type = part_dict.get("type")
    if not part_type:
        return None

    if part_type == "image":
        image_url = part_dict.get("image_url")
        if isinstance(image_url, dict):
            url = image_url.get("url", "")
            if isinstance(url, str) and url and not url.startswith("/"):
                image_url = {"url": file_url_builder(group_id, url)}
        elif isinstance(image_url, str) and image_url and not image_url.startswith(
            "/",
        ):
            image_url = {"url": file_url_builder(group_id, image_url)}
        part_dict["image_url"] = image_url

    if part_type == "file":
        file_url = part_dict.get("file_url")
        if isinstance(file_url, str) and file_url and not file_url.startswith("/"):
            part_dict["file_url"] = file_url_builder(group_id, file_url)

    return part_dict


class GroupTranscriptCollector:
    """Collect public transcript messages from SSE chunks."""

    def __init__(self, group_id: str, file_url_builder) -> None:
        self.group_id = group_id
        self._file_url_builder = file_url_builder
        self._messages: list[dict[str, Any]] = []
        self._active: dict[str, dict[str, Any]] = {}

    def add_user_message(self, request_input: list[dict[str, Any]]) -> None:
        """Append the user message for the current turn."""
        if not request_input:
            return

        first = request_input[0]
        content = first.get("content") or []
        content_parts = []
        for part in content:
            converted = _content_part_to_dict(
                part,
                group_id=self.group_id,
                file_url_builder=self._file_url_builder,
            )
            if converted is not None:
                content_parts.append(converted)

        self._messages.append(
            {
                "id": str(uuid.uuid4()),
                "object": "message",
                "type": "message",
                "status": "completed",
                "role": "user",
                "content": content_parts,
                "metadata": {"group_id": self.group_id},
            },
        )

    def _start_message(self, event: dict[str, Any]) -> None:
        msg_id = str(event.get("id") or uuid.uuid4())
        self._active[msg_id] = {
            "id": msg_id,
            "object": "message",
            "type": event.get("type", "message"),
            "status": "completed",
            "role": event.get("role", "assistant"),
            "content": [],
            "metadata": flatten_metadata(event.get("metadata"), self.group_id),
        }

    def _append_content(self, event: dict[str, Any]) -> None:
        msg_id = str(event.get("msg_id") or "")
        if not msg_id:
            return
        message = self._active.get(msg_id)
        if message is None:
            return

        event_type = event.get("type")
        if event_type == "text":
            text = str(event.get("text") or "")
            if (
                message["content"]
                and message["content"][-1].get("type") == "text"
            ):
                message["content"][-1]["text"] += text
            else:
                message["content"].append({"type": "text", "text": text})
        elif event_type == "data":
            message["content"].append(
                {
                    "type": "data",
                    "delta": False,
                    "data": event.get("data") or {},
                },
            )

    def _complete_message(self, event: dict[str, Any]) -> None:
        msg_id = str(event.get("id") or "")
        if not msg_id:
            return
        message = self._active.pop(msg_id, None)
        if message is None:
            return
        if message["content"] or message["type"] != "message":
            self._messages.append(message)

    def consume_sse_chunk(self, chunk: str) -> None:
        """Update transcript state from a SSE chunk."""
        for line in chunk.splitlines():
            if not line.startswith("data: "):
                continue
            raw = line[6:].strip()
            if not raw or raw == "[DONE]":
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if not isinstance(event, dict):
                continue

            if event.get("object") == "message":
                if event.get("status") == "in_progress":
                    self._start_message(event)
                elif event.get("status") == "completed":
                    self._complete_message(event)
            elif event.get("object") == "content":
                self._append_content(event)

    def finalize(self) -> list[dict[str, Any]]:
        """Finalize and return collected messages."""
        for message in list(self._active.values()):
            if message["content"] or message["type"] != "message":
                self._messages.append(message)
        self._active.clear()
        return list(self._messages)
