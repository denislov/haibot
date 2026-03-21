// ── Workspace / Files ────────────────────────────────────────────────────────

export interface MdFileInfo {
  filename: string
  path: string
  size: number
  created_time: string
  modified_time: string
}

export interface MdFileContent {
  content: string
}

export interface WorkspaceStatus {
  total_files: number
  total_size: number
  last_updated?: string
}
