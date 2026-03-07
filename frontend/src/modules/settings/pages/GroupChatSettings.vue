<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">{{ $t('settings.groupChats.title') }}</h1>
      </div>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        {{ $t('settings.groupChats.create') }}
      </el-button>
    </div>

    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading"><Loading /></el-icon>
    </div>

    <div v-else class="group-chats-list">
      <div v-if="groupChats.length === 0" class="empty-state">{{ $t('common.noData') }}</div>
      <div v-for="gc in groupChats" :key="gc.id" class="gc-card">
        <div class="gc-header">
          <span class="gc-name">{{ gc.name }}</span>
          <span class="gc-id mono">{{ gc.id }}</span>
        </div>
        <div class="gc-meta">
          <span>{{ $t('settings.groupChats.host') }}: <strong>{{ gc.host_agent_id }}</strong></span>
          <span>{{ $t('settings.groupChats.participants') }}: {{ gc.participant_agent_ids.join(', ') }}</span>
          <span>{{ $t('settings.groupChats.maxRounds') }}: {{ gc.max_rounds }}</span>
        </div>
        <div class="gc-actions">
          <el-button size="small" text type="primary" @click="openEdit(gc)">
            <el-icon><Edit /></el-icon>
            {{ $t('common.edit') }}
          </el-button>
          <el-button size="small" text type="danger" @click="handleDelete(gc)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="editingGC ? $t('common.edit') : $t('settings.groupChats.create')"
      width="520px"
      destroy-on-close
    >
      <el-form :model="form" label-position="top">
        <el-form-item :label="$t('settings.groupChats.groupId')" required>
          <el-input v-model="form.id" :disabled="!!editingGC" placeholder="e.g. my-group" />
        </el-form-item>
        <el-form-item :label="$t('common.edit') === 'Edit' ? 'Name' : '名称'" required>
          <el-input v-model="form.name" placeholder="e.g. Research Team" />
        </el-form-item>
        <el-form-item :label="$t('settings.groupChats.host')" required>
          <el-select v-model="form.host_agent_id" style="width: 100%" @change="onHostChange">
            <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('settings.groupChats.participants')" required>
          <el-select
            v-model="form.participant_agent_ids"
            multiple
            style="width: 100%"
          >
            <el-option
              v-for="a in participantOptions"
              :key="a.id"
              :label="a.name"
              :value="a.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('settings.groupChats.maxRounds')" required>
          <el-input-number v-model="form.max_rounds" :min="1" :max="50" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="save">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listGroupChats, createGroupChat, updateGroupChat, deleteGroupChat } from '@/api/group_chats'
import { listAgents } from '@/api/agents'
import type { GroupChatConfig } from '@/types/group_chat'
import type { AgentInfo } from '@/types'

const groupChats = ref<GroupChatConfig[]>([])
const agents = ref<AgentInfo[]>([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editingGC = ref<GroupChatConfig | null>(null)

const form = reactive({
  id: '',
  name: '',
  host_agent_id: '',
  participant_agent_ids: [] as string[],
  max_rounds: 10,
})

const participantOptions = computed(() =>
  agents.value.filter(a => a.id !== form.host_agent_id)
)

function onHostChange() {
  // Remove host from participants if selected
  form.participant_agent_ids = form.participant_agent_ids.filter(id => id !== form.host_agent_id)
}

async function load() {
  loading.value = true
  try {
    [groupChats.value, agents.value] = await Promise.all([listGroupChats(), listAgents()])
  } catch (e: unknown) {
    ElMessage.error(String(e))
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingGC.value = null
  Object.assign(form, { id: '', name: '', host_agent_id: '', participant_agent_ids: [], max_rounds: 10 })
  dialogVisible.value = true
}

function openEdit(gc: GroupChatConfig) {
  editingGC.value = gc
  Object.assign(form, {
    id: gc.id,
    name: gc.name,
    host_agent_id: gc.host_agent_id,
    participant_agent_ids: [...gc.participant_agent_ids],
    max_rounds: gc.max_rounds,
  })
  dialogVisible.value = true
}

async function save() {
  if (!form.id.trim() || !form.name.trim() || !form.host_agent_id) {
    ElMessage.warning('Please fill in all required fields')
    return
  }
  saving.value = true
  try {
    if (editingGC.value) {
      await updateGroupChat(form.id, { ...form, created_at: editingGC.value.created_at })
    } else {
      await createGroupChat({ ...form })
    }
    dialogVisible.value = false
    await load()
  } catch (e: unknown) {
    ElMessage.error(String(e))
  } finally {
    saving.value = false
  }
}

async function handleDelete(gc: GroupChatConfig) {
  try {
    await ElMessageBox.confirm(`Delete group chat "${gc.name}"?`, 'Confirm', { type: 'warning' })
    await deleteGroupChat(gc.id)
    await load()
  } catch {
    // cancelled
  }
}

onMounted(load)
</script>

<style scoped>
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text-1); }
.loading-state { display: flex; justify-content: center; padding: 60px 0; color: var(--text-4); font-size: 24px; }
.empty-state { text-align: center; padding: 40px 0; color: var(--text-4); font-size: 14px; }
.group-chats-list { display: flex; flex-direction: column; gap: 12px; }
.gc-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px;
}
.gc-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.gc-name { font-size: 14px; font-weight: 600; color: var(--text-1); }
.gc-id { font-size: 12px; color: var(--text-4); }
.mono { font-family: 'Fira Code', Consolas, monospace; }
.gc-meta { display: flex; flex-wrap: wrap; gap: 12px; font-size: 12px; color: var(--text-3); margin-bottom: 10px; }
.gc-actions { display: flex; align-items: center; gap: 8px; padding-top: 10px; border-top: 1px solid var(--border); }
</style>
