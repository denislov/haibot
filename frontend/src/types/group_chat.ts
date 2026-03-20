export interface GroupChatConfig {
  id: string
  name: string
  host_agent_id: string
  participant_agent_ids: string[]
  max_rounds: number
  created_at: string
}
