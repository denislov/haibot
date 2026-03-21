// ── Channels ─────────────────────────────────────────────────────────────────
export interface BaseChannelConfig {
  enabled: boolean
  bot_prefix: string
  filter_tool_messages?: boolean
  filter_thinking?: boolean
  dm_policy?: 'open' | 'allowlist'
  group_policy?: 'open' | 'allowlist'
  allow_from?: string[]
  deny_message?: string
  require_mention?: boolean
}

export interface ConsoleConfig extends BaseChannelConfig {}
export interface DingTalkConfig extends BaseChannelConfig {
  client_id: string
  client_secret: string
}
export interface FeishuConfig extends BaseChannelConfig {
  app_id: string
  app_secret: string
  encrypt_key: string
  verification_token: string
  media_dir: string
}
export interface QQConfig extends BaseChannelConfig {
  app_id: string
  client_secret: string
}
export interface DiscordConfig extends BaseChannelConfig {
  bot_token: string
  http_proxy: string
  http_proxy_auth: string
}
export interface IMessageConfig extends BaseChannelConfig {
  db_path: string
  poll_sec: number
}
export interface TelegramConfig extends BaseChannelConfig {
  bot_token: string
  http_proxy: string
  http_proxy_auth: string
  show_typing?: boolean
}
export interface MattermostConfig extends BaseChannelConfig {
  url: string
  token: string
}
export interface MQTTConfig extends BaseChannelConfig {
  broker_url: string
  topic_subscribe: string
  topic_publish: string
  username: string
  password: string
}
export interface MatrixConfig extends BaseChannelConfig {
  homeserver_url: string
  user_id: string
  access_token: string
}
export interface VoiceChannelConfig extends BaseChannelConfig {
  port: number
}
export interface WecomConfig extends BaseChannelConfig {
  corp_id: string
  agent_id: string
  secret: string
  token: string
  encoding_aes_key: string
}
export interface XiaoYiConfig extends BaseChannelConfig {
  api_key: string
}

export type ChannelType =
  | 'console' | 'dingtalk' | 'feishu' | 'qq' | 'discord' | 'imessage'
  | 'telegram' | 'mattermost' | 'mqtt' | 'matrix' | 'voice' | 'wecom' | 'xiaoyi'

export type AnyChannelConfig =
  | ConsoleConfig
  | DingTalkConfig
  | FeishuConfig
  | QQConfig
  | DiscordConfig
  | IMessageConfig
  | TelegramConfig
  | MattermostConfig
  | MQTTConfig
  | MatrixConfig
  | VoiceChannelConfig
  | WecomConfig
  | XiaoYiConfig
