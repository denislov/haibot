import api from './index'
import type {
  AuthLoginRequest,
  AuthLoginResponse,
  AuthStatusResponse,
  AuthUpdateProfileRequest,
  AuthVerifyResponse,
} from '@/types'

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authStatus = () =>
  api.get<AuthStatusResponse>('/auth/status', { skipAuthHandling: true } as any).then((r) => r.data)

export const login = (data: AuthLoginRequest) =>
  api.post<AuthLoginResponse>('/auth/login', data, { skipAuthHandling: true } as any).then((r) => r.data)

export const register = (data: AuthLoginRequest) =>
  api.post<AuthLoginResponse>('/auth/register', data, { skipAuthHandling: true } as any).then((r) => r.data)

export const verifyToken = () =>
  api.get<AuthVerifyResponse>('/auth/verify', { skipAuthHandling: true } as any).then((r) => r.data)

export const updateProfile = (data: AuthUpdateProfileRequest) =>
  api.post<AuthLoginResponse>('/auth/update-profile', data).then((r) => r.data)
