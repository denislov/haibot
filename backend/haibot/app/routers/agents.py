# -*- coding: utf-8 -*-
"""API routes for agent management.

Provides CRUD operations for agents. Each agent has its own workspace
directory under WORKING_DIR/workspace/{agent_id}/ containing markdown
configuration files (AGENTS.md, SOUL.md, PROFILE.md, MEMORY.md).
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Body, HTTPException, Path as PathParam
from pydantic import BaseModel, Field

from ...constant import WORKING_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])

# Files that every agent workspace should contain
AGENT_FILES = ["AGENTS.md", "SOUL.md", "PROFILE.md", "MEMORY.md"]
# Additional file only for the main agent
MAIN_ONLY_FILES = ["HEARTBEAT.md"]
# Default md_files source directory for template content
MD_FILES_DIR = Path(__file__).resolve().parents[2] / "agents" / "md_files"

WORKSPACE_DIR = WORKING_DIR / "workspace"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class AgentInfo(BaseModel):
    """Agent information for API responses."""

    id: str = Field(..., description="Agent identifier (directory name)")
    name: str = Field(..., description="Display name")
    description: str = Field(default="", description="Agent description")
    is_main: bool = Field(..., description="Whether this is the main agent")
    files: List[str] = Field(
        default_factory=list, description="List of workspace files"
    )
    created_at: str = Field(
        default="", description="Creation timestamp (ISO 8601)"
    )


class CreateAgentRequest(BaseModel):
    """Request body for creating a new agent."""

    id: str = Field(
        ...,
        description="Agent ID (lowercase, alphanumeric, hyphens, underscores)",
        pattern=r"^[a-z0-9][a-z0-9_-]*$",
    )
    name: str = Field(..., description="Display name")
    description: str = Field(default="", description="Agent description")


class UpdateAgentRequest(BaseModel):
    """Request body for updating an agent's metadata."""

    name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, description="Agent description")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_META_FILE = ".agent_meta.json"


def _ensure_workspace():
    """Ensure the workspace directory structure exists."""
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


def _get_agent_dir(agent_id: str) -> Path:
    return WORKSPACE_DIR / agent_id


def _read_meta(agent_dir: Path) -> dict:
    """Read agent metadata from .agent_meta.json."""
    import json

    meta_file = agent_dir / _META_FILE
    if meta_file.exists():
        try:
            return json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _write_meta(agent_dir: Path, meta: dict):
    """Write agent metadata to .agent_meta.json."""
    import json

    meta_file = agent_dir / _META_FILE
    meta_file.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _build_agent_info(agent_id: str) -> AgentInfo:
    """Build AgentInfo from an agent workspace directory."""
    agent_dir = _get_agent_dir(agent_id)
    if not agent_dir.is_dir():
        raise HTTPException(404, detail=f"Agent '{agent_id}' not found")

    meta = _read_meta(agent_dir)
    files = sorted(
        f.name
        for f in agent_dir.iterdir()
        if f.is_file() and not f.name.startswith(".")
    )

    return AgentInfo(
        id=agent_id,
        name=meta.get("name", agent_id),
        description=meta.get("description", ""),
        is_main=(agent_id == "main"),
        files=files,
        created_at=meta.get(
            "created_at",
            datetime.fromtimestamp(
                agent_dir.stat().st_ctime, tz=timezone.utc
            ).isoformat(),
        ),
    )


def _get_template_content(filename: str, language: str = "zh") -> str:
    """Get template content for a workspace file."""
    template = MD_FILES_DIR / language / filename
    if template.exists():
        return template.read_text(encoding="utf-8")
    # Fallback to English
    template_en = MD_FILES_DIR / "en" / filename
    if template_en.exists():
        return template_en.read_text(encoding="utf-8")
    return f"# {filename}\n"


