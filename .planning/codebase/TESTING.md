# Testing Patterns

**Analysis Date:** 2026-03-27

## Test Framework

**Runner:**
- `pytest` is the test runner, declared in the `dev` extra in `pyproject.toml`.
- Async support comes from `pytest-asyncio`, also declared in `pyproject.toml`.
- Config lives in `pyproject.toml` under `[tool.pytest.ini_options]` with `asyncio_mode = "auto"` and `asyncio_default_fixture_loop_scope = "function"`.
- No separate `pytest.ini`, `tox.ini`, or `noxfile` is detected.
- No frontend test runner config is detected under `frontend/`; `vitest.config.*`, `jest.config.*`, and browser E2E config files are absent.

**Assertion Library:**
- Tests use plain `assert` statements and `pytest` helpers such as `pytest.raises` and `pytest.fail`.
- CLI tests rely on `click.testing.CliRunner`, for example `tests/unit/cli/test_cli_shutdown.py` and `tests/unit/cli/test_cli_update.py`.
- Integration tests use `httpx` for real HTTP checks in `tests/integrated/test_app_startup.py`.

**Run Commands:**
```bash
python scripts/run_tests.py -a           # Run all unit and integrated tests
python scripts/run_tests.py -u providers # Run one unit slice
# Watch mode: Not detected
python scripts/run_tests.py -a -c        # Coverage + htmlcov/index.html
```

## Test File Organization

**Location:**
- Tests are stored in a separate top-level `tests/` tree rather than co-located with source files.
- Unit tests live under `tests/unit/<area>/test_*.py`, for example `tests/unit/providers/test_openai_provider.py`, `tests/unit/cli/test_cli_update.py`, `tests/unit/workspace/test_agent_model.py`, and `tests/unit/group_chat/test_runtime.py`.
- Integration tests live under `tests/integrated/test_*.py`, currently `tests/integrated/test_app_startup.py` and `tests/integrated/test_version.py`.
- Frontend tests are not present. No `*.spec.ts`, `*.test.ts`, `*.spec.vue`, or `*.test.vue` files are detected under `frontend/`.

**Naming:**
- Python test files follow the `test_*.py` naming pattern.
- Helper-heavy modules may group cases in `Test...` classes, as in `tests/unit/channels/test_qq_channel.py`.
- Simpler modules use flat `test_*` functions, as in `tests/unit/providers/test_openai_provider.py` and `tests/unit/workspace/test_workspace.py`.

**Structure:**
```text
tests/
├── integrated/
│   ├── test_app_startup.py
│   └── test_version.py
└── unit/
    ├── channels/
    ├── cli/
    ├── group_chat/
    ├── providers/
    └── workspace/
```

## Test Structure

**Suite Organization:**
- Most files keep builders and fixtures at the top, then place tests below them. `tests/unit/providers/test_openai_provider.py` starts with `_make_provider()` and then a run of focused async tests.
- Very large surface-area modules may use class-based grouping for related helper behavior. `tests/unit/channels/test_qq_channel.py` groups cases under classes like `TestSanitizeQQText`, `TestAsBool`, and `TestWSState`.

**Pattern from `tests/unit/providers/test_openai_provider.py`:**
```python
def _make_provider(is_custom: bool = False) -> OpenAIProvider:
    return OpenAIProvider(...)


async def test_check_connection_success(monkeypatch) -> None:
    provider = _make_provider()
    ...
    ok, msg = await provider.check_connection(timeout=2.5)

    assert ok is True
    assert msg == ""
```

**Pattern from `tests/unit/channels/test_qq_channel.py`:**
```python
class TestSanitizeQQText:
    def test_single_url(self):
        text, removed = _sanitize_qq_text("visit https://example.com now")
        assert removed is True
        assert "https://example.com" not in text
```

