import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { setAgentHeader } from '@/api/index'
import { listAgents } from '@/api/agents'
import type { AgentInfo } from '@/types'

/**
 * Shared store for settings pages — holds the selected agent and
 * sets the X-Agent-Id header on every API request automatically.
 */
export const useSettingsStore = defineStore('settings', () => {
  const agents = ref<AgentInfo[]>([])
  const selectedAgentId = ref<string>('')
  const loaded = ref(false)

  // Keep X-Agent-Id header in sync
  watch(selectedAgentId, (id) => {
    setAgentHeader(id)
  })

  async function loadAgents() {
    try {
      agents.value = await listAgents()
      if (agents.value.length > 0 && !selectedAgentId.value) {
        selectedAgentId.value = agents.value[0].id
      }
      loaded.value = true
    } catch {
      agents.value = [{ id: 'main', name: 'Main', description: '', is_main: true, files: [], created_at: '' }]
      if (!selectedAgentId.value) selectedAgentId.value = 'main'
      loaded.value = true
    }
  }

  return { agents, selectedAgentId, loaded, loadAgents }
})