def ensure_main_workspace():
    """Ensure the main workspace exists.

    If WORKING_DIR has root-level md files but no workspace/main/,
    migrate them. Otherwise, create from templates.
    """
    _ensure_workspace()
    main_dir = _get_agent_dir("main")

    if main_dir.is_dir():
        return  # Already exists

    main_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Creating main agent workspace at %s", main_dir)

    # Try migrating from root WORKING_DIR
    migrated = False
    for filename in AGENT_FILES + MAIN_ONLY_FILES:
        src = WORKING_DIR / filename
        if src.exists():
            shutil.copy2(src, main_dir / filename)
            migrated = True
            logger.info("Migrated %s to workspace/main/", filename)

    if not migrated:
        # Create from templates
        for filename in AGENT_FILES + MAIN_ONLY_FILES:
            content = _get_template_content(filename)
            (main_dir / filename).write_text(content, encoding="utf-8")

    # Write metadata
    _write_meta(
        main_dir,
        {
            "name": "Main",
            "description": "Default main agent",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=List[AgentInfo],
    summary="List all agents",
)
async def list_agents() -> List[AgentInfo]:
    """Get list of all configured agents."""
    ensure_main_workspace()
    agents = []
    for d in sorted(WORKSPACE_DIR.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            try:
                agents.append(_build_agent_info(d.name))
            except Exception as e:
                logger.warning("Skipping agent dir %s: %s", d.name, e)
    return agents


@router.post(
    "",
    response_model=AgentInfo,
    summary="Create a new agent",
    status_code=201,
)
async def create_agent(req: CreateAgentRequest = Body(...)) -> AgentInfo:
    """Create a new agent with workspace directory and template files."""
    _ensure_workspace()

    agent_dir = _get_agent_dir(req.id)
    if agent_dir.exists():
        raise HTTPException(
            400,
            detail=f"Agent '{req.id}' already exists",
        )

    agent_dir.mkdir(parents=True, exist_ok=True)

    # Create workspace files from templates
    for filename in AGENT_FILES:
        content = _get_template_content(filename)
        (agent_dir / filename).write_text(content, encoding="utf-8")

    # Write metadata
    _write_meta(
        agent_dir,
        {
            "name": req.name,
            "description": req.description,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    return _build_agent_info(req.id)


@router.get(
    "/{agent_id}",
    response_model=AgentInfo,
    summary="Get agent details",
)
async def get_agent(
    agent_id: str = PathParam(...),
) -> AgentInfo:
    """Get details of a specific agent."""
    return _build_agent_info(agent_id)


@router.put(
    "/{agent_id}",
    response_model=AgentInfo,
    summary="Update agent metadata",
)
async def update_agent(
    agent_id: str = PathParam(...),
    updates: UpdateAgentRequest = Body(...),
) -> AgentInfo:
    """Update an agent's display name and description."""
    agent_dir = _get_agent_dir(agent_id)
    if not agent_dir.is_dir():
        raise HTTPException(404, detail=f"Agent '{agent_id}' not found")

    meta = _read_meta(agent_dir)
    if updates.name is not None:
        meta["name"] = updates.name
    if updates.description is not None:
        meta["description"] = updates.description
    _write_meta(agent_dir, meta)

    return _build_agent_info(agent_id)


@router.delete(
    "/{agent_id}",
    response_model=dict,
    summary="Delete an agent",
)
async def delete_agent(
    agent_id: str = PathParam(...),
) -> dict:
    """Delete an agent and its workspace directory."""
    if agent_id == "main":
        raise HTTPException(
            400,
            detail="Cannot delete the main agent",
        )

    agent_dir = _get_agent_dir(agent_id)
    if not agent_dir.is_dir():
        raise HTTPException(404, detail=f"Agent '{agent_id}' not found")

    shutil.rmtree(agent_dir)
    return {"message": f"Agent '{agent_id}' deleted successfully"}


# ---------------------------------------------------------------------------
# Workspace file endpoints
# ---------------------------------------------------------------------------

ALLOWED_FILES = {"AGENTS.md", "SOUL.md", "PROFILE.md", "MEMORY.md",
                 "HEARTBEAT.md", "BOOTSTRAP.md"}


@router.get(
    "/{agent_id}/files",
    response_model=List[dict],
    summary="List agent workspace files",
)
async def list_agent_files(
    agent_id: str = PathParam(...),
) -> List[dict]:
    """List files in an agent's workspace directory."""
    agent_dir = _get_agent_dir(agent_id)
    if not agent_dir.is_dir():
        raise HTTPException(404, detail=f"Agent '{agent_id}' not found")

    files = []
    for f in sorted(agent_dir.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
            })
    return files


@router.get(
    "/{agent_id}/files/{filename}",
    response_model=dict,
    summary="Read an agent workspace file",
)
async def read_agent_file(
    agent_id: str = PathParam(...),
    filename: str = PathParam(...),
) -> dict:
    """Read content of a specific file in an agent's workspace."""
    agent_dir = _get_agent_dir(agent_id)
    file_path = agent_dir / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, detail=f"File '{filename}' not found")

    # Security: ensure path stays within agent_dir
    if not file_path.resolve().is_relative_to(agent_dir.resolve()):
        raise HTTPException(400, detail="Invalid file path")

    content = file_path.read_text(encoding="utf-8")
    return {"name": filename, "content": content}


@router.put(
    "/{agent_id}/files/{filename}",
    response_model=dict,
    summary="Write an agent workspace file",
)
async def write_agent_file(
    agent_id: str = PathParam(...),
    filename: str = PathParam(...),
    body: dict = Body(...),
) -> dict:
    """Write content to a specific file in an agent's workspace."""
    if filename not in ALLOWED_FILES:
        raise HTTPException(
            400,
            detail=f"File '{filename}' is not an allowed workspace file",
        )

    agent_dir = _get_agent_dir(agent_id)
    if not agent_dir.is_dir():
        raise HTTPException(404, detail=f"Agent '{agent_id}' not found")

    file_path = agent_dir / filename

    content = body.get("content", "")
    file_path.write_text(content, encoding="utf-8")
    return {"written": True}


# ---------------------------------------------------------------------------
# Skills config endpoints
# ---------------------------------------------------------------------------


class AgentSkillsConfig(BaseModel):
    """Per-agent skills enable/disable flags."""
    skills_config: dict[str, bool] = Field(default_factory=dict)


@router.get(
    "/{agent_id}/skills",
    response_model=AgentSkillsConfig,
    summary="Get per-agent skills config",
)
async def get_agent_skills(
    agent_id: str = PathParam(...),
) -> AgentSkillsConfig:
    """Return skills_config for a specific agent, merged with full skill list."""
    from ...agents.skills_manager import get_agent_skills_config, list_available_skills
    agent_dir = _get_agent_dir(agent_id)
    if not agent_dir.is_dir():
        raise HTTPException(404, detail=f"Agent '{agent_id}' not found")
    skills_config = get_agent_skills_config(workspace_dir=agent_dir)
    all_skills = list_available_skills()
    # Merge: show all skills with their current enabled state (default True)
    merged = {s: skills_config.get(s, True) for s in all_skills}
    return AgentSkillsConfig(skills_config=merged)


@router.put(
    "/{agent_id}/skills",
    response_model=AgentSkillsConfig,
    summary="Update per-agent skills config",
)
async def update_agent_skills(
    agent_id: str = PathParam(...),
    body: AgentSkillsConfig = Body(...),
) -> AgentSkillsConfig:
    """Update skills_config in agent .agent_meta.json."""
    agent_dir = _get_agent_dir(agent_id)
    if not agent_dir.is_dir():
        raise HTTPException(404, detail=f"Agent '{agent_id}' not found")
    meta = _read_meta(agent_dir)
    meta["skills_config"] = body.skills_config
    _write_meta(agent_dir, meta)
    from ...agents.skills_manager import get_agent_skills_config, list_available_skills
    all_skills = list_available_skills()
    updated_config = get_agent_skills_config(workspace_dir=agent_dir)
    merged = {s: updated_config.get(s, True) for s in all_skills}
    return AgentSkillsConfig(skills_config=merged)
