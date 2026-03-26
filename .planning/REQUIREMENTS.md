# Requirements: HaiBot

**Defined:** 2026-03-27
**Core Value:** Agent conversations must stay locally controlled,
inspectable, and useful even when they include richer media output and
long-running external tool execution.

## v1 Requirements

Requirements for the current brownfield enhancement milestone.

### Rich Rendering

- [ ] **RICH-01**: User can see `image_block` content in the web console
  during live chat streaming and after reloading chat history.
- [ ] **RICH-02**: User can see `audio_block` content in the web console
  with inline playback controls during live chat streaming and after
  reloading chat history.
- [ ] **RICH-03**: User can see `video_block` content in the web console
  with inline playback controls or preview during live chat streaming and
  after reloading chat history.
- [ ] **RICH-04**: Mixed messages preserve ordering when text, reasoning,
  tool-call, image, audio, and video blocks are emitted together.

### CLI Tools

- [ ] **CLI-01**: Agent can invoke Claude Code CLI through a dedicated tool
  path instead of a hand-crafted shell workaround.
- [ ] **CLI-02**: Agent can invoke Codex CLI through a dedicated tool path
  instead of a hand-crafted shell workaround.
- [ ] **CLI-03**: Agent can invoke Gemini CLI through a dedicated tool path
  instead of a hand-crafted shell workaround.
- [ ] **CLI-04**: While one of these CLIs is running, the user can see
  transcript/progress updates inside the active chat session.
- [ ] **CLI-05**: Completed CLI runs persist enough structured output that a
  refreshed chat session shows the same transcript/result context users saw
  live.

### Runtime Safety

- [ ] **SAFE-01**: CLI-backed tool execution respects existing approval or
  denial flows before running external commands when approvals are enabled.
- [ ] **SAFE-02**: CLI-backed tool execution enforces bounded working
  directory, timeout, and failure reporting semantics compatible with the
  current tool runtime.
- [ ] **SAFE-03**: If a CLI is unavailable, exits non-zero, or times out,
  the chat session remains usable and shows actionable failure state.

### Message Contract

- [ ] **MSG-01**: Backend chat event and persisted message structures expose
  enough typed metadata for `image_block`, `audio_block`, and `video_block`
  rendering in the console.
- [ ] **MSG-02**: Backend chat event and persisted message structures expose
  enough typed metadata for streaming and replaying CLI transcript entries.
- [ ] **MSG-03**: Single-agent chat and group-chat views can share the same
  rendering contract for these new blocks where the underlying messages are
  available.

## v2 Requirements

### Extended Integrations

- **CLI-06**: Support additional external coding CLIs beyond Claude Code,
  Codex, and Gemini CLI.
- **RICH-05**: Add richer gallery/timeline UX for large media outputs.
- **OBS-01**: Add dedicated execution timeline or analytics views for
  long-running external tool sessions.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Generic arbitrary process orchestration UI | Too broad for the initial CLI-tool milestone |
| Non-web client redesign | Current request is about the existing frontend console |
| Media creation/editing workflow | This milestone is about rendering and replaying emitted blocks |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| RICH-01 | Phase 1 | Pending |
| RICH-02 | Phase 1 | Pending |
| RICH-03 | Phase 1 | Pending |
| RICH-04 | Phase 1 | Pending |
| CLI-01 | Phase 1 | Pending |
| CLI-02 | Phase 1 | Pending |
| CLI-03 | Phase 1 | Pending |
| CLI-04 | Phase 1 | Pending |
| CLI-05 | Phase 1 | Pending |
| SAFE-01 | Phase 1 | Pending |
| SAFE-02 | Phase 1 | Pending |
| SAFE-03 | Phase 1 | Pending |
| MSG-01 | Phase 1 | Pending |
| MSG-02 | Phase 1 | Pending |
| MSG-03 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 15 total
- Mapped to phases: 15
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-27*
*Last updated: 2026-03-27 after initial definition*
