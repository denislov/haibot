# Coding Conventions

**Analysis Date:** 2026-03-27

## Naming Patterns

**Files:**
- Python modules use `snake_case` names under `src/haibot/`, with role suffixes when useful: `src/haibot/cli/update_cmd.py`, `src/haibot/app/runner/task_tracker.py`, `src/haibot/providers/openai_provider.py`.
- CLI command modules conventionally end in `_cmd.py`: `src/haibot/cli/app_cmd.py`, `src/haibot/cli/shutdown_cmd.py`, `src/haibot/cli/providers_cmd.py`.
- Vue single-file components use `PascalCase` filenames inside feature folders: `frontend/src/modules/chat/ChatLayout.vue`, `frontend/src/modules/chat/components/ChatWindow.vue`, `frontend/src/modules/settings/pages/ModelsSettings.vue`.
- Frontend stores, composables, and utilities use `camelCase` filenames: `frontend/src/stores/auth.ts`, `frontend/src/modules/chat/composables/useChat.ts`, `frontend/src/utils/useTheme.ts`.

**Functions:**
- Python functions and methods use `snake_case`; internal helpers are prefixed with `_`, for example `_probe_service` in `src/haibot/cli/update_cmd.py` and `_record` in `src/haibot/cli/main.py`.
- Frontend functions use `camelCase`; composables and store hooks use `useXxx`, for example `useAuthStore` in `frontend/src/stores/auth.ts` and `useChat` in `frontend/src/modules/chat/composables/useChat.ts`.
- Async functions are named for behavior rather than prefixed with `async_`: `create_pending` in `src/haibot/app/approvals/service.py`, `streamQuery` in `frontend/src/api/chats.ts`.

**Variables:**
- Python locals and attributes use `snake_case`; constants use `UPPER_SNAKE_CASE`, for example `_PYPI_JSON_URL` in `src/haibot/cli/update_cmd.py` and `_GC_MAX_AGE_SECONDS` in `src/haibot/app/approvals/service.py`.
- Frontend refs, computeds, and store state use `camelCase`, for example `leftCollapsed` and `selectedContact` in `frontend/src/modules/chat/ChatLayout.vue`.
- Backend JSON-facing field names generally stay `snake_case` to match persisted config and API payloads, for example `workspace_dir`, `session_id`, and `group_id` in `src/haibot/config/config.py` and `src/haibot/app/runner/models.py`.

**Types:**
- Python classes use `PascalCase`; Pydantic models are commonly suffixed with `Config`, `Info`, `Request`, or `Response`, for example `ProviderConfigRequest` in `src/haibot/app/routers/providers.py` and `HeartbeatConfig` in `src/haibot/config/config.py`.
- In-memory state holders often use `@dataclass`, for example `PendingApproval` in `src/haibot/app/approvals/service.py` and `InstallInfo` in `src/haibot/cli/update_cmd.py`.
- Frontend interfaces and type aliases use `PascalCase`, for example `AgentProfileConfig` in `frontend/src/types/agent.ts` and `AuthMode` in `frontend/src/stores/auth.ts`.

## Code Style

**Formatting:**
- Python formatting is governed by Black through `.pre-commit-config.yaml`, with a 79-character limit mirrored in `.flake8`.
- UTF-8 headers are common in Python source and tests, for example `src/haibot/cli/main.py`, `src/haibot/config/config.py`, and `tests/integrated/test_app_startup.py`.
- Many Python files also use `from __future__ import annotations`, especially newer or actively maintained modules such as `src/haibot/app/approvals/service.py`, `src/haibot/cli/main.py`, and most provider tests.
- Frontend application code under `frontend/src/` generally uses 2-space indentation, single quotes, and no semicolons, as seen in `frontend/src/stores/app.ts`, `frontend/src/stores/auth.ts`, and `frontend/src/modules/chat/ChatLayout.vue`.
- Frontend config files are less uniform. `frontend/vite.config.ts` uses double quotes and semicolons, so config files should match nearby style instead of forcing the application-file style.

**Linting:**
- `pre-commit` is the repository’s main quality gate via `.pre-commit-config.yaml`.
- Python checks include Black, Flake8, mypy, pylint, and hygiene hooks such as `check-yaml`, `check-json`, and `trailing-whitespace`.
- Flake8 is intentionally relaxed in `.flake8`: `F401`, `F403`, `W503`, and `E731` are ignored, and `max-line-length` remains 79.
- mypy is configured only through `.pre-commit-config.yaml`; there is no standalone `mypy.ini`. The hook ignores missing imports, skips import following, and disables several error codes, so typing is encouraged but not maximally strict.
- pylint is also configured only in `.pre-commit-config.yaml` and disables many style and complexity checks. Local suppressions are accepted where framework behavior or orchestration code makes them necessary.
- Frontend linting beyond Prettier is not detected. No `eslint.config.*`, `.eslintrc*`, `biome.json`, or frontend test linter config is present.

