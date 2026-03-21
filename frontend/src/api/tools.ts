import api from './index'
import type { ToolInfo } from '@/types'

export const listTools = () =>
  api.get<ToolInfo[]>('/tools').then((r) => r.data)

export const toggleTool = (toolName: string) =>
  api.patch<ToolInfo>(`/tools/${toolName}/toggle`).then((r) => r.data)
