// ── Skills ────────────────────────────────────────────────────────────────────
export interface SkillSpec {
  name: string
  description?: string
  content: string
  source: string
  path: string
  references?: Record<string, unknown>
  scripts?: Record<string, unknown>
  enabled: boolean
}

// ── Skills Hub ────────────────────────────────────────────────────────────────
export interface HubSkillSpec {
  slug: string
  name: string
  description?: string
  version?: string
  source_url?: string
}

export interface HubInstallRequest {
  slug: string
  enable?: boolean
}

export interface HubInstallTask {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  message?: string
}

export interface AIOptimizeSkillRequest {
  content: string
  language?: string
}
