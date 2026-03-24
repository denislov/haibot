# -*- coding: utf-8 -*-
"""Console APIs: push messages, chat, and file upload for chat."""
from __future__ import annotations

import json
import logging
import re
import uuid
from pathlib import Path
from typing import AsyncGenerator, Union

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from starlette.responses import FileResponse, StreamingResponse

from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest
from ..agent_context import get_agent_for_request


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/console", tags=["console"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def _safe_filename(name: str) -> str:
    """Safe basename, alphanumeric/./-/_, max 200 chars."""
    base = Path(name).name if name else "file"
    return re.sub(r"[^\w.\-]", "_", base)[:200] or "file"


def _extract_session_and_payload(request_data: Union[AgentRequest, dict]):
    """Extract run_key (ChatSpec.id), session_id, and native payload.

    run_key must be ChatSpec.id (chat_id) so it matches list_chats/get_chat.
    """
    if isinstance(request_data, AgentRequest):
        # Use getattr to avoid AttributeError if fields are missing in some versions
        channel_id = getattr(request_data, "channel", None)
        sender_id = getattr(request_data, "user_id", "default")
        session_id = getattr(request_data, "session_id", "default")
        metadata = getattr(request_data, "metadata", {})

        # Pydantic V2 extra fields are in model_extra
        if hasattr(request_data, "model_extra") and request_data.model_extra:
            extra = request_data.model_extra
            if channel_id is None:
                channel_id = extra.get("channel")
            if not metadata:
                metadata = extra.get("metadata", {})

        channel_id = channel_id or "console"
        content_parts = (
            list(request_data.input[0].content) if request_data.input else []
        )
    else:
        channel_id = request_data.get("channel", "console")
        sender_id = request_data.get("user_id", "default")
        session_id = request_data.get("session_id", "default")
        metadata = request_data.get("metadata", {})
        input_data = request_data.get("input", [])
        content_parts = []
        for content_part in input_data:
            if hasattr(content_part, "content"):
                content_parts.extend(list(content_part.content or []))
            elif isinstance(content_part, dict) and "content" in content_part:
                content_parts.extend(content_part["content"] or [])

    native_payload = {
        "channel_id": channel_id,
        "sender_id": sender_id,
        "content_parts": content_parts,
        "meta": {
            "session_id": session_id,
            "user_id": sender_id,
            **metadata,
        },
    }
    return native_payload


