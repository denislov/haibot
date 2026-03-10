# Three-Column Chat Layout Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign the chat UI into a three-column layout: left contact sidebar (agents + group chats), center chat area, right collapsible history sidebar.

**Architecture:** Replace `ChatSidebar.vue` with two new components — `ContactSidebar.vue` (left, always visible, collapsible) and `HistorySidebar.vue` (right, collapsible, state persisted to localStorage). `ChatLayout.vue` is refactored to own `selectedContact` state and wire both sidebars together.

**Tech Stack:** Vue 3 + TypeScript, Pinia (`useChatStore`), Element Plus icons, CSS custom properties (`data-theme`), `localStorage` for sidebar collapse state.

---

### Task 1: Create `ContactSidebar.vue`

**Files:**
- Create: `frontend/src/modules/chat/components/ContactSidebar.vue`

The left sidebar replaces the old `ChatSidebar.vue`. It shows agents and group chats as a contact list.

**Step 1: Create the component**

```vue
<template>
  <div class="contact-sidebar" :class="{ collapsed }">
    <div class="cs-header">
      <span class="cs-logo">
        <span class="logo-hai">Hai</span><span class="logo-bot">Bot</span>
      </span>
      <button class="cs-toggle" @click="$emit('toggle')">
        <el-icon><Fold /></el-icon>
      </button>
    </div>

    <!-- Agents -->
    <div class="cs-section-label">{{ $t('settings.agents.title') }}</div>
    <div class="cs-list">
      <div
        v-for="agent in agents"
        :key="agent.id"
        class="cs-item"
        :class="{ active: selectedType === 'agent' && selectedId === agent.id }"
        @click="$emit('selectAgent', agent)"
      >
        <div class="cs-avatar" :style="{ background: avatarColor(agent.id) }">
          {{ agent.name.charAt(0).toUpperCase() }}
        </div>
        <span class="cs-name">{{ agent.name }}</span>
      </div>
    </div>

    <!-- Group Chats -->
    <template v-if="groupChats.length > 0">
      <div class="cs-section-label">{{ $t('chat.groupChats') }}</div>
      <div class="cs-list">
        <div
          v-for="gc in groupChats"
          :key="gc.id"
          class="cs-item"
          :class="{ active: selectedType === 'group' && selectedId === gc.id }"
          @click="$emit('selectGroup', gc)"
        >
          <div class="cs-avatar group-avatar">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          <span class="cs-name">{{ gc.name }}</span>
        </div>
      </div>
    </template>

    <div class="cs-footer">
      <button class="cs-footer-btn" @click="$emit('openSettings')" :title="$t('common.settings')">
        <el-icon><Setting /></el-icon>
        <span>{{ $t('common.settings') }}</span>
      </button>
      <button class="cs-footer-btn cs-theme-btn" @click="toggleTheme()" :title="isDark ? $t('theme.light') : $t('theme.dark')">
        <el-icon v-if="isDark"><Sunny /></el-icon>
        <el-icon v-else><Moon /></el-icon>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AgentInfo } from '@/types'
import type { GroupChatConfig } from '@/types/group_chat'
import { useTheme } from '@/utils/useTheme'

const { isDark, toggleTheme } = useTheme()

defineProps<{
  agents: AgentInfo[]
  groupChats: GroupChatConfig[]
  selectedId: string | null
  selectedType: 'agent' | 'group' | null
  collapsed: boolean
}>()

defineEmits<{
  toggle: []
  selectAgent: [agent: AgentInfo]
  selectGroup: [gc: GroupChatConfig]
  openSettings: []
}>()

// Generate a stable color from the agent id string
const AVATAR_COLORS = [
  '#5b5bd6', '#0ea5e9', '#10b981', '#f59e0b',
  '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6',
]
function avatarColor(id: string): string {
  let hash = 0
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) & 0xffff
  return AVATAR_COLORS[hash % AVATAR_COLORS.length]
}
</script>

<style scoped>
.contact-sidebar {
  width: 220px;
  flex-shrink: 0;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width var(--transition-slow), opacity var(--transition-slow);
}
.contact-sidebar.collapsed {
  width: 0;
  opacity: 0;
  border-right: none;
  pointer-events: none;
  visibility: hidden;
}

.cs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 14px 10px;
  flex-shrink: 0;
}
.cs-logo { font-size: 18px; font-weight: 700; letter-spacing: -0.5px; }
.logo-hai { color: var(--primary); }
.logo-bot { color: var(--text-1); }

.cs-toggle {
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px;
  border: none; background: none;
  cursor: pointer; color: var(--text-4);
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}
.cs-toggle:hover { background: var(--border); color: var(--text-2); }

.cs-section-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 10px 14px 4px;
  flex-shrink: 0;
}

.cs-list {
  display: flex;
  flex-direction: column;
  padding: 0 6px;
  gap: 1px;
  overflow-y: auto;
}

.cs-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 8px;
  border-radius: var(--radius);
  cursor: pointer;
  transition: background var(--transition-fast);
}
.cs-item:hover { background: var(--bg); }
.cs-item.active { background: var(--primary-light); }

.cs-avatar {
  width: 32px; height: 32px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700;
  color: white;
  flex-shrink: 0;
}
.group-avatar {
  background: var(--border-strong);
  color: var(--text-3);
  font-size: 16px;
}
[data-theme="dark"] .group-avatar { background: var(--border); }

.cs-name {
  font-size: 13px; font-weight: 500;
  color: var(--text-1);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.cs-footer {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 10px;
  border-top: 1px solid var(--border);
  margin-top: auto;
  flex-shrink: 0;
}
.cs-footer-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 7px 10px;
  border: none; background: none;
  cursor: pointer; color: var(--text-3);
  font-size: 13px;
  border-radius: var(--radius);
  transition: background var(--transition-fast), color var(--transition-fast);
}
.cs-footer-btn:hover { background: var(--bg); color: var(--text-1); }
.cs-footer-btn .el-icon { font-size: 16px; }
.cs-theme-btn { margin-left: auto; padding: 7px; }
</style>
```

