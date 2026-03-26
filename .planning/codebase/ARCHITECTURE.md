# Architecture

**Analysis Date:** 2026-03-27

## Pattern Overview

**Overall:** Monolithic Python application with a packaged Vue SPA, organized around a multi-agent workspace runtime.

**Key Characteristics:**
- The process boundary is the FastAPI app in `src/haibot/app/_app.py`; agent isolation happens inside the process through per-agent `Workspace` instances managed by `src/haibot/app/multi_agent_manager.py`.
- Runtime composition is service-based rather than inheritance-based: `src/haibot/app/workspace/workspace.py` registers services declaratively and `src/haibot/app/workspace/service_manager.py` starts them by priority.
- HTTP APIs, channel ingress, cron jobs, and group-chat flows all converge on the same runner path in `src/haibot/app/runner/runner.py` and the same agent construction path in `src/haibot/agents/react_agent.py`.
- Persistence is primarily filesystem-backed JSON and markdown managed by `src/haibot/config/config.py`, `src/haibot/app/runner/repo/json_repo.py`, `src/haibot/app/crons/repo/json_repo.py`, and `src/haibot/app/runner/session.py`.
- A separate database/ORM layer is not detected. A separate message bus is not detected. Most coordination is in-process via managers, locks, queues, and context variables.

## Layers

**CLI Bootstrap Layer:**
- Purpose: Expose command-line entry points, startup/bootstrap commands, and small HTTP client helpers.
- Location: `src/haibot/__main__.py`, `src/haibot/cli/main.py`, `src/haibot/cli/app_cmd.py`, `src/haibot/cli/init_cmd.py`, `src/haibot/cli/http.py`, `src/haibot/cli/*_cmd.py`
- Contains: Click root group, lazy subcommand loading, interactive setup, uvicorn startup, and API-oriented helper commands.
- Depends on: `src/haibot/config/`, `src/haibot/app/`, `src/haibot/providers/`
- Used by: Shell users, local scripts, `python -m haibot`, and the console script declared in `pyproject.toml`

**HTTP App Composition Layer:**
- Purpose: Build the FastAPI application, mount API routers, apply middleware, and serve the packaged console.
- Location: `src/haibot/app/_app.py`, `src/haibot/app/auth.py`, `src/haibot/app/routers/__init__.py`, `src/haibot/app/routers/*.py`
- Contains: Lifespan startup/shutdown, auth middleware, CORS, static asset mounting, root routes, and API router registration.
- Depends on: `src/haibot/config/`, `src/haibot/envs/store.py`, `src/haibot/app/multi_agent_manager.py`, `src/haibot/providers/provider_manager.py`
- Used by: Browser clients, CLI HTTP helpers, external channels, and AgentScope runtime endpoints

**Agent Context and Workspace Lifecycle Layer:**
- Purpose: Resolve which agent a request targets and create/manage that agent's isolated runtime.
- Location: `src/haibot/app/agent_context.py`, `src/haibot/app/multi_agent_manager.py`, `src/haibot/app/workspace/workspace.py`, `src/haibot/app/workspace/service_manager.py`, `src/haibot/app/workspace/service_factories.py`
- Contains: Agent ID resolution, lazy workspace loading, zero-downtime reload, reusable service handoff, and service dependency ordering.
- Depends on: `src/haibot/config/config.py`, `src/haibot/app/runner/`, `src/haibot/app/channels/`, `src/haibot/app/mcp/`, `src/haibot/app/crons/`
- Used by: API routers, AgentScope runner wrapper, and group-chat coordinator

**Execution Runtime Layer:**
- Purpose: Turn normalized requests into model/tool execution, session persistence, and streamed outputs.
- Location: `src/haibot/app/runner/runner.py`, `src/haibot/app/runner/api.py`, `src/haibot/app/runner/manager.py`, `src/haibot/app/runner/task_tracker.py`, `src/haibot/app/runner/session.py`, `src/haibot/agents/react_agent.py`, `src/haibot/agents/model_factory.py`
- Contains: `AgentRunner`, chat registry, session serialization, SSE reconnection buffers, agent prompt/model/tool assembly, and command handling.
- Depends on: `src/haibot/agents/`, `src/haibot/providers/`, `src/haibot/local_models/`, `src/haibot/security/`, `src/haibot/token_usage/`
- Used by: Console chat, channel handlers, cron execution, and group-chat delegation

