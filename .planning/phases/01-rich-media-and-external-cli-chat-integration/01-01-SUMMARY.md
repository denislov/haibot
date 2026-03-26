---
phase: 01-rich-media-and-external-cli-chat-integration
plan: 01
subsystem: ui
tags: [media, sse, runner, preview, typescript]
requires: []
provides:
  - assistant rich media blocks now have an explicit frontend display contract
  - streamed chat mapping no longer drops assistant image/audio/video content
  - runner utility tests now cover rich media and tool-result conversion
affects: [external-cli-tools, chat-ui, group-chat]
tech-stack:
  added: []
  patterns: [preview-route-based local media rendering, lazy streamed content block creation]
key-files:
  created: [tests/unit/app/test_runner_utils.py]
  modified: [src/haibot/app/runner/utils.py, frontend/src/types/chat.ts, frontend/src/modules/chat/composables/useChat.ts]
key-decisions:
  - "Map local assistant media paths to `/api/files/preview...` URLs in the frontend instead of inventing a second backend media contract."
  - "Create streamed text blocks lazily on first text delta so media-only assistant messages do not leave empty text shells."
  - "Keep CLI transcript wiring on the existing tool-call `call_id` path and extend block typing instead of creating a detached transcript bubble type."
patterns-established:
  - "Assistant message history and SSE mapping should share the same block factory helpers."
  - "Runtime `file://` paths must normalize consistently for Unix and Windows before frontend preview routing."
requirements-completed: [MSG-01, MSG-02, MSG-03, RICH-04]
duration: 6min
completed: 2026-03-27
---

# Phase 1: Rich Media and External CLI Chat Integration Summary

**Rich media chat blocks now survive runtime conversion, history replay, and live SSE mapping without breaking the existing tool-call lifecycle.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-26T17:30:00Z
- **Completed:** 2026-03-26T17:36:29Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Added explicit frontend block typing for assistant image, audio, and video
  content.
- Taught the chat composable to map local media to preview URLs and to render
  rich content from both history and live SSE events.
- Added regression coverage for runner-side media conversion and tool-result
  payload preservation.

## Task Commits

Each task was committed atomically:

1. **Task 1: Lock the shared media and tool-output contract** - `cbdefb4`
   (`feat`)
2. **Task 2: Update history and SSE mapping to stop dropping rich content** -
   `0eb67d2` (`feat`)
3. **Task 3: Add regression tests for runtime message conversion** -
   `fcbe332` (`test`)

**Plan metadata:** pending summary/state commit

## Files Created/Modified

- `src/haibot/app/runner/utils.py` - normalizes local `file://` paths
  consistently for Unix and Windows preview routing
- `frontend/src/types/chat.ts` - defines explicit display block variants and
  media/tool metadata
- `frontend/src/modules/chat/composables/useChat.ts` - maps rich media content
  for history replay and live chat streaming
- `tests/unit/app/test_runner_utils.py` - covers runner-side rich media and
  tool-result conversion behavior

## Decisions Made

- Local assistant media should reuse the existing `/api/files/preview/...`
  route instead of adding a new backend transport.
- Text blocks for streamed assistant messages should be created lazily on first
  delta so media-only messages remain clean.
- Tool output replay continues to use `call_id` linkage so later CLI work can
  stream transcript updates through the existing tool-call surface.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `pytest` was not available on PATH in the sandbox, so verification used
  `./.venv/bin/python -m pytest ...` instead.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The chat contract for assistant rich media is explicit and verified.
- Wave 2 can now add dedicated CLI tools and UI rendering components without
  needing to redefine the underlying message model.

## Self-Check: PASSED

- Verified `tests/unit/app/test_runner_utils.py` passes
- Verified `cd frontend && pnpm build` passes after the contract/mapping
  changes

---
*Phase: 01-rich-media-and-external-cli-chat-integration*
*Completed: 2026-03-27*
