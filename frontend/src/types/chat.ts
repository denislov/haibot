// ── Chat / Session ──────────────────────────────────────────────────────────
export interface ChatSpec {
  id: string
  name: string
  session_id: string
  user_id: string
  channel: string
  created_at: string
  updated_at: string
  meta: Record<string, unknown>
}

export interface ContentItem {
  type: 'text' | 'image' | 'data' | 'file' | 'audio' | 'video'
  text?: string
  url?: string
  data?: Record<string, unknown>
  index?: number
  delta?: boolean
  msg_id?: string
  status?: string
  object?: string
}

export interface AgentMessage {
  id?: string
  object?: string
  type: string
  status?: string
  role?: 'user' | 'assistant' | 'system' | 'tool'
  content?: ContentItem[]
  name?: string
  arguments?: string
  output?: string
  error?: { message: string }
  sequence_number?: number
}

// UI display model
export interface DisplayBlock {
  id: string
  kind: 'text' | 'tool_call' | 'tool_output' | 'reasoning'
  text?: string
  toolType?: string
  toolName?: string
  toolArgs?: string
  toolOutput?: string
  expanded?: boolean
  loading?: boolean
}

export interface DisplayMessage {
  id: string
  role: 'user' | 'assistant'
  blocks: DisplayBlock[]
  streaming?: boolean
}
