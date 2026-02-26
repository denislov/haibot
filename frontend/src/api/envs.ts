import api from './index'
import type { EnvVar } from '@/types'

export const listEnvs = () =>
  api.get<EnvVar[]>('/envs').then((r) => r.data)

export const saveEnvs = (data: Record<string, string>) =>
  api.put<EnvVar[]>('/envs', data).then((r) => r.data)

export const deleteEnv = (key: string) =>
  api.delete<EnvVar[]>(`/envs/${encodeURIComponent(key)}`).then((r) => r.data)
