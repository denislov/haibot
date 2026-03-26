<template>
  <div class="chat-layout">
    <!-- Left sidebar: contacts (agents + group chats) -->
    <ContactSidebar
      :agents="agentsList"
      :group-chats="groupChats"
      :selected-id="selectedContact?.id ?? null"
      :selected-type="selectedContact?.type ?? null"
      :collapsed="leftCollapsed"
      @toggle="toggleLeftSidebar"
      @select-agent="handleSelectAgent"
      @select-group="handleSelectGroup"
      @open-settings="router.push('/settings')"
    />

    <!-- Left expand button (shown when left sidebar collapsed) -->
    <button v-if="leftCollapsed" class="expand-btn expand-btn-left" @click="openLeftSidebar">
      <el-icon><Expand /></el-icon>
    </button>

    <div
      v-if="showSidebarBackdrop"
      class="sidebar-backdrop"
      @click="closeMobileDrawers"
    />

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
        <div v-else-if="chat.welcomeMessage.value" class="welcome-container">
          <div class="welcome-bubble">
            {{ chat.welcomeMessage.value }}
          </div>
        </div>
        <ChatWindow
          v-else
          ref="chatWindowRef"
          :messages="chat.displayMessages.value"
          :mode="currentGroupId ? 'group' : 'single'"
          :streaming="chat.streaming.value"
          :allow-regenerate="!currentGroupId"
          @regenerate="handleRegenerate"
        />
        <ChatInput
          v-model="chat.inputText.value"
          :streaming="chat.streaming.value"
          :attachments="attachments"
          @send="sendMessage"
          @stop="chat.stopStreaming(resolveChatAgentId(chatStore.activeChat), currentGroupId ?? undefined)"
          @add-files="handleAddFiles"
          @remove-attachment="handleRemoveAttachment"
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
      @toggle="toggleRightSidebar"
      @select-chat="selectChat"
      @chat-action="handleChatAction"
      @new-chat="handleNewChat"
    />

    <!-- Right expand button (shown when right sidebar collapsed AND a contact is selected) -->
    <button v-if="rightCollapsed && selectedContact" class="expand-btn expand-btn-right" @click="openRightSidebar">
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
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useMediaQuery, useStorage } from '@vueuse/core'
import { useChatStore } from '@/stores/chat'
import { useChat } from './composables/useChat'
import { uploadFile, uploadGroupFile } from '@/api/console'
import { listAgents } from '@/api/agents'
import { listGroupChats } from '@/api/group_chats'
import type { ChatSpec, AgentInfo, FileAttachment } from '@/types'
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

const isMobile = useMediaQuery('(max-width: 960px)')
const desktopLeftCollapsed = useStorage('haibot-left-sidebar', false)
const desktopRightCollapsed = useStorage('haibot-history-sidebar', false)
const mobileLeftCollapsed = ref(true)
const mobileRightCollapsed = ref(true)

const leftCollapsed = computed({
  get: () => (
    isMobile.value ? mobileLeftCollapsed.value : desktopLeftCollapsed.value
  ),
  set: (value: boolean) => {
    if (isMobile.value) mobileLeftCollapsed.value = value
    else desktopLeftCollapsed.value = value
  },
})

const rightCollapsed = computed({
  get: () => (
    isMobile.value ? mobileRightCollapsed.value : desktopRightCollapsed.value
  ),
  set: (value: boolean) => {
    if (isMobile.value) mobileRightCollapsed.value = value
    else desktopRightCollapsed.value = value
  },
})

const selectedContact = ref<{ type: 'agent' | 'group'; id: string } | null>(null)

const renameDialogVisible = ref(false)
const renameName = ref('')
const renamingChatId = ref<string | null>(null)
const historyLoading = ref(false)

// ── File attachments ──
const attachments = ref<FileAttachment[]>([])

// ── Agent selector ──
const agentsList = ref<AgentInfo[]>([])
const selectedAgentId = ref('default')

// ── Group chats ──
const groupChats = ref<GroupChatConfig[]>([])

