<template>
  <div class="chat-layout">
    <!-- Sidebar -->
    <ChatSidebar
      :chats="chatStore.chats"
      :active-chat-id="chatStore.activeChat?.id ?? null"
      :collapsed="sidebarCollapsed"
      :group-chats="groupChats"
      :active-group-id="currentGroupId"
      @toggle="sidebarCollapsed = !sidebarCollapsed"
      @new-chat="handleNewChat"
      @select-chat="selectChat"
      @chat-action="handleChatAction"
      @open-settings="router.push('/settings')"
      @new-group-chat-session="handleNewGroupChatSession"
    />

    <!-- Expand button (when sidebar collapsed) -->
    <button
      v-if="sidebarCollapsed"
      class="expand-sidebar-btn"
      @click="sidebarCollapsed = false"
    >
      <el-icon><Expand /></el-icon>
    </button>

    <!-- Chat area -->
    <div class="chat-main">
      <template v-if="chatStore.activeChat">
        <!-- Agent selector bar -->
        <div class="agent-bar">
          <span class="agent-bar-label">{{ $t('settings.agents.selectAgent') }}:</span>
          <el-select
            v-model="selectedAgentId"
            size="small"
            style="width: 160px"
            @change="handleAgentChange"
          >
            <el-option
              v-for="a in agentsList"
              :key="a.id"
              :label="a.name"
              :value="a.id"
            />
          </el-select>
        </div>
        <ChatWindow
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
          <p>{{ $t('chat.emptyState') }}</p>
          <button class="start-chat-btn" @click="handleNewChat">
            <el-icon><Plus /></el-icon>
            {{ $t('chat.newChat') }}
          </button>
        </div>
      </div>
    </div>

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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useChatStore } from '@/stores/chat'
import { useChat } from './composables/useChat'
import { createChat } from '@/api/chats'
import { listAgents } from '@/api/agents'
import { listGroupChats } from '@/api/group_chats'
import type { ChatSpec, AgentInfo } from '@/types'
import type { GroupChatConfig } from '@/types/group_chat'
import ChatSidebar from './components/ChatSidebar.vue'
import ChatWindow from './components/ChatWindow.vue'
import ChatInput from './components/ChatInput.vue'

const { t } = useI18n()
const router = useRouter()
const chatStore = useChatStore()
const chat = useChat()
const chatWindowRef = ref<InstanceType<typeof ChatWindow> | null>(null)

const sidebarCollapsed = ref(false)
const renameDialogVisible = ref(false)
const renameName = ref('')
const renamingChatId = ref<string | null>(null)

// ── Agent selector ──
const agentsList = ref<AgentInfo[]>([])
const selectedAgentId = ref('main')

// ── Group chats ──
const groupChats = ref<GroupChatConfig[]>([])
const currentGroupId = ref<string | null>(null)

function uuidv4(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
  })
}

// ── New Chat ──────────────────────────────────────────────────────────────
function handleNewChat() {
  const temp: ChatSpec = {
    id: 'new-' + Date.now(),
    name: 'New Chat',
    session_id: uuidv4(),
    user_id: 'default',
    channel: 'console',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    meta: { _isTemp: true, agent_id: selectedAgentId.value },
  }
  chatStore.chats.unshift(temp)
  chatStore.setActiveChat(temp)
  chat.clearMessages()
}

// ── New Group Chat Session ────────────────────────────────────────────────
function handleNewGroupChatSession(gc: GroupChatConfig) {
  currentGroupId.value = gc.id
  const temp: ChatSpec = {
    id: 'new-' + Date.now(),
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
  chatStore.setActiveChat(selected)
  chat.clearMessages()
  // Restore agent selection from chat meta
  selectedAgentId.value = (selected.meta?.agent_id as string) || 'main'
  currentGroupId.value = (selected.meta?.group_id as string) ?? null
  if (selected.meta?._isTemp) return
  try {
    const history = await chatStore.getChatHistory(selected.id)
    const display = chat.convertHistoryToDisplay(history.messages as unknown as Record<string, unknown>[])
    chat.setMessages(display)
    chatWindowRef.value?.scrollToBottom()
  } catch {
    // new chat, no history
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
  const activeGroupId = (chatStore.activeChat!.meta?.group_id as string) || currentGroupId.value || undefined

  await chat.sendMessage(
    text,
    chatStore.activeChat!.session_id,
    chatStore.activeChat!.user_id,
    () => chatWindowRef.value?.scrollToBottom(),
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
        else chatStore.chats = chatStore.chats.filter((c) => c.id !== chatItem.id)
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
  if (active && !active.meta?._isTemp) {
    selectedAgentId.value = (active.meta?.agent_id as string) || 'main'
    try {
      const history = await chatStore.getChatHistory(active.id)
      const display = chat.convertHistoryToDisplay(history.messages as unknown as Record<string, unknown>[])
      chat.setMessages(display)
      chatWindowRef.value?.scrollToBottom()
    } catch {
      // no history yet
    }
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

.expand-sidebar-btn {
  position: fixed;
  top: 12px;
  left: 12px;
  z-index: 100;
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-card);
  cursor: pointer;
  color: var(--text-3);
  box-shadow: var(--shadow-sm);
  transition: background var(--transition-fast);
}
.expand-sidebar-btn:hover {
  background: var(--bg);
  color: var(--text-1);
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.agent-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.agent-bar-label {
  font-size: 13px;
  color: var(--text-3);
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

.start-chat-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-size: 14px; font-weight: 500;
  cursor: pointer;
  transition: background var(--transition-fast);
}
.start-chat-btn:hover { background: var(--primary-hover); }
</style>
