import api from './index'
import type { ProviderInfo, ActiveModelsInfo } from '@/types'

export const listProviders = () =>
  api.get<ProviderInfo[]>('/models').then((r) => r.data)

export const configureProvider = (id: string, data: { api_key?: string; base_url?: string }) =>
  api.put<ProviderInfo>(`/models/${id}/config`, data).then((r) => r.data)

export const getActiveModel = () =>
  api.get<ActiveModelsInfo>('/models/active').then((r) => r.data)

export const setActiveModel = (data: { provider_id: string; model: string }) =>
  api.put<ActiveModelsInfo>('/models/active', data).then((r) => r.data)
