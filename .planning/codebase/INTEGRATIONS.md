# External Integrations

**Analysis Date:** 2026-03-27

## Integration Overview

**Overall:** HaiBot integrates with LLM providers, chat/message transports, browser/desktop tooling, MCP clients, tunneling services, and release infrastructure. Most integrations are adapter-style modules under `src/haibot/providers/`, `src/haibot/app/channels/`, `src/haibot/app/mcp/`, and `src/haibot/tunnel/`.

## LLM Provider Integrations

**OpenAI-compatible providers:**
- OpenAI provider implementation: `src/haibot/providers/openai_provider.py`
- Compatibility wrapper for tool-call/stream quirks: `src/haibot/providers/openai_chat_model_compat.py`
- Provider registry entries are assembled in `src/haibot/providers/provider_manager.py`

**Documented built-in provider families from `src/haibot/providers/provider_manager.py`:**
- OpenAI
- Azure OpenAI
- ModelScope
- DashScope
- Aliyun CodingPlan
- Kimi CN / Kimi Intl
- DeepSeek
- LM Studio

**Native non-OpenAI providers:**
- Anthropic via `src/haibot/providers/anthropic_provider.py`
- Gemini via `src/haibot/providers/gemini_provider.py`
- MiniMax variants are registered through the provider manager catalog in `src/haibot/providers/provider_manager.py`

**Local model and local-serving integrations:**
- Ollama via `src/haibot/providers/ollama_provider.py` and `src/haibot/providers/ollama_manager.py`
- llama.cpp backend via `src/haibot/local_models/backends/llamacpp_backend.py`
- MLX backend via `src/haibot/local_models/backends/mlx_backend.py`

**Integration characteristics:**
- Provider configs, model slots, and runtime selection are persisted through `src/haibot/config/config.py` and `src/haibot/providers/models.py`.
- Retry and rate-limit behavior are centralized in `src/haibot/providers/retry_chat_model.py` and `src/haibot/providers/rate_limiter.py`.
- Multimodal capability probing is handled by `src/haibot/providers/multimodal_prober.py` and provider-specific probe methods.

## Messaging and Channel Integrations

**Built-in channel families discovered in `src/haibot/app/channels/`:**
- Console: `src/haibot/app/channels/console/channel.py`
- DingTalk: `src/haibot/app/channels/dingtalk/channel.py`
- Discord: `src/haibot/app/channels/discord_/channel.py`
- Feishu/Lark: `src/haibot/app/channels/feishu/channel.py`
- iMessage: `src/haibot/app/channels/imessage/channel.py`
- Matrix: `src/haibot/app/channels/matrix/channel.py`
- Mattermost: `src/haibot/app/channels/mattermost/channel.py`
- MQTT: `src/haibot/app/channels/mqtt/channel.py`
- QQ: `src/haibot/app/channels/qq/channel.py`
- Telegram: `src/haibot/app/channels/telegram/channel.py`
- Voice/Twilio relay: `src/haibot/app/channels/voice/channel.py`
- WeCom: `src/haibot/app/channels/wecom/channel.py`
- XiaoYi / Huawei A2A WebSocket: `src/haibot/app/channels/xiaoyi/channel.py`

**Channel management infrastructure:**
- Channel discovery and registry: `src/haibot/app/channels/registry.py`
- Channel orchestration and batching: `src/haibot/app/channels/manager.py`
- Shared rendering logic: `src/haibot/app/channels/renderer.py`
- Channel config models: `src/haibot/config/config.py`

**User-facing config/API surfaces:**
- Backend APIs: `src/haibot/app/routers/config.py`, `src/haibot/app/routers/messages.py`
- CLI configuration flows: `src/haibot/cli/channels_cmd.py`
- Frontend settings pages: `frontend/src/modules/settings/pages/ChannelsSettings.vue`

## MCP and Tool Extension Integrations

**MCP support:**
- MCP client manager: `src/haibot/app/mcp/manager.py`
- MCP REST API: `src/haibot/app/routers/mcp.py`
- Workspace service wiring: `src/haibot/app/workspace/service_factories.py`

**Supported MCP transport patterns from router/config shapes:**
- stdio command launches
- HTTP endpoint integrations
- SSE endpoint integrations

