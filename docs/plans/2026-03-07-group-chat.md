# Group Chat Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add group chat to HaiBot — a host agent routes messages to participant agents via `@mention`, with concurrent streaming and per-agent memory/skills isolation.

**Architecture:** `GroupChatOrchestrator` sits inside `AgentRunner.query_handler()`, activated when `metadata.group_id` is present. Each round, the host streams first; `@mention` parsing determines which participants run concurrently via `asyncio.gather`; `stream_merger` multiplexes their event streams into one SSE pipe tagged with `agent_id`. Prerequisites (memory isolation + skills flags) are implemented first as self-contained tasks.

**Tech Stack:** Python 3.12, FastAPI, agentscope ReActAgent + Msg, asyncio, Vue 3 + TypeScript + Pinia, Element Plus

**Tests:** `uv run pytest backend/tests/ -v` — asyncio_mode=auto (no `@pytest.mark.asyncio` needed)

---

## Task 1: Per-Agent Tool Workspace Isolation

**Files:**
- Modify: `backend/haibot/agents/react_agent.py:75-178`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/agents/__init__.py`
- Create: `backend/tests/agents/test_workspace_isolation.py`

**Context:** `HaiBotAgent._create_toolkit()` currently hard-codes `workspace_dir = WORKING_DIR / "workspace" / self._agent_id`. We need it to accept an explicit `workspace_dir` param so the orchestrator can pass it in directly.

**Step 1: Create test file**

```python
# backend/tests/agents/test_workspace_isolation.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_haibot_agent_uses_explicit_workspace_dir(tmp_path):
    """HaiBotAgent should use explicit workspace_dir for tool presets."""
    workspace = tmp_path / "my_agent"
    workspace.mkdir()

    with (
        patch("haibot.agents.react_agent.create_model_and_formatter") as mock_factory,
        patch("haibot.agents.react_agent.ensure_skills_initialized"),
        patch("haibot.agents.react_agent.list_available_skills", return_value=[]),
        patch("haibot.agents.react_agent.build_system_prompt_for_agent", return_value="sys"),
        patch("haibot.agents.react_agent.load_config"),
    ):
        mock_factory.return_value = (MagicMock(), MagicMock())
        from haibot.agents.react_agent import HaiBotAgent
        agent = HaiBotAgent(agent_id="my_agent", workspace_dir=workspace)
        assert agent._workspace_dir == workspace


def test_haibot_agent_defaults_workspace_dir_from_agent_id(tmp_path):
    """Without explicit workspace_dir, should fall back to WORKING_DIR/workspace/agent_id."""
    with (
        patch("haibot.agents.react_agent.create_model_and_formatter") as mock_factory,
        patch("haibot.agents.react_agent.ensure_skills_initialized"),
        patch("haibot.agents.react_agent.list_available_skills", return_value=[]),
        patch("haibot.agents.react_agent.build_system_prompt_for_agent", return_value="sys"),
        patch("haibot.agents.react_agent.load_config"),
        patch("haibot.agents.react_agent.WORKING_DIR", tmp_path),
    ):
        mock_factory.return_value = (MagicMock(), MagicMock())
        from haibot.agents.react_agent import HaiBotAgent
        agent = HaiBotAgent(agent_id="main")
        # Falls back to WORKING_DIR when workspace doesn't exist
        assert agent._workspace_dir in (tmp_path / "workspace" / "main", tmp_path)
```

**Step 2: Run test to confirm failure**

```
uv run pytest backend/tests/agents/test_workspace_isolation.py -v
```
Expected: `FAILED` — `HaiBotAgent.__init__` has no `workspace_dir` param.

**Step 3: Modify `HaiBotAgent.__init__` in `backend/haibot/agents/react_agent.py`**

Add `workspace_dir: Optional[Path] = None` param and store it before toolkit creation:

```python
def __init__(
    self,
    env_context: Optional[str] = None,
    enable_memory_manager: bool = True,
    mcp_clients: Optional[List[Any]] = None,
    memory_manager: MemoryManager | None = None,
    max_iters: int = 50,
    max_input_length: int = 128 * 1024,
    agent_id: str = "main",
    workspace_dir: Optional[Path] = None,   # NEW
):
    self._env_context = env_context
    self._agent_id = agent_id
    self._max_input_length = max_input_length
    self._mcp_clients = mcp_clients or []

    # Resolve workspace_dir: explicit > workspace/agent_id > WORKING_DIR
    if workspace_dir is not None:
        self._workspace_dir = workspace_dir
    else:
        candidate = WORKING_DIR / "workspace" / agent_id
        self._workspace_dir = candidate if candidate.is_dir() else WORKING_DIR

    self._memory_compact_threshold = int(max_input_length * MEMORY_COMPACT_RATIO)
    # ... rest unchanged
```

In `_create_toolkit`, replace the `workspace_dir` local variable computation with `self._workspace_dir`:

```python
def _create_toolkit(self) -> Toolkit:
    toolkit = Toolkit()
    workspace_dir = self._workspace_dir  # use stored value
    toolkit.register_tool_function(execute_shell_command, preset_kwargs={"working_dir": workspace_dir})
    toolkit.register_tool_function(read_file, preset_kwargs={"working_dir": workspace_dir})
    toolkit.register_tool_function(write_file, preset_kwargs={"working_dir": workspace_dir})
    toolkit.register_tool_function(edit_file, preset_kwargs={"working_dir": workspace_dir})
    toolkit.register_tool_function(append_file, preset_kwargs={"working_dir": workspace_dir})
    toolkit.register_tool_function(grep_search, preset_kwargs={"working_dir": workspace_dir})
    toolkit.register_tool_function(glob_search, preset_kwargs={"working_dir": workspace_dir})
    toolkit.register_tool_function(browser_use)
    toolkit.register_tool_function(desktop_screenshot)
    toolkit.register_tool_function(send_file_to_user)
    toolkit.register_tool_function(get_current_time)
    return toolkit
```

**Step 4: Run tests**

```
uv run pytest backend/tests/agents/test_workspace_isolation.py -v
```
Expected: `PASSED`

**Step 5: Commit**

```bash
git add backend/tests/__init__.py backend/tests/agents/__init__.py \
        backend/tests/agents/test_workspace_isolation.py \
        backend/haibot/agents/react_agent.py
git commit -m "feat: add workspace_dir param to HaiBotAgent for tool isolation"
```

---

## Task 2: Per-Agent MemoryManager Isolation

**Files:**
- Modify: `backend/haibot/app/runner/runner.py`
- Create: `backend/tests/app/__init__.py`
- Create: `backend/tests/app/test_memory_isolation.py`

**Context:** `AgentRunner` holds one shared `self.memory_manager`. We extend it to cache a `MemoryManager` per `agent_id`, lazily started on first use, stored in `self._memory_managers: dict[str, MemoryManager]`.

**Step 1: Write test**

```python
# backend/tests/app/test_memory_isolation.py
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


async def test_runner_creates_per_agent_memory_manager(tmp_path):
    """Each agent_id should get its own MemoryManager on first query."""
    with patch("haibot.app.runner.runner.WORKING_DIR", tmp_path):
        workspace = tmp_path / "workspace" / "alice"
        workspace.mkdir(parents=True)

        from haibot.app.runner.runner import AgentRunner
        runner = AgentRunner()
        runner._memory_managers = {}

        mm = await runner._get_or_create_memory_manager("alice")

        assert "alice" in runner._memory_managers
        assert runner._memory_managers["alice"] is mm


