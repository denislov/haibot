# -*- coding: utf-8 -*-
"""Runtime storage for a single group chat."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..runner.manager import ChatManager
from ..runner.models import ChatSpec
from ..runner.repo.json_repo import JsonChatRepository
from ..runner.session import SafeJSONSession
from ..runner.task_tracker import TaskTracker


class GroupChatRuntime:
    """Per-group runtime with isolated chat registry and sessions."""

    def __init__(self, group_id: str, base_dir: Path) -> None:
        self.group_id = group_id
        self.base_dir = base_dir.expanduser()
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.chat_manager = ChatManager(
            repo=JsonChatRepository(self.base_dir / "chats.json"),
        )
        self.session = SafeJSONSession(
            save_dir=str(self.base_dir / "sessions"),
        )
        self.task_tracker = TaskTracker()

        self.media_dir = self.base_dir / "media"
        self.media_dir.mkdir(parents=True, exist_ok=True)

    def _transcript_path(self, session_id: str, user_id: str) -> Path:
        """Return transcript storage path for the public group session."""
        # pylint: disable=protected-access
        return Path(self.session._get_save_path(session_id, user_id))

    async def list_chats(self) -> list[ChatSpec]:
        """List group chat sessions with runtime status."""
        chats = await self.chat_manager.list_chats()
        result = []
        for spec in chats:
            status = await self.task_tracker.get_status(spec.id)
            result.append(spec.model_copy(update={"status": status}))
        return result

    async def get_chat(self, chat_id: str) -> ChatSpec | None:
        """Return chat spec by id."""
        return await self.chat_manager.get_chat(chat_id)

    async def create_chat(self, spec: ChatSpec) -> ChatSpec:
        """Persist a new group-scoped chat."""
        spec.meta = {**spec.meta, "group_id": self.group_id}
        return await self.chat_manager.create_chat(spec)

    async def update_chat(self, spec: ChatSpec) -> ChatSpec:
        """Update a group-scoped chat."""
        spec.meta = {**spec.meta, "group_id": self.group_id}
        return await self.chat_manager.update_chat(spec)

    async def delete_chat(self, chat_id: str) -> bool:
        """Delete a group-scoped chat."""
        return await self.chat_manager.delete_chats([chat_id])

    async def append_transcript_messages(
        self,
        session_id: str,
        user_id: str,
        messages: list[dict[str, Any]],
    ) -> None:
        """Append messages to the persisted public transcript."""
        path = self._transcript_path(session_id, user_id)
        if path.exists():
            state = json.loads(path.read_text(encoding="utf-8"))
        else:
            state = {}
        existing = state.get("group", {}).get("messages", [])
        existing.extend(messages)
        state.setdefault("group", {})["messages"] = existing
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(state, ensure_ascii=False),
            encoding="utf-8",
        )

    async def get_history(self, chat_id: str) -> dict[str, Any]:
        """Load history and current runtime status."""
        spec = await self.chat_manager.get_chat(chat_id)
        if spec is None:
            raise ValueError(f"Chat not found: {chat_id}")

        path = self._transcript_path(spec.session_id, spec.user_id)
        if path.exists():
            state = json.loads(path.read_text(encoding="utf-8"))
        else:
            state = {}
        status = await self.task_tracker.get_status(spec.id)
        raw_messages = state.get("group", {}).get("messages", [])
        return {"messages": raw_messages, "status": status}
