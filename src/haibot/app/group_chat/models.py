# -*- coding: utf-8 -*-
"""Models for group chat runtime."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GroupChatStreamRequest(BaseModel):
    """Request body for group chat streaming."""

    chat_id: str = Field(..., description="Group chat session id")
    session_id: str = Field(..., description="Client session id")
    user_id: str = Field(..., description="User id")
    input: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Agent request input array",
    )
    reconnect: bool = Field(default=False)
    regenerate: bool = Field(default=False)


class DelegationRequest(BaseModel):
    """Reserved model for future host delegation support."""

    agent_id: str
    task: str