// ── Computed ───────────────────────────────────────────────────────────────

const fallbackAgentId = computed(() => agentsList.value[0]?.id ?? 'default')

// Derive currentGroupId from selectedContact (replaces the old ref)
const currentGroupId = computed(() =>
  selectedContact.value?.type === 'group' ? selectedContact.value.id : null
)

const showSidebarBackdrop = computed(
  () => isMobile.value && (!leftCollapsed.value || !rightCollapsed.value),
)

function closeMobileDrawers() {
  if (!isMobile.value) return
  leftCollapsed.value = true
  rightCollapsed.value = true
}

function openLeftSidebar() {
  if (isMobile.value) rightCollapsed.value = true
  leftCollapsed.value = false
}

function openRightSidebar() {
  if (isMobile.value) leftCollapsed.value = true
  rightCollapsed.value = false
}

function toggleLeftSidebar() {
  if (isMobile.value && leftCollapsed.value) {
    openLeftSidebar()
    return
  }
  leftCollapsed.value = !leftCollapsed.value
}

function toggleRightSidebar() {
  if (isMobile.value && rightCollapsed.value) {
    openRightSidebar()
    return
  }
  rightCollapsed.value = !rightCollapsed.value
}

// Chats filtered to the selected contact
const contactChats = computed(() => {
  if (!selectedContact.value) return []
  const { type, id } = selectedContact.value
  return chatStore.chats.filter((c) => {
    if (type === 'agent') return c.meta?.agent_id != null && String(c.meta.agent_id) === id && !c.meta?.group_id
    return c.meta?.group_id != null && String(c.meta.group_id) === id
  })
})

function resolveChatAgentId(chat?: ChatSpec | null): string {
  const chatAgentId = chat?.meta?.agent_id
  if (typeof chatAgentId === 'string' && chatAgentId) return chatAgentId
  if (selectedContact.value?.type === 'agent') return selectedContact.value.id
  if (selectedAgentId.value) return selectedAgentId.value
  return fallbackAgentId.value
}

function resolveChatAgentName(chat?: ChatSpec | null): string {
  const chatAgentId = resolveChatAgentId(chat)
  const agent = agentsList.value.find((item) => item.id === chatAgentId)
  if (agent?.name) return agent.name
  if (selectedContact.value?.type === 'agent') {
    const selected = agentsList.value.find((item) => item.id === selectedContact.value?.id)
    if (selected?.name) return selected.name
  }
  return 'Assistant'
}

function resolveAgentNameById(agentId?: string): string | undefined {
  if (!agentId) return undefined
  return agentsList.value.find((item) => item.id === agentId)?.name
}

// ── File upload handling ──────────────────────────────────────────────────

function handleAddFiles(files: File[]) {
  const currentAgentId = resolveChatAgentId(chatStore.activeChat)
  const activeGroupId = currentGroupId.value

  for (const file of files) {
    if (file.size > 10 * 1024 * 1024) {
      ElMessage.warning(t('chat.fileTooLarge'))
      continue
    }
    const att: FileAttachment = {
      id: uuidv4(),
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
      uploading: true,
    }
    attachments.value.push(att)

    const uploadPromise = activeGroupId
      ? uploadGroupFile(file, activeGroupId)
      : uploadFile(file, currentAgentId)

    uploadPromise
      .then((res) => {
        att.uploadedUrl = res.url
        att.uploading = false
      })
      .catch((e) => {
        att.error = e instanceof Error ? e.message : String(e)
        att.uploading = false
        ElMessage.error(t('chat.uploadFailed'))
      })
  }
}

function handleRemoveAttachment(id: string) {
  const idx = attachments.value.findIndex((a) => a.id === id)
  if (idx !== -1) {
    const att = attachments.value[idx]
    if (att.previewUrl) URL.revokeObjectURL(att.previewUrl)
    attachments.value.splice(idx, 1)
  }
}