async def test_runner_reuses_memory_manager_for_same_agent(tmp_path):
    """Second call for same agent_id returns the cached instance."""
    with patch("haibot.app.runner.runner.WORKING_DIR", tmp_path):
        workspace = tmp_path / "workspace" / "bob"
        workspace.mkdir(parents=True)

        from haibot.app.runner.runner import AgentRunner
        runner = AgentRunner()
        runner._memory_managers = {}

        mm1 = await runner._get_or_create_memory_manager("bob")
        mm2 = await runner._get_or_create_memory_manager("bob")

        assert mm1 is mm2
```

**Step 2: Run test to confirm failure**

```
uv run pytest backend/tests/app/test_memory_isolation.py -v
```
Expected: `FAILED` — `_get_or_create_memory_manager` does not exist.

**Step 3: Modify `backend/haibot/app/runner/runner.py`**

Add `_memory_managers` dict and `_get_or_create_memory_manager` method:

```python
class AgentRunner(Runner):
    def __init__(self) -> None:
        super().__init__()
        self.framework_type = "agentscope"
        self._chat_manager = None
        self._mcp_manager = None
        self.memory_manager: MemoryManager | None = None
        self._memory_managers: dict[str, MemoryManager] = {}  # NEW

    async def _get_or_create_memory_manager(self, agent_id: str) -> MemoryManager:
        """Return a started MemoryManager for the given agent_id, creating if needed."""
        if agent_id in self._memory_managers:
            return self._memory_managers[agent_id]

        workspace_dir = WORKING_DIR / "workspace" / agent_id
        working_dir = str(workspace_dir) if workspace_dir.is_dir() else str(WORKING_DIR)
        mm = MemoryManager(working_dir=working_dir)
        try:
            await mm.start()
        except Exception as e:
            logger.warning("MemoryManager start failed for agent %s: %s", agent_id, e)
        self._memory_managers[agent_id] = mm
        return mm
```

In `query_handler`, replace `memory_manager=self.memory_manager` with:

```python
memory_manager = await self._get_or_create_memory_manager(agent_id)

agent = HaiBotAgent(
    env_context=env_context,
    mcp_clients=mcp_clients,
    memory_manager=memory_manager,
    max_iters=max_iters,
    max_input_length=max_input_length,
    agent_id=agent_id,
)
```

In `init_handler`, keep `self.memory_manager` for backward compat (pre-populate "main"):

```python
async def init_handler(self, *args, **kwargs):
    # ... existing dotenv/session setup ...
    try:
        main_mm = await self._get_or_create_memory_manager("main")
        self.memory_manager = main_mm  # backward compat
    except Exception as e:
        logger.exception(f"MemoryManager start failed: {e}")
```

In `shutdown_handler`, close all cached managers:

```python
async def shutdown_handler(self, *args, **kwargs):
    for agent_id, mm in self._memory_managers.items():
        try:
            await mm.close()
        except Exception as e:
            logger.warning("MemoryManager stop failed for %s: %s", agent_id, e)
    self._memory_managers.clear()
```

**Step 4: Run tests**

```
uv run pytest backend/tests/app/test_memory_isolation.py -v
```
Expected: `PASSED`

**Step 5: Commit**

```bash
git add backend/tests/app/__init__.py backend/tests/app/test_memory_isolation.py \
        backend/haibot/app/runner/runner.py
git commit -m "feat: per-agent MemoryManager isolation in AgentRunner"
```

---

## Task 3: Per-Agent Skills Flags — Backend

**Files:**
- Modify: `backend/haibot/agents/skills_manager.py`
- Modify: `backend/haibot/agents/react_agent.py`
- Modify: `backend/haibot/app/routers/agents.py`
- Create: `backend/tests/agents/test_skills_flags.py`

**Context:** Add `skills_config: dict[str, bool]` to `.agent_meta.json`. Filter `list_available_skills()` output by it in `HaiBotAgent`. Expose GET/PUT `/api/agents/{id}/skills`.

**Step 1: Write tests**

```python
# backend/tests/agents/test_skills_flags.py
import json
import pytest
from pathlib import Path
from unittest.mock import patch


def test_get_agent_skills_config_reads_meta(tmp_path):
    """Should read skills_config from .agent_meta.json."""
    meta = {"name": "Test", "skills_config": {"web_search": False, "code_runner": True}}
    (tmp_path / ".agent_meta.json").write_text(json.dumps(meta))

    with patch("haibot.agents.skills_manager.WORKING_DIR", tmp_path / "wd"):
        from haibot.agents.skills_manager import get_agent_skills_config
        # Pass workspace dir directly
        config = get_agent_skills_config(workspace_dir=tmp_path)
        assert config == {"web_search": False, "code_runner": True}


def test_get_agent_skills_config_missing_meta(tmp_path):
    """Missing .agent_meta.json returns empty dict (all skills enabled)."""
    from haibot.agents.skills_manager import get_agent_skills_config
    config = get_agent_skills_config(workspace_dir=tmp_path)
    assert config == {}


def test_filter_skills_by_config():
    """Skills disabled in config should be excluded from list."""
    from haibot.agents.skills_manager import filter_skills_by_config
    skills = ["web_search", "code_runner", "browser_use"]
    config = {"web_search": False, "browser_use": False}
    result = filter_skills_by_config(skills, config)
    assert result == ["code_runner"]


def test_filter_skills_empty_config_enables_all():
    """Empty config means all skills pass through."""
    from haibot.agents.skills_manager import filter_skills_by_config
    skills = ["web_search", "code_runner"]
    assert filter_skills_by_config(skills, {}) == skills
```

**Step 2: Run test to confirm failure**

```
uv run pytest backend/tests/agents/test_skills_flags.py -v
```
Expected: `FAILED`

**Step 3: Add helpers to `backend/haibot/agents/skills_manager.py`**

Append these two functions to the module (before the end):

```python
def get_agent_skills_config(workspace_dir: Path) -> dict[str, bool]:
    """Read skills_config from agent workspace .agent_meta.json.

    Returns empty dict if file absent or has no skills_config key
    (meaning all skills are enabled by default).
    """
    import json as _json
    meta_file = workspace_dir / ".agent_meta.json"
    if not meta_file.exists():
        return {}
    try:
        data = _json.loads(meta_file.read_text(encoding="utf-8"))
        return dict(data.get("skills_config", {}))
    except Exception:
        return {}


def filter_skills_by_config(
    skill_names: list[str],
    skills_config: dict[str, bool],
) -> list[str]:
    """Return skill_names filtered by skills_config.

    Absent keys default to True (enabled).
    """
    return [s for s in skill_names if skills_config.get(s, True)]
```

**Step 4: Apply filter in `HaiBotAgent._register_skills`**

```python
def _register_skills(self, toolkit: Toolkit) -> None:
    ensure_skills_initialized()
    working_skills_dir = get_working_skills_dir()
    available_skills = list_available_skills()

    # Apply per-agent skills filter
    from .skills_manager import get_agent_skills_config, filter_skills_by_config
    skills_config = get_agent_skills_config(self._workspace_dir)
    available_skills = filter_skills_by_config(available_skills, skills_config)

    for skill_name in available_skills:
        skill_dir = working_skills_dir / skill_name
        if skill_dir.exists():
            try:
                toolkit.register_agent_skill(str(skill_dir))
                logger.debug("Registered skill: %s", skill_name)
            except Exception as e:
                logger.error("Failed to register skill '%s': %s", skill_name, e)
