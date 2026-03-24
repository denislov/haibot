# -*- coding: utf-8 -*-
"""Runtime APIs for group chat sessions."""
from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi import Path as PathParam
from starlette.responses import FileResponse, StreamingResponse

from ...config import load_config
from ..group_chat.coordinator import GroupChatCoordinator
from ..group_chat.models import GroupChatStreamRequest
from ..runner.models import ChatSpec

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/group-chats", tags=["group-chat-runtime"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def _safe_filename(name: str) -> str:
    return Path(name or "file").name.replace("/", "_").replace("\\", "_")


def _get_group_chat_manager(request: Request):
    manager = getattr(request.app.state, "group_chat_manager", None)
    if manager is None:
        raise HTTPException(
            status_code=500,
            detail="GroupChatManager not initialized",
        )
    return manager


async def _get_runtime(request: Request, group_id: str):
    manager = _get_group_chat_manager(request)
    try:
        return await manager.get_runtime(group_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/{group_id}/chats",
    response_model=list[ChatSpec],
    summary="List group chat sessions",
)
async def list_group_chat_sessions(
    request: Request,
    group_id: str = PathParam(...),
) -> list[ChatSpec]:
    runtime = await _get_runtime(request, group_id)
    return await runtime.list_chats()


@router.post(
    "/{group_id}/chats",
    response_model=ChatSpec,
    summary="Create group chat session",
)
async def create_group_chat_session(
    request: Request,
    spec: ChatSpec,
    group_id: str = PathParam(...),
) -> ChatSpec:
    runtime = await _get_runtime(request, group_id)
    created = ChatSpec(
        id=str(uuid.uuid4()),
        name=spec.name,
        session_id=spec.session_id,
        user_id=spec.user_id,
        channel=spec.channel,
        meta={**spec.meta, "group_id": group_id},
    )
    return await runtime.create_chat(created)


@router.get(
    "/{group_id}/chats/{chat_id}",
    summary="Get group chat history",
)
async def get_group_chat_history(
    request: Request,
    group_id: str = PathParam(...),
    chat_id: str = PathParam(...),
) -> dict:
    runtime = await _get_runtime(request, group_id)
    try:
        return await runtime.get_history(chat_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put(
    "/{group_id}/chats/{chat_id}",
    response_model=ChatSpec,
    summary="Update group chat session",
)
async def update_group_chat_session(
    request: Request,
    spec: ChatSpec,
    group_id: str = PathParam(...),
    chat_id: str = PathParam(...),
) -> ChatSpec:
    if spec.id != chat_id:
        raise HTTPException(status_code=400, detail="chat_id mismatch")

    runtime = await _get_runtime(request, group_id)
    existing = await runtime.get_chat(chat_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return await runtime.update_chat(spec)


@router.delete(
    "/{group_id}/chats/{chat_id}",
    response_model=dict,
    summary="Delete group chat session",
)
async def delete_group_chat_session(
    request: Request,
    group_id: str = PathParam(...),
    chat_id: str = PathParam(...),
) -> dict:
    runtime = await _get_runtime(request, group_id)
    deleted = await runtime.delete_chat(chat_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"deleted": True}


@router.post(
    "/{group_id}/stream",
    summary="Stream group chat response",
)
async def post_group_chat_stream(
    request: Request,
    body: GroupChatStreamRequest,
    group_id: str = PathParam(...),
) -> StreamingResponse:
    if body.regenerate:
        raise HTTPException(
            status_code=400,
            detail="Group chat regenerate is not supported yet",
        )

    config = load_config()
    group_config = config.group_chats.get(group_id)
    if group_config is None:
        raise HTTPException(status_code=404, detail="Group chat not found")

    runtime = await _get_runtime(request, group_id)
    chat = await runtime.get_chat(body.chat_id)
    if chat is None:
        title = "New Chat"
        for item in body.input:
            for content in item.get("content") or []:
                if content.get("type") == "text":
                    title = str(content.get("text") or "")[:20] or title
                    break
            break
        chat = await runtime.create_chat(
            ChatSpec(
                id=body.chat_id,
                name=title,
                session_id=body.session_id,
                user_id=body.user_id,
                channel="console",
                meta={"group_id": group_id},
            ),
        )

    if body.reconnect:
        queue = await runtime.task_tracker.attach(chat.id)
        if queue is None:
            raise HTTPException(
                status_code=404,
                detail="No running group chat for this session",
            )
    else:
        coordinator = GroupChatCoordinator()
        queue, _ = await runtime.task_tracker.attach_or_start(
            chat.id,
            body,
            lambda payload: coordinator.stream_turn(
                request,
                runtime,
                group_config,
                payload,
            ),
        )

    async def event_generator() -> AsyncGenerator[str, None]:
        stream_it = runtime.task_tracker.stream_from_queue(queue, chat.id)
        try:
            async for event_data in stream_it:
                yield event_data
        except Exception as exc:
            logger.exception("Group chat stream error")
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            await stream_it.aclose()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post(
    "/{group_id}/stop",
    response_model=dict,
    summary="Stop running group chat",
)
async def post_group_chat_stop(
    request: Request,
    body: dict,
    group_id: str = PathParam(...),
) -> dict:
    chat_id = str(body.get("chat_id") or "").strip()
    if not chat_id:
        raise HTTPException(status_code=400, detail="chat_id required")
    runtime = await _get_runtime(request, group_id)
    stopped = await runtime.task_tracker.request_stop(chat_id)
    return {"stopped": stopped}


@router.post(
    "/{group_id}/upload",
    response_model=dict,
    summary="Upload file for group chat",
)
async def post_group_chat_upload(
    request: Request,
    file: UploadFile = File(...),
    group_id: str = PathParam(...),
) -> dict:
    runtime = await _get_runtime(request, group_id)
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail="File too large (max 10 MB)",
        )
    safe_name = _safe_filename(file.filename or "file")
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"
    (runtime.media_dir / stored_name).write_bytes(data)
    return {
        "url": stored_name,
        "file_name": safe_name,
        "size": len(data),
    }


@router.get(
    "/{group_id}/files/{filename}",
    summary="Serve uploaded group chat file",
)
async def get_group_chat_file(
    request: Request,
    group_id: str = PathParam(...),
    filename: str = PathParam(...),
):
    if "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    runtime = await _get_runtime(request, group_id)
    path = (runtime.media_dir / filename).resolve()
    try:
        path.relative_to(runtime.media_dir)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found") from None
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path, filename=filename)
