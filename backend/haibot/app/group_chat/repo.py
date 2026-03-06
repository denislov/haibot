# -*- coding: utf-8 -*-
import json
import logging
from pathlib import Path
from typing import List, Optional

from .models import GroupChatConfig

logger = logging.getLogger(__name__)


class GroupChatRepo:
    """Persists GroupChatConfig objects to a single JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def _load(self) -> dict[str, dict]:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _dump(self, data: dict[str, dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def list(self) -> List[GroupChatConfig]:
        return [GroupChatConfig.model_validate(v) for v in self._load().values()]

    def get(self, group_id: str) -> Optional[GroupChatConfig]:
        data = self._load()
        if group_id not in data:
            return None
        return GroupChatConfig.model_validate(data[group_id])

    def save(self, config: GroupChatConfig) -> GroupChatConfig:
        data = self._load()
        data[config.id] = config.model_dump(mode="json")
        self._dump(data)
        return config

    def delete(self, group_id: str) -> bool:
        data = self._load()
        if group_id not in data:
            return False
        del data[group_id]
        self._dump(data)
        return True
