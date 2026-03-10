<template>
  <div class="chat-layout">
    <!-- Left sidebar: contacts (agents + group chats) -->
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

    <!-- Left expand button (shown when left sidebar collapsed) -->
    <button v-if="leftCollapsed" class="expand-btn expand-btn-left" @click="leftCollapsed = false">
      <el-icon><Expand /></el-icon>
    </button>

    <!-- Chat area -->
    <div class="chat-main">
      <template v-if="chatStore.activeChat">
        <!-- Session title bar -->
        <div class="chat-titlebar">
          <span class="chat-titlebar-name">{{ chatStore.activeChat.name }}</span>
        </div>
        <!-- History loading skeleton -->
        <div v-if="historyLoading" class="history-loading">
          <div class="skeleton-list">
            <div class="skeleton-row user">
              <div class="skeleton-bubble" style="width: 52%" />
            </div>
            <div class="skeleton-row assistant">
              <div class="skeleton-lines">
                <div class="skeleton-line" style="width: 88%" />
                <div class="skeleton-line" style="width: 74%" />
                <div class="skeleton-line" style="width: 60%" />
              </div>
            </div>
            <div class="skeleton-row user">
              <div class="skeleton-bubble" style="width: 38%" />
            </div>
            <div class="skeleton-row assistant">
              <div class="skeleton-lines">
                <div class="skeleton-line" style="width: 92%" />
                <div class="skeleton-line" style="width: 68%" />
              </div>
            </div>
          </div>
        </div>
        <ChatWindow
          v-else
          ref="chatWindowRef"
          :messages="chat.displayMessages.value"
        />
        <ChatInput
          v-model="chat.inputText.value"
          :streaming="chat.streaming.value"
          @send="sendMessage"
          @stop="chat.stopStreaming"
        />
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

    <!-- Right sidebar: session history for selected contact -->
    <HistorySidebar
      :chats="contactChats"
      :active-chat-id="chatStore.activeChat?.id ?? null"
      :collapsed="rightCollapsed"
      @toggle="rightCollapsed = !rightCollapsed"
      @select-chat="selectChat"
      @chat-action="handleChatAction"
    />

    <!-- Right expand button (shown when right sidebar collapsed AND a contact is selected) -->
    <button v-if="rightCollapsed && selectedContact" class="expand-btn expand-btn-right" @click="rightCollapsed = false">
      <el-icon><Expand /></el-icon>
    </button>

    <!-- Rename dialog -->
    <el-dialog v-model="renameDialogVisible" :title="$t('chat.rename')" width="360px">
      <el-input v-model="renameName" :placeholder="$t('chat.renamePlaceholder')" />
      <template #footer>
        <el-button @click="renameDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="confirmRename">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useStorage } from '@vueuse/core'
import { useChatStore } from '@/stores/chat'
import { useChat } from './composables/useChat'
import { createChat } from '@/api/chats'
import { listAgents } from '@/api/agents'
import { listGroupChats } from '@/api/group_chats'
import type { ChatSpec, AgentInfo } from '@/types'
import type { GroupChatConfig } from '@/types/group_chat'
import { uuidv4 } from '@/utils/uuid'
import ContactSidebar from './components/ContactSidebar.vue'
import HistorySidebar from './components/HistorySidebar.vue'
import ChatWindow from './components/ChatWindow.vue'
import ChatInput from './components/ChatInput.vue'

const { t } = useI18n()
const router = useRouter()
const chatStore = useChatStore()
const chat = useChat()
const chatWindowRef = ref<InstanceType<typeof ChatWindow> | null>(null)

const leftCollapsed = useStorage('haibot-left-sidebar', false)
const rightCollapsed = useStorage('haibot-history-sidebar', false)

const selectedContact = ref<{ type: 'agent' | 'group'; id: string } | null>(null)

const renameDialogVisible = ref(false)
const renameName = ref('')
const renamingChatId = ref<string | null>(null)
const historyLoading = ref(false)

// ── Agent selector ──
const agentsList = ref<AgentInfo[]>([])
const selectedAgentId = ref('main')