```

**Step 5: Add API endpoints to `backend/haibot/app/routers/agents.py`**

Append to the bottom of the file:

```python
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
async def get_agent_skills(agent_id: str = PathParam(...)) -> AgentSkillsConfig:
    """Return skills_config for a specific agent."""
    from ...agents.skills_manager import get_agent_skills_config, list_available_skills
    agent_dir = _get_agent_dir(agent_id)
    if not agent_dir.is_dir():
        raise HTTPException(404, detail=f"Agent '{agent_id}' not found")
    skills_config = get_agent_skills_config(workspace_dir=agent_dir)
    # Merge with full skill list so frontend sees all skills with defaults
    all_skills = list_available_skills()
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
    return body
```

**Step 6: Run tests**

```
uv run pytest backend/tests/agents/test_skills_flags.py -v
```
Expected: `PASSED`

**Step 7: Commit**

```bash
git add backend/haibot/agents/skills_manager.py \
        backend/haibot/agents/react_agent.py \
        backend/haibot/app/routers/agents.py \
        backend/tests/agents/test_skills_flags.py
git commit -m "feat: per-agent skills flags (skills_config in agent_meta)"
```

---

## Task 4: Per-Agent Skills Flags — Frontend

**Files:**
- Modify: `frontend/src/api/agents.ts` (create if absent)
- Modify: `frontend/src/modules/settings/pages/AgentsSettings.vue`

**Context:** Add a skill toggle section to the agent detail view. No new files needed beyond extending existing components.

**Step 1: Check if `frontend/src/api/agents.ts` exists**

```bash
ls frontend/src/api/
```

**Step 2: Add skills API calls to `frontend/src/api/agents.ts`**

Add at the bottom of the existing file (or create if missing):

```typescript
import api from './index'

// ... existing agent CRUD calls (keep them) ...

export const getAgentSkills = (agentId: string) =>
  api.get<{ skills_config: Record<string, boolean> }>(`/agents/${agentId}/skills`)
    .then(r => r.data)

export const updateAgentSkills = (agentId: string, skillsConfig: Record<string, boolean>) =>
  api.put<{ skills_config: Record<string, boolean> }>(`/agents/${agentId}/skills`, {
    skills_config: skillsConfig,
  }).then(r => r.data)
```

**Step 3: Add skills toggle section to `AgentsSettings.vue`**

In the agent detail panel (where files are listed), add below the files section:

```vue
<!-- Skills config section -->
<div v-if="selectedAgent" class="agent-skills-section">
  <div class="section-title">{{ $t('agents.skills') }}</div>
  <div v-if="agentSkills" class="skills-list">
    <div
      v-for="(enabled, skillName) in agentSkills"
      :key="skillName"
      class="skill-row"
    >
      <span class="skill-name">{{ skillName }}</span>
      <el-switch
        :model-value="enabled"
        @change="(val: boolean) => toggleSkill(skillName, val)"
      />
    </div>
  </div>
</div>
```

In the script section, add:

```typescript
import { getAgentSkills, updateAgentSkills } from '@/api/agents'

const agentSkills = ref<Record<string, boolean> | null>(null)

async function loadAgentSkills(agentId: string) {
  const data = await getAgentSkills(agentId)
  agentSkills.value = data.skills_config
}

async function toggleSkill(skillName: string, enabled: boolean) {
  if (!selectedAgent.value || !agentSkills.value) return
  agentSkills.value[skillName] = enabled
  await updateAgentSkills(selectedAgent.value.id, agentSkills.value)
}

// Call loadAgentSkills(agent.id) when selectedAgent changes
watch(selectedAgent, (agent) => {
  if (agent) loadAgentSkills(agent.id)
  else agentSkills.value = null
})
```

Add i18n key `agents.skills` to `frontend/src/i18n/locales/zh-CN.ts` and `en.ts`.

**Step 4: Commit**

```bash
git add frontend/src/api/agents.ts \
        frontend/src/modules/settings/pages/AgentsSettings.vue \
        frontend/src/i18n/locales/zh-CN.ts \
        frontend/src/i18n/locales/en.ts
git commit -m "feat: per-agent skills flags UI in AgentsSettings"
```

---

## Task 5: Group Chat Data Model + Repo

**Files:**
- Create: `backend/haibot/app/group_chat/__init__.py`
- Create: `backend/haibot/app/group_chat/models.py`
- Create: `backend/haibot/app/group_chat/repo.py`
- Create: `backend/tests/group_chat/__init__.py`
- Create: `backend/tests/group_chat/test_repo.py`

**Step 1: Write tests**

```python
# backend/tests/group_chat/test_repo.py
import pytest
from pathlib import Path
from haibot.app.group_chat.models import GroupChatConfig
from haibot.app.group_chat.repo import GroupChatRepo


def test_create_and_get(tmp_path):
    repo = GroupChatRepo(path=tmp_path / "group_chats.json")
    cfg = GroupChatConfig(
        id="team_alpha",
        name="Team Alpha",
        host_agent_id="main",
        participant_agent_ids=["analyst", "coder"],
    )
    repo.save(cfg)
    result = repo.get("team_alpha")
    assert result is not None
    assert result.name == "Team Alpha"
    assert result.participant_agent_ids == ["analyst", "coder"]


def test_list(tmp_path):
    repo = GroupChatRepo(path=tmp_path / "group_chats.json")
    repo.save(GroupChatConfig(id="g1", name="G1", host_agent_id="main", participant_agent_ids=[]))
    repo.save(GroupChatConfig(id="g2", name="G2", host_agent_id="main", participant_agent_ids=[]))
    assert len(repo.list()) == 2


def test_delete(tmp_path):
    repo = GroupChatRepo(path=tmp_path / "group_chats.json")
    repo.save(GroupChatConfig(id="g1", name="G1", host_agent_id="main", participant_agent_ids=[]))
    assert repo.delete("g1") is True
    assert repo.get("g1") is None


def test_delete_missing_returns_false(tmp_path):
    repo = GroupChatRepo(path=tmp_path / "group_chats.json")
    assert repo.delete("nonexistent") is False


def test_get_missing_returns_none(tmp_path):
    repo = GroupChatRepo(path=tmp_path / "group_chats.json")
    assert repo.get("missing") is None
```

**Step 2: Run test to confirm failure**

```
uv run pytest backend/tests/group_chat/test_repo.py -v
```
Expected: `FAILED` — modules don't exist yet.

**Step 3: Create `backend/haibot/app/group_chat/__init__.py`** (empty)

**Step 4: Create `backend/haibot/app/group_chat/models.py`**

```python
# -*- coding: utf-8 -*-
from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, Field


class GroupChatConfig(BaseModel):
    id: str = Field(..., description="Unique group chat slug")
    name: str = Field(..., description="Display name")
    host_agent_id: str = Field(..., description="Agent ID of the host/moderator")
    participant_agent_ids: List[str] = Field(
        default_factory=list,
        description="Ordered list of participant agent IDs",
    )
    max_rounds: int = Field(default=10, ge=1, description="Max host↔participant loop iterations")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
```

**Step 5: Create `backend/haibot/app/group_chat/repo.py`**

```python
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
```

**Step 6: Run tests**

```
uv run pytest backend/tests/group_chat/test_repo.py -v
```
Expected: `PASSED`

**Step 7: Commit**

```bash
git add backend/haibot/app/group_chat/ \
        backend/tests/group_chat/__init__.py \
        backend/tests/group_chat/test_repo.py
