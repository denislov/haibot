// ── Models / Providers ────────────────────────────────────────────────────────

export interface ModelInfo {
  id: string
  name: string
}

export interface ProviderInfo {
  id: string
  name: string
  base_url: string
  api_key: string
  chat_model: string
  models: ModelInfo[]
  extra_models: ModelInfo[]
  api_key_prefix: string
  is_local: boolean
  freeze_url: boolean
  require_api_key: boolean
  is_custom: boolean
  support_model_discovery: boolean
  support_connection_check: boolean
  generate_kwargs: Record<string, any>
}

export interface ModelSlotConfig {
  provider_id: string
  model: string
}

export interface ActiveModelsInfo {
  active_llm: ModelSlotConfig | null
}