// ── Select Agent ──────────────────────────────────────────────────────────
async function handleSelectAgent(agent: AgentInfo) {
  if (selectedContact.value?.type === 'agent' && selectedContact.value.id === agent.id && chatStore.activeChat?.meta?._isTemp) {
    return
  }
  selectedContact.value = { type: 'agent', id: agent.id }
  selectedAgentId.value = agent.id
  await chatStore.loadChats(agent.id)

  // Find existing temp chat for this agent
  const existingTemp = chatStore.chats.find(c => c.meta?._isTemp && c.meta?.agent_id === agent.id && !c.meta?.group_id)
  if (existingTemp) {
    chatStore.setActiveChat(existingTemp)
    chat.setChatId(existingTemp.id)
    chat.clearMessages()
    chat.setWelcomeMessage(t('chat.emptyState'))
    return
  }

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
  chat.setChatId(temp.id)
  chat.clearMessages()
  chat.setWelcomeMessage(t('chat.emptyState'))
  closeMobileDrawers()
}

// ── Select Group Chat ─────────────────────────────────────────────────────
async function handleSelectGroup(gc: GroupChatConfig) {
  if (selectedContact.value?.type === 'group' && selectedContact.value.id === gc.id && chatStore.activeChat?.meta?._isTemp) {
    return
  }
  selectedContact.value = { type: 'group', id: gc.id }
  await chatStore.loadChats(undefined, gc.id)

  const existingTemp = chatStore.chats.find(c => c.meta?._isTemp && c.meta?.group_id === gc.id)
  if (existingTemp) {
    chatStore.setActiveChat(existingTemp)
    chat.setChatId(existingTemp.id)
    chat.clearMessages()
    chat.setWelcomeMessage(t('chat.emptyState'))
    return
  }

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
  chat.setChatId(temp.id)
  chat.clearMessages()
  chat.setWelcomeMessage(t('chat.emptyState'))
  closeMobileDrawers()
}

// ── New Chat ──
function handleNewChat() {
  if (!selectedContact.value) return
  if (selectedContact.value.type === 'agent') {
    const agent = agentsList.value.find(a => a.id === selectedContact.value!.id)
    if (agent) handleSelectAgent(agent)
  } else {
    const gc = groupChats.value.find(g => g.id === selectedContact.value!.id)
    if (gc) handleSelectGroup(gc)
  }
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
  chat.setChatId(selected.id)
  chat.clearMessages()
  selectedAgentId.value = resolveChatAgentId(selected)
  if (selected.meta?._isTemp) {
    chat.setWelcomeMessage(t('chat.emptyState'))
    return
  }
  historyLoading.value = true
  try {
    const currentAgentId = resolveChatAgentId(selected)
    const history = await chatStore.getChatHistory(
      selected.id,
      selected.meta?.group_id ? undefined : currentAgentId,
      selected.meta?.group_id ? String(selected.meta.group_id) : undefined,
    )
    const display = chat.convertHistoryToDisplay(
      history.messages as unknown as Record<string, unknown>[],
      resolveAgentNameById,
      selected.meta?.group_id ? undefined : currentAgentId,
    )
    chat.setMessages(display)
    chatWindowRef.value?.scrollToBottom()

    // Reconnect if chat is still running on server
    if (history.status === 'running') {
      const activeGroupId = currentGroupId.value || undefined

      await chat.sendMessage(
        '',
        selected.session_id,
        selected.user_id,
        () => chatWindowRef.value?.scrollIfNearBottom(),
        () => void (
          activeGroupId
            ? chatStore.loadChats(undefined, activeGroupId)
            : chatStore.loadChats(currentAgentId)
        ),
        (e) => ElMessage.error(t('chat.requestFailed') + ': ' + e.message),
        activeGroupId ? undefined : currentAgentId,
        activeGroupId ? undefined : resolveChatAgentName(selected),
        activeGroupId ?? undefined,
        true, // reconnect
        selected.id,
      )
    }
  } catch {
    // no history
  } finally {
    historyLoading.value = false
  }
  closeMobileDrawers()
}

