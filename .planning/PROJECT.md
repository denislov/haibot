# HaiBot

## What This Is

HaiBot is a self-hosted multi-agent assistant platform with a FastAPI
backend, a packaged Vue web console, multiple channel integrations, and a
tool/skill/MCP runtime that runs in the user's own environment. This
planning project focuses on evolving the existing brownfield product so the
console can render richer multimodal chat output and agents can invoke
external coding CLIs with their live transcript shown in the same chat
experience.

## Core Value

Agent conversations must stay locally controlled, inspectable, and useful
even when they include richer media output and long-running external tool
execution.

## Requirements

### Validated

- ✓ User can run HaiBot locally with a FastAPI backend and packaged web
  console — existing
- ✓ User can chat with agents through the web console and multiple external
  channels — existing
- ✓ User can manage agents, models, tools, envs, skills, MCP, group chats,
  and security settings from the product — existing
- ✓ Agents can use built-in tools, skills, memory, and multi-agent workspace
  runtime features — existing
- ✓ The runtime already supports streaming chat updates, reconnectable
  console sessions, and persisted chat history — existing

### Active

- [ ] The console can render non-text chat blocks for image, audio, and
  video content in live streams and persisted history.
- [ ] Agents can invoke Claude Code CLI, Codex CLI, and Gemini CLI through
  first-class tools without breaking the current tool approval/runtime
  model.
- [ ] CLI transcript/progress output is streamed into the same backend and
  frontend chat surfaces users already use for agent conversations.

### Out of Scope

- Native mobile app support — this milestone stays within the existing web
  console and backend runtime.
- A general multimedia composition/upload redesign — scope is rendering and
  transport of emitted blocks, not a new authoring workflow.
- Arbitrary support for every external CLI — this milestone is explicitly
  bounded to Claude Code CLI, Codex CLI, and Gemini CLI.

## Context

This is a brownfield Python/Vue codebase. The current architecture and
conventions are documented in `.planning/codebase/`. The backend is centered
around `src/haibot/app/`, `src/haibot/agents/`, and `src/haibot/providers/`,
while the editable frontend lives in `frontend/src/` and packaged static
assets live in `src/haibot/console/`.

The current chat UI already supports text-centric message rendering with
specialized blocks such as markdown, reasoning, and tool-call views. The
agent runtime already has a tool guard, shell/file/browser tools, approval
flows, reconnectable chat streaming, and persisted session history. The new
work should extend those existing pathways rather than invent a parallel
runtime or a second chat event model.

The immediate product need comes from two user-visible gaps:
- non-text `image_block`, `audio_block`, and `video_block` content is not
  surfaced well enough in the current console experience
- external coding assistants invoked from the agent runtime are not yet
  modeled as first-class tools with frontend-visible transcript streaming

## Constraints

- **Tech stack**: Build on the existing FastAPI + AgentScope runtime + Vue
  console architecture — avoid introducing a separate backend service or a
  separate frontend app.
- **Compatibility**: Existing text, reasoning, tool-call, and chat-history
  flows must keep working while richer blocks are added.
- **Safety**: External CLI execution must respect the current approval and
  security posture instead of bypassing tool guard or shell boundaries.
- **UX**: CLI progress must appear in the same chat session users already
  watch, not in a disconnected log-only surface.
- **Brownfield reality**: Changes must account for the existing packaged
  frontend flow (`frontend/` source and `src/haibot/console/` bundle).

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Treat this as a brownfield enhancement, not a rewrite | Existing runtime, chat UX, and settings surfaces already solve most of the product | ✓ Good |
| Keep the milestone bounded to image/audio/video rendering plus 3 named CLIs | Prevents the roadmap from expanding into a generic process-orchestration platform | ✓ Good |
| Stream CLI progress into the main chat contract instead of a side panel | Users need one conversation surface for prompts, tool activity, and outputs | — Pending |
| Use PRD-style planning input instead of a separate discuss step for this request | The user already provided a focused implementation brief | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-27 after initialization*
