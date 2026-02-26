import api from './index'
import type { SkillSpec } from '@/types'

export const listSkills = () =>
  api.get<SkillSpec[]>('/skills').then((r) => r.data)

export const enableSkill = (name: string) =>
  api.post<{ enabled: boolean }>(`/skills/${name}/enable`).then((r) => r.data)

export const disableSkill = (name: string) =>
  api.post<{ disabled: boolean }>(`/skills/${name}/disable`).then((r) => r.data)

export const deleteSkill = (name: string) =>
  api.delete<{ deleted: boolean }>(`/skills/${name}`).then((r) => r.data)

export interface CreateSkillPayload {
  name: string
  content: string
  references?: Record<string, unknown>
  scripts?: Record<string, unknown>
}

export const createSkill = (data: CreateSkillPayload) =>
  api.post<{ created: boolean }>('/skills', data).then((r) => r.data)

export const updateSkill = (name: string, content: string) =>
  api.put<{ updated: boolean }>(`/skills/${name}`, { content }).then((r) => r.data)
