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

      <div v-else class="agents-table-container">
        <el-table :data="agents" style="width: 100%">
          <el-table-column :label="$t('settings.agents.displayName')" min-width="200">
            <template #default="{ row }">
              <div class="agent-name-cell">
                <el-icon class="agent-icon"><Avatar /></el-icon>
                <span class="agent-name">{{ row.name }}</span>
                <span v-if="row.is_main" class="agent-badge badge-main">Main</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="id" label="ID" width="120" />
          <el-table-column prop="description" :label="$t('settings.agents.description')" min-width="250">
            <template #default="{ row }">
              <span class="agent-desc-cell">{{ row.description }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="workspace_dir" label="Workspace Path" min-width="280">
            <template #default="{ row }">
              <span class="agent-path-cell">{{ row.workspace_dir }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('common.actions')" width="200" fixed="right">
            <template #default="{ row }">
              <div class="agent-table-actions">
                <el-button size="small" text type="primary" @click="openEditDialog(row)">
                  <el-icon><EditPen /></el-icon>
                  {{ $t('common.edit') }}
                </el-button>
                <el-button v-if="!row.is_main" size="small" text type="danger" @click="confirmDelete(row)">
                  <el-icon><Delete /></el-icon>
                  {{ $t('common.delete') }}
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>

    <!-- ═══════════════ Create Agent Dialog ═══════════════ -->
    <el-dialog v-model="createDialogVisible" :title="$t('settings.agents.createAgent')" width="440px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item :label="$t('settings.agents.displayName')" required>
          <el-input v-model="createForm.name" :placeholder="$t('settings.agents.displayNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('settings.agents.description')">
          <el-input v-model="createForm.description" type="textarea" :rows="3" :placeholder="$t('settings.agents.descriptionPlaceholder')" />
        </el-form-item>
        <el-form-item label="Workspace Path">
          <el-input v-model="createForm.workspace_dir" placeholder="e.g. ~/.haibot/workspaces/my-agent" />
          <div class="form-hint">Leave empty to auto-generate in ~/.haibot/workspaces/&lt;id&gt;</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="creating" :disabled="!createForm.name" @click="handleCreate">
          {{ $t('common.create') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- ═══════════════ Edit Agent Dialog ═══════════════ -->
    <el-dialog
      v-model="editDialogVisible"
      :title="`Edit Agent - ${editForm.name}`"
      width="500px"
      destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="ID">
          <el-input v-model="editForm.id" disabled />
        </el-form-item>
        <el-form-item label="Name" required>
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item :label="$t('settings.agents.description')">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="Workspace Path">
          <el-input v-model="editForm.workspace_dir" disabled />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="editing" :disabled="!editForm.name" @click="handleEditSave">
          {{ $t('common.save') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Avatar, Delete, EditPen, Loading, Plus } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import {
  listAgents,
  createAgent as apiCreate,
  deleteAgent as apiDelete,
  updateAgent as apiUpdate,
} from '@/api/agents'
import type { AgentInfo, AgentProfileConfig } from '@/types'

const { t } = useI18n()

const agents = ref<AgentInfo[]>([])
const loading = ref(false)

// ── Create ──
const createDialogVisible = ref(false)
const createForm = reactive({ name: '', description: '', workspace_dir: '' })
const creating = ref(false)

// ── Edit Profile ──
const editDialogVisible = ref(false)
const editForm = reactive({ id: '', name: '', description: '', workspace_dir: '' })
const editing = ref(false)

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
  createForm.name = ''
  createForm.description = ''
  createForm.workspace_dir = ''
  createDialogVisible.value = true
}

async function handleCreate() {
  creating.value = true
  try {
    await apiCreate({
      name: createForm.name,
      description: createForm.description || undefined,
      workspace_dir: createForm.workspace_dir || undefined,
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

// ── Edit Profile ──
function openEditDialog(agent: AgentInfo) {
  editForm.id = agent.id
  editForm.name = agent.name
  editForm.description = agent.description || ''
  editForm.workspace_dir = agent.workspace_dir || ''
  editDialogVisible.value = true
}

async function handleEditSave() {
  editing.value = true
  try {
    const data: Partial<AgentProfileConfig> = {
      id: editForm.id,
      name: editForm.name,
      description: editForm.description,
    }
    await apiUpdate(editForm.id, data)
    ElMessage.success(t('common.saveSuccess'))
    editDialogVisible.value = false
    await loadData()
  } catch (e: unknown) {
    ElMessage.error(t('common.saveFailed') + ': ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    editing.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.page { max-width: 960px; }
.section { margin-bottom: 36px; }
.section-title { font-size: 18px; font-weight: 700; color: var(--text-1); margin-bottom: 4px; }
.section-desc { font-size: 13px; color: var(--text-3); margin-bottom: 0; }
.section-header-row { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }

.loading-state { display: flex; justify-content: center; padding: 40px 0; color: var(--text-4); font-size: 24px; }

/* ── Agent Table ── */
.agents-table-container {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  background: var(--bg-card);
}

.agent-name-cell { display: flex; align-items: center; gap: 8px; }
.agent-icon { font-size: 18px; color: var(--text-3); }
.agent-name { font-size: 14px; font-weight: 500; color: var(--text-1); }
.agent-badge {
  font-size: 11px; font-weight: 500;
  padding: 1px 8px; border-radius: var(--radius-sm);
  border: 1px solid;
}
.badge-main { color: #7c3aed; border-color: #ddd6fe; background: #f5f3ff; }

.agent-desc-cell, .agent-path-cell { font-size: 13px; color: var(--text-2); }
.agent-path-cell { font-family: Consolas, monospace; font-size: 12px; }

.agent-table-actions {
  display: flex; gap: 4px; align-items: center;
}

/* ── Dialogs ── */
.form-hint { font-size: 12px; color: var(--text-4); margin-top: 4px; }

/* ── Dark mode ── */
[data-theme="dark"] .badge-main { color: #a78bfa; border-color: rgba(124,58,237,.3); background: rgba(124,58,237,.1); }
</style>
