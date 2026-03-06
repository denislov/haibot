# Group Chat Design

**Date**: 2026-03-07
**Status**: Approved

## Overview

Add group chat functionality to HaiBot. Users create a group chat by designating a **host agent** and one or more **participant agents**. When the user sends a message, the host agent decides whether to reply directly or summon participants via `@name` mentions (WeChat-style). The system parses `@mentions` to route messages; multiple simultaneous `@mentions` trigger concurrent agent execution. The host controls the discussion lifecycle (continue / pause / end).

Two prerequisite improvements are bundled into this work:
1. **Per-agent memory isolation** — each agent's memory reads/writes from its own workspace directory.
2. **Per-agent skills flags** — each agent's `skills_config` in `.agent_meta.json` controls which skills are active.

---

## Prerequisite 1: Per-Agent Memory Isolation

### Problem
`HaiBotAgent` currently resolves memory from `WORKING_DIR/memory/`. All agents share the same memory space.

### Solution
Pass `workspace_dir` explicitly when constructing `HaiBotAgent`. The `MemoryManager` uses `{workspace_dir}/memory/` instead of the global `WORKING_DIR/memory/`.

### Changes
- `HaiBotAgent.__init__` accepts `workspace_dir: Path` (default: `WORKING_DIR`).
- `AgentRunner.query_handler()` computes `workspace_dir = WORKING_DIR / "workspace" / agent_id` and passes it to `HaiBotAgent`.
- `MemoryManager.__init__` accepts `working_dir` (already does), caller now supplies per-agent path.

---

## Prerequisite 2: Per-Agent Skills Flags

### Problem
All agents load the same set of active skills. There is no per-agent enable/disable.

### Solution
Store `skills_config: { "<skill_name>": true|false }` in each agent's `.agent_meta.json`. When loading skills for an agent, filter the active skills list by this config. Absent keys default to `true` (enabled).

### Data Shape (`.agent_meta.json` extension)
```json
{
  "name": "Coder",
  "description": "...",
  "skills_config": {
    "browser_use": false,
    "desktop_screenshot": false
  }
}
```

### Changes
- `agents/skills_manager.py`: new helper `get_agent_skills_config(agent_id) -> dict[str, bool]` reads from workspace `.agent_meta.json`.
- `HaiBotAgent.__init__` accepts `skills_config: dict[str, bool] | None`; applies it when building the toolkit.
- New API endpoints:
  - `GET  /api/agents/{agent_id}/skills` — returns skill list with per-agent enabled flags.
  - `PUT  /api/agents/{agent_id}/skills` — updates `skills_config` in `.agent_meta.json`.
- Frontend: `AgentsSettings.vue` exposes a skill toggle list per agent.

---

## Core Feature: Group Chat

### Data Model

**`GroupChatConfig`** (Pydantic, stored in `~/.haibot/group_chats.json`):

```python
class GroupChatConfig(BaseModel):
    id: str                          # unique slug, e.g. "project_alpha"
    name: str                        # display name
    host_agent_id: str               # must be an existing agent id
    participant_agent_ids: list[str] # ordered; must all be existing agent ids
    max_rounds: int = 10             # safety cap on host↔participant loops
    created_at: str
```

**`GroupChatRound`** (in-memory, per conversation turn):
```python
@dataclass
class GroupChatRound:
    round_index: int
    host_msg: Msg
    participant_msgs: list[Msg]       # one per responding participant, in order
```

Group chat conversation history (all rounds) is stored in the standard JSONSession under key `group_{group_id}`, so it persists across user turns.

### API Routes

```
GET    /api/group-chats              # list all group chats
POST   /api/group-chats              # create
GET    /api/group-chats/{id}         # get
PUT    /api/group-chats/{id}         # update
DELETE /api/group-chats/{id}         # delete
```

Sending a message to a group chat uses the **existing** `/api/agent/process` endpoint. The caller sets `metadata.group_id = "<id>"` in the request body. `AgentRunner.query_handler()` detects this field and delegates to `GroupChatOrchestrator`.

### Module Layout

```
backend/haibot/app/group_chat/
  __init__.py
  models.py          # GroupChatConfig, GroupChatRound
  repo.py            # load/save group_chats.json
  mention_parser.py  # parse @name tokens from Msg text
  stream_merger.py   # merge N async generators via asyncio.Queue
  orchestrator.py    # GroupChatOrchestrator
app/routers/group_chats.py           # FastAPI CRUD routes
```

### Orchestrator Flow

```
GroupChatOrchestrator.run(user_msg, session_id, user_id, channel)
│
│  Load group config + conversation history from session
│
└─ for round_index in range(max_rounds):
   │
   ├─ 1. Build host HaiBotAgent
   │      workspace_dir  = workspace/{host_agent_id}/
   │      system prompt += GROUP_HOST.md  (injected template)
   │      GROUP_HOST.md tells host: participant names/roles,
   │        current round index, how to use @name to summon agents,
   │        how to signal end (no @mention = done)
   │
   ├─ 2. Feed input to host
   │      round 0 : [user_msg]
   │      round N : [last_participant_replies...] (MultiAgent format)
   │
   ├─ 3. Stream host response
   │      yield each SSE event tagged with agent_id=host_agent_id
   │
   ├─ 4. Parse @mentions from host's final text
   │      → empty  : break  (host signalled end)
   │      → names  : continue
   │
   ├─ 5. Resolve mentioned names → agent_ids
   │      (unknown names are silently ignored)
   │
   ├─ 6. Build one HaiBotAgent per mentioned participant
   │      workspace_dir  = workspace/{participant_id}/
   │      input          = host's message + full group history (MultiAgent fmt)
   │
   ├─ 7. asyncio.gather all participant agents concurrently
   │      stream_merger multiplexes their SSE event streams via Queue
   │      each event is tagged with that participant's agent_id/agent_name
   │      yield events as they arrive (true real-time parallel streaming)
   │
   ├─ 8. Collect final Msg from each participant
   │      append to GroupChatRound; append round to session history
   │
   └─ 9. Loop → next round (participant replies become next host input)

After loop: yield a synthetic "group_done" marker event so frontend
knows discussion has ended.
```