// ── Send Message ──────────────────────────────────────────────────────────
async function sendMessage() {
  const text = chat.inputText.value.trim()
  if (!text || !chatStore.activeChat) return

  // Check all attachments finished uploading
  if (attachments.value.some((a) => a.uploading)) {
    ElMessage.warning(t('chat.uploading'))
    return
  }

  chat.inputText.value = ''
  chat.setWelcomeMessage(null)

  // Collect attachment info before clearing
  const sentAttachments = attachments.value
    .filter((a) => a.uploadedUrl && !a.error)
    .map((a) => ({ url: a.uploadedUrl!, name: a.name, type: a.type }))

  // Clear attachments
  for (const att of attachments.value) {
    if (att.previewUrl) URL.revokeObjectURL(att.previewUrl)
  }
  attachments.value = []

  let activeChat = chatStore.activeChat

  // Persist temp chat on first message
  if (activeChat.meta?._isTemp) {
    try {
      const currentAgentId = resolveChatAgentId(activeChat)
      const persisted = await chatStore.addChat({
        name: text.slice(0, 20),
        session_id: activeChat.session_id,
        user_id: activeChat.user_id,
        channel: 'console',
        meta: {
          ...(activeChat.meta?.group_id ? { group_id: activeChat.meta.group_id } : {}),
          ...(activeChat.meta?.group_id ? {} : { agent_id: currentAgentId }),
        },
      },
      activeChat.meta?.group_id ? undefined : currentAgentId,
      activeChat.meta?.group_id ? String(activeChat.meta.group_id) : undefined,
      )
      const idx = chatStore.chats.findIndex((c) => c.id === activeChat.id)
      if (idx !== -1) chatStore.chats[idx] = persisted
      chatStore.setActiveChat(persisted)
      activeChat = persisted
      chat.setChatId(persisted.id)
    } catch (e: unknown) {
      ElMessage.error(t('chat.createFailed') + ': ' + (e instanceof Error ? e.message : String(e)))
      return
    }
  }

  const currentAgentId = resolveChatAgentId(activeChat)
  const activeGroupId = currentGroupId.value || undefined

  await chat.sendMessage(
    text,
    activeChat.session_id,
    activeChat.user_id,
    () => chatWindowRef.value?.scrollIfNearBottom(),
    () => void (
      activeGroupId
        ? chatStore.loadChats(undefined, activeGroupId)
        : chatStore.loadChats(currentAgentId)
    ),
    (e) => ElMessage.error(t('chat.requestFailed') + ': ' + e.message),
    activeGroupId ? undefined : currentAgentId,
    activeGroupId ? undefined : resolveChatAgentName(activeChat),
    activeGroupId ?? undefined,
    false, // not reconnect
    activeChat.id,
    sentAttachments.length > 0 ? sentAttachments : undefined,
  )
}