**Representative Python import pattern from `src/haibot/app/approvals/service.py`:**
```python
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ...security.tool_guard.approval import ApprovalDecision
```

**Representative frontend import pattern from `frontend/src/stores/auth.ts`:**
```ts
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import api from '@/api/index'
import {
  authStatus,
  login as loginApi,
  register as registerApi,
} from '@/api/auth'
```

## Import Organization

**Order:**
1. Python files usually start with an encoding header and may add `from __future__ import annotations`.
2. Standard-library imports come first, followed by third-party imports, then local or relative imports separated by blank lines.
3. File-local exceptions are allowed when startup behavior matters, for example lazy imports in `src/haibot/cli/main.py` use `# noqa: E402` and `# pylint: disable=wrong-import-position`.

**Path Aliases:**
- Frontend path alias `@/*` resolves to `frontend/src/*` via `frontend/tsconfig.app.json`.
- Frontend modules prefer `@/` imports for app code and relative imports only for same-feature files, for example `frontend/src/api/chats.ts` importing `./index`.
- Python code uses package-relative imports inside `src/haibot/` and package-absolute imports in tests, for example `from haibot.cli.main import cli` in `tests/unit/cli/test_cli_update.py`.

## Typing

**Python:**
- Type annotations are common on public functions, helper functions, and model attributes. Files like `src/haibot/cli/update_cmd.py`, `src/haibot/app/approvals/service.py`, and `src/haibot/app/routers/providers.py` annotate parameters and return types consistently.
- Two syntax styles coexist:
  - Modern built-in generics and PEP 604 unions in newer files, for example `list[int]` and `str | None` in `src/haibot/cli/update_cmd.py` and `src/haibot/cli/main.py`.
  - Older `typing.List`, `typing.Dict`, and `Optional[...]` syntax in Pydantic-heavy modules such as `src/haibot/config/config.py` and `src/haibot/app/routers/providers.py`.
- Follow the surrounding file’s existing style instead of mass-converting annotation syntax in unrelated edits.
- Pydantic models define persisted and API contracts in `src/haibot/config/config.py`, `src/haibot/providers/provider.py`, `src/haibot/app/routers/*.py`, and `src/haibot/app/runner/models.py`.
- `@dataclass` is used for internal state and policy records in `src/haibot/app/approvals/service.py`, `src/haibot/providers/retry_chat_model.py`, and `src/haibot/security/tool_guard/models.py`.
- `TYPE_CHECKING`, `Protocol`, and `TypedDict` are used where interface contracts or import-cycle avoidance matter, for example `src/haibot/app/channels/schema.py` and `src/haibot/agents/schema.py`.

**Frontend:**
- TypeScript strict mode is enabled in `frontend/tsconfig.app.json` with `strict`, `noUnusedLocals`, `noUnusedParameters`, and `noFallthroughCasesInSwitch`.
- Frontend DTOs are defined with `interface` and `type` in `frontend/src/types/*.ts` and reused from API modules and stores.
- `import type` is used regularly in `frontend/src/modules/chat/ChatLayout.vue`, `frontend/src/api/chats.ts`, and `frontend/src/stores/settings.ts`.
- Escape hatches exist but are not the default. `as any` appears in a few frontend files such as `frontend/src/stores/auth.ts`, `frontend/src/api/auth.ts`, and settings pages where library typings are inconvenient.

## Error Handling

**Patterns:**
- FastAPI route handlers raise `HTTPException` with explicit `status_code` and `detail`, for example in `src/haibot/app/routers/providers.py`, `src/haibot/app/runner/api.py`, and `src/haibot/app/agent_context.py`.
- CLI code raises `click.ClickException` for user-facing failures, for example `_fetch_latest_version` in `src/haibot/cli/update_cmd.py`.
- Provider and service methods often normalize failures into tuples or sentinel values instead of propagating raw SDK errors, for example `check_connection` and `check_model_connection` paths in `src/haibot/providers/openai_provider.py`, `src/haibot/providers/gemini_provider.py`, and `src/haibot/providers/anthropic_provider.py`.
- Exception chaining with `raise ... from exc` is used when preserving cause matters, for example in `src/haibot/cli/update_cmd.py`, `src/haibot/providers/retry_chat_model.py`, and `src/haibot/tunnel/binary_manager.py`.
- Broad exception catches are accepted in channel/runtime code when the system must keep running, but they are usually paired with logging. Examples appear throughout `src/haibot/app/channels/qq/channel.py`, `src/haibot/app/channels/xiaoyi/channel.py`, and `src/haibot/app/channels/matrix/channel.py`.
- Frontend transport errors are normalized in `frontend/src/api/index.ts`. Stores either intentionally swallow non-critical errors, as in `frontend/src/stores/app.ts`, or surface them via UI messaging and thrown `Error` objects.

