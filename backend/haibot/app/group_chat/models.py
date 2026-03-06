# -*- coding: utf-8 -*-
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class GroupChatConfig(BaseModel):
    id: str = Field(..., description="Unique group chat slug")
    name: str = Field(..., description="Display name")
    host_agent_id: str = Field(..., description="Agent ID of the host/moderator")
    participant_agent_ids: list[str] = Field(
        default_factory=list,
        description="Ordered list of participant agent IDs",
    )
    max_rounds: int = Field(default=10, ge=1, description="Max host<->participant loop iterations")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC ISO 8601 timestamp of creation",
    )