git commit -m "feat: GroupChatConfig model and JSON repo"
```

---

## Task 6: @Mention Parser

**Files:**
- Create: `backend/haibot/app/group_chat/mention_parser.py`
- Create: `backend/tests/group_chat/test_mention_parser.py`

**Step 1: Write tests**

```python
# backend/tests/group_chat/test_mention_parser.py
import pytest
from haibot.app.group_chat.mention_parser import parse_mentions, resolve_mentions


def test_parse_simple_mentions():
    text = "让我们听听 @analyst 和 @coder 的意见"
    assert parse_mentions(text) == ["analyst", "coder"]


def test_parse_chinese_names():
    text = "请 @分析师 先发言"
    assert parse_mentions(text) == ["分析师"]


def test_parse_no_mentions():
    assert parse_mentions("这个问题我来回答") == []


def test_parse_deduplicates():
    text = "@alpha 说完再请 @alpha 补充"
    assert parse_mentions(text) == ["alpha"]


def test_resolve_by_agent_id():
    participants = [
        {"id": "analyst", "name": "分析师"},
        {"id": "coder", "name": "程序员"},
    ]
    result = resolve_mentions(["analyst"], participants)
    assert result == ["analyst"]


def test_resolve_by_display_name():
    participants = [
        {"id": "analyst", "name": "分析师"},
    ]
    result = resolve_mentions(["分析师"], participants)
    assert result == ["analyst"]


def test_resolve_unknown_name_ignored():
    participants = [{"id": "analyst", "name": "分析师"}]
    result = resolve_mentions(["unknown"], participants)
    assert result == []


def test_resolve_mixed():
    participants = [
        {"id": "analyst", "name": "分析师"},
        {"id": "coder", "name": "程序员"},
    ]
    result = resolve_mentions(["analyst", "程序员", "ghost"], participants)
    assert result == ["analyst", "coder"]
```

**Step 2: Run test to confirm failure**

```
uv run pytest backend/tests/group_chat/test_mention_parser.py -v
```

**Step 3: Create `backend/haibot/app/group_chat/mention_parser.py`**

```python
# -*- coding: utf-8 -*-
"""Parse @mention tokens from agent reply text."""
import re
from typing import List


# Matches @word where word includes ASCII alphanumerics/underscore/hyphen
# and CJK unified ideographs (U+4E00–U+9FFF)
_MENTION_RE = re.compile(r"@([\w\u4e00-\u9fff]+)")


def parse_mentions(text: str) -> List[str]:
    """Extract unique @mentioned names from text, in order of first appearance."""
    seen: list[str] = []
    for match in _MENTION_RE.finditer(text):
        name = match.group(1)
        if name not in seen:
            seen.append(name)
    return seen


def resolve_mentions(
    raw_names: List[str],
    participants: List[dict],
) -> List[str]:
    """Map raw @mention names to agent IDs.

    Matches by agent ``id`` first, then by ``name`` field (case-insensitive).
    Unknown names are silently dropped.

    Args:
        raw_names: Strings extracted by parse_mentions().
        participants: List of dicts with ``id`` and ``name`` keys.

    Returns:
        Ordered, deduplicated list of resolved agent IDs.
    """
    id_set = {p["id"] for p in participants}
    name_to_id = {p["name"].lower(): p["id"] for p in participants}

    result: list[str] = []
    seen: set[str] = set()

    for name in raw_names:
        if name in id_set:
            agent_id = name
        else:
            agent_id = name_to_id.get(name.lower())

        if agent_id and agent_id not in seen:
            result.append(agent_id)
            seen.add(agent_id)

    return result
```

**Step 4: Run tests**

```
uv run pytest backend/tests/group_chat/test_mention_parser.py -v
```
Expected: `PASSED`

**Step 5: Commit**

```bash
git add backend/haibot/app/group_chat/mention_parser.py \
        backend/tests/group_chat/test_mention_parser.py
git commit -m "feat: @mention parser for group chat routing"
```

---

## Task 7: Stream Merger

**Files:**
- Create: `backend/haibot/app/group_chat/stream_merger.py`
- Create: `backend/tests/group_chat/test_stream_merger.py`

**Context:** Merges N async generators into one via `asyncio.Queue`. Order within each stream is preserved; streams interleave as events arrive.

**Step 1: Write tests**

```python
# backend/tests/group_chat/test_stream_merger.py
import asyncio
import pytest
from haibot.app.group_chat.stream_merger import merge_streams


async def _gen(items, delay=0):
    for item in items:
        if delay:
            await asyncio.sleep(delay)
        yield item


async def test_merge_single_stream():
    results = []
    async for item in merge_streams([_gen([1, 2, 3])]):
        results.append(item)
    assert results == [1, 2, 3]


async def test_merge_two_sequential_streams():
    results = []
    async for item in merge_streams([_gen([1, 2]), _gen([3, 4])]):
        results.append(item)
    assert sorted(results) == [1, 2, 3, 4]


async def test_merge_empty():
    results = []
    async for item in merge_streams([]):
        results.append(item)
    assert results == []


async def test_merge_preserves_all_items():
    """All items from all streams must appear in output."""
    stream_a = _gen(["a1", "a2", "a3"])
    stream_b = _gen(["b1", "b2"])
    results = []
    async for item in merge_streams([stream_a, stream_b]):
        results.append(item)
    assert sorted(results) == ["a1", "a2", "a3", "b1", "b2"]
```

**Step 2: Run test to confirm failure**

```
uv run pytest backend/tests/group_chat/test_stream_merger.py -v
```

**Step 3: Create `backend/haibot/app/group_chat/stream_merger.py`**

```python
# -*- coding: utf-8 -*-
"""Merge multiple async generators into one via asyncio.Queue."""
import asyncio
from typing import Any, AsyncGenerator, AsyncIterable, List


async def merge_streams(
    streams: List[AsyncIterable[Any]],
) -> AsyncGenerator[Any, None]:
    """Merge N async iterables into one, interleaved as items arrive.

    Args:
        streams: List of async iterables to merge.

    Yields:
        Items from any stream in arrival order.
    """
    if not streams:
        return

    queue: asyncio.Queue = asyncio.Queue()
    _SENTINEL = object()
    remaining = len(streams)

    async def _drain(stream: AsyncIterable[Any]) -> None:
        try:
            async for item in stream:
                await queue.put(item)
        finally:
            await queue.put(_SENTINEL)

    tasks = [asyncio.create_task(_drain(s)) for s in streams]

    try:
        while remaining > 0:
            item = await queue.get()
            if item is _SENTINEL:
                remaining -= 1
            else:
                yield item
    except asyncio.CancelledError:
        for t in tasks:
            t.cancel()
        raise
```

**Step 4: Run tests**

```
uv run pytest backend/tests/group_chat/test_stream_merger.py -v
```
Expected: `PASSED`

**Step 5: Commit**

```bash
git add backend/haibot/app/group_chat/stream_merger.py \
        backend/tests/group_chat/test_stream_merger.py
git commit -m "feat: async stream merger for concurrent agent responses"
```

---

## Task 8: GROUP_HOST.md Templates

**Files:**
- Create: `backend/haibot/agents/md_files/zh/GROUP_HOST.md`
- Create: `backend/haibot/agents/md_files/en/GROUP_HOST.md`

**Context:** Injected into the host agent's system prompt during group chat rounds. Uses `{participant_list}`, `{round_index}`, `{max_rounds}` placeholders replaced at runtime by the orchestrator via `str.format()`.

**Step 1: Create `backend/haibot/agents/md_files/zh/GROUP_HOST.md`**

```markdown
## 群聊主持规则

