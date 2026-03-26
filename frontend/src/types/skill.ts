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
  bundle_url: string
  version?: string
  enable?: boolean
  overwrite?: boolean
}

export interface UploadSkillResult {
  imported: string[]
  count: number
  enabled: boolean
}

export interface HubInstallResult {
  installed: boolean
  name: string
  enabled: boolean
  source_url: string
}

export interface HubInstallTask {
  task_id: string
  bundle_url: string
  version?: string
  enable: boolean
  overwrite: boolean
  status: 'pending' | 'importing' | 'completed' | 'failed' | 'cancelled'
  error?: string | null
  result?: HubInstallResult | null
  created_at: number
  updated_at: number
}

export interface AIOptimizeSkillRequest {
  content: string
  language?: string
}
