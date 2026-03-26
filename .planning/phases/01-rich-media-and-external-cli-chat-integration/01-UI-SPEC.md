---
phase: 01
slug: rich-media-and-external-cli-chat-integration
status: draft
shadcn_initialized: false
preset: none
created: 2026-03-27
---

# Phase 01 — UI Design Contract

> Visual and interaction contract for frontend work in the existing HaiBot
> console.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none |
| Preset | not applicable |
| Component library | existing Element Plus app |
| Icon library | Element Plus icons |
| Font | inherit current app sans-serif + existing monospace blocks for tool output |

---

## Spacing Scale

Declared values (must be multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon gaps, inline status pills |
| sm | 8px | Media meta labels, compact padding |
| md | 16px | Default block spacing |
| lg | 24px | Card padding and section gaps |
| xl | 32px | Major message-to-message separation |
| 2xl | 48px | Empty-state or large media breathing room |
| 3xl | 64px | Not used in this phase |

Exceptions: none

---

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 14-15px | 400 | 1.6 |
| Label | 12px | 600 | 1.4 |
| Heading | 13-14px | 600 | 1.4 |
| Display | 16px | 600 | 1.4 |

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `var(--bg-card)` / `#ffffff` | Assistant message surfaces, media frames, transcript panels |
| Secondary (30%) | `var(--bg)` / `#f7f7f8` | Nested code/output wells, empty background, soft separators |
| Accent (10%) | `var(--primary)` / `#5b5bd6` | Active tool state, selected controls, focused playback accents only |
| Destructive | `var(--error)` / `#ef4444` | Failed CLI state and destructive confirmation only |

Accent reserved for: active playback state, running CLI indicator, focused media actions

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA | Keep existing chat send affordance; no new CTA in this phase |
| Empty state heading | `No rich output yet` |
| Empty state body | `Media blocks and CLI transcript output will appear here when the agent emits them.` |
| Error state | `Output unavailable. Retry the run or inspect the tool status for details.` |
| Destructive confirmation | `Stop run`: `This stops the active agent run and ends live transcript updates.` |

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| existing local components | `MessageBubble`, `ToolCallBlock`, new `MediaBlock` | not required |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
