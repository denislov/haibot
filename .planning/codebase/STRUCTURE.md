# Codebase Structure

**Analysis Date:** 2026-03-27

## Directory Layout

```text
[project-root]/
├── src/haibot/                 # Main Python package
│   ├── app/                    # FastAPI app, routers, channels, runner, workspaces
│   ├── agents/                 # Agent assembly, prompts, tools, skills, memory
│   ├── cli/                    # Click commands and local HTTP helpers
│   ├── config/                 # Pydantic config models and path utilities
│   ├── providers/              # Remote provider abstractions and model registry
│   ├── local_models/           # Local model backends and factories
│   ├── security/               # Tool guard and skill scanner
│   ├── console/                # Built frontend bundle served by FastAPI
│   ├── envs/                   # Persisted env var storage helpers
│   ├── token_usage/            # Token accounting wrappers
│   ├── tunnel/                 # Cloudflare tunnel helpers
│   └── utils/                  # Logging and telemetry helpers
├── src/copaw/agents/skills/    # Additional packaged skill assets, not a Python package root
├── frontend/src/               # Editable Vue/TypeScript console source
├── tests/unit/                 # Unit tests grouped by backend area
├── tests/integrated/           # Integration/startup coverage
├── deploy/                     # Docker and process-manager packaging
├── scripts/                    # Install, test, packaging, and release helpers
└── .planning/codebase/         # Generated mapping docs for later planning
```

## Directory Purposes

**`src/haibot/app/`:**
- Purpose: Own the running application shell and all runtime-facing backend features.
- Contains: `src/haibot/app/_app.py`, `src/haibot/app/routers/`, `src/haibot/app/channels/`, `src/haibot/app/runner/`, `src/haibot/app/workspace/`, `src/haibot/app/group_chat/`, `src/haibot/app/crons/`, `src/haibot/app/mcp/`
- Key files: `src/haibot/app/_app.py`, `src/haibot/app/multi_agent_manager.py`, `src/haibot/app/agent_context.py`

**`src/haibot/app/routers/`:**
- Purpose: Group FastAPI endpoints by feature/domain.
- Contains: Router modules whose filenames mirror API areas such as `src/haibot/app/routers/agents.py`, `src/haibot/app/routers/console.py`, `src/haibot/app/routers/group_chat_runtime.py`, `src/haibot/app/routers/tools.py`
- Key files: `src/haibot/app/routers/__init__.py`, `src/haibot/app/routers/agent_scoped.py`

**`src/haibot/app/channels/`:**
- Purpose: Host all transport adapters for console and external messaging platforms.
- Contains: Shared channel contract in `src/haibot/app/channels/base.py`, manager/registry/helpers, plus one subdirectory per channel transport such as `src/haibot/app/channels/console/` and `src/haibot/app/channels/discord_/`
- Key files: `src/haibot/app/channels/manager.py`, `src/haibot/app/channels/registry.py`, `src/haibot/app/channels/utils.py`

**`src/haibot/app/runner/`:**
- Purpose: Own single-agent chat execution, session persistence, task tracking, and chat repositories.
- Contains: `AgentRunner`, `ChatManager`, `TaskTracker`, `SafeJSONSession`, runner API, and `repo/` implementations
- Key files: `src/haibot/app/runner/runner.py`, `src/haibot/app/runner/api.py`, `src/haibot/app/runner/task_tracker.py`

**`src/haibot/app/workspace/`:**
- Purpose: Assemble per-agent runtime services and manage their lifecycle.
- Contains: Workspace composition root, service descriptors, and factory hooks
- Key files: `src/haibot/app/workspace/workspace.py`, `src/haibot/app/workspace/service_manager.py`, `src/haibot/app/workspace/service_factories.py`

**`src/haibot/agents/`:**
- Purpose: Build the actual agent behavior on top of AgentScope.
- Contains: `HaiBotAgent`, prompt construction, command handling, model factory, skill syncing, tool definitions, and memory managers
- Key files: `src/haibot/agents/react_agent.py`, `src/haibot/agents/model_factory.py`, `src/haibot/agents/skills_manager.py`, `src/haibot/agents/prompt.py`

**`src/haibot/agents/skills/` and `src/haibot/agents/md_files/`:**
- Purpose: Store packaged skill bundles and prompt markdown templates that get copied or activated in workspaces.
- Contains: One directory per skill with `SKILL.md`, optional `scripts/`, and optional `references/`
- Key files: `src/haibot/agents/skills/file_reader/SKILL.md`, `src/haibot/agents/skills/pdf/SKILL.md`, `src/haibot/agents/md_files/en/AGENTS.md`