**Step 2: Verify file exists**
```bash
ls frontend/src/modules/chat/components/ContactSidebar.vue
```

**Step 3: Commit**
```bash
git add frontend/src/modules/chat/components/ContactSidebar.vue
git commit -m "feat: add ContactSidebar component (agents + group chats contact list)"
```

---

### Task 2: Create `HistorySidebar.vue`

**Files:**
- Create: `frontend/src/modules/chat/components/HistorySidebar.vue`

The right sidebar shows history for the currently selected contact, with time-based dividers.

**Step 1: Create the component**

```vue
<template>
  <div class="history-sidebar" :class="{ collapsed }">
    <div class="hs-header">
      <span class="hs-title">{{ $t('chat.history') }}</span>
      <button class="hs-toggle" @click="$emit('toggle')">
        <el-icon><Fold style="transform: rotate(180deg)" /></el-icon>
      </button>
    </div>

    <div class="hs-list">
      <template v-if="groups.length === 0">
        <div class="hs-empty">{{ $t('chat.noHistory') }}</div>
      </template>
      <template v-for="group in groups" :key="group.label">
        <div class="hs-divider">{{ group.label }}</div>
        <div
          v-for="chat in group.chats"
          :key="chat.id"
          class="hs-item"
          :class="{
            active: activeChatId === chat.id,
            'is-group': !!chat.meta?.group_id,
          }"
          @click="$emit('selectChat', chat)"
        >
          <div class="hs-item-inner">
            <span class="hs-item-name">{{ chat.name }}</span>
            <span class="hs-item-preview">{{ getPreview(chat) }}</span>
          </div>
          <el-dropdown trigger="click" @command="(cmd: string) => $emit('chatAction', cmd, chat)" @click.stop>
            <el-icon class="hs-more"><More /></el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="rename">{{ $t('chat.rename') }}</el-dropdown-item>
                <el-dropdown-item command="delete" class="danger-item">{{ $t('common.delete') }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ChatSpec } from '@/types'

const { t, locale } = useI18n()

const props = defineProps<{
  chats: ChatSpec[]          // all chats, filtered externally by contact
  activeChatId: string | null
  collapsed: boolean
}>()

defineEmits<{
  toggle: []
  selectChat: [chat: ChatSpec]
  chatAction: [cmd: string, chat: ChatSpec]
}>()

function getPreview(chat: ChatSpec): string {
  return (chat.meta?.preview as string) || ''
}

interface Group { label: string; chats: ChatSpec[] }

const groups = computed((): Group[] => {
  // Sort newest first, skip temp chats
  const sorted = [...props.chats]
    .filter((c) => !c.meta?._isTemp)
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())

  if (sorted.length === 0) return []

  const now = new Date()
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const ms7 = 7 * 24 * 60 * 60 * 1000
  const ms30 = 30 * 24 * 60 * 60 * 1000

  const buckets = new Map<string, ChatSpec[]>()

  function bucketLabel(chat: ChatSpec): string {
    const d = new Date(chat.updated_at)
    const diff = startOfToday.getTime() - new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
    if (diff <= 0) return t('chat.timeToday')
    if (diff < ms7) return t('chat.time7days')
    if (diff < ms30) return t('chat.time30days')
    // Specific month label
    return d.toLocaleDateString(locale.value === 'zh-CN' ? 'zh-CN' : 'en-US', {
      year: 'numeric', month: 'long',
    })
  }

  for (const chat of sorted) {
    const label = bucketLabel(chat)
    if (!buckets.has(label)) buckets.set(label, [])
    buckets.get(label)!.push(chat)
  }

  return [...buckets.entries()].map(([label, chats]) => ({ label, chats }))
})
</script>

<style scoped>
.history-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: var(--bg-sidebar);
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width var(--transition-slow), opacity var(--transition-slow);
}
.history-sidebar.collapsed {
  width: 0;
  opacity: 0;
  border-left: none;
  pointer-events: none;
  visibility: hidden;
}

.hs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 14px 10px;
  flex-shrink: 0;
}
.hs-title { font-size: 13px; font-weight: 600; color: var(--text-2); }

.hs-toggle {
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px;
  border: none; background: none;
  cursor: pointer; color: var(--text-4);
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}
.hs-toggle:hover { background: var(--border); color: var(--text-2); }

.hs-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 6px 8px;
}

.hs-empty {
  padding: 24px 8px;
  text-align: center;
  font-size: 12px;
  color: var(--text-4);
}

.hs-divider {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-4);
  padding: 10px 8px 4px;
  letter-spacing: 0.3px;
}

.hs-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 7px 8px;
  border-radius: var(--radius);
  cursor: pointer;
  transition: background var(--transition-fast);
  margin-bottom: 1px;
}
.hs-item:hover { background: var(--bg); }
.hs-item.active { background: var(--primary-light); }

/* Group chat sessions: left accent line */
.hs-item.is-group {
  border-left: 2px solid var(--primary);
  padding-left: 6px;
}

.hs-item-inner { flex: 1; min-width: 0; }
.hs-item-name {
  display: block;
  font-size: 13px; font-weight: 500; color: var(--text-1);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.hs-item-preview {
  display: block;
  font-size: 11px; color: var(--text-4);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  margin-top: 2px;
}

.hs-more {
  flex-shrink: 0; color: var(--text-4);
  font-size: 16px; padding: 2px;
  border-radius: 4px; cursor: pointer;
  opacity: 0;
  transition: opacity var(--transition-fast);
}
.hs-item:hover .hs-more,
.hs-item.active .hs-more { opacity: 1; }
.hs-more:hover { color: var(--text-2); background: var(--border); }

:deep(.danger-item) { color: var(--error) !important; }
</style>
```

