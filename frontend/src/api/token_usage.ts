import api from './index'

// ── Token Usage ───────────────────────────────────────────────────────────────

export interface TokenUsageStats {
  prompt_tokens: number
  completion_tokens: number
  call_count: number
}

export interface TokenUsageByModel extends TokenUsageStats {
  provider_id: string
  model: string
}

export interface TokenUsageSummary {
  total_prompt_tokens: number
  total_completion_tokens: number
  total_calls: number
  by_model: Record<string, TokenUsageByModel>
  by_provider: Record<string, TokenUsageStats>
  by_date: Record<string, TokenUsageStats>
}

export const getTokenUsage = (params?: {
  start_date?: string
  end_date?: string
  model?: string
  provider?: string
}) =>
  api.get<TokenUsageSummary>('/token-usage', { params }).then((r) => r.data)
