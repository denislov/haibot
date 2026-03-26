# Tech Stack

**Analysis Date:** 2026-03-27

## Stack Overview

**Overall:** HaiBot is a Python-first agent runtime with a packaged Vue single-page app and a filesystem-backed multi-agent workspace model.

**Primary implementation surfaces:**
- Backend application code lives in `src/haibot/`.
- Editable frontend source lives in `frontend/src/`.
- Packaged static frontend assets are committed under `src/haibot/console/`.
- Repository automation and packaging scripts live under `scripts/`, `deploy/`, and `.github/workflows/`.

## Languages

**Primary languages:**
- Python is the dominant implementation language across `src/haibot/`, `tests/`, and most `scripts/`.
- TypeScript is used for the web console in `frontend/src/` and Vite tooling in `frontend/`.
- Vue single-file components (`.vue`) are used for the frontend UI, for example `frontend/src/modules/chat/ChatLayout.vue`.

**Supporting formats and scripting:**
- YAML is used for GitHub Actions and rule/policy files, for example `.github/workflows/tests.yml` and `src/haibot/security/skill_scanner/rules/signatures/*.yaml`.
- Markdown is used heavily for built-in skills and docs, for example `src/haibot/agents/skills/*/SKILL.md`.
- Shell and PowerShell are used in packaging/install scripts, for example `scripts/install.sh`, `scripts/wheel_build.sh`, and `scripts/wheel_build.ps1`.
- JSON/TOML are used for package metadata and runtime config surfaces, notably `pyproject.toml` and the file-backed repos referenced from `src/haibot/config/config.py`.

## Runtime Platforms

**Python runtime:**
- `pyproject.toml` declares `requires-python = ">=3.10,<3.14"`.
- CI explicitly runs Python `3.10`, `3.12`, and `3.13` in `.github/workflows/tests.yml` and `.github/workflows/publish-pypi.yml`.

**Node runtime:**
- `frontend/package.json` declares the SPA toolchain.
- GitHub Actions use Node `20` in `.github/workflows/tests.yml`, `.github/workflows/publish-pypi.yml`, and `.github/workflows/desktop-release.yml`.
- `frontend/package.json` pins `pnpm@10.11.0`.

**Cross-platform intent:**
- Windows-specific stdout/stderr UTF-8 handling appears in `src/haibot/cli/main.py`.
- Desktop packaging workflows exist for Windows and macOS in `.github/workflows/desktop-release.yml`.
- Docker packaging exists in `deploy/Dockerfile` and `.github/workflows/docker-release.yml`.

## Backend Frameworks and Core Libraries

**Application framework:**
- FastAPI is the HTTP application framework in `src/haibot/app/_app.py` and `src/haibot/app/routers/*.py`.
- Uvicorn is the app server used by `src/haibot/cli/app_cmd.py`.

**Agent runtime:**
- `agentscope==1.0.17` and `agentscope-runtime==1.1.2b2` are declared in `pyproject.toml`.
- The main agent class extends `ReActAgent` in `src/haibot/agents/react_agent.py`.
- Runtime request handling is built around `AgentRunner` in `src/haibot/app/runner/runner.py`.

**Configuration and modeling:**
- Pydantic models are used extensively in `src/haibot/config/config.py`, `src/haibot/providers/provider.py`, and multiple router modules.
- `python-dotenv` is used in `src/haibot/constant.py` to load `.env` early.
- `shortuuid` is used for short agent identifiers in `src/haibot/config/config.py`.

**HTTP and async support:**
- `httpx` is used across providers, update checks, telemetry, and tunnel downloads, for example `src/haibot/providers/openai_provider.py`, `src/haibot/cli/update_cmd.py`, and `src/haibot/tunnel/binary_manager.py`.
- `aiofiles` is declared in `pyproject.toml` and supports async file workflows.

**Scheduling and background tasks:**
- APScheduler is used for cron-style scheduling in `src/haibot/app/crons/manager.py`.
- Async task coordination is central to the runtime in `src/haibot/app/multi_agent_manager.py`, `src/haibot/app/group_chat/manager.py`, and `src/haibot/app/runner/task_tracker.py`.

## AI, Model, and Tooling Stack

**Remote model providers:**
- OpenAI-compatible providers are implemented in `src/haibot/providers/openai_provider.py`.
- Anthropic support is implemented in `src/haibot/providers/anthropic_provider.py`.
- Gemini support is implemented in `src/haibot/providers/gemini_provider.py`.
- Ollama support is implemented in `src/haibot/providers/ollama_provider.py` and `src/haibot/providers/ollama_manager.py`.
- The provider registry and default provider catalog live in `src/haibot/providers/provider_manager.py`.

