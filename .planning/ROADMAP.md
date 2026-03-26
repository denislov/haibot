# Roadmap: HaiBot

## Overview

This roadmap covers the current brownfield enhancement milestone for HaiBot.
The existing product already provides a multi-agent runtime, a web console,
streaming chat, tools, skills, MCP, and multiple channel integrations. This
milestone is focused on making that existing chat experience richer and more
powerful by adding multimodal block rendering and first-class external coding
CLI execution with transcript visibility in chat.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Rich Media and External CLI Chat Integration** - Add
  multimodal block rendering and chat-visible Claude Code, Codex, and Gemini
  CLI tooling to the existing HaiBot runtime and console.

## Phase Details

### Phase 1: Rich Media and External CLI Chat Integration
**Goal**: Extend the current backend message contract, agent tool surface, and Vue console so users can see image/audio/video blocks and live or replayed Claude Code, Codex, and Gemini CLI transcript output in one chat surface.
**Depends on**: Nothing (first phase)
**Requirements**: [RICH-01, RICH-02, RICH-03, RICH-04, CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, SAFE-01, SAFE-02, SAFE-03, MSG-01, MSG-02, MSG-03]
**UI hint**: yes
**Canonical refs**:
- `.planning/codebase/ARCHITECTURE.md` — current runtime composition and data
  flow
- `.planning/codebase/STRUCTURE.md` — current repository layout and key
  module boundaries
- `.planning/codebase/CONVENTIONS.md` — current Python/TypeScript coding
  conventions
- `.planning/codebase/TESTING.md` — current test structure and gaps
- `.planning/requests/phase-1-rich-media-and-cli.md` — user request driving
  this milestone
**Success Criteria** (what must be TRUE):
  1. User can receive and view `image_block`, `audio_block`, and `video_block` content in live chat and history replay without losing ordering relative to existing text, reasoning, and tool-call blocks.
  2. User can watch Claude Code, Codex, and Gemini CLI runs emit progress and transcript messages directly in the active chat session.
  3. Refreshing or reconnecting the console preserves enough stored message structure to replay media blocks and CLI transcript output accurately.
  4. Approval, timeout, unavailable CLI, and command failure states are shown clearly and do not break the rest of the chat session.
  5. Single-agent chat and group-chat paths stay compatible with the new rendering contract where the underlying messages are available.
**Plans**: 3 plans

Plans:
- [x] 01-01: Define and persist rich media block and CLI transcript message
  structures across backend chat flows
- [ ] 01-02: Add dedicated Claude Code, Codex, and Gemini CLI tools with
  streaming runtime integration
- [ ] 01-03: Render and replay rich media blocks and CLI transcript messages
  in the existing frontend chat UI

## Progress

**Execution Order:**
Phases execute in numeric order: 1

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Rich Media and External CLI Chat Integration | 1/3 | In Progress|  |