**Patterns:**
- Setup pattern: use local helper constructors such as `_make_provider` in `tests/unit/providers/test_openai_provider.py`, `_install_info` in `tests/unit/cli/test_cli_update.py`, and `_make_channel` in `tests/unit/channels/test_qq_channel.py`.
- Teardown pattern: rely on fixture cleanup (`tmp_path`, `TemporaryDirectory`) for unit tests; use explicit `finally` cleanup for subprocess-based integration tests in `tests/integrated/test_app_startup.py`.
- Assertion pattern: prefer direct state assertions; add custom assertion messages only around process/network checks where failure context matters.

## Mocking

**Framework:** `pytest` `monkeypatch` plus `unittest.mock`

**Patterns:**
- `monkeypatch.setattr(...)` is the dominant technique for replacing collaborators, for example provider clients in `tests/unit/providers/test_openai_provider.py` and CLI helpers in `tests/unit/cli/test_cli_shutdown.py`.
- `AsyncMock`, `MagicMock`, and `patch` are used when the unit under test depends on async methods or complex object graphs, especially in `tests/unit/channels/test_qq_channel.py` and `tests/unit/workspace/test_cli_agent_id.py`.
- Environment mutation uses `monkeypatch.setenv(...)` and `monkeypatch.delenv(...)`, for example `tests/unit/providers/test_ollama_provider.py` and `tests/unit/providers/test_ollama_manager_timeout.py`.

**Representative pattern from `tests/unit/cli/test_cli_shutdown.py`:**
```python
monkeypatch.setattr(
    "haibot.cli.shutdown_cmd._terminate_pid",
    lambda _pid: True,
)

result = CliRunner().invoke(cli, ["shutdown"])

assert result.exit_code == 0
```

**Representative pattern from `tests/unit/providers/test_openai_provider.py`:**
```python
fake_client = SimpleNamespace(models=FakeModels())
monkeypatch.setattr(provider, "_client", lambda timeout=5: fake_client)

ok, msg = await provider.check_connection(timeout=2.5)
assert ok is True
```

**What to Mock:**
- SDK clients and transport layers in provider tests, for example `_client` methods in `tests/unit/providers/test_openai_provider.py`, `tests/unit/providers/test_gemini_provider.py`, and `tests/unit/providers/test_anthropic_provider.py`.
- Filesystem roots and persisted config locations, for example `WORKING_DIR` in `tests/unit/workspace/test_agent_model.py` and `SECRET_DIR` in `tests/unit/providers/test_provider_manager.py`.
- CLI subprocess, HTTP, and process-discovery helpers in `tests/unit/cli/test_cli_update.py` and `tests/unit/cli/test_cli_shutdown.py`.
- Internal async methods on channel objects in `tests/unit/channels/test_qq_channel.py`.

**What NOT to Mock:**
- `tests/integrated/test_app_startup.py` deliberately boots the real package through `python -m haibot app` and checks real HTTP endpoints. Follow that pattern for end-to-end startup coverage.
- The current suite does not use `FastAPI TestClient`. Integration coverage goes through subprocess plus network instead of in-process app clients.
- Frontend component, store, or browser behavior is not tested at all, so there is no established frontend mocking pattern to copy.

## Fixtures and Factories

**Test Data:**
- Fixtures are defined inline in the module that uses them. Shared fixtures are not centralized.
- Common fixture patterns patch a temporary workspace or secret directory and then build only the files needed by the test.

**Pattern from `tests/unit/workspace/test_agent_model.py`:**
```python
@pytest.fixture
def mock_agent_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr("haibot.config.utils.WORKING_DIR", tmp_path)
    monkeypatch.setattr("haibot.config.config.WORKING_DIR", tmp_path)
    ...
    return workspace_dir
```

**Pattern from `tests/unit/providers/test_provider_manager.py`:**
```python
@pytest.fixture
def isolated_secret_dir(monkeypatch, tmp_path):
    secret_dir = tmp_path / ".haibot.secret"
    monkeypatch.setattr(provider_manager_module, "SECRET_DIR", secret_dir)
    return secret_dir
```

