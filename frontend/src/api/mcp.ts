import api from './index'
import type { MCPClientInfo } from '@/types'

export const listMCPClients = () =>
  api.get<MCPClientInfo[]>('/mcp').then((r) => r.data)

export const getMCPClient = (key: string) =>
  api.get<MCPClientInfo>(`/mcp/${key}`).then((r) => r.data)

export const createMCPClient = (data: { client_key: string; client: Record<string, any> }) =>
  api.post<MCPClientInfo>('/mcp', data).then((r) => r.data)

export const updateMCPClient = (key: string, data: Record<string, any>) =>
  api.put<MCPClientInfo>(`/mcp/${key}`, data).then((r) => r.data)

export const toggleMCPClient = (key: string) =>
  api.patch<MCPClientInfo>(`/mcp/${key}/toggle`).then((r) => r.data)

export const deleteMCPClient = (key: string) =>
  api.delete<{ message: string }>(`/mcp/${key}`).then((r) => r.data)
