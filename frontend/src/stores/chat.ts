import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listChats, createChat, deleteChat, updateChat, getChat } from '@/api/chats'
import type { ChatSpec } from '@/types'

export const useChatStore = defineStore('chat', () => {
  const chats = ref<ChatSpec[]>([])
  const activeChat = ref<ChatSpec | null>(null)

  async function loadChats() {
    try {
      chats.value = await listChats()
    } catch {
      // ignore on startup
    }
  }

  function setActiveChat(chat: ChatSpec | null) {
    activeChat.value = chat
  }

  async function addChat(data: Partial<ChatSpec>): Promise<ChatSpec> {
    const created = await createChat(data)
    chats.value.unshift(created)
    return created
  }

  async function removeChat(id: string) {
    await deleteChat(id)
    chats.value = chats.value.filter((c) => c.id !== id)
    if (activeChat.value?.id === id) {
      activeChat.value = null
    }
  }

  async function renameChat(id: string, name: string) {
    const chat = chats.value.find((c) => c.id === id)
    if (!chat) return
    const updated = { ...chat, name }
    await updateChat(id, updated)
    const idx = chats.value.findIndex((c) => c.id === id)
    if (idx !== -1) chats.value[idx] = updated
    if (activeChat.value?.id === id) activeChat.value = updated
  }

  async function getChatHistory(id: string) {
    return getChat(id)
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