// ── Group chats ──
const groupChats = ref<GroupChatConfig[]>([])

// ── Computed ───────────────────────────────────────────────────────────────

// Derive currentGroupId from selectedContact (replaces the old ref)
const currentGroupId = computed(() =>
  selectedContact.value?.type === 'group' ? selectedContact.value.id : null
)

// Chats filtered to the selected contact
const contactChats = computed(() => {
  if (!selectedContact.value) return []
  const { type, id } = selectedContact.value
  return chatStore.chats.filter((c) => {
    if (type === 'agent') return c.meta?.agent_id != null && String(c.meta.agent_id) === id && !c.meta?.group_id
    return c.meta?.group_id != null && String(c.meta.group_id) === id
  })
})

// ── Select Agent ──────────────────────────────────────────────────────────
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

// ── Select Group Chat ─────────────────────────────────────────────────────
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

// ── Select Chat ───────────────────────────────────────────────────────────
async function selectChat(selected: ChatSpec) {
  if (chatStore.activeChat?.id === selected.id) return
  // Restore selectedContact from chat meta
  if (selected.meta?.group_id) {
    selectedContact.value = { type: 'group', id: String(selected.meta.group_id) }
  } else if (selected.meta?.agent_id) {
    selectedContact.value = { type: 'agent', id: String(selected.meta.agent_id) }
  }
  chatStore.setActiveChat(selected)
  chat.clearMessages()
  selectedAgentId.value = selected.meta?.agent_id ? String(selected.meta.agent_id) : 'main'
  if (selected.meta?._isTemp) return
  historyLoading.value = true
  try {
    const history = await chatStore.getChatHistory(selected.id)
    const display = chat.convertHistoryToDisplay(history.messages as unknown as Record<string, unknown>[])
    chat.setMessages(display)
    chatWindowRef.value?.scrollToBottom()
  } catch {
    // no history
  } finally {
    historyLoading.value = false
  }
}

// ── Send Message ──────────────────────────────────────────────────────────
async function sendMessage() {
  const text = chat.inputText.value.trim()
  if (!text || !chatStore.activeChat) return
  chat.inputText.value = ''

  const activeChat = chatStore.activeChat

  // Persist temp chat on first message
  if (activeChat.meta?._isTemp) {
    try {
      const persisted = await createChat({
        name: text.slice(0, 20),
        session_id: activeChat.session_id,
        user_id: activeChat.user_id,
        channel: 'console',
        meta: { agent_id: selectedAgentId.value, ...(activeChat.meta?.group_id ? { group_id: activeChat.meta.group_id } : {}) },
      })
      const idx = chatStore.chats.findIndex((c) => c.id === activeChat.id)
      if (idx !== -1) chatStore.chats[idx] = persisted
      chatStore.setActiveChat(persisted)
    } catch (e: unknown) {
      ElMessage.error(t('chat.createFailed') + ': ' + (e instanceof Error ? e.message : String(e)))
      return
    }
  }

  const currentAgentId = (chatStore.activeChat!.meta?.agent_id as string) || selectedAgentId.value
  const activeGroupId = currentGroupId.value || undefined

  await chat.sendMessage(
    text,
    chatStore.activeChat!.session_id,
    chatStore.activeChat!.user_id,
    () => chatWindowRef.value?.scrollIfNearBottom(),
    () => chatStore.loadChats(),
    (e) => ElMessage.error(t('chat.requestFailed') + ': ' + e.message),
    activeGroupId ? undefined : currentAgentId,
    activeGroupId ?? undefined,
  )
}

// ── Agent change ──
function handleAgentChange(agentId: string) {
  if (chatStore.activeChat) {
    chatStore.activeChat.meta = { ...chatStore.activeChat.meta, agent_id: agentId }
  }
}

