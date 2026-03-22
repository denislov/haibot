import api from './index'
import type { 
  AgentsRunningConfig, 
  ToolGuardConfig, 
  ToolGuardRuleConfig,
  SkillScannerConfig,
  SkillScannerBlockedHistoryEntry
} from '@/types'

// --- Running Config ---
export const getRunningConfig = () =>
  api.get<AgentsRunningConfig>('/agent/running-config').then((r) => r.data)

export const updateRunningConfig = (data: AgentsRunningConfig) =>
  api.put<AgentsRunningConfig>('/agent/running-config', data).then((r) => r.data)

export const getAgentLanguage = () =>
  api.get<{ language: string, agent_id: string }>('/agent/language').then((r) => r.data)

export const updateAgentLanguage = (language: string) =>
  api.put<{ language: string, copied_files: string[], agent_id: string }>('/agent/language', { language }).then((r) => r.data)

export const getUserTimezone = () =>
  api.get<{ timezone: string }>('/config/user-timezone').then((r) => r.data)

export const updateUserTimezone = (timezone: string) =>
  api.put<{ timezone: string }>('/config/user-timezone', { timezone }).then((r) => r.data)

// --- Security: Tool Guard ---
export const getToolGuardConfig = () =>
  api.get<ToolGuardConfig>('/config/security/tool-guard').then((r) => r.data)

export const updateToolGuardConfig = (data: ToolGuardConfig) =>
  api.put<ToolGuardConfig>('/config/security/tool-guard', data).then((r) => r.data)

export const getToolGuardBuiltinRules = () =>
  api.get<ToolGuardRuleConfig[]>('/config/security/tool-guard/builtin-rules').then((r) => r.data)

// --- Security: Skill Scanner ---
export const getSkillScannerConfig = () =>
  api.get<SkillScannerConfig>('/config/security/skill-scanner').then((r) => r.data)

export const updateSkillScannerConfig = (data: SkillScannerConfig) =>
  api.put<SkillScannerConfig>('/config/security/skill-scanner', data).then((r) => r.data)

export const getSkillScannerBlockedHistory = () =>
  api.get<SkillScannerBlockedHistoryEntry[]>('/config/security/skill-scanner/blocked-history').then((r) => r.data)

export const clearSkillScannerBlockedHistory = () =>
  api.delete<{ cleared: boolean }>('/config/security/skill-scanner/blocked-history').then((r) => r.data)

export const deleteSkillScannerBlockedHistoryEntry = (index: number) =>
  api.delete<{ removed: boolean }>(`/config/security/skill-scanner/blocked-history/${index}`).then((r) => r.data)

export const addSkillScannerWhitelist = (skill_name: string, content_hash: string = '') =>
  api.post<{ whitelisted: boolean, skill_name: string }>('/config/security/skill-scanner/whitelist', { skill_name, content_hash }).then((r) => r.data)

export const removeSkillScannerWhitelist = (skill_name: string) =>
  api.delete<{ removed: boolean, skill_name: string }>(`/config/security/skill-scanner/whitelist/${skill_name}`).then((r) => r.data)
