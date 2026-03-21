<template>
  <div class="settings-page">
    <div class="page-header">
      <div>
        <h2>{{ $t('settings.tools.title') }}</h2>
        <p class="desc">{{ $t('settings.tools.desc') }}</p>
      </div>
      <div class="agent-selector-wrapper">
        <span class="selector-label">{{ $t('settings.agents.title') }}</span>
        <el-select v-model="selectedAgentId" :placeholder="$t('settings.agents.displayNamePlaceholder') || 'Select Agent'" @change="onAgentChange" style="width: 200px" size="small">
          <el-option v-for="agent in agents" :key="agent.id" :label="agent.name" :value="agent.id" />
        </el-select>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="4" animated />
    </div>

    <div v-else-if="tools.length === 0" class="empty-state">
      <p>{{ $t('settings.tools.noTools') }}</p>
    </div>

    <div v-else class="tools-grid">
      <div v-for="tool in tools" :key="tool.name" class="tool-card">
        <div class="tool-info">
          <div class="tool-name">{{ tool.name }}</div>
          <div v-if="tool.description" class="tool-desc">{{ tool.description }}</div>
        </div>
        <el-switch
          :model-value="tool.enabled"
          :loading="togglingSet.has(tool.name)"
          @change="handleToggle(tool)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { listTools, toggleTool } from '@/api/tools'
import { listAgents } from '@/api/agents'
import { setAgentHeader } from '@/api/index'
import type { ToolInfo, AgentSummary } from '@/types'

const { t } = useI18n()
const agents = ref<AgentSummary[]>([])
const selectedAgentId = ref<string>('')
const tools = ref<ToolInfo[]>([])
const loading = ref(true)
const togglingSet = ref<Set<string>>(new Set())

async function loadAgents() {
  try {
    agents.value = await listAgents()
    if (agents.value.length > 0) {
      selectedAgentId.value = agents.value[0].id
      onAgentChange()
    }
  } catch (e: unknown) {
    ElMessage.error(String(e))
  }
}

function onAgentChange() {
  if (!selectedAgentId.value) return
  setAgentHeader(selectedAgentId.value)
  fetchTools()
}

async function fetchTools() {
  if (!selectedAgentId.value) return
  loading.value = true
  try {
    tools.value = await listTools()
  } catch {
    ElMessage.error(t('common.loadFailed'))
  } finally {
    loading.value = false
  }
}

async function handleToggle(tool: ToolInfo) {
  togglingSet.value.add(tool.name)
  try {
    const updated = await toggleTool(tool.name)
    const idx = tools.value.findIndex((t) => t.name === tool.name)
    if (idx !== -1) tools.value[idx] = updated
  } catch {
    ElMessage.error(t('common.saveFailed'))
  } finally {
    togglingSet.value.delete(tool.name)
  }
}

onMounted(loadAgents)
</script>

<style scoped>
.settings-page h2 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-1);
  margin-bottom: 4px;
}
.desc {
  color: var(--text-3);
  font-size: 13px;
  margin-bottom: 0px;
}
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; }
.agent-selector-wrapper { display: flex; align-items: center; gap: 8px; }
.selector-label { font-size: 12px; font-weight: 500; color: var(--text-3); white-space: nowrap; }

.loading-state { max-width: 600px; }
.empty-state { color: var(--text-4); font-size: 14px; }

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.tool-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--bg-card);
  transition: box-shadow var(--transition-fast);
}
.tool-card:hover { box-shadow: var(--shadow-sm); }

.tool-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-1);
  font-family: 'SF Mono', 'Fira Code', monospace;
}
.tool-desc {
  font-size: 12px;
  color: var(--text-3);
  margin-top: 2px;
}
</style>