你正在主持一场多智能体群聊讨论。

**参与者列表：**
{participant_list}

**当前轮次：** 第 {round_index} 轮（最多 {max_rounds} 轮）

**发言规则：**
- 如需某位或多位参与者发言，在回复末尾使用 `@姓名`（例如：`@分析师 @程序员`）。
- 可同时 @ 多人，他们将并行发言。
- 若你认为讨论已足够充分，或问题已解决，**直接给出最终回复，不要添加任何 @**，讨论将就此结束。
- 每位参与者都能看到完整的讨论历史。
```

**Step 2: Create `backend/haibot/agents/md_files/en/GROUP_HOST.md`**

```markdown
## Group Chat Hosting Rules

You are moderating a multi-agent group chat discussion.

**Participants:**
{participant_list}

**Current round:** {round_index} of {max_rounds}

**Rules:**
- To ask one or more participants to respond, end your reply with `@name` mentions (e.g. `@analyst @coder`).
- Multiple `@mentions` trigger parallel responses.
- If the discussion is sufficiently complete or the task is done, **reply without any @mention** — the discussion will end.
- Every participant sees the full discussion history.
```

**Step 3: Commit**

```bash
git add backend/haibot/agents/md_files/zh/GROUP_HOST.md \
        backend/haibot/agents/md_files/en/GROUP_HOST.md
git commit -m "feat: GROUP_HOST.md templates for host agent in group chat"
```

---

## Task 9: GroupChatOrchestrator

**Files:**
- Create: `backend/haibot/app/group_chat/orchestrator.py`
- Create: `backend/tests/group_chat/test_orchestrator.py`

**Context:** Core loop. Creates host + participant `HaiBotAgent` instances, chains rounds, merges streams, tags events with `agent_id`/`agent_name`.

**Step 1: Write tests (using mocks)**

```python
# backend/tests/group_chat/test_orchestrator.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agentscope.message import Msg
from haibot.app.group_chat.models import GroupChatConfig
from haibot.app.group_chat.orchestrator import GroupChatOrchestrator, tag_event


def test_tag_event_adds_agent_fields():
    event = {"object": "message", "type": "message"}
    tagged = tag_event(event, agent_id="analyst", agent_name="分析师")
    assert tagged["agent_id"] == "analyst"
    assert tagged["agent_name"] == "分析师"
    assert tagged["object"] == "message"  # original fields preserved


def test_tag_event_does_not_mutate_original():
    original = {"object": "content"}
    tagged = tag_event(original, agent_id="x", agent_name="X")
    assert "agent_id" not in original


async def test_orchestrator_single_round_no_mentions(tmp_path):
    """Host replies without @mention → single round, no participants run."""
    config = GroupChatConfig(
        id="test_group",
        name="Test",
        host_agent_id="main",
        participant_agent_ids=["analyst"],
        max_rounds=5,
    )

    host_reply = Msg("main", "这个问题我来回答，无需讨论。", "assistant")

    async def fake_stream_agent(agent, msgs, agent_id, agent_name):
        yield {"object": "message", "type": "message", "status": "in_progress",
               "id": "m1", "agent_id": agent_id, "agent_name": agent_name}
        yield {"object": "group_final_msg", "msg": host_reply, "agent_id": agent_id}

    with patch(
        "haibot.app.group_chat.orchestrator.stream_agent",
        side_effect=fake_stream_agent,
    ):
        orchestrator = GroupChatOrchestrator(
            config=config,
            agent_meta={"main": {"name": "Main"}, "analyst": {"name": "分析师"}},
            memory_manager_factory=AsyncMock(return_value=None),
            mcp_clients=[],
            env_context_factory=MagicMock(return_value=""),
            language="zh",
        )

        user_msg = Msg("user", "今天天气怎么样？", "user")
        events = []
        async for event in orchestrator.run(
            user_msg=user_msg,
            session_id="sess1",
            user_id="u1",
            channel="console",
        ):
            events.append(event)

    # Should have ended with group_done after one round (no @mentions)
    objects = [e.get("object") for e in events]
    assert "group_event" in objects
    done_events = [e for e in events if e.get("type") == "group_done"]
    assert len(done_events) == 1
```

**Step 2: Run test to confirm failure**

```
uv run pytest backend/tests/group_chat/test_orchestrator.py -v
```

**Step 3: Create `backend/haibot/app/group_chat/orchestrator.py`**

```python
# -*- coding: utf-8 -*-
"""GroupChatOrchestrator: manages multi-agent group chat rounds."""
import logging
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from agentscope.message import Msg
from agentscope.pipeline import stream_printing_messages

from .mention_parser import parse_mentions, resolve_mentions
from .models import GroupChatConfig
from .stream_merger import merge_streams
from ...agents.react_agent import HaiBotAgent
from ...agents.prompt import PromptBuilder
from ...constant import WORKING_DIR

logger = logging.getLogger(__name__)


def tag_event(event: dict, agent_id: str, agent_name: str) -> dict:
    """Return a copy of event with agent_id and agent_name added."""
    return {**event, "agent_id": agent_id, "agent_name": agent_name}


async def stream_agent(
    agent: HaiBotAgent,
    msgs: List[Msg],
    agent_id: str,
    agent_name: str,
) -> AsyncGenerator[dict, None]:
    """Stream one agent's response, tagging every event with agent_id/name.

    Yields raw SSE-style event dicts. The last item is a special
    ``{"object": "group_final_msg", "msg": <Msg>, "agent_id": agent_id}``
    sentinel that carries the final reply for history tracking.
    """
    final_msg: Optional[Msg] = None
    async for msg, last in stream_printing_messages(
        agents=[agent],
        coroutine_task=agent(msgs),
    ):
        # Convert agentscope stream item to an event dict the SSE layer can emit
        event = _msg_to_event(msg, last)
        if event:
            yield tag_event(event, agent_id=agent_id, agent_name=agent_name)
        if last:
            final_msg = msg

    if final_msg is not None:
        yield {
            "object": "group_final_msg",
            "msg": final_msg,
            "agent_id": agent_id,
        }


def _msg_to_event(msg: Any, last: bool) -> Optional[dict]:
    """Convert an agentscope stream Msg to a minimal SSE event dict.

    Returns None for items that should not be forwarded to the client.
    """
    if msg is None:
        return None
    # agentscope_runtime already emits proper event dicts; pass through
    if isinstance(msg, dict):
        return msg
    return None


def _build_group_host_context(
    config: GroupChatConfig,
    round_index: int,
    agent_meta: Dict[str, dict],
    language: str,
) -> str:
    """Build the GROUP_HOST.md injection string for this round."""
    template_path = (
        Path(__file__).resolve().parents[2]
        / "agents" / "md_files" / language / "GROUP_HOST.md"
    )
    if not template_path.exists():
        template_path = (
            Path(__file__).resolve().parents[2]
            / "agents" / "md_files" / "zh" / "GROUP_HOST.md"
        )

    template = template_path.read_text(encoding="utf-8") if template_path.exists() else ""

    participant_lines = []
    for pid in config.participant_agent_ids:
        pname = agent_meta.get(pid, {}).get("name", pid)
        participant_lines.append(f"- @{pname} ({pid})")
    participant_list = "\n".join(participant_lines)

    return template.format(
        participant_list=participant_list,
        round_index=round_index + 1,
        max_rounds=config.max_rounds,
    )


