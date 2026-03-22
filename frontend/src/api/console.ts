import api from './index'

// ── Console ───────────────────────────────────────────────────────────────────

/** Upload a file for use in chat. */
export const uploadFile = (file: File, agentId?: string) => {
  const form = new FormData()
  form.append('file', file)
  const url = agentId ? `/agents/${agentId}/console/upload` : '/console/upload'
  return api.post<{ url: string; file_name: string; size: number }>(url, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)
}

/** Get SSE push messages stream URL. */
export const getPushMessagesUrl = () => '/api/console/push-messages'
