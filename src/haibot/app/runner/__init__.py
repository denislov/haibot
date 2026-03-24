# -*- coding: utf-8 -*-
"""Runner module exports.

Keep this package init lightweight. Heavy modules such as ``runner`` and
``api`` are imported lazily so utility modules can depend on
``haibot.app.runner.manager`` without dragging in the full application stack.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .api import router
    from .manager import ChatManager
    from .models import ChatHistory, ChatSpec, ChatsFile
    from .repo import BaseChatRepository, JsonChatRepository
    from .runner import AgentRunner


__all__ = [
    "AgentRunner",
    "ChatManager",
    "router",
    "ChatSpec",
    "ChatHistory",
    "ChatsFile",
    "BaseChatRepository",
    "JsonChatRepository",
]


def __getattr__(name: str):
    if name == "AgentRunner":
        from .runner import AgentRunner

        return AgentRunner
    if name == "router":
        from .api import router

        return router
    if name == "ChatManager":
        from .manager import ChatManager

        return ChatManager
    if name in {"ChatSpec", "ChatHistory", "ChatsFile"}:
        from .models import ChatHistory, ChatSpec, ChatsFile

        return {
            "ChatSpec": ChatSpec,
            "ChatHistory": ChatHistory,
            "ChatsFile": ChatsFile,
        }[name]
    if name in {"BaseChatRepository", "JsonChatRepository"}:
        from .repo import BaseChatRepository, JsonChatRepository

        return {
            "BaseChatRepository": BaseChatRepository,
            "JsonChatRepository": JsonChatRepository,
        }[name]
    raise AttributeError(name)