**Skill loading and extension surfaces:**
- Built-in skill sync and activation: `src/haibot/agents/skills_manager.py`
- Skill security scanning: `src/haibot/security/skill_scanner/scanner.py`
- Built-in skill packages: `src/haibot/agents/skills/*/SKILL.md`
- Custom skill and custom channel directories are defined from runtime constants in `src/haibot/constant.py`

## Browser, File, and Desktop Integrations

**Browser automation:**
- Playwright-backed browser tooling lives in `src/haibot/agents/tools/browser_control.py`.
- Browser snapshots live in `src/haibot/agents/tools/browser_snapshot.py`.
- Chromium executable path handling is exposed through `src/haibot/config/utils.py`.

**File and media handling:**
- File IO tools live in `src/haibot/agents/tools/file_io.py`.
- File search tooling lives in `src/haibot/agents/tools/file_search.py`.
- Image viewing and screenshot capture live in `src/haibot/agents/tools/view_image.py` and `src/haibot/agents/tools/desktop_screenshot.py`.
- Audio transcription helpers live in `src/haibot/agents/utils/audio_transcription.py`.

**Desktop app surface:**
- `pywebview` is declared in `pyproject.toml`.
- Desktop startup/packaging logic exists in `src/haibot/cli/desktop_cmd.py` and `.github/workflows/desktop-release.yml`.

## Voice, Tunneling, and Webhook Integrations

**Voice integration:**
- Twilio request validation and voice routes live in `src/haibot/app/routers/voice.py`.
- Twilio client wrapper lives in `src/haibot/app/channels/voice/twilio_manager.py`.
- Conversation relay logic lives in `src/haibot/app/channels/voice/conversation_relay.py`.

**Public tunnel integration:**
- Cloudflare tunnel process management lives in `src/haibot/tunnel/cloudflare.py`.
- Auto-download and binary management for `cloudflared` lives in `src/haibot/tunnel/binary_manager.py`.
- Voice channel startup wires the tunnel into Twilio webhook registration in `src/haibot/app/channels/voice/channel.py`.

## Frontend-to-Backend Integrations

**Browser client to API:**
- Axios base client and auth/agent header injection are in `frontend/src/api/index.ts`.
- Chat-specific API wrappers live in `frontend/src/api/chats.ts`, `frontend/src/api/console.ts`, and `frontend/src/api/group_chat_runtime.ts`.
- The UI route tree is defined in `frontend/src/router/index.ts`.

**Auth/session integration:**
- Frontend auth utilities live in `frontend/src/utils/authSession.ts`.
- Backend auth middleware and routes live in `src/haibot/app/auth.py` and `src/haibot/app/routers/auth.py`.

**Static asset serving:**
- FastAPI serves the packaged console from `src/haibot/app/_app.py`.
- Packaged assets currently exist under `src/haibot/console/index.html` and `src/haibot/console/assets/*`.

## Operational and Release Integrations

**Package and release infrastructure:**
- PyPI publishing: `.github/workflows/publish-pypi.yml`
- Docker image release: `.github/workflows/docker-release.yml`
- Desktop release builds: `.github/workflows/desktop-release.yml`
- GitHub Pages website deployment: `.github/workflows/deploy-website.yml`

**Update/telemetry/network integrations:**
- Update checks use `httpx` in `src/haibot/cli/update_cmd.py`.
- Telemetry upload logic exists in `src/haibot/utils/telemetry.py`.
- Remote binary download logic exists in `src/haibot/tunnel/binary_manager.py`.

## Data and Persistence Integrations

**Filesystem-backed repos instead of external services:**
- Chat/session persistence: `src/haibot/app/runner/session.py` and `src/haibot/app/runner/repo/`
- Job persistence: `src/haibot/app/crons/repo/json_repo.py`
- Env persistence: `src/haibot/envs/store.py`
- Config persistence: `src/haibot/config/config.py`

**Implication:**
- No external SQL or NoSQL database integration is detected in the main runtime path.
- No Redis cache/session store integration is detected.

## Integrations Not Detected

- OAuth provider integrations are not clearly detected.
- Stripe, payment, billing, or SaaS subscription integrations are not detected.
- Kubernetes-specific runtime adapters are not detected.
- A third-party observability stack such as Sentry, Datadog, or OpenTelemetry instrumentation is not clearly detected in the main app code.
