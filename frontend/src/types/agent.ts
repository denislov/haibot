// ── Agents ────────────────────────────────────────────────────────────────────

/**
 * Agent summary for lists
 */
export interface AgentSummary {
  id: string
  name: string
  description: string
  workspace_dir: string
}

/**
 * Response for listing agents
 */
export interface AgentListResponse {
  agents: AgentSummary[]
}

/**
 * Full agent configuration
 */
export interface AgentProfileConfig {
  id: string
  name: string
  description?: string
  workspace_dir?: string
  language?: string
  system_prompt_files?: string[]
  active_model?: {
    provider_id: string
    model: string
  }
  // Simplified for now, can be expanded as needed
  channels?: Record<string, any>
  tools?: {
    builtin_tools: Record<string, any>
  }
  running?: Record<string, any>
  security?: Record<string, any>
}

/**
 * Request for creating an agent
 */
export interface CreateAgentRequest {
  name: string
  description?: string
  workspace_dir?: string
  language?: string
}

/**
 * Legacy/Compatibility type - will be phased out in components
 */
export type AgentInfo = AgentSummary & {
  is_main?: boolean
  created_at?: string
}