// ── Regenerate ───────────────────────────────────────────────────────────
async function handleRegenerate() {
  if (!chatStore.activeChat) return
  const activeChat = chatStore.activeChat
  const currentAgentId = resolveChatAgentId(activeChat)
  const activeGroupId = currentGroupId.value || undefined

  await chat.regenerateLastMessage(
    activeChat.session_id,
    activeChat.user_id,
    () => chatWindowRef.value?.scrollIfNearBottom(),
    () => void (
      activeGroupId
        ? chatStore.loadChats(undefined, activeGroupId)
        : chatStore.loadChats(currentAgentId)
    ),
    (e) => ElMessage.error(t('chat.requestFailed') + ': ' + e.message),
    activeGroupId ? undefined : currentAgentId,
    activeGroupId ? undefined : resolveChatAgentName(activeChat),
    activeGroupId ?? undefined,
    activeChat.id,
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
        if (!chatItem.meta?._isTemp) {
          await chatStore.removeChat(
            chatItem.id,
            chatItem.meta?.group_id ? undefined : resolveChatAgentId(chatItem),
            chatItem.meta?.group_id ? String(chatItem.meta.group_id) : undefined,
          )
        } else {
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
    const chatItem = chatStore.chats.find((chat) => chat.id === renamingChatId.value)
    await chatStore.renameChat(
      renamingChatId.value,
      renameName.value,
      chatItem?.meta?.group_id ? undefined : (chatItem ? resolveChatAgentId(chatItem) : undefined),
      chatItem?.meta?.group_id ? String(chatItem.meta.group_id) : undefined,
    )
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
    // fallback to default only
    agentsList.value = [{ id: 'default', name: 'Default', description: '', is_main: true, files: [], created_at: '' }]
  }

  selectedAgentId.value = fallbackAgentId.value

  // Load group chats
  try {
    groupChats.value = await listGroupChats()
  } catch {
    // group chats optional
  }

  // Restore active chat's history if returning from settings
  const active = chatStore.activeChat
  if (active && !active.meta?._isTemp) {
    // Restore selectedContact from active chat meta
    if (active.meta?.group_id) {
      selectedContact.value = { type: 'group', id: String(active.meta.group_id) }
      await chatStore.loadChats(undefined, String(active.meta.group_id))
    } else {
      const agentId = active.meta?.agent_id ? String(active.meta.agent_id) : fallbackAgentId.value
      selectedContact.value = { type: 'agent', id: agentId }
      selectedAgentId.value = agentId
      await chatStore.loadChats(resolveChatAgentId(active))
    }
    historyLoading.value = true
    try {
      const history = await chatStore.getChatHistory(
        active.id,
        active.meta?.group_id ? undefined : resolveChatAgentId(active),
        active.meta?.group_id ? String(active.meta.group_id) : undefined,
      )
      const display = chat.convertHistoryToDisplay(
        history.messages as unknown as Record<string, unknown>[],
        resolveAgentNameById,
        active.meta?.group_id ? undefined : resolveChatAgentId(active),
      )
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
    handleSelectAgent(agentsList.value[0])
  }
})

watch(
  isMobile,
  (mobile) => {
    if (mobile) {
      mobileLeftCollapsed.value = true
      mobileRightCollapsed.value = true
    }
  },
  { immediate: true },
)
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: 100dvh;
  overflow: hidden;
  background: var(--bg);
}

.sidebar-backdrop {
  position: fixed;
  inset: 0;
  z-index: 109;
  background: rgba(8, 10, 18, 0.42);
  backdrop-filter: blur(4px);
}

.expand-btn {
  position: fixed;
  z-index: 130;
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
  min-width: 0;
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

/* ── Welcome message ── */
.welcome-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.welcome-bubble {
  max-width: 500px;
  background: var(--bg-user-message);
  color: var(--text-2);
  padding: 16px 20px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.6;
  text-align: center;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  animation: slide-up 0.4s ease-out;
}

@keyframes slide-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
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
.skeleton-row.user { justify-content: flex-start; }
.skeleton-row.assistant { justify-content: flex-start; }

.skeleton-bubble {
  height: 40px;
  border-radius: var(--radius-lg);
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

@media (max-width: 960px) {
  .expand-btn {
    top: calc(12px + var(--safe-top));
  }

  .expand-btn-left {
    left: calc(12px + var(--safe-left));
  }

  .expand-btn-right {
    right: calc(12px + var(--safe-right));
  }

  .chat-titlebar {
    padding:
      calc(10px + var(--safe-top))
      calc(56px + var(--safe-right))
      10px
      calc(56px + var(--safe-left));
    min-height: calc(52px + var(--safe-top));
  }

  .chat-titlebar-name {
    max-width: 100%;
    font-size: 13px;
  }

  .history-loading,
  .welcome-container {
    padding: 18px 12px;
  }

  .welcome-bubble {
    max-width: 100%;
    padding: 14px 16px;
    font-size: 14px;
  }

  .empty-logo {
    font-size: 24px;
  }

  .empty-content p {
    font-size: 13px;
    text-align: center;
  }
}
</style>
