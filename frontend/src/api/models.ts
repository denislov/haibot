import api from './index'
import type { ProviderInfo, ActiveModelsInfo } from '@/types'

/**
 * List all available model providers and their models
 */
export const listProviders = () =>
  api.get<ProviderInfo[]>('/models').then((r) => r.data)

/**
 * Update provider configuration (API key, base URL, etc.)
 */
export const configureProvider = (providerId: string, data: { api_key?: string; base_url?: string; chat_model?: string }) =>
  api.put<ProviderInfo>(`/models/${providerId}/config`, data).then((r) => r.data)

/**
 * Create a new user-defined provider
 */
export const createCustomProvider = (data: { id: string; name: string; default_base_url?: string; api_key_prefix?: string }) =>
  api.post<ProviderInfo>('/models/custom-providers', data).then((r) => r.data)

/**
 * Delete a user-defined provider
 */
export const deleteCustomProvider = (providerId: string) =>
  api.delete<ProviderInfo[]>(`/models/custom-providers/${providerId}`).then((r) => r.data)

/**
 * Add an extra model to a provider
 */
export const addModel = (providerId: string, data: { id: string; name: string }) =>
  api.post<ProviderInfo>(`/models/${providerId}/models`, data).then((r) => r.data)

/**
 * Remove an extra model from a provider
 */
export const removeModel = (providerId: string, modelId: string) =>
  api.delete<ProviderInfo>(`/models/${providerId}/models/${modelId}`).then((r) => r.data)

/**
 * Get current system-wide active models
 */
export const getActiveModel = () =>
  api.get<ActiveModelsInfo>('/models/active').then((r) => r.data)

/**
 * Set the system-wide active LLM
 */
export const setActiveModel = (data: { provider_id: string; model: string }) =>
  api.put<ActiveModelsInfo>('/models/active', data).then((r) => r.data)

// ── Diagnostics and Discovery ──────────────────────────────────────────────────

/**
 * Test connectivity to a provider's API
 */
export const testProvider = (providerId: string, data?: { api_key?: string; base_url?: string }) =>
  api.post<{ success: boolean; message: string }>(`/models/${providerId}/test`, data ?? null).then((r) => r.data)

/**
 * Fetch available models from a provider's API
 */
export const discoverModels = (providerId: string, data?: { api_key?: string; base_url?: string }) =>
  api.post<{ models: { id: string; name: string }[] }>(`/models/${providerId}/discover`, data ?? null).then((r) => r.data)

/**
 * Test connectivity and behavior for a specific model
 */
export const testModel = (providerId: string, data: { model_id: string }) =>
  api.post<{ success: boolean; message: string }>(`/models/${providerId}/models/test`, data).then((r) => r.data)
