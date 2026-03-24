# -*- coding: utf-8 -*-
"""Manager for group chat runtimes."""
from __future__ import annotations

import asyncio
from pathlib import Path

from ...config import load_config
from ...constant import WORKING_DIR
from .runtime import GroupChatRuntime


class GroupChatManager:
    """Create and cache group chat runtimes."""

    def __init__(self, working_dir: str | Path | None = None) -> None:
        self._working_dir = Path(working_dir or WORKING_DIR).expanduser()
        self._lock = asyncio.Lock()
        self._runtimes: dict[str, GroupChatRuntime] = {}

    async def get_runtime(self, group_id: str) -> GroupChatRuntime:
        """Return runtime for an existing group config."""
        async with self._lock:
            if group_id in self._runtimes:
                return self._runtimes[group_id]

            config = load_config()
            if group_id not in config.group_chats:
                raise ValueError(f"Group chat '{group_id}' not found")

            runtime = GroupChatRuntime(
                group_id=group_id,
                base_dir=self._working_dir / "group_chats" / group_id,
            )
            self._runtimes[group_id] = runtime
            return runtime

    async def stop_all(self) -> None:
        """Stop all active group chat runs."""
        async with self._lock:
            runtimes = list(self._runtimes.values())

        for runtime in runtimes:
            active = await runtime.task_tracker.list_active_tasks()
            for chat_id in active:
                await runtime.task_tracker.request_stop(chat_id)
