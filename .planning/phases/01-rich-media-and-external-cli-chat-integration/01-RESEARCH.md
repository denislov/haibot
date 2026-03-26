# Phase 1: Rich Media and External CLI Chat Integration - Research

**Researched:** 2026-03-27
**Status:** Ready for planning

## Summary

This phase is a brownfield extension, not a greenfield feature build. The
backend already understands image/audio/video content at the AgentScope-to-
runtime conversion layer, but the console display model only renders text,
reasoning, and tool-call blocks. The cleanest path is to extend the existing
display pipeline and tool-call UX instead of introducing a second event model.

For CLI integration, HaiBot already has subprocess execution patterns,
built-in tool registration, and approval handling. The safest approach is to
add three explicit tools backed by one shared helper and stream transcript
updates through the same chat/tool-call event pathway users already inspect.

## Existing System Findings

### Backend content support already exists
- `src/haibot/app/runner/utils.py` already converts AgentScope `image`,
  `audio`, and `video` blocks into runtime `ImageContent`, `AudioContent`,
  and `VideoContent`.
- `src/haibot/app/channels/console/channel.py` already recognizes image,
  audio, video, and file content types for console upload/reference
  resolution.
- This means the backend contract is partially present; the missing work is
  mostly at the display-model, streaming, replay, and tooling layers.

### Frontend display pipeline is the current bottleneck
- `frontend/src/types/chat.ts` defines `ContentItem` types for `image`,
  `audio`, and `video`, but `DisplayBlock.kind` currently only includes
  `text`, `tool_call`, `tool_output`, and `reasoning`.
- `frontend/src/modules/chat/composables/useChat.ts` maps history and SSE
  events only for text/data/tool lifecycle and does not materialize media
  display blocks.
- `frontend/src/modules/chat/components/MessageBubble.vue` only renders text,
  reasoning, and tool-call blocks.

### Tooling extension path is well-defined
- Built-in tools are defined in `src/haibot/config/config.py`,
  exported through `src/haibot/agents/tools/__init__.py`,
  and registered in `src/haibot/agents/react_agent.py`.
- Tool enable/disable UX already exists in `src/haibot/app/routers/tools.py`
  and the settings frontend.
- Approval and guarded execution already have central hooks in
  `src/haibot/security/tool_guard/` and `src/haibot/app/approvals/service.py`.

## Recommended Technical Approach

### 1. Keep one chat contract
- Do not invent a parallel "CLI transcript bus".
- Represent media blocks and transcript-bearing tool output in the same
  persisted/live message stream that the console already consumes.
- Keep live SSE handling and history replay aligned by using the same content
  shapes in both paths.

### 2. Extend the frontend display model explicitly
- Add new `DisplayBlock.kind` values for image, audio, and video rendering.
- Decide whether CLI transcript lives as:
  - streamed `toolOutput` inside the existing tool-call block, or
  - a dedicated `cli_transcript` display block
- For brownfield fit, prefer extending `ToolCallBlock` with streaming
  transcript/progress support rather than introducing a totally new top-level
  bubble type.

### 3. Add explicit CLI tools, not generic shell recipes
- Add dedicated tool entry points for Claude Code CLI, Codex CLI, and Gemini
  CLI.
- Route them through a shared helper that:
  - resolves cwd consistently
  - enforces timeout/cancellation
  - captures structured transcript chunks
  - returns normalized status/error payloads
- Keep generic `execute_shell_command` intact for other needs; do not overload
  it with product-specific transcript semantics.

### 4. Plan for both live and replayed transcript behavior
- A streaming-only implementation is insufficient; users explicitly need
  transcript visibility synchronized into the frontend and persisted in chat
  history.
- The stored message format should preserve transcript chunks or the final
  assembled transcript in a way the history loader can reconstruct.

## Risks and Pitfalls

### Ordering drift
- `useChat.ts` currently groups blocks by event/message type. Adding media and
  transcript support naively could reorder content relative to reasoning or
  tool lifecycle updates.
- Mitigation: preserve ordering by message id / stream sequence and update
  blocks in place only when the protocol indicates continuation.

### Brownfield packaging drift
- The repo uses `frontend/` as source but ships committed assets under
  `src/haibot/console/`.
- Mitigation: any execution plan touching frontend must include build/packaging
  verification, not just source edits.

### CLI environment variability
- The named CLIs may be missing, differently installed, or configured with
  different auth/env expectations.
- Mitigation: normalize "not installed / not configured / exit non-zero /
  timeout" states into explicit user-visible outcomes.

### Tool-guard bypass risk
- A thin wrapper around shell execution could accidentally bypass existing
  approval semantics.
- Mitigation: integrate via the normal built-in tool registry and current
  guard/approval pathway rather than hidden subprocess calls elsewhere.

## Validation Architecture

### Automated checks
- Python backend/unit slice:
  `pytest tests/unit/providers tests/unit/workspace tests/unit/cli -q`
- Full Python suite:
  `python scripts/run_tests.py -a`
- Frontend compile gate:
  `cd frontend && pnpm build`

### Manual-only checks
- Verify media blocks render correctly in the actual chat UI
- Verify CLI transcript streaming feels coherent during a live long-running
  run
- Verify reconnect/history replay reproduces the same visible output after
  refresh

### Feedback strategy
- After schema/backend task completion: run targeted Python tests
- After frontend rendering task completion: run frontend build and manual chat
  verification
- Before phase sign-off: run full Python suite plus frontend build

## Suggested Plan Split

### Plan 01
Define and persist the rich block / transcript contract across backend and
frontend display-model boundaries.

### Plan 02
Implement dedicated CLI tools and wire transcript streaming through the
runtime/tool path.

### Plan 03
Implement media rendering and transcript replay/visualization in the Vue chat
UI.

---

*Phase: 01-rich-media-and-external-cli-chat-integration*
*Research completed: 2026-03-27*
