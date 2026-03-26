import api, { buildApiUrl, createAuthHeaders } from './index'
import { notifyUnauthorized } from '@/utils/authSession'
import type {
  SkillSpec,
  HubSkillSpec,
  HubInstallRequest,
  HubInstallResult,
  HubInstallTask,
  UploadSkillResult,
} from '@/types'

// ── Core CRUD ─────────────────────────────────────────────────────────────
export const listSkills = () =>
  api.get<SkillSpec[]>('/skills').then((r) => r.data)

export const getAvailableSkills = () =>
  api.get<SkillSpec[]>('/skills/available').then((r) => r.data)

export const createSkill = (data: { name: string; content: string; references?: Record<string, any>; scripts?: Record<string, any> }) =>
  api.post('/skills', data).then((r) => r.data)

export const updateSkill = createSkill

export const enableSkill = (name: string) =>
  api.post(`/skills/${name}/enable`).then((r) => r.data)

export const disableSkill = (name: string) =>
  api.post(`/skills/${name}/disable`).then((r) => r.data)

export const deleteSkill = (name: string) =>
  api.delete(`/skills/${name}`).then((r) => r.data)

// ── Batch operations ──────────────────────────────────────────────────────
export const batchEnableSkills = (names: string[]) =>
  api.post('/skills/batch-enable', names).then((r) => r.data)

export const batchDisableSkills = (names: string[]) =>
  api.post('/skills/batch-disable', names).then((r) => r.data)

// ── Skill file access ─────────────────────────────────────────────────────
export const loadSkillFile = (skillName: string, source: string, filePath: string) =>
  api.get(`/skills/${skillName}/files/${source}/${filePath}`).then((r) => r.data)

// ── Upload ────────────────────────────────────────────────────────────────
export const uploadSkillZip = (file: File, options?: { enable?: boolean; overwrite?: boolean }) => {
  const form = new FormData()
  form.append('file', file)
  const params: Record<string, unknown> = {}
  if (options?.enable) params.enable = true
  if (options?.overwrite) params.overwrite = true
  return api.post<UploadSkillResult>('/skills/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    params,
    timeout: 120000,
  }).then((r) => r.data)
}

// ── Skills Hub ────────────────────────────────────────────────────────────
export const searchHub = (q?: string, limit?: number) =>
  api.get<HubSkillSpec[]>('/skills/hub/search', { params: { q, limit } }).then((r) => r.data)

export const installFromHub = (data: HubInstallRequest) =>
  api.post<HubInstallResult>('/skills/hub/install', data, {
    timeout: 120000,
  }).then((r) => r.data)

export const startInstallFromHub = (data: HubInstallRequest) =>
  api.post<HubInstallTask>('/skills/hub/install/start', data).then((r) => r.data)

export const getHubInstallStatus = (taskId: string) =>
  api.get<HubInstallTask>(`/skills/hub/install/status/${taskId}`).then((r) => r.data)

export const cancelHubInstall = (taskId: string) =>
  api.post(`/skills/hub/install/cancel/${taskId}`).then((r) => r.data)

// ── AI Optimize (streaming) ───────────────────────────────────────────────
export async function aiOptimizeSkillStream(
  content: string,
  language: string,
  onChunk: (text: string) => void,
  onDone: () => void,
  onError: (e: Error) => void,
  signal?: AbortSignal,
) {
  const url = buildApiUrl('/skills/ai/optimize/stream')

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: createAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ content, language }),
      signal,
    })

    if (!response.ok) {
      if (response.status === 401) {
        notifyUnauthorized('Invalid or expired token')
      }
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) { onDone(); return }
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const raw = line.slice(6).trim()
          if (!raw || raw === '[DONE]') continue
          try {
            const event = JSON.parse(raw)
            if (event.text) onChunk(event.text)
          } catch { /* ignore */ }
        }
      }
    }
  } catch (e: unknown) {
    if (e instanceof Error) onError(e)
    else onError(new Error(String(e)))
  }
}
