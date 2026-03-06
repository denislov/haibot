// ── Agents ────────────────────────────────────────────────────────────────────
export interface AgentInfo {
  id: string
  name: string
  description: string
  is_main: boolean
  files: string[]
  created_at: string
}
