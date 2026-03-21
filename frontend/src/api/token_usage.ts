import api from './index'

// ── Token Usage ───────────────────────────────────────────────────────────────
export interface TokenUsageSummary {
  total_input_tokens: number
  total_output_tokens: number
  total_cost: number
  by_date: { date: string; input_tokens: number; output_tokens: number; cost: number }[]
  by_model: { model: string; provider: string; input_tokens: number; output_tokens: number; cost: number }[]
}

export const getTokenUsage = (params?: {
  start_date?: string
  end_date?: string
  model?: string
  provider?: string
}) =>
  api.get<TokenUsageSummary>('/token-usage', { params }).then((r) => r.data)