**`src/haibot/config/`:**
- Purpose: Define global and per-agent config models plus config path helpers.
- Contains: Pydantic schemas, load/save helpers, timezone detection, and path utilities
- Key files: `src/haibot/config/config.py`, `src/haibot/config/utils.py`, `src/haibot/config/context.py`

**`src/haibot/providers/`:**
- Purpose: Centralize provider metadata, provider SDK adapters, retries, and capability probing.
- Contains: Provider base classes, provider implementations, manager, rate limiter, and model schemas
- Key files: `src/haibot/providers/provider_manager.py`, `src/haibot/providers/provider.py`, `src/haibot/providers/openai_provider.py`

**`src/haibot/local_models/`:**
- Purpose: Handle local model backends separately from remote provider SDKs.
- Contains: Factory functions, backend interfaces, backend implementations, and local-model schema helpers
- Key files: `src/haibot/local_models/factory.py`, `src/haibot/local_models/manager.py`, `src/haibot/local_models/backends/base.py`

**`src/haibot/security/`:**
- Purpose: Hold the safety layers applied to tools and imported skills.
- Contains: `tool_guard/` for runtime tool-call checks and `skill_scanner/` for package scanning
- Key files: `src/haibot/security/tool_guard/engine.py`, `src/haibot/security/tool_guard/models.py`, `src/haibot/security/skill_scanner/scanner.py`

**`frontend/src/`:**
- Purpose: Hold the source of the browser console before build output is generated.
- Contains: `frontend/src/api/`, `frontend/src/modules/`, `frontend/src/router/`, `frontend/src/stores/`, `frontend/src/types/`, `frontend/src/utils/`
- Key files: `frontend/src/main.ts`, `frontend/src/router/index.ts`, `frontend/src/api/index.ts`, `frontend/src/App.vue`

**`frontend/src/modules/`:**
- Purpose: Group the UI by feature rather than by framework primitive.
- Contains: `frontend/src/modules/chat/`, `frontend/src/modules/settings/`, `frontend/src/modules/auth/`
- Key files: `frontend/src/modules/chat/ChatLayout.vue`, `frontend/src/modules/settings/SettingsLayout.vue`, `frontend/src/modules/settings/pages/ModelsSettings.vue`

**`src/haibot/console/`:**
- Purpose: Store the compiled frontend bundle that the Python package actually serves.
- Contains: `index.html` and hashed `assets/*` files
- Key files: `src/haibot/console/index.html`, `src/haibot/console/assets/index-CaYTK39H.js`

**`tests/unit/`:**
- Purpose: Mirror backend feature areas with focused unit tests.
- Contains: Feature folders such as `tests/unit/providers/`, `tests/unit/workspace/`, `tests/unit/group_chat/`, `tests/unit/cli/`
- Key files: `tests/unit/workspace/test_workspace.py`, `tests/unit/providers/test_provider_manager.py`, `tests/unit/group_chat/test_runtime.py`

**`tests/integrated/`:**
- Purpose: Cover startup and broader end-to-end style flows.
- Contains: A small set of integration tests at repo root of the folder
- Key files: `tests/integrated/test_app_startup.py`, `tests/integrated/test_version.py`

**`deploy/`:**
- Purpose: Hold container-oriented runtime packaging and process management.
- Contains: Docker entrypoint and supervisor template
- Key files: `deploy/Dockerfile`, `deploy/entrypoint.sh`, `deploy/config/supervisord.conf.template`

**`scripts/`:**
- Purpose: Hold operational helpers for testing, installation, packaging, and website/wheel builds.
- Contains: Shell/PowerShell scripts plus desktop-packaging helpers under `scripts/pack/`
- Key files: `scripts/run_tests.py`, `scripts/install.sh`, `scripts/pack/build_common.py`

**`src/copaw/agents/skills/`:**
- Purpose: Store extra skill assets shipped alongside the repo.
- Contains: Additional `SKILL.md` files such as `src/copaw/agents/skills/copaw_source_index/SKILL.md`
- Key files: `src/copaw/agents/skills/browser_cdp/SKILL.md`, `src/copaw/agents/skills/multi_agent_collaboration/SKILL.md`

## Key File Locations