class GroupChatOrchestrator:
    """Manages multi-agent group chat: host routing, participant concurrency."""

    def __init__(
        self,
        config: GroupChatConfig,
        agent_meta: Dict[str, dict],
        memory_manager_factory: Callable,
        mcp_clients: List[Any],
        env_context_factory: Callable,
        language: str = "zh",
    ) -> None:
        self._config = config
        self._agent_meta = agent_meta
        self._mm_factory = memory_manager_factory
        self._mcp_clients = mcp_clients
        self._env_ctx_factory = env_context_factory
        self._language = language

    def _get_participant_info(self) -> List[dict]:
        return [
            {"id": pid, "name": self._agent_meta.get(pid, {}).get("name", pid)}
            for pid in self._config.participant_agent_ids
        ]

    async def _make_agent(
        self,
        agent_id: str,
        extra_sys_context: str = "",
        session_id: str = "",
        user_id: str = "",
        channel: str = "console",
    ) -> HaiBotAgent:
        workspace_dir = WORKING_DIR / "workspace" / agent_id
        if not workspace_dir.is_dir():
            workspace_dir = WORKING_DIR

        env_context = self._env_ctx_factory(
            session_id=session_id,
            user_id=user_id,
            channel=channel,
            working_dir=str(workspace_dir),
        )
        if extra_sys_context:
            env_context = extra_sys_context + "\n\n" + (env_context or "")

        memory_manager = await self._mm_factory(agent_id)

        return HaiBotAgent(
            env_context=env_context,
            mcp_clients=self._mcp_clients,
            memory_manager=memory_manager,
            agent_id=agent_id,
            workspace_dir=workspace_dir,
            enable_memory_manager=(memory_manager is not None),
        )

    async def run(
        self,
        user_msg: Msg,
        session_id: str,
        user_id: str,
        channel: str,
    ) -> AsyncGenerator[dict, None]:
        """Run the group chat loop, yielding tagged SSE event dicts."""
        config = self._config
        participant_info = self._get_participant_info()
        history: List[Msg] = [user_msg]

        for round_index in range(config.max_rounds):
            # ── 1. Host turn ──────────────────────────────────────────────
            host_context = _build_group_host_context(
                config, round_index, self._agent_meta, self._language
            )
            host_name = self._agent_meta.get(config.host_agent_id, {}).get(
                "name", config.host_agent_id
            )
            host = await self._make_agent(
                config.host_agent_id,
                extra_sys_context=host_context,
                session_id=session_id,
                user_id=user_id,
                channel=channel,
            )
            await host.register_mcp_clients()
            host.set_console_output_enabled(enabled=False)

            host_final: Optional[Msg] = None
            async for event in stream_agent(
                host, list(history), config.host_agent_id, host_name
            ):
                if event.get("object") == "group_final_msg":
                    host_final = event["msg"]
                else:
                    yield event

            if host_final is None:
                break

            history.append(host_final)

            # ── 2. Parse @mentions ────────────────────────────────────────
            text = host_final.get_text_content() or ""
            raw_names = parse_mentions(text)
            mentioned_ids = resolve_mentions(raw_names, participant_info)

            if not mentioned_ids:
                break  # Host chose to end discussion

            # ── 3. Participant turn (concurrent) ──────────────────────────
            participant_finals: List[Msg] = []

            async def _participant_stream(pid: str):
                pname = self._agent_meta.get(pid, {}).get("name", pid)
                agent = await self._make_agent(
                    pid,
                    session_id=session_id,
                    user_id=user_id,
                    channel=channel,
                )
                await agent.register_mcp_clients()
                agent.set_console_output_enabled(enabled=False)
                async for ev in stream_agent(agent, list(history), pid, pname):
                    yield ev

            participant_streams = [_participant_stream(pid) for pid in mentioned_ids]

            async for event in merge_streams(participant_streams):
                if event.get("object") == "group_final_msg":
                    participant_finals.append(event["msg"])
                else:
                    yield event

            history.extend(participant_finals)

        # ── Discussion ended ──────────────────────────────────────────────
        yield {"object": "group_event", "type": "group_done"}
```

**Step 4: Run tests**

```
uv run pytest backend/tests/group_chat/test_orchestrator.py -v
```
Expected: `PASSED`

**Step 5: Commit**

```bash
git add backend/haibot/app/group_chat/orchestrator.py \
        backend/tests/group_chat/test_orchestrator.py
git commit -m "feat: GroupChatOrchestrator with host/participant round loop"
```

---

## Task 10: AgentRunner Integration

**Files:**
- Modify: `backend/haibot/app/runner/runner.py`
- Modify: `backend/haibot/app/_app.py`

**Context:** When `request.metadata["group_id"]` is present, `query_handler` delegates to `GroupChatOrchestrator`. The `GroupChatRepo` lives on `app.state`; `AgentRunner` receives it via a setter (same pattern as `chat_manager`).

**Step 1: Add `set_group_chat_repo` to `AgentRunner`**

In `runner.py`, add to `__init__`:
```python
self._group_chat_repo = None
```

Add setter:
```python
def set_group_chat_repo(self, repo) -> None:
    self._group_chat_repo = repo
```

**Step 2: Add group chat branch in `query_handler`**

At the top of `query_handler`, after extracting `agent_id`:

```python
# Check for group chat
group_id = None
if hasattr(request, "metadata") and isinstance(request.metadata, dict):
    group_id = request.metadata.get("group_id")

if group_id and self._group_chat_repo is not None:
    config = self._group_chat_repo.get(group_id)
    if config is None:
        raise ValueError(f"Group chat '{group_id}' not found")

    from ..group_chat.orchestrator import GroupChatOrchestrator
    from ..runner.utils import build_env_context

    # Build agent_meta: {agent_id: {name: ...}} for all involved agents
    all_ids = [config.host_agent_id] + config.participant_agent_ids
    agent_meta = {}
    for aid in all_ids:
        workspace = WORKING_DIR / "workspace" / aid
        meta_file = workspace / ".agent_meta.json"
        if meta_file.exists():
            import json as _json
            try:
                m = _json.loads(meta_file.read_text(encoding="utf-8"))
                agent_meta[aid] = m
            except Exception:
                agent_meta[aid] = {"name": aid}
        else:
            agent_meta[aid] = {"name": aid}

    from ...config import load_config as _load_config
    _cfg = _load_config()
    language = _cfg.agents.language

    orchestrator = GroupChatOrchestrator(
        config=config,
        agent_meta=agent_meta,
        memory_manager_factory=self._get_or_create_memory_manager,
        mcp_clients=mcp_clients,
        env_context_factory=build_env_context,
        language=language,
    )

    async for event in orchestrator.run(
        user_msg=msgs[0] if msgs else Msg("user", "", "user"),
        session_id=session_id,
        user_id=user_id,
        channel=channel,
    ):
        yield event, False  # group chat events: last=False until group_done
    return
```

Note: The `mcp_clients` block must be moved above this check so it's available.

**Step 3: Wire `group_chat_repo` in `_app.py` lifespan**

In the `lifespan` function, after `chat_manager` init:

```python
from .group_chat.repo import GroupChatRepo
from ..config.utils import get_config_path

