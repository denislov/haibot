# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HaiBot is a personal AI assistant built on [agentscope](https://github.com/modelscope/agentscope). It exposes a FastAPI backend, a Vue 3 web console, and a CLI. The agent runs a ReAct loop and supports multi-channel messaging (Discord, DingTalk, Feishu, QQ, Telegram, iMessage, Console), MCP tool integrations, cron jobs, and skills.

## Commands

### Backend (Python / uv)

```bash
# Install dependencies
uv sync

# Initialize working directory (~/.haibot/) interactively
uv run haibot init

# Start the API server (default: http://127.0.0.1:8088)
uv run haibot app

# Start with options
uv run haibot app --host 0.0.0.0 --port 8088 --reload --log-level debug

# Run tests
uv run pytest

# Run a single test file
uv run pytest backend/path/to/test_file.py

# Run tests excluding slow ones
uv run pytest -m "not slow"
```

### Frontend (Vue 3 / pnpm)

```bash
cd frontend

# Install dependencies
pnpm install

# Dev server (port 5173, proxies /api/* to backend at :8088)
pnpm dev

# Build for production (outputs to backend/haibot/console/)
pnpm build

# Type-check without building
vue-tsc --noEmit
```

## Architecture

### Directory Layout

```
backend/haibot/        # Main Python package
  app/                 # FastAPI application
    _app.py            # App factory, lifespan (startup/shutdown), route mounting
    runner/            # AgentRunner - per-request agent lifecycle & session persistence
    channels/          # Multi-channel connectors (discord_, dingtalk, feishu, qq, telegram, imessage, console)
    crons/             # APScheduler-based cron job manager
    mcp/               # MCP client manager + hot-reload config watcher
    routers/           # FastAPI route handlers
  agents/              # Agent core
    react_agent.py     # HaiBotAgent (extends agentscope ReActAgent) with tools + skills
    tools/             # Built-in tools (file I/O, shell, browser, screenshot, search, ...)
    skills_manager.py  # Skills loading from ~/.haibot/active_skills/
    memory/            # Memory manager (MemoryManager, HaiBotInMemoryMemory)
    md_files/          # Agent persona files (SOUL.md, PROFILE.md, AGENTS.md, etc.) in en/ and zh/
  config/              # Config loading/saving (config.json via Pydantic)
    config.py          # All config models (Config, ChannelConfig, MCPConfig, AgentsConfig, ...)
    utils.py           # load_config(), save_config(), path helpers
  cli/                 # Click CLI commands (app, init, channels, crons, models, skills, envs, ...)
  providers/           # AI provider registry (LLM provider + model config, providers.json)
  local_models/        # Local GGUF/ONNX model management
  envs/                # Persistent environment variable store (~/.haibot/envs.json)

frontend/src/
  modules/chat/        # Chat UI (ChatLayout, ChatWindow, ChatSidebar, MessageBubble, MarkdownBlock)
  modules/settings/    # Settings pages (one per domain: channels, models, MCP, crons, skills, ...)
  api/                 # Axios wrappers per domain (agents, channels, chats, crons, mcp, models, ...)
  stores/              # Pinia stores (app.ts, chat.ts)
  types/               # TypeScript type definitions per domain
```

### Key Data Flow

1. `haibot init` creates `~/.haibot/` with `config.json`, `HEARTBEAT.md`, and agent MD files.
2. `haibot app` starts uvicorn serving `haibot.app._app:app`.
3. On startup (`lifespan`): AgentRunner starts, MCP clients connect, channel connectors start, CronManager starts, ConfigWatcher starts.
4. Incoming messages (from any channel or the web console) are forwarded to `AgentRunner.query_handler()`.
5. `query_handler` constructs a `HaiBotAgent` per request, loads session state, runs the ReAct loop, streams responses back, then saves session state.
6. The frontend is a Vue 3 SPA served as static files by FastAPI at `/`. In dev mode it runs at `:5173` with the Vite proxy.

### Working Directory (`~/.haibot/`)

All runtime state lives here (configurable via `HAIBOT_WORKING_DIR`):
- `config.json` - channels, MCP clients, agent settings, last API host/port
- `sessions/` - persisted agent conversation state (JSON)
- `active_skills/` - skills available to the agent
- `customized_skills/` - user-authored skills
- `memory/` - long-term memory files
- `jobs.json` - cron job definitions
- `chats.json` - chat history index
- `providers.json` - LLM provider and model config

### Config Model

`backend/haibot/config/config.py` defines the full Pydantic `Config` model. `load_config()` / `save_config()` in `config/utils.py` read/write `~/.haibot/config.json`.

### Channel System

Each channel subclasses `BaseChannel` (`app/channels/base.py`). Channels are registered in `app/channels/registry.py` and instantiated by `ChannelManager.from_config()`. The `ConfigWatcher` hot-reloads channels when `config.json` changes.

### Agent Skills

Skills are Markdown files (`.md`) in `~/.haibot/active_skills/`. `HaiBotAgent` loads them via `skills_manager.py`. Built-in skills live in `backend/haibot/agents/skills/` and are synced to the working dir via `haibot init` or `haibot skills`.

### MCP Integration

`MCPClientManager` (`app/mcp/manager.py`) manages MCP client connections. Clients are defined in `config.json` under `mcp.clients`. `MCPConfigWatcher` hot-reloads clients when config changes.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HAIBOT_WORKING_DIR` | `~/.haibot` | Working directory |
| `HAIBOT_LOG_LEVEL` | `info` | Log level |
| `HAIBOT_OPENAPI_DOCS` | `false` | Enable `/docs` and `/redoc` |
| `HAIBOT_ENABLED_CHANNELS` | (all) | Comma-separated channel whitelist |
| `COPAW_RUNNING_IN_CONTAINER` | `false` | Set to `1` inside Docker |
| `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` | (auto) | Override Chromium path |

## pytest Configuration

`pyproject.toml` sets `asyncio_mode = "auto"` — all async test functions run automatically without `@pytest.mark.asyncio`. Mark slow tests with `@pytest.mark.slow`.
