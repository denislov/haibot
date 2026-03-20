<template>
  <div class="page">
    <section class="section">
      <div class="section-header-row">
        <div>
          <h2 class="section-title">{{ $t('settings.agents.title') }}</h2>
          <p class="section-desc">{{ $t('settings.agents.desc') }}</p>
        </div>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          {{ $t('settings.agents.createAgent') }}
        </el-button>
      </div>

      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
      </div>

      <div v-else class="agents-grid">
        <div
          v-for="agent in agents"
          :key="agent.id"
          class="agent-card"
          :class="{ main: agent.is_main }"
        >
          <div class="agent-header">
            <div class="agent-name-line">
              <el-icon class="agent-icon"><Avatar /></el-icon>
              <span class="agent-name">{{ agent.name }}</span>
              <span v-if="agent.is_main" class="agent-badge badge-main">Main</span>
            </div>
          </div>

          <div v-if="agent.description" class="agent-desc">{{ agent.description }}</div>

          <div class="agent-files">
            <span v-for="f in agent.files" :key="f" class="file-tag">{{ f }}</span>
          </div>

          <div class="agent-actions">
            <el-button size="small" text type="primary" @click="openWorkspace(agent)">
              <el-icon><EditPen /></el-icon>
              {{ $t('settings.agents.workspace') }}
            </el-button>
            <el-button v-if="!agent.is_main" size="small" text type="danger" @click="confirmDelete(agent)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════ Create Agent Dialog ═══════════════ -->
    <el-dialog v-model="createDialogVisible" :title="$t('settings.agents.createAgent')" width="440px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item :label="$t('settings.agents.agentId')" required>
          <el-input v-model="createForm.id" :placeholder="$t('settings.agents.agentIdPlaceholder')" />
          <div class="form-hint">{{ $t('settings.agents.agentIdHint') }}</div>
        </el-form-item>
        <el-form-item :label="$t('settings.agents.displayName')" required>
          <el-input v-model="createForm.name" :placeholder="$t('settings.agents.displayNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('settings.agents.description')">
          <el-input v-model="createForm.description" type="textarea" :rows="3" :placeholder="$t('settings.agents.descriptionPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="creating" :disabled="!createForm.id || !createForm.name" @click="handleCreate">
          {{ $t('common.create') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- ═══════════════ Workspace Editor Dialog ═══════════════ -->
    <el-dialog
      v-model="workspaceDialogVisible"
      :title="`${workspaceAgent?.name} — ${$t('settings.agents.workspace')}`"
      width="720px"
      destroy-on-close
      top="5vh"
    >
      <div class="workspace-editor">
        <div class="workspace-tabs">
          <button
            v-for="f in workspaceFiles"
            :key="f.name"
            class="ws-tab"
            :class="{ active: activeFile === f.name }"
            @click="selectFile(f.name)"
          >
            {{ f.name }}
          </button>
        </div>
        <div v-if="loadingFile" class="ws-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
        </div>
        <el-input
          v-else
          v-model="fileContent"
          type="textarea"
          :rows="20"
          class="ws-textarea"
        />
        <!-- Skills config section -->
        <div v-if="workspaceAgent" class="agent-skills-section">
          <div class="section-title">{{ $t('settings.agents.skills') }}</div>
          <div v-if="agentSkills" class="skills-list">
            <div
              v-for="(enabled, skillName) in agentSkills"
              :key="skillName"
              class="skill-row"
            >
              <span class="skill-name">{{ skillName }}</span>
              <el-switch
                :model-value="enabled"
                @change="(val: boolean) => toggleSkill(skillName, val)"
              />
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="workspaceDialogVisible = false">{{ $t('common.close') }}</el-button>
        <el-button type="primary" :loading="savingFile" @click="saveFile">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Avatar, Delete, EditPen, Loading, Plus } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import {
  listAgents,
  createAgent as apiCreate,
  deleteAgent as apiDelete,
  listAgentFiles,
  readAgentFile,
  writeAgentFile,
  getAgentSkills,
  updateAgentSkills,
} from '@/api/agents'
import type { AgentInfo } from '@/types'

const { t } = useI18n()

const agents = ref<AgentInfo[]>([])
const loading = ref(false)

// ── Create ──
const createDialogVisible = ref(false)
const createForm = reactive({ id: '', name: '', description: '' })
const creating = ref(false)

// ── Workspace Editor ──
const workspaceDialogVisible = ref(false)
const workspaceAgent = ref<AgentInfo | null>(null)
const agentSkills = ref<Record<string, boolean> | null>(null)
const workspaceFiles = ref<Array<{ name: string; size: number }>>([])
const activeFile = ref('')
const fileContent = ref('')
const loadingFile = ref(false)
const savingFile = ref(false)

async function loadData() {
  loading.value = true
  try {
    agents.value = await listAgents()
  } catch (e: unknown) {
    ElMessage.error('Load failed: ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    loading.value = false
  }
}

// ── Create ──
function openCreateDialog() {
  createForm.id = ''
  createForm.name = ''
  createForm.description = ''
  createDialogVisible.value = true
}

async function handleCreate() {
  creating.value = true
  try {
    await apiCreate({
      id: createForm.id,
      name: createForm.name,
      description: createForm.description || undefined,
    })
    createDialogVisible.value = false
    ElMessage.success(t('common.createSuccess'))
    await loadData()
  } catch (e: unknown) {
    ElMessage.error(t('common.createFailed') + ': ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    creating.value = false
  }
}

// ── Delete ──
async function confirmDelete(agent: AgentInfo) {
  try {
    await ElMessageBox.confirm(
      t('settings.agents.deleteConfirm', { name: agent.name }),
      t('common.deleteConfirm'),
      { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' },
    )
    await apiDelete(agent.id)
    ElMessage.success(t('common.deleteSuccess'))
    await loadData()
  } catch (e: unknown) {
    if (e !== 'cancel' && (e as any) !== 'cancel') {
      ElMessage.error(t('common.deleteFailed') + ': ' + (e instanceof Error ? e.message : String(e)))
    }
  }
}

// ── Workspace Editor ──
async function openWorkspace(agent: AgentInfo) {
  workspaceAgent.value = agent
  workspaceDialogVisible.value = true
  loadingFile.value = true
  try {
    workspaceFiles.value = await listAgentFiles(agent.id)
    if (workspaceFiles.value.length > 0) {
      await selectFile(workspaceFiles.value[0].name)
    }
  } catch (e: unknown) {
    ElMessage.error('Load files failed: ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    loadingFile.value = false
  }
}

async function selectFile(filename: string) {
  if (!workspaceAgent.value) return
  activeFile.value = filename
  loadingFile.value = true
  try {
    const data = await readAgentFile(workspaceAgent.value.id, filename)
    fileContent.value = data.content
  } catch (e: unknown) {
    ElMessage.error('Read failed: ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    loadingFile.value = false
  }
}

async function saveFile() {
  if (!workspaceAgent.value || !activeFile.value) return
  savingFile.value = true
  try {
    await writeAgentFile(workspaceAgent.value.id, activeFile.value, fileContent.value)
    ElMessage.success(t('common.saveSuccess'))
  } catch (e: unknown) {
    ElMessage.error(t('common.saveFailed') + ': ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    savingFile.value = false
  }
}

async function loadAgentSkills(agentId: string) {
  try {
    const data = await getAgentSkills(agentId)
    agentSkills.value = data.skills_config
  } catch (e: unknown) {
    ElMessage.error('Failed to load agent skills: ' + (e instanceof Error ? e.message : String(e)))
  }
}

async function toggleSkill(skillName: string, enabled: boolean) {
  if (!workspaceAgent.value || !agentSkills.value) return
  const prev = agentSkills.value[skillName]
  agentSkills.value[skillName] = enabled
  try {
    await updateAgentSkills(workspaceAgent.value.id, agentSkills.value)
  } catch (e: unknown) {
    agentSkills.value[skillName] = prev
    ElMessage.error('Failed to update skill: ' + (e instanceof Error ? e.message : String(e)))
  }
}

watch(workspaceAgent, (agent) => {
  if (agent) loadAgentSkills(agent.id)
  else agentSkills.value = null
})

onMounted(loadData)
</script>

<style scoped>
.page { max-width: 960px; }
.section { margin-bottom: 36px; }
.section-title { font-size: 18px; font-weight: 700; color: var(--text-1); margin-bottom: 4px; }
.section-desc { font-size: 13px; color: var(--text-3); margin-bottom: 0; }
.section-header-row { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }

.loading-state { display: flex; justify-content: center; padding: 40px 0; color: var(--text-4); font-size: 24px; }

/* ── Agent Cards ── */
.agents-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.agent-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 18px;
  transition: box-shadow var(--transition-fast), border-color var(--transition-fast);
}
.agent-card:hover { box-shadow: var(--shadow-md); }
.agent-card.main { border-color: var(--primary); }

.agent-header { margin-bottom: 8px; }
.agent-name-line { display: flex; align-items: center; gap: 8px; }
.agent-icon { font-size: 20px; color: var(--primary); }
.agent-name { font-size: 15px; font-weight: 600; color: var(--text-1); }
.agent-badge {
  font-size: 11px; font-weight: 500;
  padding: 1px 8px; border-radius: var(--radius-sm);
  border: 1px solid;
}
.badge-main { color: #7c3aed; border-color: #ddd6fe; background: #f5f3ff; }

.agent-desc { font-size: 12px; color: var(--text-3); margin-bottom: 8px; }

.agent-files { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
.file-tag {
  font-size: 11px; color: var(--text-3);
  background: var(--bg); padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-family: Consolas, monospace;
}

.agent-actions {
  margin-top: 8px; border-top: 1px solid var(--border);
  padding-top: 10px; display: flex; gap: 4px; justify-content: flex-end;
}

/* ── Create dialog ── */
.form-hint { font-size: 12px; color: var(--text-4); margin-top: 4px; }

/* ── Workspace Editor ── */
.workspace-editor { display: flex; flex-direction: column; gap: 12px; }
.workspace-tabs { display: flex; gap: 4px; flex-wrap: wrap; }
.ws-tab {
  padding: 6px 14px; border: 1px solid var(--border);
  border-radius: var(--radius-sm); background: var(--bg);
  font-size: 12px; color: var(--text-2); cursor: pointer;
  font-family: Consolas, monospace;
  transition: all var(--transition-fast);
}
.ws-tab:hover { border-color: var(--primary); color: var(--primary); }
.ws-tab.active { background: var(--primary); color: white; border-color: var(--primary); }

.ws-loading { display: flex; justify-content: center; padding: 40px; color: var(--text-4); }

.ws-textarea :deep(.el-textarea__inner) {
  font-family: 'Fira Code', 'Cascadia Code', Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
  background: var(--bg);
  border-radius: var(--radius);
}

/* ── Skills section ── */
.agent-skills-section {
  margin-top: 16px;
}

.skills-list {
  margin-top: 8px;
}

.skill-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
}

.skill-name {
  font-size: 13px;
  color: var(--el-text-color-regular);
}

/* ── Dark mode ── */
[data-theme="dark"] .badge-main { color: #a78bfa; border-color: rgba(124,58,237,.3); background: rgba(124,58,237,.1); }
</style>