**Transport and Channel Layer:**
- Purpose: Normalize inbound channel payloads, debounce/batch them, and render outbound messages per transport.
- Location: `src/haibot/app/channels/base.py`, `src/haibot/app/channels/manager.py`, `src/haibot/app/channels/registry.py`, `src/haibot/app/channels/utils.py`, `src/haibot/app/channels/*/channel.py`
- Contains: `BaseChannel`, `ChannelManager`, channel discovery, request construction, transport-specific SDK integrations, and message rendering.
- Depends on: `src/haibot/config/config.py`, `src/haibot/app/runner/`, external SDKs, and `src/haibot/app/channels/renderer.py`
- Used by: Agent workspaces, approval notifications, and direct user-facing messaging

**Configuration and Persistence Layer:**
- Purpose: Define configuration models, locate runtime directories, persist config/env/session/job/chat state, and migrate old layouts.
- Location: `src/haibot/config/config.py`, `src/haibot/config/utils.py`, `src/haibot/constant.py`, `src/haibot/envs/store.py`, `src/haibot/app/migration.py`
- Contains: Global `Config`, per-agent `AgentProfileConfig`, path helpers, runtime constants, env persistence, and workspace migration logic.
- Depends on: Filesystem, Pydantic, and model slot schemas from `src/haibot/providers/models.py`
- Used by: Every other backend layer

**Model and Provider Layer:**
- Purpose: Abstract remote model providers and local model backends behind a single model factory.
- Location: `src/haibot/providers/provider_manager.py`, `src/haibot/providers/provider.py`, `src/haibot/providers/*_provider.py`, `src/haibot/providers/retry_chat_model.py`, `src/haibot/local_models/factory.py`, `src/haibot/local_models/backends/*.py`
- Contains: Provider registry, provider metadata, active-model resolution, rate limiting, retry wrappers, multimodal probing, and local backend adapters.
- Depends on: Provider SDKs, AgentScope model interfaces, and config model slots
- Used by: `src/haibot/agents/model_factory.py`, provider settings APIs, and model capability checks

**Frontend Console Layer:**
- Purpose: Present the browser UI for chat, settings, auth, and agent/group management.
- Location: `frontend/src/main.ts`, `frontend/src/router/index.ts`, `frontend/src/api/*.ts`, `frontend/src/modules/`, `frontend/src/stores/`
- Contains: Vue app bootstrap, Pinia stores, route definitions, Axios API wrappers, chat UI, and settings pages.
- Depends on: `/api` endpoints exposed by `src/haibot/app/routers/`, Element Plus, Vue Router, and Pinia
- Used by: Web browser clients; built output is served from `src/haibot/console/`

## Data Flow

**Console Chat Request:**

1. The browser boots from `frontend/src/main.ts`; chat UI in `frontend/src/modules/chat/ChatLayout.vue` sends requests through Axios wrappers in `frontend/src/api/index.ts`.
2. Axios prefixes every request with `/api` and injects `X-Agent-Id` when the selected agent changes through `frontend/src/stores/settings.ts`.
3. `src/haibot/app/routers/console.py` resolves the target workspace through `src/haibot/app/agent_context.py`, creates or reuses a chat via `src/haibot/app/runner/manager.py`, and allocates a reconnectable stream via `src/haibot/app/runner/task_tracker.py`.
4. `src/haibot/app/channels/console/channel.py` converts the HTTP payload into an AgentScope `AgentRequest` and invokes the runner through the process callback attached by `src/haibot/app/channels/utils.py`.
5. `src/haibot/app/runner/runner.py` loads the per-agent config, resolves MCP clients, builds a `HaiBotAgent` from `src/haibot/agents/react_agent.py`, and streams model/tool events.
6. Session and chat metadata persist through `src/haibot/app/runner/session.py`, `src/haibot/app/runner/repo/json_repo.py`, and memory backends under `src/haibot/agents/memory/`.
7. SSE chunks are buffered by `src/haibot/app/runner/task_tracker.py` so reconnect requests can replay prior events before following the live stream.

**Workspace Startup and Lazy Loading:**

1. FastAPI startup in `src/haibot/app/_app.py` migrates legacy layout and ensures built-in agents exist through `src/haibot/app/migration.py`.
2. Requests reach `src/haibot/app/agent_context.py`, which resolves the agent in this order: path parameter, `X-Agent-Id`, then active agent from `src/haibot/config/config.py`.
3. `src/haibot/app/multi_agent_manager.py` lazy-loads missing agents by creating a `Workspace`.
4. `src/haibot/app/workspace/workspace.py` loads `agent.json` and registers all runtime services.
5. `src/haibot/app/workspace/service_manager.py` starts services in priority groups, while `src/haibot/app/workspace/service_factories.py` wires the runner to memory, chats, MCP, channels, cron, and config watchers.

**External Channel Ingress:**

