import api from './index'
import type { ProviderInfo, ActiveModelsInfo, ModelInfo } from '@/types'

export const listProviders = () =>
  api.get<ProviderInfo[]>('/models').then((r) => r.data)

export const configureProvider = (id: string, data: { api_key?: string; base_url?: string }) =>
  api.put<ProviderInfo>(`/models/${id}/config`, data).then((r) => r.data)

export const getActiveModel = () =>
  api.get<ActiveModelsInfo>('/models/active').then((r) => r.data)

export const setActiveModel = (data: { provider_id: string; model: string }) =>
  api.put<ActiveModelsInfo>('/models/active', data).then((r) => r.data)

export const createCustomProvider = (data: {
  id: string
  name: string
  default_base_url?: string
  api_key_prefix?: string
  models?: ModelInfo[]
}) => api.post<ProviderInfo>('/models/custom-providers', data).then((r) => r.data)

export const deleteCustomProvider = (id: string) =>
  api.delete<ProviderInfo[]>(`/models/custom-providers/${id}`).then((r) => r.data)

export const addModel = (providerId: string, data: { id: string; name: string }) =>
  api.post<ProviderInfo>(`/models/${providerId}/models`, data).then((r) => r.data)

export const removeModel = (providerId: string, modelId: string) =>
  api.delete<ProviderInfo>(`/models/${providerId}/models/${encodeURIComponent(modelId)}`).then((r) => r.data)