**Entry Points:**
- `pyproject.toml`: Declares the `haibot` console script and packaged data.
- `src/haibot/__main__.py`: Module execution entry for `python -m haibot`.
- `src/haibot/cli/main.py`: Root Click command with lazy subcommand registration.
- `src/haibot/cli/app_cmd.py`: Uvicorn launcher for the FastAPI app.
- `src/haibot/app/_app.py`: FastAPI app module with lifespan bootstrap and static console serving.
- `frontend/src/main.ts`: Vue entry point for the web console.
- `frontend/vite.config.ts`: Frontend build config that emits to `src/haibot/console/`.

**Configuration:**
- `src/haibot/config/config.py`: Canonical config schemas and agent/global load-save functions.
- `src/haibot/config/utils.py`: Path helpers, last-API persistence, browser detection, and compatibility utilities.
- `src/haibot/constant.py`: Environment-derived working directories and runtime constants.
- `src/haibot/envs/store.py`: Secret-side `envs.json` persistence and `os.environ` synchronization.
- `src/haibot/app/migration.py`: Legacy-to-multi-agent workspace migration.

**Core Logic:**
- `src/haibot/app/multi_agent_manager.py`: Lazy workspace registry plus hot reload and graceful swap logic.
- `src/haibot/app/workspace/workspace.py`: Per-agent runtime composition root.
- `src/haibot/app/workspace/service_manager.py`: Generic service lifecycle orchestration.
- `src/haibot/app/runner/runner.py`: AgentScope execution bridge.
- `src/haibot/agents/react_agent.py`: Application-specific agent definition with tools and skills.
- `src/haibot/agents/model_factory.py`: Model/provider selection and formatter wiring.
- `src/haibot/app/channels/manager.py`: Channel queueing, batching, and worker management.
- `src/haibot/app/group_chat/coordinator.py`: Host/participant routing for group chat turns.

**Testing:**
- `tests/unit/workspace/test_workspace.py`: Workspace start/stop and service assembly coverage.
- `tests/unit/providers/test_provider_manager.py`: Provider registration/selection coverage.
- `tests/unit/group_chat/test_runtime.py`: Group chat runtime behavior.
- `tests/unit/cli/test_cli_update.py`: CLI command behavior.
- `tests/integrated/test_app_startup.py`: App startup and boot flow.

## Naming Conventions

**Files:**
- Python modules use `snake_case.py`: `src/haibot/app/multi_agent_manager.py`, `src/haibot/app/routers/group_chat_runtime.py`, `src/haibot/agents/model_factory.py`
- CLI command modules end in `_cmd.py`: `src/haibot/cli/app_cmd.py`, `src/haibot/cli/channels_cmd.py`, `src/haibot/cli/update_cmd.py`
- API router filenames generally mirror their URL domain: `src/haibot/app/routers/agents.py` for `/agents`, `src/haibot/app/routers/console.py` for `/console`
- Repository implementations live in local `repo/` packages: `src/haibot/app/runner/repo/json_repo.py`, `src/haibot/app/crons/repo/json_repo.py`
- Vue components use `PascalCase.vue`: `frontend/src/modules/chat/ChatLayout.vue`, `frontend/src/modules/settings/pages/AgentsSettings.vue`
- Frontend API wrappers use lowercase feature files: `frontend/src/api/agents.ts`, `frontend/src/api/group_chats.ts`, `frontend/src/api/token_usage.ts`
- Skill directories are lowercase folder names with a required `SKILL.md`: `src/haibot/agents/skills/file_reader/SKILL.md`

**Directories:**
- Backend code is feature-grouped under `src/haibot/app/` and `src/haibot/agents/`, not split into a separate `services/` vs `controllers/` top-level tree.
- Frontend code is feature-grouped under `frontend/src/modules/`; common client pieces are centralized under `frontend/src/api/`, `frontend/src/stores/`, `frontend/src/types/`, and `frontend/src/utils/`.
- Transport implementations get one subdirectory per channel under `src/haibot/app/channels/`.
- Generated/static frontend output stays in `src/haibot/console/`. Editable frontend source stays in `frontend/src/`.
- A separate server-template directory is not detected. A separate migrations framework directory is not detected.

## Where to Add New Code