1. Workspace startup creates a `ChannelManager` in `src/haibot/app/workspace/service_factories.py` using `make_process_from_runner` from `src/haibot/app/channels/utils.py`.
2. `src/haibot/app/channels/registry.py` combines built-in channels and custom channel modules from `CUSTOM_CHANNELS_DIR`.
3. Each channel implementation under `src/haibot/app/channels/*/channel.py` normalizes its native SDK/webhook payloads into the shared `AgentRequest` shape defined by `src/haibot/app/channels/base.py`.
4. `src/haibot/app/channels/manager.py` owns per-channel queues, same-session batching, debounce, and worker tasks, then hands requests to the same runner used by the console route.
5. Outbound agent messages are rendered transport-specifically through `src/haibot/app/channels/renderer.py` and sent back by the concrete channel class.

**Group Chat Runtime:**

1. Group chat configuration is stored globally through `src/haibot/app/routers/group_chats.py` and consumed in the UI through `frontend/src/api/group_chats.ts`.
2. Live group-chat execution goes through `src/haibot/app/routers/group_chat_runtime.py`.
3. `src/haibot/app/group_chat/manager.py` creates a `GroupChatRuntime` with its own chats, sessions, media directory, and task tracker under `src/haibot/app/group_chat/runtime.py`.
4. `src/haibot/app/group_chat/coordinator.py` routes a turn to the host agent or delegated participant agents by calling each target agent's console channel stream.
5. Host-to-participant delegation is mediated through callback registration in `src/haibot/app/group_chat/delegation_registry.py` and group metadata is flattened into streamed events before reaching the client.

**Runtime Configuration Reload:**

1. Agent config writes land in workspace `agent.json` through APIs such as `src/haibot/app/routers/agents.py`, `src/haibot/app/routers/config.py`, `src/haibot/app/routers/mcp.py`, and related frontend pages under `frontend/src/modules/settings/pages/`.
2. `src/haibot/app/agent_config_watcher.py` polls the agent config file, reloads changed channels in place, and reschedules heartbeat jobs when the heartbeat section changes.
3. MCP clients are managed separately by `src/haibot/app/mcp/manager.py` and optional watcher logic under `src/haibot/app/mcp/watcher.py`.
4. Full agent reloads use `src/haibot/app/multi_agent_manager.py`, which can swap in a new `Workspace` while letting existing streamed tasks finish on the old one.

**State Management:**
- Backend request state is mostly a mix of context variables in `src/haibot/app/agent_context.py`, app-scoped singletons on `app.state` in `src/haibot/app/_app.py`, and per-workspace service instances in `src/haibot/app/workspace/workspace.py`.
- Persisted state is file-based: config/envs under `src/haibot/config/` and `src/haibot/envs/store.py`, chat/job repos under `src/haibot/app/runner/repo/` and `src/haibot/app/crons/repo/`, and session JSON files through `src/haibot/app/runner/session.py`.
- Frontend state lives in Pinia stores under `frontend/src/stores/`. A separate frontend state machine library is not detected.

## Key Abstractions

**Workspace:**
- Purpose: Represent one fully isolated agent runtime inside the shared process.
- Examples: `src/haibot/app/workspace/workspace.py`, `src/haibot/app/multi_agent_manager.py`
- Pattern: Composition root per agent; services are looked up as properties on the workspace rather than through global singletons.

**ServiceDescriptor and ServiceManager:**
- Purpose: Describe startup/shutdown/reuse behavior for workspace services.
- Examples: `src/haibot/app/workspace/service_manager.py`, `src/haibot/app/workspace/workspace.py`
- Pattern: Lightweight dependency container with priority-based initialization and optional reusable services for hot reload.

**AgentRunner and TaskTracker:**
- Purpose: Execute one chat turn and manage long-lived/reconnectable streaming tasks.
- Examples: `src/haibot/app/runner/runner.py`, `src/haibot/app/runner/task_tracker.py`
- Pattern: Async runner plus buffered fan-out stream tracker keyed by chat ID.

**HaiBotAgent:**
- Purpose: Assemble prompt files, tools, skills, MCP clients, model, and memory into the actual ReAct agent.
- Examples: `src/haibot/agents/react_agent.py`, `src/haibot/agents/prompt.py`, `src/haibot/agents/skills_manager.py`
- Pattern: Thin application-specific wrapper around AgentScope `ReActAgent`.

**BaseChannel and ChannelManager:**
- Purpose: Normalize transport differences and present one request/response contract to the runtime.
- Examples: `src/haibot/app/channels/base.py`, `src/haibot/app/channels/manager.py`, `src/haibot/app/channels/console/channel.py`
- Pattern: Adapter pattern for channels, orchestrated by a manager-owned queue and worker model.