## Logging

**Framework:** Python standard-library `logging`

**Patterns:**
- Modules typically create a module logger with `logger = logging.getLogger(__name__)`, for example `src/haibot/cli/main.py`, `src/haibot/app/approvals/service.py`, and `src/haibot/providers/openai_provider.py`.
- Operational milestones are logged with `info`, transient or recoverable issues with `warning`, and unexpected failures with `error` or `exception`.
- `%s` placeholder formatting is common in logging calls, for example `src/haibot/providers/provider_manager.py` and `src/haibot/security/skill_scanner/scanner.py`.
- f-strings also appear in some logging code, for example `src/haibot/cli/main.py` and `src/haibot/app/channels/qq/channel.py`. Match the local file rather than mixing styles inside one edit.
- A structured frontend logging framework is not detected. User-facing feedback in the frontend is usually handled with Element Plus messaging or silent fallbacks, as seen in `frontend/src/modules/chat/ChatLayout.vue` and `frontend/src/stores/app.ts`.

## Comments

**When to Comment:**
- Use module, class, and function docstrings for public behavior and non-obvious flow. This is common across backend modules such as `src/haibot/providers/provider.py`, `src/haibot/providers/ollama_manager.py`, and `src/haibot/app/approvals/service.py`.
- Use inline comments sparingly for platform quirks, lazy import rationale, and high-level sectioning. Examples appear in `src/haibot/cli/main.py`, `src/haibot/config/config.py`, and `frontend/src/modules/chat/ChatLayout.vue`.
- Large files often use divider comments to separate concerns, especially tests like `tests/unit/channels/test_qq_channel.py`.

**JSDoc/TSDoc:**
- Python docstrings are common and usually short, imperative descriptions.
- Frontend JSDoc appears mainly in API and type files such as `frontend/src/api/chats.ts`, `frontend/src/api/console.ts`, `frontend/src/api/workspace.ts`, and `frontend/src/types/agent.ts`.
- Vue components sometimes use concise `/** ... */` comments for tricky behavior, for example scroll handling in `frontend/src/modules/chat/components/ChatWindow.vue`.

## Function Design

**Size:** Keep helper functions small unless the file is an orchestration hotspot.
- Small, focused helpers are common in `src/haibot/cli/update_cmd.py`, `src/haibot/providers/provider.py`, and `frontend/src/api/chats.ts`.
- Large orchestration files are tolerated when they coordinate network state, streaming, or multi-channel behavior. These files often carry targeted pylint suppressions, for example `src/haibot/app/channels/qq/channel.py`, `src/haibot/app/runner/runner.py`, and `src/haibot/agents/tools/browser_control.py`.

**Parameters:** Prefer explicit, typed parameters over generic bags.
- Backend APIs wrap payloads in Pydantic models, for example `ProviderConfigRequest` in `src/haibot/app/routers/providers.py`.
- Keyword-only parameters appear when call-site clarity matters, for example `ApprovalService.create_pending` in `src/haibot/app/approvals/service.py`.
- Frontend API helpers usually accept typed DTOs plus explicit optional IDs, for example `streamQuery` in `frontend/src/api/chats.ts`.

**Return Values:** Return concrete shapes and keep side effects obvious.
- Backend functions commonly return `None`, booleans, `(success, message)` tuples, or Pydantic models depending on role.
- Frontend API wrappers usually return typed payloads with `.then((r) => r.data)`, for example `listChats` and `createChat` in `frontend/src/api/chats.ts`.
- Pinia stores return refs plus action functions from the store factory, as in `frontend/src/stores/app.ts` and `frontend/src/stores/auth.ts`.

## Module Design

**Exports:** Prefer direct module exports over indirection.
- Python modules typically expose classes and functions directly from the file they live in. Private helpers stay private with `_` prefixes, for example `_detect_running_service` in `src/haibot/cli/update_cmd.py`.
- Tests and callers usually import from concrete modules such as `haibot.cli.main`, `haibot.providers.openai_provider`, or `haibot.app.group_chat.runtime`.
- Package `__init__.py` files exist, but Python barrel-style re-exporting is not a dominant pattern in `src/haibot/`.

**Barrel Files:** Limited and mostly frontend-specific.
- Frontend uses `frontend/src/types/index.ts` to re-export domain types.
- `frontend/src/api/index.ts` is an infrastructure module exporting the configured Axios client plus helpers, not a broad barrel of every API function.
- `frontend/src/router/index.ts` and `frontend/src/i18n/index.ts` act as single-entry modules for those subsystems.
- Additional barrel layers are not common elsewhere. If adding a new frontend domain type, extend `frontend/src/types/index.ts`; otherwise prefer direct imports.

---

*Convention analysis: 2026-03-27*
