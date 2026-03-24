import api from './index'
import type { ChatHistory, ChatSpec } from '@/types'

const getGroupChatsEndpoint = (groupId: string) => `/group-chats/${groupId}/chats`

export const listGroupChatSessions = (groupId: string) =>
  api.get<ChatSpec[]>(getGroupChatsEndpoint(groupId)).then((r) => r.data)

export const createGroupChatSession = (
  groupId: string,
  data: Partial<ChatSpec>,
) => api.post<ChatSpec>(getGroupChatsEndpoint(groupId), data).then((r) => r.data)

export const getGroupChatSession = (groupId: string, chatId: string) =>
  api.get<ChatHistory>(`${getGroupChatsEndpoint(groupId)}/${chatId}`).then((r) => r.data)

export const updateGroupChatSession = (
  groupId: string,
  chatId: string,
  data: ChatSpec,
) => api.put<ChatSpec>(`${getGroupChatsEndpoint(groupId)}/${chatId}`, data).then((r) => r.data)

export const deleteGroupChatSession = (groupId: string, chatId: string) =>
  api.delete<{ deleted: boolean }>(`${getGroupChatsEndpoint(groupId)}/${chatId}`).then((r) => r.data)

export const stopGroupChat = (groupId: string, chatId: string) =>
  api.post<{ stopped: boolean }>(`/group-chats/${groupId}/stop`, {
    chat_id: chatId,
  }).then((r) => r.data)
