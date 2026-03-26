import axios from 'axios'
import { getAuthToken, notifyUnauthorized } from '@/utils/authSession'


declare const BASE_URL: string;

const api = axios.create({
  baseURL: '/',
  timeout: 30000,
  headers: { 
    'Content-Type': 'application/json',
  },
})

export function getApiBaseUrl() {
  return typeof BASE_URL !== 'undefined' ? BASE_URL : ''
}

export function buildApiUrl(path: string) {
  const base = getApiBaseUrl()
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${base}/api${normalizedPath}`
}

export function createAuthHeaders(
  init: Record<string, string> = {},
): Record<string, string> {
  const headers = { ...init }
  const token = getAuthToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  return headers
}

api.interceptors.request.use(
  config => {
    const token = getAuthToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    } else if (config.headers?.Authorization) {
      delete config.headers.Authorization
    }
    const normalizedPath = config.url?.startsWith('/') ? config.url : `/${config.url}`
    config.url = buildApiUrl(normalizedPath)
    return config
  }
)

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status
    const skipAuthHandling = Boolean(err.config?.skipAuthHandling)
    const msg = err.response?.data?.detail || err.message || '请求失败'
    if (status === 401 && !skipAuthHandling) {
      notifyUnauthorized(String(msg))
    }
    return Promise.reject(new Error(String(msg)))
  },
)

export const setAgentHeader = (agentId: string) => {
  if (agentId) {
    api.defaults.headers.common['X-Agent-Id'] = agentId
  } else {
    delete api.defaults.headers.common['X-Agent-Id']
  }
}

export default api
