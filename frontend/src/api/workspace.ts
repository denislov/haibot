import api from './index'
import type { MdFileInfo, MdFileContent } from '@/types'

/**
 * List files in the active agent's workspace
 */
export const listAgentFiles = () =>
  api.get<MdFileInfo[]>('/agent/files').then((r) => r.data)

/**
 * Read a file from the active agent's workspace
 */
export const readAgentFile = (filename: string) =>
  api.get<MdFileContent>(`/agent/files/${filename}`).then((r) => r.data.content)

/**
 * Write a file to the active agent's workspace
 */
export const writeAgentFile = (filename: string, content: string) =>
  api.put<MdFileInfo>(`/agent/files/${filename}`, { content }).then((r) => r.data)

/**
 * Download the entire workspace as a zip archive
 */
export const downloadWorkspace = () => {
  const a = document.createElement('a')
  // Use absolute URL for download
  const base = (api.defaults.baseURL === '/' ? '' : api.defaults.baseURL) || ''
  a.href = `${base}/api/workspace/download`
  a.download = 'haibot_workspace.zip'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

/**
 * Upload a zip archive to merge into the workspace
 */
export const uploadWorkspace = async (file: File) => {
  const form = new FormData()
  form.append('file', file)
  const r = await api.post<{ success: boolean }>('/workspace/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return r.data
}
