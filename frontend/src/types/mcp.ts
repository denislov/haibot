// ── MCP (Model Context Protocol) ──────────────────────────────────────────────
export interface MCPClientInfo {
  key: string
  name: string
  description: string
  enabled: boolean
  transport: 'stdio' | 'streamable_http' | 'sse'
  url: string
  headers: Record<string, string>
  command: string
  args: string[]
  env: Record<string, string>
  cwd: string
}