group_chat_repo = GroupChatRepo(
    path=WORKING_DIR / "group_chats.json"
)
runner.set_group_chat_repo(group_chat_repo)
app.state.group_chat_repo = group_chat_repo
```

Add `WORKING_DIR` import to `_app.py`:
```python
from ..constant import DOCS_ENABLED, LOG_LEVEL_ENV, WORKING_DIR
```

**Step 4: Smoke test manually**

```bash
uv run haibot app --log-level debug
# In another terminal, create a group chat via API:
# POST /api/group-chats  (after Task 11)
```

**Step 5: Commit**

```bash
git add backend/haibot/app/runner/runner.py \
        backend/haibot/app/_app.py
git commit -m "feat: integrate GroupChatOrchestrator into AgentRunner"
```

---

## Task 11: Group Chats API Routes

**Files:**
- Create: `backend/haibot/app/routers/group_chats.py`
- Modify: `backend/haibot/app/routers/__init__.py`

**Step 1: Create `backend/haibot/app/routers/group_chats.py`**

```python
# -*- coding: utf-8 -*-
"""CRUD API for group chat configurations."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

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


@router.get("", response_model=List[GroupChatConfig])
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
```

**Step 2: Register in `backend/haibot/app/routers/__init__.py`**

```python
from .group_chats import router as group_chats_router
# ...
router.include_router(group_chats_router)
```

**Step 3: Commit**

```bash
git add backend/haibot/app/routers/group_chats.py \
        backend/haibot/app/routers/__init__.py
git commit -m "feat: CRUD API routes for group chat configuration"
```

---

## Task 12: Frontend — Type Extensions

**Files:**
- Modify: `frontend/src/types/chat.ts`
- Create: `frontend/src/types/group_chat.ts`

**Step 1: Update `DisplayMessage` in `frontend/src/types/chat.ts`**

```typescript
export interface DisplayMessage {
  id: string
  role: 'user' | 'assistant'
  agentId?: string     // set for all messages in group chat mode
  agentName?: string   // display name badge
  blocks: DisplayBlock[]
  streaming?: boolean
}
```

**Step 2: Create `frontend/src/types/group_chat.ts`**

```typescript
export interface GroupChatConfig {
  id: string
  name: string
  host_agent_id: string
  participant_agent_ids: string[]
  max_rounds: number
  created_at: string
}
```

**Step 3: Commit**

```bash
git add frontend/src/types/chat.ts frontend/src/types/group_chat.ts
git commit -m "feat: extend DisplayMessage with agentId/agentName for group chat"
```

---

## Task 13: Frontend — Multi-Agent Streaming in `useChat.ts`

**Files:**
- Modify: `frontend/src/modules/chat/composables/useChat.ts`

**Context:** When events carry `agent_id`, route to per-agent `DisplayMessage` bubbles. Single-agent events (no `agent_id`) use the existing `"__main__"` path unchanged.

**Step 1: Modify `onEvent` inside `sendMessage`**

Replace the current block map setup and `onEvent` with the extended version below. The key change is that `msgBlockMap` becomes per-agent:

```typescript
// Per-agent maps: agentId → msgId → DisplayBlock
const agentMsgBlockMap = new Map<string, Map<string, DisplayBlock>>()
const agentCallBlockMap = new Map<string, Map<string, DisplayBlock>>()
const agentOutputMsgIds = new Map<string, Set<string>>()
const agentBubbleMap = new Map<string, DisplayMessage>()  // agentId → bubble

const MAIN = '__main__'

function getOrCreateBubble(agentId: string, agentName?: string): DisplayMessage {
  if (agentBubbleMap.has(agentId)) return agentBubbleMap.get(agentId)!
  // First event for this agent: push a new bubble
  const bubble: DisplayMessage = {
    id: uuidv4(),
    role: 'assistant',
    agentId,
    agentName,
    blocks: [],
    streaming: true,
  }
  displayMessages.value.push(bubble)
  agentBubbleMap.set(agentId, bubble)
  agentMsgBlockMap.set(agentId, new Map())
  agentCallBlockMap.set(agentId, new Map())
  agentOutputMsgIds.set(agentId, new Set())
  return bubble
}

function onEvent(event: Record<string, unknown>) {
  const agentId = (event.agent_id as string | undefined) ?? MAIN
  const agentName = event.agent_name as string | undefined

  // group_done: mark all agent bubbles as not streaming
  if (event.object === 'group_event' && event.type === 'group_done') {
    for (const bubble of agentBubbleMap.values()) {
      bubble.streaming = false
    }
    assistantMsg.streaming = false
    return
  }

  // For single-agent mode (no agent_id) use existing assistantMsg
  const bubble = agentId === MAIN
    ? assistantMsg
    : getOrCreateBubble(agentId, agentName)

  const msgBlockMap = agentMsgBlockMap.get(agentId) ?? msgBlockMap  // fallback
  const callBlockMap = agentCallBlockMap.get(agentId) ?? callBlockMap
  const outputMsgIds = agentOutputMsgIds.get(agentId) ?? outputMsgIds

  function pushBlock(block: DisplayBlock): DisplayBlock {
    bubble.blocks.push(block)
    return bubble.blocks[bubble.blocks.length - 1]
  }

  // ... rest of onEvent logic unchanged, but using the per-agent maps and pushBlock
}
```

> **Note:** Refactor `onEvent` so the existing logic (message/content handling) operates on the local `pushBlock`, `msgBlockMap`, `callBlockMap`, `outputMsgIds` variables scoped per-agent. The logic itself does not change — only the routing to the right bubble + maps changes.

After `streamQuery` completes (in `onDone`):

```typescript
async () => {
  for (const [aid, blockMap] of agentMsgBlockMap) {
    for (const block of blockMap.values()) {
      if (block.kind === 'tool_call' && block.loading) block.loading = false
    }
  }
  streaming.value = false
  for (const bubble of agentBubbleMap.values()) bubble.streaming = false
  assistantMsg.streaming = false
  abortController = null
  onDone?.()
}
```

In `sendMessage`, keep the initial `assistantMsg` push for single-agent backward compat. In group chat mode, the initial shell will remain empty and agent-specific bubbles are created dynamically.

**Step 2: Update `streamQuery` call to pass `groupId`**

```typescript
// sendMessage signature: add optional groupId param
async function sendMessage(
  text: string, sessionId: string, userId: string,
  scrollToBottom: () => void,
  onDone?: () => void, onError?: (e: Error) => void,
  agentId?: string,
  groupId?: string,   // NEW
)
```

In `streamQuery` body construction:

```typescript
if (groupId) {
  body.metadata = { ...(body.metadata as object || {}), group_id: groupId }
}
```

**Step 3: Commit**

```bash
git add frontend/src/modules/chat/composables/useChat.ts
git commit -m "feat: multi-agent bubble routing in useChat for group chat streaming"
```

---

## Task 14: Frontend — Agent Name Badge in `MessageBubble.vue`

**Files:**
- Modify: `frontend/src/modules/chat/components/MessageBubble.vue`

**Step 1: Add agent name badge to the assistant template**

In the `<template v-else>` block (assistant messages), add above `<div class="msg-assistant">`:

```vue
<template v-else>
  <!-- Agent name badge for group chat participants -->
  <div v-if="message.agentName" class="agent-name-badge">
    {{ message.agentName }}
  </div>
  <div class="msg-assistant" :class="{ 'group-agent': message.agentId }">
    <!-- existing block loop unchanged -->
  </div>
</template>
```

**Step 2: Add styles**

```css
.agent-name-badge {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-color-primary);
  margin-bottom: 4px;
  padding-left: 2px;
  opacity: 0.85;
}
.msg-assistant.group-agent {
  border-left: 2px solid var(--el-color-primary-light-5);
  padding-left: 8px;
}
```

**Step 3: Commit**

```bash
git add frontend/src/modules/chat/components/MessageBubble.vue
git commit -m "feat: agent name badge in MessageBubble for group chat"
```

---

## Task 15: Frontend — Group Chat API + Settings Page

**Files:**
- Create: `frontend/src/api/group_chats.ts`
- Create: `frontend/src/modules/settings/pages/GroupChatSettings.vue`
- Modify: `frontend/src/modules/settings/SettingsLayout.vue`
- Modify: `frontend/src/i18n/locales/zh-CN.ts`
- Modify: `frontend/src/i18n/locales/en.ts`

**Step 1: Create `frontend/src/api/group_chats.ts`**

```typescript
import api from './index'
import type { GroupChatConfig } from '@/types/group_chat'

export const listGroupChats = () =>
  api.get<GroupChatConfig[]>('/group-chats').then(r => r.data)

export const createGroupChat = (data: Omit<GroupChatConfig, 'created_at'>) =>
  api.post<GroupChatConfig>('/group-chats', data).then(r => r.data)

export const updateGroupChat = (id: string, data: GroupChatConfig) =>
  api.put<GroupChatConfig>(`/group-chats/${id}`, data).then(r => r.data)

export const deleteGroupChat = (id: string) =>
  api.delete<{ deleted: boolean }>(`/group-chats/${id}`).then(r => r.data)
```

**Step 2: Create `GroupChatSettings.vue`**

The page lists group chats with create/edit/delete dialogs. Each form has:
- `id` (slug, required on create)
- `name` (display)
- `host_agent_id` (dropdown of existing agents)
- `participant_agent_ids` (multi-select of agents, excluding host)
- `max_rounds` (number input, 1–50)

Use Element Plus `<el-dialog>`, `<el-select>`, `<el-input-number>`. Fetch agents list from `listAgents()` (already in `frontend/src/api/agents.ts`). Follow the same pattern as `CronsSettings.vue`.

**Step 3: Register in `SettingsLayout.vue`**

Add a new tab/nav entry `groupchats` pointing to `GroupChatSettings`. Follow the same pattern as other settings pages.

**Step 4: Add i18n keys**

```typescript
// zh-CN.ts additions
groupChats: {
  title: '群聊配置',
  create: '新建群聊',
  host: '主持人',
  participants: '参与者',
  maxRounds: '最大轮次',
  groupId: '群聊 ID',
}

// en.ts additions
groupChats: {
  title: 'Group Chats',
  create: 'New Group Chat',
  host: 'Host Agent',
  participants: 'Participants',
  maxRounds: 'Max Rounds',
  groupId: 'Group Chat ID',
}
```

**Step 5: Commit**

```bash
git add frontend/src/api/group_chats.ts \
        frontend/src/modules/settings/pages/GroupChatSettings.vue \
        frontend/src/modules/settings/SettingsLayout.vue \
        frontend/src/i18n/locales/zh-CN.ts \
        frontend/src/i18n/locales/en.ts
git commit -m "feat: GroupChatSettings page with CRUD UI"
```

---

## Task 16: Frontend — ChatSidebar Group Chats Section

**Files:**
- Modify: `frontend/src/modules/chat/components/ChatSidebar.vue`
- Modify: `frontend/src/modules/chat/ChatLayout.vue`

**Context:** Group chats appear as a separate labelled section in the sidebar. Clicking one opens a new conversation with `metadata.group_id` set.

**Step 1: Extend `ChatSidebar.vue` props and template**

Add `groupChats` prop and `newGroupChatSession` emit:

```typescript
defineProps<{
  chats: ChatSpec[]
  groupChats: GroupChatConfig[]   // NEW
  activeChatId: string | null
  collapsed: boolean
}>()

defineEmits<{
  toggle: []
  newChat: []
  selectChat: [chat: ChatSpec]
  chatAction: [cmd: string, chat: ChatSpec]
  openSettings: []
  newGroupChatSession: [groupChat: GroupChatConfig]   // NEW
}>()
```

In template, after existing chat list, add a group chats section:

```vue
<!-- Group chats section -->
<template v-if="groupChats.length > 0">
  <div class="section-label">{{ $t('chat.groupChats') }}</div>
  <div
    v-for="gc in groupChats"
    :key="'gc-' + gc.id"
    class="chat-item group-chat-item"
    @click="$emit('newGroupChatSession', gc)"
  >
    <el-icon><ChatDotSquare /></el-icon>
    <span class="chat-item-name">{{ gc.name }}</span>
  </div>
</template>
```

**Step 2: Update `ChatLayout.vue`**

- Import `listGroupChats` and fetch on mount into a `groupChats` ref.
- Pass `groupChats` to `<ChatSidebar>`.
- Handle `newGroupChatSession` emit: create a new chat with `meta: { type: 'group', group_id: gc.id }` and route `streamQuery` with `groupId`.

```typescript
const groupChats = ref<GroupChatConfig[]>([])
onMounted(async () => {
  groupChats.value = await listGroupChats()
})

function handleNewGroupChatSession(gc: GroupChatConfig) {
  // Create a new chat session for this group chat
  // setActiveGroupId(gc.id) so sendMessage includes metadata.group_id
  currentGroupId.value = gc.id
  startNewChat()  // existing function or equivalent
}
```

Pass `groupId` through to `sendMessage`:

```typescript
await chat.sendMessage(
  inputText, sessionId, userId,
  scrollToBottom,
  onDone, onError,
  selectedAgentId.value,
  currentGroupId.value,  // NEW
)
```

**Step 3: Add i18n key**

```typescript
// zh-CN.ts
chat: { ..., groupChats: '群聊' }
// en.ts
chat: { ..., groupChats: 'Group Chats' }
```

**Step 4: Commit**

```bash
git add frontend/src/modules/chat/components/ChatSidebar.vue \
        frontend/src/modules/chat/ChatLayout.vue
git commit -m "feat: group chats section in ChatSidebar"
```

---

## Task 17: Run Full Test Suite + Final Smoke Test

**Step 1: Run all backend tests**

```
uv run pytest backend/tests/ -v
```
Expected: All tests `PASSED`.

**Step 2: Build frontend**

```
cd frontend && pnpm build
```
Expected: no TypeScript errors, dist written to `backend/haibot/console/`.

**Step 3: Smoke test end-to-end**

```bash
# 1. Start server
uv run haibot app

# 2. Open http://localhost:8088
# 3. Go to Settings → Group Chats → create a group with host=main, participants=analyst
# 4. In sidebar, click the group → new conversation
# 5. Send a message that requires analysis
# 6. Verify: host streams first, @analyst triggers parallel bubble, group_done ends conversation
```

**Step 4: Final commit**

```bash
git add CLAUDE.md  # update if needed
git commit -m "feat: group chat feature complete (v1)"
```

---

## Test File Summary

| Test file | What it covers |
|---|---|
| `backend/tests/agents/test_workspace_isolation.py` | HaiBotAgent workspace_dir param |
| `backend/tests/app/test_memory_isolation.py` | Per-agent MemoryManager caching |
| `backend/tests/agents/test_skills_flags.py` | skills_config read/filter |
| `backend/tests/group_chat/test_repo.py` | GroupChatRepo CRUD |
| `backend/tests/group_chat/test_mention_parser.py` | @mention parsing + resolution |
| `backend/tests/group_chat/test_stream_merger.py` | Async stream multiplexing |
| `backend/tests/group_chat/test_orchestrator.py` | Orchestrator round loop |
