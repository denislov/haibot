// ── Models / Providers ────────────────────────────────────────────────────────
export interface ModelInfo {
  id: string
  name: string
}

export interface ProviderInfo {
  id: string
  name: string
  api_key_prefix: string
  models: ModelInfo[]
  extra_models: ModelInfo[]
  is_custom: boolean
  is_local: boolean
  needs_base_url?: boolean
  has_api_key: boolean
  current_api_key: string
  current_base_url: string
}

export interface ModelSlotConfig {
  provider_id: string
  model: string
}

export interface ActiveModelsInfo {
  active_llm: ModelSlotConfig
}
