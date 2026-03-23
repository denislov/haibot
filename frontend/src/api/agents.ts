import api from './index'
import type { 
  AgentListResponse, 
  AgentProfileConfig, 
  CreateAgentRequest,
  MdFileInfo,
  MdFileContent
} from '@/types'

/**
 * List all available agents
 */
export const listAgents = () =>
  api.get<AgentListResponse>('/agents').then((r) => r.data.agents)

/**
 * Create a new agent
 */
export const createAgent = (data: CreateAgentRequest) =>
  api.post<{ id: string; workspace_dir: string }>('/agents', data).then((r) => r.data)

/**
 * Get detailed agent configuration
 */
export const getAgent = (id: string) =>
  api.get<AgentProfileConfig>(`/agents/${id}`).then((r) => r.data)

/**
 * Update agent configuration
 */
export const updateAgent = (id: string, data: Partial<AgentProfileConfig>) =>
  api.put<AgentProfileConfig>(`/agents/${id}`, { ...data, id }).then((r) => r.data)

/**
 * Delete an agent
 */
export const deleteAgent = (id: string) =>
  api.delete<{ message: string }>(`/agents/${id}`).then((r) => r.data)

/**
 * List files in an agent's workspace
 */
export const listAgentFiles = (agentId: string) =>
  api.get<MdFileInfo[]>(`/agents/${agentId}/files`).then((r) => r.data)

/**
 * Read a file from an agent's workspace
 */
export const readAgentFile = (agentId: string, filename: string) =>
  api.get<MdFileContent>(`/agents/${agentId}/files/${filename}`).then((r) => r.data)

/**
 * Write a file to an agent's workspace
 */
export const writeAgentFile = (agentId: string, filename: string, content: string) =>
  api.put<MdFileInfo>(`/agents/${agentId}/files/${filename}`, { content }).then((r) => r.data)

/**
 * Get agent's skill configuration
 */
export const getAgentSkills = (agentId: string) =>
  api.get<{ skills_config: Record<string, boolean> }>(`/agents/${agentId}/skills`)
    .then(r => r.data)

/**
 * Update agent's skill configuration
 */
export const updateAgentSkills = (agentId: string, skillsConfig: Record<string, boolean>) =>
  api.put<{ skills_config: Record<string, boolean> }>(`/agents/${agentId}/skills`, {
    skills_config: skillsConfig,
  }).then(r => r.data)

/**
 * Get agent's system prompt files (enabled MD files order)
 */
export const getSystemPromptFiles = () =>
  api.get<string[]>('/agent/system-prompt-files').then(r => r.data)

/**
 * Update agent's system prompt files
 */
export const updateSystemPromptFiles = (files: string[]) =>
  api.put<string[]>('/agent/system-prompt-files', files).then(r => r.data)
