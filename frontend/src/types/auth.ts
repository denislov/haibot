export interface AuthStatusResponse {
  enabled: boolean
  has_users: boolean
}

export interface AuthLoginRequest {
  username: string
  password: string
}

export interface AuthRegisterRequest {
  username: string
  password: string
}

export interface AuthLoginResponse {
  token: string
  username: string
}

export interface AuthVerifyResponse {
  valid: boolean
  username: string
}

export interface AuthUpdateProfileRequest {
  current_password: string
  new_username?: string
  new_password?: string
}
