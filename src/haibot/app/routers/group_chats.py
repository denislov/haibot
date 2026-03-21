# -*- coding: utf-8 -*-
"""Group chat CRUD API."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Body, HTTPException

from ...config import load_config, save_config, GroupChatConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/group-chats", tags=["group-chats"])


@router.get(
    "",
    response_model=list[GroupChatConfig],
    summary="List group chats",
)
async def list_group_chats() -> list[GroupChatConfig]:
    """Return every configured group chat."""
    config = load_config()
    return list(config.group_chats.values())


@router.post(
    "",
    response_model=GroupChatConfig,
    status_code=201,
    summary="Create group chat",
)
async def create_group_chat(
    gc: GroupChatConfig = Body(...),
) -> GroupChatConfig:
    """Create a new group chat."""
    config = load_config()
    if gc.id in config.group_chats:
        raise HTTPException(
            status_code=409,
            detail=f"Group chat '{gc.id}' already exists",
        )
    if not gc.created_at:
        gc.created_at = datetime.now(timezone.utc).isoformat()
    config.group_chats[gc.id] = gc
    save_config(config)
    return gc


@router.put(
    "/{gc_id}",
    response_model=GroupChatConfig,
    summary="Update group chat",
)
async def update_group_chat(
    gc_id: str,
    gc: GroupChatConfig = Body(...),
) -> GroupChatConfig:
    """Update an existing group chat."""
    config = load_config()
    if gc_id not in config.group_chats:
        raise HTTPException(
            status_code=404,
            detail=f"Group chat '{gc_id}' not found",
        )
    gc.id = gc_id  # ensure path and body match
    config.group_chats[gc_id] = gc
    save_config(config)
    return gc


@router.delete(
    "/{gc_id}",
    summary="Delete group chat",
)
async def delete_group_chat(gc_id: str) -> dict:
    """Delete a group chat."""
    config = load_config()
    if gc_id not in config.group_chats:
        raise HTTPException(
            status_code=404,
            detail=f"Group chat '{gc_id}' not found",
        )
    del config.group_chats[gc_id]
    save_config(config)
    return {"deleted": True}
