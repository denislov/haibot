import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listChats, createChat, deleteChat, updateChat, getChat } from '@/api/chats'
import type { ChatSpec } from '@/types'

export const useChatStore = defineStore('chat', () => {
  const chats = ref<ChatSpec[]>([])
  const activeChat = ref<ChatSpec | null>(null)

  function normalizeChat(chat: ChatSpec, agentId?: string): ChatSpec {
    if (!agentId) return chat
    return {
      ...chat,
      meta: {
        ...chat.meta,
        agent_id: chat.meta?.agent_id ?? agentId,
      },
    }
  }

  function getChatAgentId(chat: ChatSpec): string | null {
    const agentId = chat.meta?.agent_id
    return typeof agentId === 'string' && agentId ? agentId : null
  }

  function replaceChatsForAgent(agentId: string, loadedChats: ChatSpec[]) {
    const normalized = loadedChats.map((chat) => normalizeChat(chat, agentId))
    const preserved = chats.value.filter((chat) => {
      const chatAgentId = getChatAgentId(chat)
      return chat.meta?._isTemp || chatAgentId !== agentId
    })
    chats.value = [...preserved, ...normalized]
  }

  async function loadChats(agentId?: string) {
    try {
      const loadedChats = await listChats(undefined, agentId)
      if (agentId) {
        replaceChatsForAgent(agentId, loadedChats)
      } else {
        chats.value = loadedChats
      }
    } catch {
      // ignore on startup
    }
  }

  function setActiveChat(chat: ChatSpec | null) {
    activeChat.value = chat
  }

  async function addChat(data: Partial<ChatSpec>, agentId?: string): Promise<ChatSpec> {
    const created = normalizeChat(await createChat(data, agentId), agentId)
    chats.value.unshift(created)
    return created
  }

  async function removeChat(id: string, agentId?: string) {
    await deleteChat(id, agentId)
    chats.value = chats.value.filter((c) => c.id !== id)
    if (activeChat.value?.id === id) {
      activeChat.value = null
    }
  }

  async function renameChat(id: string, name: string, agentId?: string) {
    const chat = chats.value.find((c) => c.id === id)
    if (!chat) return
    const updated = { ...chat, name }
    await updateChat(id, updated, agentId)
    const idx = chats.value.findIndex((c) => c.id === id)
    if (idx !== -1) chats.value[idx] = updated
    if (activeChat.value?.id === id) activeChat.value = updated
  }

  async function getChatHistory(id: string, agentId?: string) {
    return getChat(id, agentId)
  }

  return {
    chats,
    activeChat,
    loadChats,
    setActiveChat,
    addChat,
    removeChat,
    renameChat,
    getChatHistory,
  }
})
