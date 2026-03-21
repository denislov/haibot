import api from './index'

// ── Console ───────────────────────────────────────────────────────────────────

/** Upload a file for use in chat. */
export const uploadFile = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<{ url: string }>('/console/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)
}

/** Get SSE push messages stream URL. */
export const getPushMessagesUrl = () => '/api/console/push-messages'
