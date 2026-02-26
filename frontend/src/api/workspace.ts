import api from './index'
import type { MdFileInfo } from '@/types'

export const listAgentFiles = () =>
  api.get<MdFileInfo[]>('/agent/files').then((r) => r.data)

export const readAgentFile = (name: string) =>
  api.get<{ content: string }>(`/agent/files/${name}`).then((r) => r.data.content)

export const writeAgentFile = (name: string, content: string) =>
  api.put<{ written: boolean }>(`/agent/files/${name}`, { content }).then((r) => r.data)

export const downloadWorkspace = () => {
  const a = document.createElement('a')
  a.href = '/workspace/download'
  a.download = 'haibot_workspace.zip'
  a.click()
}

export const uploadWorkspace = async (file: File) => {
  const form = new FormData()
  form.append('file', file)
  const r = await api.post<{ success: boolean} >('/workspace/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return r.data
}