@router.post(
    "/chat",
    status_code=200,
    summary="Chat with console (streaming response)",
    description="Agent API Request Format. See runtime.agentscope.io. "
    "Use body.reconnect=true to attach to a running stream.",
)
async def post_console_chat(
    request_data: Union[AgentRequest, dict],
    request: Request,
) -> StreamingResponse:
    """Stream agent response. Run continues in background after disconnect.
    Stop via POST /console/chat/stop. Reconnect with body.reconnect=true.
    """
    workspace = await get_agent_for_request(request)
    console_channel = await workspace.channel_manager.get_channel("console")
    if console_channel is None:
        raise HTTPException(
            status_code=503,
            detail="Channel Console not found",
        )
    try:
        native_payload = _extract_session_and_payload(request_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    session_id = console_channel.resolve_session_id(
        sender_id=native_payload["sender_id"],
        channel_meta=native_payload["meta"],
    )
    name = "New Chat"
    if len(native_payload["content_parts"]) > 0:
        content = native_payload["content_parts"][0]
        if content:
            name = getattr(content, "text", "")[:10]
            if not name and isinstance(content, dict):
                name = content.get("text", "")[:10]
        else:
            name = "Media Message"
    chat = await workspace.chat_manager.get_or_create_chat(
        session_id,
        native_payload["sender_id"],
        native_payload["channel_id"],
        name=name,
    )
    tracker = workspace.task_tracker

    is_reconnect = False
    if isinstance(request_data, dict):
        is_reconnect = request_data.get("reconnect") is True
    else:
        is_reconnect = getattr(request_data, "reconnect", False) is True
        if not is_reconnect and hasattr(request_data, "model_extra") and request_data.model_extra:
            is_reconnect = request_data.model_extra.get("reconnect") is True

    if is_reconnect:
        queue = await tracker.attach(chat.id)
        if queue is None:
            raise HTTPException(
                status_code=404,
                detail="No running chat for this session",
            )
    else:
        # ── Regenerate: truncate memory to last user message ──
        is_regenerate = False
        if isinstance(request_data, dict):
            is_regenerate = request_data.get("regenerate") is True
        else:
            is_regenerate = getattr(request_data, "regenerate", False) is True
            if (
                not is_regenerate
                and hasattr(request_data, "model_extra")
                and request_data.model_extra
            ):
                is_regenerate = (
                    request_data.model_extra.get("regenerate") is True
                )

        if is_regenerate:
            try:
                state = (
                    await workspace.runner.session.get_session_state_dict(
                        session_id, native_payload["sender_id"]
                    )
                )
                memory = state.get("agent", {}).get("memory", {})
                content_list = memory.get("content", [])
                last_user_idx = None
                for i in range(len(content_list) - 1, -1, -1):
                    if content_list[i].get("role") == "user":
                        last_user_idx = i
                        break
                if last_user_idx is not None:
                    memory["content"] = content_list[: last_user_idx]
                    await workspace.runner.session.update_session_state(
                        session_id,
                        "agent.memory",
                        memory,
                        user_id=native_payload["sender_id"],
                    )
            except Exception:
                logger.warning(
                    "Failed to truncate memory for regenerate",
                    exc_info=True,
                )

        queue, _ = await tracker.attach_or_start(
            chat.id,
            native_payload,
            console_channel.stream_one,
        )

    async def event_generator() -> AsyncGenerator[str, None]:
        # Hold iterator so finally can aclose(); guarantees stream_from_queue's
        # finally (detach_subscriber) on client abort / generator teardown.
        stream_it = tracker.stream_from_queue(queue, chat.id)
        try:
            try:
                async for event_data in stream_it:
                    yield event_data
            except Exception as e:
                logger.exception("Console chat stream error")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
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
    "/chat/stop",
    status_code=200,
    summary="Stop running console chat",
)
async def post_console_chat_stop(
    request: Request,
    chat_id: str = Query(..., description="Chat id (ChatSpec.id) to stop"),
) -> dict:
    """Stop the running chat. Only stops when called."""
    workspace = await get_agent_for_request(request)
    stopped = await workspace.task_tracker.request_stop(chat_id)
    return {"stopped": stopped}


@router.post("/upload", response_model=dict, summary="Upload file for chat")
async def post_console_upload(
    request: Request,
    file: UploadFile = File(..., description="File to attach"),
) -> dict:
    """Save to console channel media_dir."""

    workspace = await get_agent_for_request(request)
    console_channel = await workspace.channel_manager.get_channel("console")
    if console_channel is None:
        raise HTTPException(
            status_code=503,
            detail="Channel Console not found",
        )
    media_dir = console_channel.media_dir
    media_dir.mkdir(parents=True, exist_ok=True)
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail="File too large (max "
            f"{MAX_UPLOAD_BYTES // (1024 * 1024)} MB)",
        )
    safe_name = _safe_filename(file.filename or "file")
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"
    (media_dir / stored_name).write_bytes(data)
    return {
        "url": stored_name,
        "file_name": safe_name,
        "size": len(data),
    }


@router.get("/files/{agent_id}/{filename}", summary="Serve uploaded chat file")
async def get_console_file(
    request: Request,
    agent_id: str,
    filename: str,
):
    """Serve file from console channel media_dir."""

    if "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    workspace = await get_agent_for_request(request, agent_id)
    if workspace.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Not found")
    console_channel = await workspace.channel_manager.get_channel("console")
    if console_channel is None:
        raise HTTPException(
            status_code=503,
            detail="Channel Console not found",
        )
    media_dir = console_channel.media_dir
    path = (media_dir / filename).resolve()
    try:
        path.relative_to(media_dir)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found") from None
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path, filename=filename)


@router.get("/push-messages")
async def get_push_messages(
    session_id: str | None = Query(None, description="Optional session id"),
):
    """
    Return pending push messages. Without session_id: recent messages
    (all sessions, last 60s), not consumed so every tab sees them.
    """
    from ..console_push_store import get_recent, take

    if session_id:
        messages = await take(session_id)
    else:
        messages = await get_recent()
    return {"messages": messages}
