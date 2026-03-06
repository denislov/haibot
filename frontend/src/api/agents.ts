import api from './index'
import type { AgentInfo } from '@/types'

export const listAgents = () =>
  api.get<AgentInfo[]>('/agents').then((r) => r.data)

export const createAgent = (data: { id: string; name: string; description?: string }) =>
  api.post<AgentInfo>('/agents', data).then((r) => r.data)

export const getAgent = (id: string) =>
  api.get<AgentInfo>(`/agents/${id}`).then((r) => r.data)

export const updateAgent = (id: string, data: { name?: string; description?: string }) =>
  api.put<AgentInfo>(`/agents/${id}`, data).then((r) => r.data)

export const deleteAgent = (id: string) =>
  api.delete<{ message: string }>(`/agents/${id}`).then((r) => r.data)

export const listAgentFiles = (agentId: string) =>
  api.get<Array<{ name: string; size: number }>>(`/agents/${agentId}/files`).then((r) => r.data)

export const readAgentFile = (agentId: string, filename: string) =>
  api.get<{ name: string; content: string }>(`/agents/${agentId}/files/${filename}`).then((r) => r.data)

export const writeAgentFile = (agentId: string, filename: string, content: string) =>
  api.put<{ written: boolean }>(`/agents/${agentId}/files/${filename}`, { content }).then((r) => r.data)