**Local model backends:**
- Local model abstraction lives in `src/haibot/local_models/`.
- `src/haibot/local_models/backends/llamacpp_backend.py` supports `llama-cpp-python`.
- `src/haibot/local_models/backends/mlx_backend.py` supports `mlx-lm` on macOS.

**Prompt/tool stack:**
- Built-in tool registration happens in `src/haibot/agents/react_agent.py`.
- File, shell, browser, image, screenshot, and token tools live in `src/haibot/agents/tools/`.
- MCP client integration is part of the runtime via `src/haibot/app/mcp/manager.py` and `src/haibot/app/routers/mcp.py`.

**Memory and token accounting:**
- Memory manager implementations live in `src/haibot/agents/memory/`.
- Token usage tracking lives in `src/haibot/token_usage/`.
- Tokenizer assets are packaged under `src/haibot/tokenizer/`.

## Frontend Stack

**Framework and build system:**
- Vue `3.5.29` is the frontend framework in `frontend/package.json`.
- Vite `7.3.1` is the build/dev server in `frontend/package.json`.
- TypeScript `5.9.3` is used for the application and config typing.

**State, routing, and UI:**
- Pinia is used for client state in `frontend/src/stores/*.ts`.
- Vue Router is configured in `frontend/src/router/index.ts`.
- Element Plus is the component library, initialized in `frontend/src/main.ts`.
- `@vueuse/core` is used for reactive browser utilities, for example in `frontend/src/modules/chat/ChatLayout.vue`.

**Frontend organization:**
- API wrappers live in `frontend/src/api/`.
- Route-level features live in `frontend/src/modules/`.
- DTO and shared type definitions live in `frontend/src/types/`.
- i18n resources live in `frontend/src/i18n/`.

## Developer Tooling and Quality Gates

**Python quality tooling:**
- `pytest`, `pytest-asyncio`, `pytest-cov`, `pre-commit`, and `hypothesis` are in the `dev` extra in `pyproject.toml`.
- `.pre-commit-config.yaml` runs Black, Flake8, mypy, pylint, Prettier, and standard hygiene hooks.

**Frontend tooling:**
- `frontend/package.json` exposes `dev`, `build`, and `preview`.
- Type-checking is coupled to the build through `vue-tsc --noEmit && vite build`.
- No dedicated frontend unit test runner is detected in `frontend/package.json`.

**Local development commands already codified in repo guidance:**
- Backend tests are wrapped by `scripts/run_tests.py`.
- Frontend development is expected to run from `frontend/`.
- Packaging copies built assets into `src/haibot/console/`.

## Packaging and Distribution

**Python packaging:**
- The project uses setuptools via `pyproject.toml`.
- The console entry point is `haibot = "haibot.cli.main:cli"` in `pyproject.toml`.
- Package data includes `console/**`, bundled skill files, tokenizer data, and security rule YAMLs.

**Optional dependency groups:**
- `dev`, `local`, `llamacpp`, `mlx`, `ollama`, `whisper`, and `full` extras are declared in `pyproject.toml`.
- The `full` extra aggregates local model, Ollama, llama.cpp, Whisper, and macOS MLX support.

**Release surfaces:**
- PyPI publishing is automated by `.github/workflows/publish-pypi.yml`.
- Docker image publishing is automated by `.github/workflows/docker-release.yml`.
- Desktop installers/apps are built by `.github/workflows/desktop-release.yml`.
- GitHub Pages website deployment exists in `.github/workflows/deploy-website.yml`.

## Runtime Storage and Assets

**Filesystem-backed runtime:**
- Core runtime paths are defined in `src/haibot/constant.py`, including `WORKING_DIR`, `SECRET_DIR`, `MEMORY_DIR`, and `MODELS_DIR`.
- Config and channel settings are modeled in `src/haibot/config/config.py`.
- Persisted environment variables are handled in `src/haibot/envs/store.py`.
- Built frontend assets are served from `src/haibot/console/` by `src/haibot/app/_app.py`.

**Asset-heavy areas:**
- Tokenizer artifacts are committed under `src/haibot/tokenizer/`.
- Bundled frontend artifacts are committed under `src/haibot/console/assets/`.
- Built-in skill assets and scripts live under `src/haibot/agents/skills/`.

## What Is Not Detected

- A relational database or ORM layer is not detected.
- Redis, Kafka, RabbitMQ, or another dedicated message bus is not detected.
- A separate backend microservice split is not detected; this is a monolithic application repository.
- ESLint, Vitest, Jest, Playwright frontend test config, or Cypress config are not detected for the `frontend/` app.