### @Mention Parser

Regex: `@([\w\u4e00-\u9fff]+)` applied to the **text content** of the host's final `Msg`. Agent names are matched case-insensitively against `participant_agent_ids` using both `agent_id` and the `name` field from `.agent_meta.json`.

### Stream Merger

```python
async def merge_agent_streams(
    streams: list[AsyncGenerator[tuple[Msg, bool], None]]
) -> AsyncGenerator[tuple[Msg, bool], None]:
    """
    Merges N async generators into one.
    Each yielded item is already tagged with agent_id by the caller.
    Uses asyncio.Queue + sentinel pattern.
    Order within each stream is preserved; streams are interleaved as
    events arrive (no artificial ordering).
    """
```

### SSE Event Extension

Two new optional fields are appended to existing event dicts. Clients that do not understand them ignore them — single-agent behaviour is unchanged.

```jsonc
// Message-level event
{
  "object": "message",
  "type": "message",
  "status": "in_progress",
  "id": "msg_abc",
  "agent_id": "analyst",        // NEW: source agent id
  "agent_name": "分析师"         // NEW: display name
}

// Content delta event
{
  "object": "content",
  "type": "text",
  "delta": true,
  "text": "我认为……",
  "msg_id": "msg_abc",
  "agent_id": "analyst"         // NEW: used by frontend to route delta
}

// Discussion-end marker (synthetic, no agentscope equivalent)
{
  "object": "group_event",
  "type": "group_done"
}
```

### GROUP_HOST.md Template (injected into host system prompt)

```markdown
## 群聊主持规则

你正在主持一场群聊讨论。参与者列表：
{participant_list}   <!-- e.g. "- @分析师 (analyst)\n- @程序员 (coder)" -->

当前轮次：{round_index} / {max_rounds}

**发言规则**：
- 如需某位或多位参与者发言，在回复末尾使用 @姓名（可同时 @ 多人）。
- 如认为讨论已完成或无需继续，直接给出最终回复，**不要**添加任何 @。
- 每轮参与者会看到完整的讨论历史。
```

---

## Frontend Changes

### `DisplayMessage` Type Extension

```typescript
interface DisplayMessage {
  id: string
  role: 'user' | 'assistant'
  agentId?: string      // present when message is from a named group participant
  agentName?: string    // display name badge
  blocks: DisplayBlock[]
  streaming?: boolean
}
```

`agentId` is also set for the host agent in group chat mode so each bubble is labelled.

### `useChat.ts` Changes

- `onEvent` inspects incoming `agent_id` field.
- When a new `agent_id` is seen (via `message` event with `status: "in_progress"`), a new `DisplayMessage` shell is pushed to `displayMessages`.
- `msgBlockMap` becomes `Map<agentId, Map<msgId, DisplayBlock>>` — deltas are routed by `agent_id`.
- Single-agent events (no `agent_id`) are routed to a default `"__main__"` key, preserving existing behaviour.
- On `group_done` event: mark all streaming bubbles as `streaming: false`.

### `MessageBubble.vue` Changes

When `message.agentName` is set, render a small coloured name badge above the bubble (similar to WeChat group chat). Host and each participant get a consistent colour derived from `agentId`.

### New Settings Page: `GroupChatSettings.vue`

- List existing group chats.
- Create / edit: pick name, select host agent (dropdown of existing agents), select participants (multi-select).
- Set `max_rounds`.

### `ChatSidebar.vue` Changes

- Group chats appear as a separate section below regular chats.
- Creating a new group chat conversation sets `metadata.group_id` on the `streamQuery` call.

---

## Session & History Storage

Group chat history is stored in the **existing** `JSONSession` mechanism under the key:
`session_id = "{original_session_id}"`, `user_id = "{user_id}"`.

The agent saved in the session is the **host agent**. Participant replies are appended to the host agent's memory in `MultiAgent` format so the host sees the full conversation when session resumes.

This means `/api/chats/{id}` history view already works — messages from participants are stored as `Msg` objects with the participant's `name` field set, and the existing `agentscope_msg_to_message` conversion preserves them.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Host mentions unknown agent name | Silently ignore; log warning |
| Participant agent fails mid-stream | Emit error text block tagged with that `agent_id`; other participants continue |
| `max_rounds` reached | Orchestrator stops loop; emits `group_done` |
| User aborts (AbortController) | `asyncio.CancelledError` propagates through orchestrator; all participant tasks cancelled |
| Group chat id not found | 404 from `/api/group-chats/{id}`; `query_handler` raises 400 |

---

## Out of Scope (This PR)

- Group chat channels (DingTalk/Discord/etc.) — group chat is console/web only for now.
- Per-group agent memory (participants share their personal memory across all group chats they join).
- Cron-triggered group chats.