// ── Chat Actions ──────────────────────────────────────────────────────────
function handleChatAction(cmd: string, chatItem: ChatSpec) {
  if (cmd === 'rename') {
    renamingChatId.value = chatItem.id
    renameName.value = chatItem.name
    renameDialogVisible.value = true
  } else if (cmd === 'delete') {
    ElMessageBox.confirm(
      t('chat.deleteConfirm', { name: chatItem.name }),
      t('common.deleteConfirm'),
      { confirmButtonText: t('common.delete'), cancelButtonText: t('common.cancel'), type: 'warning' },
    )
      .then(async () => {
        if (!chatItem.meta?._isTemp) await chatStore.removeChat(chatItem.id)
        else {
          const idx = chatStore.chats.findIndex((c) => c.id === chatItem.id)
          if (idx !== -1) chatStore.chats.splice(idx, 1)
        }
        if (chatStore.activeChat?.id === chatItem.id) {
          chatStore.setActiveChat(null)
          chat.clearMessages()
        }
      })
      .catch(() => {})
  }
}

async function confirmRename() {
  if (!renamingChatId.value) return
  try {
    await chatStore.renameChat(renamingChatId.value, renameName.value)
  } catch {
    // ignore
  }
  renameDialogVisible.value = false
}

onMounted(async () => {
  // Load agents list
  try {
    agentsList.value = await listAgents()
  } catch {
    // fallback to main only
    agentsList.value = [{ id: 'main', name: 'Main', description: '', is_main: true, files: [], created_at: '' }]
  }

  // Load group chats
  try {
    groupChats.value = await listGroupChats()
  } catch {
    // group chats optional
  }

  await chatStore.loadChats()
  // Restore active chat's history if returning from settings
  const active = chatStore.activeChat
  console.log("active ", active)
  if (active && !active.meta?._isTemp) {
    // Restore selectedContact from active chat meta
    if (active.meta?.group_id) {
      selectedContact.value = { type: 'group', id: String(active.meta.group_id) }
    } else {
      const agentId = active.meta?.agent_id ? String(active.meta.agent_id) : (agentsList.value[0]?.id ?? 'main')
      selectedContact.value = { type: 'agent', id: agentId }
      selectedAgentId.value = agentId
    }
    historyLoading.value = true
    try {
      const history = await chatStore.getChatHistory(active.id)
      const display = chat.convertHistoryToDisplay(history.messages as unknown as Record<string, unknown>[])
      chat.setMessages(display)
      chatWindowRef.value?.scrollToBottom()
    } catch {
      // no history yet
    } finally {
      historyLoading.value = false
    }
  } else if (agentsList.value.length > 0) {
    selectedContact.value = { type: 'agent', id: agentsList.value[0].id }
    selectedAgentId.value = agentsList.value[0].id
  }
})
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--bg);
}

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
@keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-titlebar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.chat-titlebar-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-1);
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.empty-logo {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.5px;
}
.logo-hai { color: var(--primary); }
.logo-bot { color: var(--text-1); }

.empty-content p {
  color: var(--text-4);
  font-size: 14px;
}

/* ── History loading skeleton ── */
.history-loading {
  flex: 1;
  overflow: hidden;
  padding: 24px 16px;
}

.skeleton-list {
  max-width: 768px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

@media (min-width: 1200px) { .skeleton-list { max-width: 800px; } }
@media (min-width: 1600px) { .skeleton-list { max-width: 860px; } }

.skeleton-row {
  display: flex;
}
.skeleton-row.user { justify-content: flex-end; }
.skeleton-row.assistant { justify-content: flex-start; }

.skeleton-bubble {
  height: 40px;
  border-radius: 18px;
  border-bottom-right-radius: 4px;
  background: var(--border);
  animation: skeleton-shimmer 1.4s ease-in-out infinite;
}

.skeleton-lines {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 70%;
}

.skeleton-line {
  height: 14px;
  border-radius: 6px;
  background: var(--border);
  animation: skeleton-shimmer 1.4s ease-in-out infinite;
}
.skeleton-line:nth-child(2) { animation-delay: 0.1s; }
.skeleton-line:nth-child(3) { animation-delay: 0.2s; }

@keyframes skeleton-shimmer {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
}
</style>
