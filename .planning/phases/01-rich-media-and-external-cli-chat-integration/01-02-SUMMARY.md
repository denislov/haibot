---
phase: 01-rich-media-and-external-cli-chat-integration
plan: 02
subsystem: infra
tags: [cli, claude, codex, gemini, tools]
requires:
  - phase: 01
    provides: rich media/tool-output display contract shared by chat history and SSE
provides:
  - dedicated Claude Code CLI wrapper
  - dedicated Codex CLI wrapper
  - dedicated Gemini CLI wrapper
  - built-in tool registration and config exposure for external coding CLIs
affects: [chat-ui, tool-settings, approvals]
tech-stack:
  added: []
  patterns: [provider-specific non-interactive CLI adapters, structured tool output payloads]
key-files:
  created: [src/haibot/agents/tools/external_cli.py, tests/unit/agents/test_external_cli_tools.py]
  modified: [src/haibot/agents/tools/__init__.py, src/haibot/agents/react_agent.py, src/haibot/config/config.py]
key-decisions:
  - "Return structured JSON ToolResponse payloads with provider, command, status, exit_code, output, and stderr so the existing tool-call UI can render transcript details."
  - "Use provider-specific non-interactive flags (`claude --print`, `codex exec --json`, `gemini -p ... --output-format stream-json`) instead of forcing a generic shell recipe."
  - "Allow Gemini help-probe timeout while still supporting execution, because the installed Gemini CLI exposes non-interactive flags in its shipped config source but does not return promptly for `--help` in this environment."
patterns-established:
  - "External coding CLIs should be wrapped in first-class built-in tools, not hidden behind execute_shell_command prompts."
  - "CLI wrappers should normalize availability, timeout, and failure states into one JSON tool output shape."
requirements-completed: [CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, SAFE-01, SAFE-02, SAFE-03, MSG-02]
duration: 4min
completed: 2026-03-27
---

# Phase 1: Rich Media and External CLI Chat Integration Summary

**HaiBot now has first-class Claude Code, Codex, and Gemini CLI tools that return structured transcript-capable output through the existing tool-call lifecycle.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-26T17:49:56Z
- **Completed:** 2026-03-26T17:54:03Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Added a shared external CLI helper with provider-specific command builders
  for Claude Code, Codex, and Gemini.
- Registered the three wrappers as built-in HaiBot tools so they participate
  in normal tool toggles and approval flow.
- Added focused unit coverage for unavailable, unsupported, timeout, and
  successful transcript-returning CLI executions.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement a shared external CLI helper and three named tools** -
   `96aef12` (`feat`)
2. **Task 2: Register the new tools and preserve approval semantics** -
   `1343257` (`feat`)
3. **Task 3: Cover failure modes and transcript normalization with tests** -
   `6a21822` (`test`)

**Plan metadata:** pending summary/state commit

## Files Created/Modified

- `src/haibot/agents/tools/external_cli.py` - provider-specific non-interactive
  wrappers and shared subprocess execution helper
- `src/haibot/agents/tools/__init__.py` - exports the new CLI wrappers
- `src/haibot/agents/react_agent.py` - registers the new built-in tools in the
  toolkit map
- `src/haibot/config/config.py` - exposes the three CLI tools in default tool
  configuration
- `tests/unit/agents/test_external_cli_tools.py` - verifies missing executable,
  unsupported probe, timeout, and success payloads

## Decisions Made

- CLI wrappers return one structured JSON string instead of raw free-form text
  so downstream rendering can show command, status, transcript, and stderr
  together.
- The new CLIs are first-class tools and therefore stay inside existing
  tool-toggle and approval mechanisms.
- Gemini support remains enabled even though `gemini --help` hangs locally,
  because the installed CLI package exposes non-interactive `-p` and
  `--output-format` flags in its shipped config implementation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Gemini help probe did not return in the local environment**
- **Found during:** Task 1 (Implement a shared external CLI helper and three named tools)
- **Issue:** The installed `gemini` binary existed, but `gemini --help` and
  related read-only probes did not emit output before timeout.
- **Fix:** Confirmed non-interactive flags from the installed CLI's shipped
  source, then treated Gemini probe timeout as allowable while still enforcing
  timeout on the actual command execution path.
- **Files modified:** `src/haibot/agents/tools/external_cli.py`
- **Verification:** `tests/unit/agents/test_external_cli_tools.py` covers the
  timeout path and successful normalized payload generation.
- **Committed in:** `96aef12` (part of Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The deviation preserved phase scope and avoided disabling
Gemini support due to an environment-specific help behavior.

## Issues Encountered

- None beyond the handled Gemini probe behavior.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The runtime can now call the three external coding CLIs through dedicated
  tools.
- The remaining work is purely frontend-facing: render media blocks and present
  structured CLI output more clearly in the existing chat UI.

## Self-Check: PASSED

- Verified `tests/unit/agents/test_external_cli_tools.py` passes
- Verified runtime registration/config changes are present in tool exports and
  built-in tool defaults

---
*Phase: 01-rich-media-and-external-cli-chat-integration*
*Completed: 2026-03-27*
