import api from './index'
import type { GroupChatConfig } from '@/types/group_chat'

export const listGroupChats = () =>
  api.get<GroupChatConfig[]>('/group-chats').then(r => r.data)

export const createGroupChat = (data: Omit<GroupChatConfig, 'created_at'>) =>
  api.post<GroupChatConfig>('/group-chats', data).then(r => r.data)

export const updateGroupChat = (id: string, data: GroupChatConfig) =>
  api.put<GroupChatConfig>(`/group-chats/${id}`, data).then(r => r.data)

export const deleteGroupChat = (id: string) =>
  api.delete<{ deleted: boolean }>(`/group-chats/${id}`).then(r => r.data)
