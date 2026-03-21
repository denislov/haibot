import api from './index'

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authStatus = () =>
  api.get<{ auth_enabled: boolean; user_exists: boolean }>('/auth/status').then((r) => r.data)

export const login = (data: { username: string; password: string }) =>
  api.post<{ token: string }>('/auth/login', data).then((r) => r.data)

export const register = (data: { username: string; password: string }) =>
  api.post('/auth/register', data).then((r) => r.data)

export const verifyToken = () =>
  api.get('/auth/verify').then((r) => r.data)
