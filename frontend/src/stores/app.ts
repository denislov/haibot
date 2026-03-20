import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/index'

export const useAppStore = defineStore('app', () => {
  const version = ref('0.0.2')

  async function fetchVersion() {
    try {
      const res = await api.get<{ version: string }>('/version')
      version.value = res.data.version
    } catch {
      // keep default
    }
  }

  return { version, fetchVersion }
})
