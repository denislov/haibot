const AUTH_TOKEN_KEY = 'haibot-auth-token'
const AUTH_USERNAME_KEY = 'haibot-auth-username'

let unauthorizedHandler: ((message?: string) => void) | null = null

function getStorage() {
  if (typeof window === 'undefined') return null
  return window.localStorage
}

export function getAuthToken(): string {
  return getStorage()?.getItem(AUTH_TOKEN_KEY) || ''
}

export function getStoredUsername(): string {
  return getStorage()?.getItem(AUTH_USERNAME_KEY) || ''
}

export function setAuthSession(token: string, username: string) {
  const storage = getStorage()
  if (!storage) return
  storage.setItem(AUTH_TOKEN_KEY, token)
  storage.setItem(AUTH_USERNAME_KEY, username)
}

export function clearAuthSession() {
  const storage = getStorage()
  if (!storage) return
  storage.removeItem(AUTH_TOKEN_KEY)
  storage.removeItem(AUTH_USERNAME_KEY)
}

export function setUnauthorizedHandler(
  handler: ((message?: string) => void) | null,
) {
  unauthorizedHandler = handler
}

export function notifyUnauthorized(message?: string) {
  unauthorizedHandler?.(message)
}