**Step 2: Add missing i18n keys to both locale files**

In `frontend/src/i18n/locales/en.ts` under `chat:`:
```ts
history: 'History',
noHistory: 'No conversations yet',
timeToday: 'Today',
time7days: 'Previous 7 days',
time30days: 'Previous 30 days',
```

In `frontend/src/i18n/locales/zh-CN.ts` under `chat:`:
```ts
history: '历史',
noHistory: '暂无会话',
timeToday: '今天',
time7days: '7 天内',
time30days: '30 天内',
```

**Step 3: Commit**
```bash
git add frontend/src/modules/chat/components/HistorySidebar.vue \
        frontend/src/i18n/locales/en.ts \
        frontend/src/i18n/locales/zh-CN.ts
git commit -m "feat: add HistorySidebar component with time-grouped session history"
```

---

### Task 3: Refactor `ChatLayout.vue`

**Files:**
- Modify: `frontend/src/modules/chat/ChatLayout.vue`

This is the main wiring task. Replace old sidebar logic with the two new components and add `selectedContact` + `rightSidebarCollapsed` state.

**Step 1: Replace imports**

Remove the `ChatSidebar` import, add `ContactSidebar` and `HistorySidebar`:
```ts
// Remove:
import ChatSidebar from './components/ChatSidebar.vue'

// Add:
import ContactSidebar from './components/ContactSidebar.vue'
import HistorySidebar from './components/HistorySidebar.vue'
```

