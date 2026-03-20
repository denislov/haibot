import api from './index'
import type { AnyChannelConfig, ChannelType } from '@/types'

export const listChannels = () =>
  api.get<Record<string, AnyChannelConfig>>('/config/channels').then((r) => r.data)

export const listChannelTypes = () =>
  api.get<ChannelType[]>('/config/channels/types').then((r) => r.data)

export const getChannel = (name: string) =>
  api.get<AnyChannelConfig>(`/config/channels/${name}`).then((r) => r.data)

export const updateChannel = (name: string, data: AnyChannelConfig) =>
  api.put<AnyChannelConfig>(`/config/channels/${name}`, data).then((r) => r.data)
