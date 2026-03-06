# -*- coding: utf-8 -*-
"""CRUD API for group chat configurations."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi import Path as PathParam

from ...app.group_chat.models import GroupChatConfig
from ...app.group_chat.repo import GroupChatRepo

router = APIRouter(prefix="/group-chats", tags=["group-chats"])


def _get_repo(request: Request) -> GroupChatRepo:
    repo = getattr(request.app.state, "group_chat_repo", None)
    if repo is None:
        raise HTTPException(503, detail="Group chat repo not initialized")
    return repo


@router.get("", response_model=list[GroupChatConfig])
async def list_group_chats(repo: GroupChatRepo = Depends(_get_repo)):
    return repo.list()


@router.post("", response_model=GroupChatConfig, status_code=201)
async def create_group_chat(
    body: GroupChatConfig = Body(...),
    repo: GroupChatRepo = Depends(_get_repo),
):
    if repo.get(body.id) is not None:
        raise HTTPException(400, detail=f"Group chat '{body.id}' already exists")
    body.created_at = datetime.now(timezone.utc).isoformat()
    return repo.save(body)


@router.get("/{group_id}", response_model=GroupChatConfig)
async def get_group_chat(
    group_id: str = PathParam(...),
    repo: GroupChatRepo = Depends(_get_repo),
):
    cfg = repo.get(group_id)
    if cfg is None:
        raise HTTPException(404, detail=f"Group chat '{group_id}' not found")
    return cfg


@router.put("/{group_id}", response_model=GroupChatConfig)
async def update_group_chat(
    group_id: str = PathParam(...),
    body: GroupChatConfig = Body(...),
    repo: GroupChatRepo = Depends(_get_repo),
):
    if repo.get(group_id) is None:
        raise HTTPException(404, detail=f"Group chat '{group_id}' not found")
    body.id = group_id
    return repo.save(body)


@router.delete("/{group_id}", response_model=dict)
async def delete_group_chat(
    group_id: str = PathParam(...),
    repo: GroupChatRepo = Depends(_get_repo),
):
    if not repo.delete(group_id):
        raise HTTPException(404, detail=f"Group chat '{group_id}' not found")
    return {"deleted": True}