**Step 2: Replace state**

Remove: `sidebarCollapsed`
Add:
```ts
import { ref, onMounted, computed } from 'vue'
import { useStorage } from '@vueuse/core'

const leftCollapsed = ref(false)
const rightCollapsed = useStorage('haibot-history-sidebar', false)

// Currently selected contact (agent or group)
const selectedContact = ref<{ type: 'agent' | 'group'; id: string } | null>(null)

// Chats filtered to the selected contact
const contactChats = computed(() => {
  if (!selectedContact.value) return []
  const { type, id } = selectedContact.value
  return chatStore.chats.filter((c) => {
    if (type === 'agent') return (c.meta?.agent_id as string | undefined) === id && !c.meta?.group_id
    return (c.meta?.group_id as string | undefined) === id
  })
})
```

Note: `currentGroupId` is now derived from `selectedContact`:
```ts
const currentGroupId = computed(() =>
  selectedContact.value?.type === 'group' ? selectedContact.value.id : null
)
```

**Step 3: Update `handleNewChat` / `handleNewGroupChatSession`**

Remove `handleNewGroupChatSession` — group chat session creation is now triggered from `selectGroup` in `ContactSidebar`. Instead, consolidate into `handleSelectAgent` and `handleSelectGroup`:

```ts
function handleSelectAgent(agent: AgentInfo) {
  selectedContact.value = { type: 'agent', id: agent.id }
  selectedAgentId.value = agent.id
  const temp: ChatSpec = {
    id: 'temp-' + uuidv4(),
    name: 'New Chat',
    session_id: uuidv4(),
    user_id: 'default',
    channel: 'console',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    meta: { _isTemp: true, agent_id: agent.id },
  }
  chatStore.chats.unshift(temp)
  chatStore.setActiveChat(temp)
  chat.clearMessages()
}

function handleSelectGroup(gc: GroupChatConfig) {
  selectedContact.value = { type: 'group', id: gc.id }
  const temp: ChatSpec = {
    id: 'temp-' + uuidv4(),
    name: gc.name,
    session_id: uuidv4(),
    user_id: 'default',
    channel: 'console',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    meta: { _isTemp: true, group_id: gc.id },
  }
  chatStore.chats.unshift(temp)
  chatStore.setActiveChat(temp)
  chat.clearMessages()
}
```

Keep `handleNewChat` for the case when no contact is selected (fallback to `selectedAgentId`).

**Step 4: Update `selectChat`**

When selecting a chat from the history sidebar, also restore `selectedContact`:
```ts
async function selectChat(selected: ChatSpec) {
  if (chatStore.activeChat?.id === selected.id) return
  // Restore selectedContact from chat meta
  if (selected.meta?.group_id) {
    selectedContact.value = { type: 'group', id: selected.meta.group_id as string }
  } else if (selected.meta?.agent_id) {
    selectedContact.value = { type: 'agent', id: selected.meta.agent_id as string }
  }
  // ... rest of existing selectChat logic unchanged
}
```

**Step 5: Replace template**