**Location:**
- Inline fixtures exist in `tests/unit/providers/test_kimi_provider.py`, `tests/unit/providers/test_provider_manager.py`, `tests/unit/workspace/test_prompt.py`, `tests/unit/workspace/test_agent_model.py`, and `tests/unit/workspace/test_cli_agent_id.py`.
- No shared `tests/conftest.py` is detected.
- No `tests/fixtures/` or `tests/factories/` directory is detected.
- Builders are usually plain helper functions at module scope rather than factory classes.

## Coverage

**Requirements:** None enforced
- `pytest-cov` is installed through the `dev` extra in `pyproject.toml`.
- `scripts/run_tests.py` adds `--cov=src/haibot --cov-report=html --cov-report=term-missing` when `-c/--coverage` is passed.
- No `fail_under` threshold or separate coverage policy config is detected in `pyproject.toml` or other config files.
- A `slow` marker is declared in `pyproject.toml`, but no tests currently use `@pytest.mark.slow`.
- `hypothesis` is listed in the `dev` extra in `pyproject.toml`, but no property-based tests are present under `tests/`.

**View Coverage:**
```bash
python scripts/run_tests.py -a -c
```

## Test Types

**Unit Tests:**
- Unit tests isolate one module or command and heavily replace collaborators with `monkeypatch` or mocks.
- Provider tests in `tests/unit/providers/` validate request shaping, normalization, and config persistence without hitting real APIs.
- CLI tests in `tests/unit/cli/` exercise command behavior through `CliRunner`.
- Workspace and group chat tests in `tests/unit/workspace/` and `tests/unit/group_chat/` use temporary directories or in-memory model objects rather than real long-running services.

**Integration Tests:**
- Integration tests are few and broad.
- `tests/integrated/test_app_startup.py` launches the real app as a subprocess, waits for `/api/version`, then checks `/console/` returns HTML.
- `tests/integrated/test_version.py` verifies packaging/version behavior through import and subprocess execution.
- Integration tests use real subprocess and socket/HTTP behavior rather than in-process web test clients.

**E2E Tests:** Not used
- No Playwright, Cypress, Selenium, or browser automation test suite is detected.
- No frontend unit test runner is detected under `frontend/`.
- The runtime dependency on `playwright` in `pyproject.toml` is for application functionality, not for test automation in this repository.

## Common Patterns

**Async Testing:**
- Async tests are common in provider and group-chat code.
- Because `asyncio_mode = "auto"` is enabled in `pyproject.toml`, some async tests omit `@pytest.mark.asyncio`, for example `tests/unit/providers/test_openai_provider.py`.
- Other files still add the marker explicitly, for example `tests/unit/group_chat/test_runtime.py` and `tests/unit/workspace/test_workspace.py`.

**Representative pattern from `tests/unit/group_chat/test_runtime.py`:**
```python
@pytest.mark.asyncio
async def test_group_chat_runtime_persists_transcript(tmp_path: Path):
    runtime = GroupChatRuntime("team", tmp_path / "group")
    ...
    history = await runtime.get_history("chat-1")

    assert history["status"] == "idle"
```

**Error Testing:**
- Validation and negative-path tests use `pytest.raises`, as in `tests/unit/providers/test_provider_manager.py` and `tests/unit/workspace/test_agent_model.py`.
- Provider connectivity tests often assert normalized failure tuples instead of exceptions, as in `tests/unit/providers/test_openai_provider.py` and `tests/unit/providers/test_gemini_provider.py`.

**Representative pattern from `tests/unit/providers/test_provider_manager.py`:**
```python
with pytest.raises(ValueError, match="Provider 'missing' not found"):
    await manager.activate_model("missing", "gpt-5")
```

**Process/CLI Testing:**
- CLI tests invoke the real Click entrypoint from `haibot.cli.main` and assert on `result.exit_code` and `result.output`.
- Integration tests that spawn subprocesses always include explicit cleanup, as shown in `tests/integrated/test_app_startup.py`.

---

*Testing analysis: 2026-03-27*
