---
status: resolved
trigger: "Investigate issue: structured-output-optional"
created: 2026-03-27T00:00:00+08:00
updated: 2026-03-27T23:30:37+08:00
---

## Current Focus

hypothesis: Confirmed and resolved.
test: Parsed each built-in tool function individually with AgentScope, then re-ran toolkit registration after the fix.
expecting: The three external CLI tools should no longer raise `_StructuredOutputDynamicClass` / `Optional` errors.
next_action: None.

## Symptoms

expected: After starting the current project and sending `hello` in the console channel, the agent should initialize and reply normally.
actual: Query handling fails before reply generation, during agent/toolkit setup.
errors: `pydantic.errors.PydanticUserError: `_StructuredOutputDynamicClass` is not fully defined; you should define `Optional`, then call `_StructuredOutputDynamicClass.model_rebuild()`.` The traceback points through `HaiBotAgent._create_toolkit()` -> `toolkit.register_tool_function()` -> `agentscope._utils._common._parse_tool_function()` -> `base_model.model_json_schema()`.
reproduction: Start the app, trigger a console query with `hello`, and observe failure while registering tool functions.
started: Observed on 2026-03-27 in the current workspace. Prior known-good state is unknown.

## Eliminated

## Evidence

- timestamp: 2026-03-27T00:03:00+08:00
  checked: .planning/debug/knowledge-base.md
  found: No knowledge base file exists in this workspace.
  implication: There is no prior resolved debug pattern to apply; investigation proceeds from code and runtime evidence.

- timestamp: 2026-03-27T00:04:00+08:00
  checked: default `python` interpreter import of `agentscope`
  found: `ModuleNotFoundError: No module named 'agentscope'`
  implication: The shell's default interpreter is not the project runtime used by the app, so reproductions and dependency inspection must account for the project environment.

- timestamp: 2026-03-27T00:08:00+08:00
  checked: `pyproject.toml` runtime dependencies and local environment markers
  found: The project pins `agentscope==1.0.17`, has a local `.venv`, and exposes `haibot` as the app entrypoint.
  implication: The bug should be reproducible and fixable against the checked-in code plus the local virtualenv dependency set.

- timestamp: 2026-03-27T00:09:00+08:00
  checked: `src/haibot/agents/react_agent.py`
  found: `HaiBotAgent` registers built-in tools, group-chat delegation tools, skill tools, and memory search via `toolkit.register_tool_function(...)` before or during agent initialization.
  implication: Any single registered tool with a problematic annotation can block all query handling before reply generation, matching the reported symptom.

- timestamp: 2026-03-27T00:13:00+08:00
  checked: `.venv/lib/python3.12/site-packages/agentscope/_utils/_common.py`
  found: `agentscope._utils._common._parse_tool_function()` builds `_StructuredOutputDynamicClass` from function parameter annotations via `pydantic.create_model(...)` and immediately calls `base_model.model_json_schema()`.
  implication: The reported error is caused by unresolved parameter annotations on a registered tool function, not by the tool's return type.

- timestamp: 2026-03-27T23:20:00+08:00
  checked: Built-in tool functions under `.venv`
  found: Only `run_claude_code_cli`, `run_codex_cli`, and `run_gemini_cli` failed `_parse_tool_function(...)`; all other built-in tools parsed successfully.
  implication: The crash is isolated to `src/haibot/agents/tools/external_cli.py`.

- timestamp: 2026-03-27T23:22:00+08:00
  checked: `src/haibot/agents/tools/external_cli.py`
  found: The module enabled `from __future__ import annotations`, so its tool signatures exposed string annotations like `'Optional[str]'` to AgentScope/Pydantic.
  implication: Removing postponed evaluation from this module should unblock tool schema generation without changing runtime behavior.

- timestamp: 2026-03-27T23:26:00+08:00
  checked: Post-fix schema parsing and toolkit registration
  found: `_parse_tool_function(...)` succeeded for all built-in tools, and `Toolkit.register_tool_function(...)` registered all 16 tools successfully.
  implication: `HaiBotAgent._create_toolkit()` no longer fails on the reported code path.

## Resolution

root_cause: `src/haibot/agents/tools/external_cli.py` used postponed annotations, so the three external CLI tool functions exposed unresolved string annotations such as `Optional[str]`. AgentScope forwarded those unresolved annotations into `pydantic.create_model(...)`, which triggered the reported `_StructuredOutputDynamicClass` error during schema generation.
fix: Removed `from __future__ import annotations` from `src/haibot/agents/tools/external_cli.py` so AgentScope receives concrete typing objects for the registered tool parameters. Added a regression test that parses the three external CLI tool schemas through AgentScope.
verification:
  - `.venv/bin/python` script: `_parse_tool_function(...)` now passes for all built-in tools.
  - `.venv/bin/python` script: `Toolkit.register_tool_function(...)` now registers all 16 built-in tools successfully.
  - `.venv/bin/pytest tests/unit/agents/test_external_cli_tools.py`: 7 passed.
files_changed:
  - src/haibot/agents/tools/external_cli.py
  - tests/unit/agents/test_external_cli_tools.py
