export interface ToolGuardRuleConfig {
  id: string
  tools: string[]
  params: string[]
  category: string
  severity: string
  patterns: string[]
  exclude_patterns: string[]
  description: string
  remediation: string
}

export interface ToolGuardConfig {
  enabled: boolean
  protected_tools: string[]
  banned_tools: string[]
  rules: Record<string, boolean>
}

export interface SkillScannerWhitelistEntry {
  skill_name: string
  content_hash: string
  added_at: string
}

export interface SkillScannerConfig {
  enabled: boolean
  mode: string // 'remind' | 'block' | 'auto_whitelist'
  scan_timeout: number
  whitelist: SkillScannerWhitelistEntry[]
}

export interface SkillScannerBlockedHistoryEntry {
  id: string
  skill: string
  reason: string
  timestamp: string
}
