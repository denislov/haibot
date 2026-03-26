# Phase 1: Rich Media and External CLI Chat Integration - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning
**Source:** PRD Express Path (`.planning/requests/phase-1-rich-media-and-cli.md`)

<domain>
## Phase Boundary

Extend the current backend message contract, agent tool surface, and Vue
console so users can see image/audio/video blocks and live or replayed Claude
Code, Codex, and Gemini CLI transcript output in one chat surface. This phase
does not redesign the full console information architecture and does not turn
HaiBot into a generic process orchestrator for arbitrary CLIs.

</domain>

<decisions>
## Implementation Decisions

### Rendering contract
- **D-01:** Reuse the existing runtime content types already emitted by
  `src/haibot/app/runner/utils.py` for `image`, `audio`, and `video` rather
  than inventing parallel backend-only aliases.
- **D-02:** Extend the frontend display-model pipeline so media blocks become
  first-class `DisplayBlock` variants instead of being silently dropped or
  treated as user-only attachments.
- **D-03:** Preserve ordering across text, reasoning, tool lifecycle, and
  media blocks by following the current streamed/history event sequence rather
  than reconstructing display order from separate arrays later.

### External CLI tooling
- **D-04:** Add three named built-in tools for Claude Code CLI, Codex CLI,
  and Gemini CLI instead of relying on free-form `execute_shell_command`
  prompts.
- **D-05:** Implement those three tools on top of one shared subprocess and
  transcript helper so timeout, cwd handling, cancellation, and output
  buffering stay consistent.
- **D-06:** Keep CLI transcript visibility inside the existing chat/tool-call
  surface rather than creating a separate log page or secondary transport.

### Safety and runtime behavior
- **D-07:** CLI-backed tools must respect the existing approval and tool-guard
  path instead of bypassing it with ad hoc shell execution.
- **D-08:** Live SSE rendering and persisted history replay must use the same
  message shape for new media and CLI transcript content.
- **D-09:** The implementation must fit the current brownfield packaging flow
  (`frontend/` source, `src/haibot/console/` bundle) rather than introducing a
  second frontend target.

### the agent's Discretion
- Exact Vue component split for media/transcript rendering
- Exact helper module names for the new CLI tool implementation
- Internal buffering policy for transcript chunk aggregation, as long as live
  display and replay semantics stay aligned

</decisions>

<specifics>
## Specific Ideas

- Render image/audio/video inline in the assistant chat flow, not in a
  detached asset tray.
- CLI transcript/progress should be visible where users already inspect
  tool-call output.
- The user specifically named Claude Code CLI, Codex CLI, and Gemini CLI;
  those names should appear in tooling and UX terminology.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and phase scope
- `.planning/PROJECT.md` — current project framing, active requirements, and
  brownfield constraints
- `.planning/ROADMAP.md` — phase goal, mapped requirements, canonical refs,
  and success criteria
- `.planning/REQUIREMENTS.md` — testable requirement contract for this phase
- `.planning/requests/phase-1-rich-media-and-cli.md` — original user request

### Codebase references
- `.planning/codebase/ARCHITECTURE.md` — runtime layers and chat/data flow
- `.planning/codebase/STRUCTURE.md` — file locations and subsystem boundaries
- `.planning/codebase/CONVENTIONS.md` — Python/TypeScript conventions to
  preserve
- `.planning/codebase/TESTING.md` — current testing patterns and gaps

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/haibot/app/runner/utils.py`: already converts AgentScope `image`,
  `audio`, and `video` blocks into runtime content objects
- `frontend/src/modules/chat/composables/useChat.ts`: central history and SSE
  event mapping layer for assistant/user display blocks
- `frontend/src/modules/chat/components/MessageBubble.vue`: current rendering
  hub for text, reasoning, and tool-call blocks
- `frontend/src/modules/chat/components/ToolCallBlock.vue`: existing surface
  that can likely host streamed CLI transcript output
- `src/haibot/agents/tools/shell.py`: subprocess execution patterns, timeout
  handling, and process cleanup behavior already exist here

### Established Patterns
- Built-in tools are declared in `src/haibot/config/config.py`, exported from
  `src/haibot/agents/tools/__init__.py`, and registered in
  `src/haibot/agents/react_agent.py`
- Tool enable/disable state is exposed through `src/haibot/app/routers/tools.py`
- Console chat input/output and streaming are mediated through
  `src/haibot/app/routers/console.py`, `src/haibot/app/channels/console/channel.py`,
  and `frontend/src/api/chats.ts`

### Integration Points
- Backend rich-block message creation: `src/haibot/app/runner/utils.py`
- Backend tool/approval path: `src/haibot/agents/react_agent.py`,
  `src/haibot/security/tool_guard/`, `src/haibot/app/approvals/service.py`
- Frontend display contract: `frontend/src/types/chat.ts`,
  `frontend/src/modules/chat/composables/useChat.ts`,
  `frontend/src/modules/chat/components/MessageBubble.vue`

</code_context>

<deferred>
## Deferred Ideas

- Additional coding CLIs beyond Claude Code, Codex, and Gemini CLI
- Dedicated transcript timeline or execution analytics UI
- Rich gallery/carousel treatment for large sets of generated media outputs

</deferred>

---

*Phase: 01-rich-media-and-external-cli-chat-integration*
*Context gathered: 2026-03-27*