**ProviderManager:**
- Purpose: Centralize model provider metadata, active model resolution, and local/remote provider access.
- Examples: `src/haibot/providers/provider_manager.py`, `src/haibot/agents/model_factory.py`
- Pattern: Process-wide manager plus per-request model factory.

**GroupChatRuntime:**
- Purpose: Keep group-chat transcripts, sessions, media, and running tasks separate from single-agent chats.
- Examples: `src/haibot/app/group_chat/runtime.py`, `src/haibot/app/group_chat/manager.py`
- Pattern: Feature-specific runtime object parallel to `Workspace`, but scoped to one configured group chat.

## Entry Points

**Python Module Entry:**
- Location: `src/haibot/__main__.py`
- Triggers: `python -m haibot`
- Responsibilities: Delegate immediately to the Click CLI in `src/haibot/cli/main.py`

**CLI Root:**
- Location: `src/haibot/cli/main.py`
- Triggers: `haibot` script declared in `pyproject.toml`
- Responsibilities: Parse global host/port options and lazily load subcommands

**Server Startup Command:**
- Location: `src/haibot/cli/app_cmd.py`
- Triggers: `haibot app`
- Responsibilities: Configure logging and launch uvicorn against `haibot.app._app:app`

**App Composition Module:**
- Location: `src/haibot/app/_app.py`
- Triggers: Uvicorn import/startup
- Responsibilities: Create FastAPI app, initialize managers in lifespan, mount routers, and serve the packaged console

**Interactive Initialization:**
- Location: `src/haibot/cli/init_cmd.py`
- Triggers: `haibot init`
- Responsibilities: Create the working directory structure, seed config, and ensure built-in workspaces exist

**Frontend Bootstrap:**
- Location: `frontend/src/main.ts`
- Triggers: Browser loading `src/haibot/console/index.html` or Vite dev server
- Responsibilities: Mount Vue, Pinia, router, i18n, and Element Plus

## Error Handling

**Strategy:** Boundary-driven error handling with extensive logging. Routers translate failures into `HTTPException`; manager/service layers log and re-raise; stream paths convert failures into SSE error events where possible.

**Patterns:**
- HTTP routes raise explicit status codes in `src/haibot/app/routers/console.py`, `src/haibot/app/routers/agents.py`, `src/haibot/app/routers/group_chat_runtime.py`, and `src/haibot/app/crons/api.py`.
- Service startup/shutdown logs and fails fast in `src/haibot/app/workspace/service_manager.py`, `src/haibot/app/workspace/workspace.py`, and `src/haibot/app/multi_agent_manager.py`.
- Streaming failures become recoverable error events in `src/haibot/app/routers/console.py`, `src/haibot/app/runner/task_tracker.py`, and `src/haibot/app/channels/console/channel.py`.
- Optional integration failures degrade gracefully in `src/haibot/app/channels/registry.py`, `src/haibot/app/mcp/manager.py`, and `src/haibot/agents/model_factory.py`.
- A transaction coordinator or saga layer is not detected; most operations are single-file writes or in-memory mutations.

## Cross-Cutting Concerns

**Logging:** Structured application logging is configured in `src/haibot/utils/logging.py` and initialized from `src/haibot/cli/app_cmd.py` and `src/haibot/app/_app.py`. Most modules keep a module-level `logger`.

**Validation:** Backend validation relies on Pydantic models in `src/haibot/config/config.py`, `src/haibot/app/runner/models.py`, `src/haibot/app/crons/models.py`, and `src/haibot/app/group_chat/models.py`. Frontend request/response shapes mirror that contract in `frontend/src/types/*.ts`.

**Authentication:** `src/haibot/app/auth.py` provides registration, token handling, and `AuthMiddleware`. The UI gates access through `frontend/src/App.vue` and auth state under `frontend/src/modules/auth/` and `frontend/src/stores/auth.ts`.

**Authorization and Runtime Safety:** Tool execution is guarded by `src/haibot/agents/tool_guard_mixin.py`, `src/haibot/security/tool_guard/engine.py`, `src/haibot/security/tool_guard/guardians/*.py`, and approval queues in `src/haibot/app/approvals/service.py`. Skill packages are scanned by `src/haibot/security/skill_scanner/`.

**Hot Reload and Dynamic Discovery:** Agent config reload is handled by `src/haibot/app/agent_config_watcher.py`; MCP reload by `src/haibot/app/mcp/manager.py` plus `src/haibot/app/mcp/watcher.py`; custom channels are discovered dynamically by `src/haibot/app/channels/registry.py`.

**Static Asset Packaging:** Editable frontend code lives under `frontend/src/`, while the shipped bundle is generated into `src/haibot/console/` by `frontend/vite.config.ts`. Server-rendered templates are not used.

---

*Architecture analysis: 2026-03-27*