```vue
<template>
  <div class="chat-layout">
    <!-- Left: Contact sidebar -->
    <ContactSidebar
      :agents="agentsList"
      :group-chats="groupChats"
      :selected-id="selectedContact?.id ?? null"
      :selected-type="selectedContact?.type ?? null"
      :collapsed="leftCollapsed"
      @toggle="leftCollapsed = !leftCollapsed"
      @select-agent="handleSelectAgent"
      @select-group="handleSelectGroup"
      @open-settings="router.push('/settings')"
    />

    <!-- Expand left sidebar button -->
    <button v-if="leftCollapsed" class="expand-btn expand-btn-left" @click="leftCollapsed = false">
      <el-icon><Expand /></el-icon>
    </button>

    <!-- Center: Chat area -->
    <div class="chat-main">
      <template v-if="chatStore.activeChat">
        <div v-if="!currentGroupId" class="agent-bar">
          <span class="agent-bar-label">{{ $t('settings.agents.selectAgent') }}:</span>
          <el-select v-model="selectedAgentId" size="small" style="width: 160px" @change="handleAgentChange">
            <el-option v-for="a in agentsList" :key="a.id" :label="a.name" :value="a.id" />
          </el-select>
        </div>
        <div v-if="historyLoading" class="history-loading"><!-- skeleton markup unchanged --></div>
        <ChatWindow v-else ref="chatWindowRef" :messages="chat.displayMessages.value" />
        <ChatInput v-model="chat.inputText.value" :streaming="chat.streaming.value" @send="sendMessage" @stop="chat.stopStreaming" />
      </template>

      <div v-else class="chat-empty-state">
        <div class="empty-content">
          <div class="empty-logo">
            <span class="logo-hai">Hai</span><span class="logo-bot">Bot</span>
          </div>
          <p>{{ $t('chat.selectContact') }}</p>
        </div>
      </div>
    </div>

    <!-- Right: History sidebar -->
    <HistorySidebar
      :chats="contactChats"
      :active-chat-id="chatStore.activeChat?.id ?? null"
      :collapsed="rightCollapsed"
      @toggle="rightCollapsed = !rightCollapsed"
      @select-chat="selectChat"
      @chat-action="handleChatAction"
    />

    <!-- Expand right sidebar button -->
    <button v-if="rightCollapsed && selectedContact" class="expand-btn expand-btn-right" @click="rightCollapsed = false">
      <el-icon><Expand style="transform: rotate(180deg)" /></el-icon>
    </button>

    <!-- Rename dialog (unchanged) -->
    <el-dialog v-model="renameDialogVisible" :title="$t('chat.rename')" width="360px">
      <el-input v-model="renameName" :placeholder="$t('chat.renamePlaceholder')" />
      <template #footer>
        <el-button @click="renameDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="confirmRename">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>
```

**Step 6: Update layout CSS**

```css
.chat-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--bg);
  position: relative;
}

/* Left expand button */
.expand-btn {
  position: fixed;
  z-index: 100;
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-card);
  cursor: pointer;
  color: var(--text-3);
  box-shadow: var(--shadow-sm);
  animation: fade-in var(--transition-fast) both;
  transition: background var(--transition-fast), color var(--transition-fast);
}
.expand-btn:hover { background: var(--bg); color: var(--text-1); }
.expand-btn-left  { top: 12px; left: 12px; }
.expand-btn-right { top: 12px; right: 12px; }
```

**Step 7: Add missing i18n key**

In `en.ts`: `selectContact: 'Select an agent or group chat to start'`
In `zh-CN.ts`: `selectContact: '选择一个智能体或群聊开始对话'`

**Step 8: Remove old `ChatSidebar.vue`**

The old sidebar is no longer used. Delete it:
```bash
rm frontend/src/modules/chat/components/ChatSidebar.vue
```

**Step 9: Commit**
```bash
git add frontend/src/modules/chat/ChatLayout.vue \
        frontend/src/i18n/locales/en.ts \
        frontend/src/i18n/locales/zh-CN.ts
git rm frontend/src/modules/chat/components/ChatSidebar.vue
git commit -m "feat: refactor ChatLayout to three-column design with ContactSidebar + HistorySidebar"
```

---

### Task 4: Restore selectedContact on page refresh

When the page is reloaded and `chatStore` restores the active chat, `selectedContact` must also be restored so the right sidebar shows the correct history.

**Files:**
- Modify: `frontend/src/modules/chat/ChatLayout.vue` — `onMounted` block

**Step 1: Update `onMounted`**

After `await chatStore.loadChats()`, restore `selectedContact` from the active chat's meta:
```ts
const active = chatStore.activeChat
if (active) {
  if (active.meta?.group_id) {
    selectedContact.value = { type: 'group', id: active.meta.group_id as string }
  } else {
    const agentId = (active.meta?.agent_id as string) || 'main'
    selectedContact.value = { type: 'agent', id: agentId }
    selectedAgentId.value = agentId
  }
  // ... existing history load logic
}
```

Also: on first load when there's no active chat, auto-select the first agent so the sidebar isn't blank:
```ts
if (!active && agentsList.value.length > 0) {
  selectedContact.value = { type: 'agent', id: agentsList.value[0].id }
  selectedAgentId.value = agentsList.value[0].id
}
```

**Step 2: Commit**
```bash
git add frontend/src/modules/chat/ChatLayout.vue
git commit -m "feat: restore selectedContact from active chat meta on page refresh"
```
