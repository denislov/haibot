// ── Skills ────────────────────────────────────────────────────────────────────
export interface SkillSpec {
  name: string
  content: string
  source: string
  path: string
  references?: Record<string, unknown>
  scripts?: Record<string, unknown>
  enabled: boolean
}
