<template>
  <div class="page">
    <div class="page-header">
      <div><h1 class="page-title">{{ $t('settings.sessions.title') }}</h1><p class="page-desc">{{ $t('settings.sessions.desc') }}</p></div>
    </div>
    <div class="filters-row">
      <el-input v-model="filterUserId" :placeholder="$t('settings.sessions.filterUser')" clearable style="width: 200px" @change="loadSessions" />
      <el-select v-model="filterChannel" :placeholder="$t('settings.sessions.filterChannel')" clearable style="width: 150px" @change="loadSessions">
        <el-option v-for="ch in channelOptions" :key="ch" :label="ch" :value="ch" />
      </el-select>
      <span class="total-label">{{ sessions.length }} items</span>
    </div>
    <div class="table-card">
      <el-table :data="pagedSessions" style="width: 100%">
        <el-table-column prop="id" label="ID" width="200" fixed="left"><template #default="{ row }"><span class="mono text-xs text-muted">{{ row.id }}</span></template></el-table-column>
        <el-table-column prop="name" :label="$t('settings.sessions.name')" min-width="140" />
        <el-table-column prop="session_id" label="SessionID" min-width="130"><template #default="{ row }"><span class="mono text-xs">{{ row.session_id }}</span></template></el-table-column>
        <el-table-column prop="user_id" label="UserID" min-width="130" />
        <el-table-column prop="channel" label="Channel" min-width="100"><template #default="{ row }"><span class="channel-tag">{{ row.channel }}</span></template></el-table-column>
        <el-table-column prop="created_at" label="Created" min-width="160"><template #default="{ row }"><span class="text-xs text-muted">{{ formatTime(row.created_at) }}</span></template></el-table-column>
        <el-table-column prop="updated_at" label="Updated" min-width="160"><template #default="{ row }"><span class="text-xs text-muted">{{ formatTime(row.updated_at) }}</span></template></el-table-column>
        <el-table-column label="Action" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link @click="openEdit(row)">{{ $t('common.edit') }}</el-button>
            <el-button size="small" link type="danger" @click="handleDelete(row)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <span class="total-info">{{ sessions.length }} items</span>
        <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="sessions.length" layout="prev, pager, next" small />
      </div>
    </div>
    <el-dialog v-model="editDialogVisible" :title="$t('common.edit')" width="440px">
      <el-form :model="editForm" label-position="top">
        <el-form-item :label="$t('settings.sessions.name')"><el-input v-model="editForm.name" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="saveSession">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listChats, updateChat, deleteChat } from '@/api/chats'
import type { ChatSpec } from '@/types'

const sessions = ref<ChatSpec[]>([])
const filterUserId = ref('')
const filterChannel = ref('')
const currentPage = ref(1)
const pageSize = 10
const saving = ref(false)
const editDialogVisible = ref(false)
const editingSession = ref<ChatSpec | null>(null)
const editForm = ref({ name: '' })
const channelOptions = ['console', 'dingtalk', 'feishu', 'qq', 'discord', 'imessage']

const pagedSessions = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return sessions.value.slice(start, start + pageSize)
})

async function loadSessions() {
  try {
    sessions.value = await listChats({ user_id: filterUserId.value || undefined, channel: filterChannel.value || undefined })
  } catch (e: unknown) { ElMessage.error('Load failed: ' + (e instanceof Error ? e.message : String(e))) }
}

function openEdit(row: ChatSpec) { editingSession.value = row; editForm.value = { name: row.name }; editDialogVisible.value = true }

async function saveSession() {
  if (!editingSession.value) return
  saving.value = true
  try {
    await updateChat(editingSession.value.id, { ...editingSession.value, name: editForm.value.name })
    ElMessage.success('Saved'); editDialogVisible.value = false; await loadSessions()
  } catch (e: unknown) { ElMessage.error('Save failed: ' + (e instanceof Error ? e.message : String(e)))
  } finally { saving.value = false }
}

async function handleDelete(row: ChatSpec) {
  try {
    await ElMessageBox.confirm(`Delete "${row.name}"?`, 'Confirm', { confirmButtonText: 'Delete', cancelButtonText: 'Cancel', type: 'warning' })
    await deleteChat(row.id); ElMessage.success('Deleted'); await loadSessions()
  } catch { /* cancelled */ }
}

function formatTime(iso: string) {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString()
}

onMounted(loadSessions)
</script>

<style scoped>
.page-header { margin-bottom: 20px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text-1); }
.page-desc { font-size: 13px; color: var(--text-3); margin-top: 4px; }
.filters-row { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.total-label { font-size: 13px; color: var(--text-3); margin-left: auto; }
.table-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); overflow: hidden; }
.pagination-row { display: flex; align-items: center; justify-content: flex-end; padding: 12px 16px; border-top: 1px solid var(--border); gap: 12px; }
.total-info { font-size: 13px; color: var(--text-3); margin-right: auto; }
.mono { font-family: 'Fira Code', Consolas, monospace; }
.text-xs { font-size: 12px; }
.text-muted { color: var(--text-4); }
.channel-tag { display: inline-block; padding: 1px 8px; border-radius: var(--radius-sm); font-size: 12px; font-weight: 500; background: var(--primary-light); color: var(--primary-text); }
</style>
