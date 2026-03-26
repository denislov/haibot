import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import api from '@/api/index'
import {
  authStatus,
  login as loginApi,
  register as registerApi,
  updateProfile as updateProfileApi,
  verifyToken,
} from '@/api/auth'
import {
  clearAuthSession,
  getAuthToken,
  getStoredUsername,
  setAuthSession,
  setUnauthorizedHandler,
} from '@/utils/authSession'

type AuthMode =
  | 'disabled'
  | 'register_required'
  | 'login_required'
  | 'bypass'
  | 'authenticated'

export const useAuthStore = defineStore('auth', () => {
  const initialized = ref(false)
  const initializing = ref(false)
  const mode = ref<AuthMode>('disabled')
  const enabled = ref(false)
  const hasUsers = ref(false)
  const token = ref(getAuthToken())
  const username = ref(getStoredUsername())

  let initPromise: Promise<void> | null = null

  setUnauthorizedHandler(() => {
    if (!enabled.value || !hasUsers.value) return
    clearAuthSession()
    token.value = ''
    username.value = ''
    mode.value = 'login_required'
    initialized.value = true
  })

  const isAuthenticated = computed(
    () => mode.value === 'authenticated' && !!token.value,
  )
  const isBypassSession = computed(() => mode.value === 'bypass')
  const requiresAuthScreen = computed(
    () =>
      mode.value === 'login_required' ||
      mode.value === 'register_required',
  )
  const canAccessApp = computed(
    () =>
      mode.value === 'disabled' ||
      mode.value === 'bypass' ||
      mode.value === 'authenticated',
  )

  async function probeProtectedAccess() {
    const response = await api.get('/agents', {
      validateStatus: () => true,
      skipAuthHandling: true,
    } as any)
    return response.status < 400
  }

  function applySession(newToken: string, newUsername: string) {
    setAuthSession(newToken, newUsername)
    token.value = newToken
    username.value = newUsername
    mode.value = 'authenticated'
    hasUsers.value = true
  }

  async function initialize() {
    if (initialized.value) return
    if (initPromise) return initPromise

    initPromise = (async () => {
      initializing.value = true
      try {
        const status = await authStatus()
        enabled.value = status.enabled
        hasUsers.value = status.has_users
        token.value = getAuthToken()
        username.value = getStoredUsername()

        if (!enabled.value) {
          mode.value = 'disabled'
          return
        }

        if (!hasUsers.value) {
          clearAuthSession()
          token.value = ''
          username.value = ''
          mode.value = 'register_required'
          return
        }

        if (token.value) {
          try {
            const verify = await verifyToken()
            username.value = verify.username || username.value
            setAuthSession(token.value, username.value)
            mode.value = 'authenticated'
            return
          } catch {
            clearAuthSession()
            token.value = ''
            username.value = ''
          }
        }

        mode.value = (await probeProtectedAccess())
          ? 'bypass'
          : 'login_required'
      } finally {
        initialized.value = true
        initializing.value = false
        initPromise = null
      }
    })()

    return initPromise
  }

  async function login(usernameValue: string, password: string) {
    const result = await loginApi({
      username: usernameValue.trim(),
      password,
    })
    applySession(result.token, result.username)
    return result
  }

  async function register(usernameValue: string, password: string) {
    const result = await registerApi({
      username: usernameValue.trim(),
      password,
    })
    applySession(result.token, result.username)
    return result
  }

  async function updateProfile(input: {
    currentPassword: string
    newUsername?: string
    newPassword?: string
  }) {
    const result = await updateProfileApi({
      current_password: input.currentPassword,
      new_username: input.newUsername?.trim() || undefined,
      new_password: input.newPassword || undefined,
    })
    applySession(result.token, result.username || username.value)
    return result
  }

  async function logout() {
    clearAuthSession()
    token.value = ''
    username.value = ''

    if (!enabled.value) {
      mode.value = 'disabled'
      return
    }

    if (!hasUsers.value) {
      mode.value = 'register_required'
      return
    }

    mode.value = (await probeProtectedAccess())
      ? 'bypass'
      : 'login_required'
  }

  return {
    initialized,
    initializing,
    enabled,
    hasUsers,
    mode,
    token,
    username,
    isAuthenticated,
    isBypassSession,
    requiresAuthScreen,
    canAccessApp,
    initialize,
    login,
    register,
    updateProfile,
    logout,
  }
})