**New Feature:**
- Primary code: Put backend HTTP-facing behavior in an existing feature package under `src/haibot/app/` and expose it via a router in `src/haibot/app/routers/` or a feature-local API module such as `src/haibot/app/crons/api.py` or `src/haibot/app/runner/api.py`.
- Primary code: If the feature needs per-agent runtime services, extend `src/haibot/app/workspace/workspace.py` and `src/haibot/app/workspace/service_factories.py` instead of wiring ad hoc globals in `src/haibot/app/_app.py`.
- Primary code: If the feature needs agent behavior changes, add it under `src/haibot/agents/` and keep provider-specific code under `src/haibot/providers/`.
- Tests: Add fast coverage under the matching folder in `tests/unit/`; add `tests/integrated/` coverage when startup, app wiring, or end-to-end API behavior changes.

**New API Endpoint:**
- Implementation: Add the router file under `src/haibot/app/routers/` if it is a top-level API area, then include it in `src/haibot/app/routers/__init__.py`.
- Implementation: If the endpoint should work under `/api/agents/{agentId}/...`, also include that router in `src/haibot/app/routers/agent_scoped.py`.
- Frontend client: Mirror the backend route in `frontend/src/api/<feature>.ts`.
- Frontend screen: Wire it into `frontend/src/router/index.ts` and the relevant page/component under `frontend/src/modules/`.

**New Channel:**
- Implementation: Create a new transport package under `src/haibot/app/channels/<channel_name>/` with its `channel.py` implementation derived from `src/haibot/app/channels/base.py`.
- Registration: Add the built-in channel spec to `src/haibot/app/channels/registry.py` or document it as a custom channel under `CUSTOM_CHANNELS_DIR`.
- Config: Add channel config schema to `src/haibot/config/config.py`.
- CLI/UI: Update `src/haibot/cli/channels_cmd.py` and the settings client in `frontend/src/api/channels.ts` plus UI in `frontend/src/modules/settings/pages/ChannelsSettings.vue`.

**New Workspace Service or Runtime Manager:**
- Implementation: Define the service in `src/haibot/app/workspace/workspace.py` using a `ServiceDescriptor`.
- Lifecycle hooks: Put complex setup/teardown wiring into `src/haibot/app/workspace/service_factories.py`.
- Runtime API: Expose the service via a focused router or feature API module under `src/haibot/app/`.

**New Skill or Prompt Asset:**
- Built-in skill: Add it under `src/haibot/agents/skills/<skill_name>/` with `SKILL.md` and any optional `scripts/` or `references/`.
- Workspace activation logic: Keep sync/activation behavior in `src/haibot/agents/skills_manager.py`.
- Prompt markdown: Add packaged defaults under `src/haibot/agents/md_files/<locale>/` if the file should be seeded into workspaces.

**New Frontend Component or Page:**
- Implementation: Put page-level settings views under `frontend/src/modules/settings/pages/` and chat-specific UI under `frontend/src/modules/chat/components/` or `frontend/src/modules/chat/composables/`.
- Shared state: Use or extend Pinia stores in `frontend/src/stores/`.
- Shared helpers: Put frontend-wide helpers in `frontend/src/utils/`, not inside a page component.

**Utilities:**
- Shared Python helpers: Put backend-wide utilities in `src/haibot/utils/`.
- Feature-specific Python helpers: Keep them next to the feature, for example `src/haibot/app/channels/utils.py` or `src/haibot/agents/utils/`.
- Generated frontend bundle: Do not edit `src/haibot/console/` directly; edit `frontend/src/` and rebuild via `frontend/vite.config.ts`.

## Special Directories

**`src/haibot/console/`:**
- Purpose: Built browser bundle served by FastAPI.
- Generated: Yes
- Committed: Yes

**`src/haibot/agents/skills/`:**
- Purpose: Built-in packaged skill assets.
- Generated: No
- Committed: Yes

**`src/copaw/agents/skills/`:**
- Purpose: Additional packaged skill assets outside the main `src/haibot/` package tree.
- Generated: No
- Committed: Yes

**`src/haibot/tokenizer/`:**
- Purpose: Tokenizer data files used by token counting utilities.
- Generated: No
- Committed: Yes

**`.planning/codebase/`:**
- Purpose: Generated mapper output consumed by later planning/execution steps.
- Generated: Yes
- Committed: Yes

**`.venv/`:**
- Purpose: Local development virtual environment.
- Generated: Yes
- Committed: No

**`logs/`:**
- Purpose: Local runtime logs produced during development or app execution.
- Generated: Yes
- Committed: No

---

*Structure analysis: 2026-03-27*
