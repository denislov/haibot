<template>
  <div class="page">
    <section class="section">
      <div class="section-header-row">
        <div>
          <h2 class="section-title">{{ $t('settings.mcp.title') }}</h2>
          <p class="section-desc">{{ $t('settings.mcp.desc') }}</p>
        </div>
        <el-button type="primary" @click="openCreateDialog">
          {{ $t('settings.mcp.createClient') }}
        </el-button>
      </div>

      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
      </div>

      <div v-else-if="clients.length === 0" class="empty-state">
        {{ $t('common.noData') }}
      </div>

      <div v-else class="clients-grid">
        <div
          v-for="client in clients"
          :key="client.key"
          class="client-card"
          :class="{ enabled: client.enabled }"
        >
          <div class="client-header">
            <div class="client-name-line">
              <el-icon class="client-icon"><Monitor /></el-icon>
              <span class="client-name">{{ client.name }}</span>
              <span class="transport-badge" :class="'badge-' + client.transport">
                {{ transportLabel(client.transport) }}
              </span>
            </div>
            <span class="client-status" :class="client.enabled ? 'status-enabled' : 'status-disabled'">
              <span class="dot" />
              {{ client.enabled ? $t('common.enabled') : $t('common.disabled') }}
            </span>
          </div>

          <div v-if="client.description" class="client-desc">{{ client.description }}</div>

          <div class="client-actions">
            <el-button size="small" text type="primary" @click="toggleClient(client)">
              {{ client.enabled ? $t('common.disable') : $t('common.enable') }}
            </el-button>
            <el-button size="small" text type="primary" @click="openEditDialog(client)">
              <el-icon><EditPen /></el-icon>
            </el-button>
            <el-button size="small" text type="danger" @click="confirmDelete(client)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════ Create Dialog ═══════════════ -->
    <el-dialog v-model="createDialogVisible" :title="$t('settings.mcp.createClient')" width="640px" destroy-on-close>
      <div class="format-hints">
        <p class="format-title">{{ $t('settings.mcp.supportedFormats') }}</p>
        <ul class="format-list">
          <li>Standard format: <code>{ "mcpServers": { "key": {...} } }</code></li>
          <li>Direct format: <code>{ "key": {...} }</code></li>
          <li>Single format: <code>{ "key": "...", "name": "...", "command": "..." }</code></li>
        </ul>
      </div>
      <el-input
        v-model="createJsonText"
        type="textarea"
        :rows="14"
        :placeholder="createPlaceholder"
        class="json-textarea"
      />
      <div v-if="createError" class="json-error">{{ createError }}</div>
      <template #footer>
        <el-button @click="createDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">{{ $t('common.create') }}</el-button>
      </template>
    </el-dialog>

    <!-- ═══════════════ Edit Dialog ═══════════════ -->
    <el-dialog v-model="editDialogVisible" :title="`${editingClient?.name} - ${$t('settings.mcp.editClient')}`" width="640px" destroy-on-close>
      <el-input
        v-model="editJsonText"
        type="textarea"
        :rows="16"
        class="json-textarea"
      />
      <div v-if="editError" class="json-error">{{ editError }}</div>
      <template #footer>
        <el-button @click="editDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="handleEdit">{{ $t('common.edit') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, EditPen, Loading, Monitor } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import {
  listMCPClients,
  createMCPClient,
  updateMCPClient,
  toggleMCPClient as apiToggle,
  deleteMCPClient,
} from '@/api/mcp'
import type { MCPClientInfo } from '@/types'

const { t } = useI18n()

const clients = ref<MCPClientInfo[]>([])
const loading = ref(false)

// ── Create ──
const createDialogVisible = ref(false)
const createJsonText = ref('')
const createError = ref('')
const creating = ref(false)

const createPlaceholder = `{
  "mcpServers": {
    "example-client": {
      "command": "npx",
      "args": ["-y", "@example/mcp-server"],
      "env": {
        "API_KEY": "<YOUR_API_KEY>"
      }
    }
  }
}`

// ── Edit ──
const editDialogVisible = ref(false)
const editingClient = ref<MCPClientInfo | null>(null)
const editJsonText = ref('')
const editError = ref('')
const saving = ref(false)

function transportLabel(t: string): string {
  const map: Record<string, string> = {
    stdio: 'Local',
    streamable_http: 'HTTP',
    sse: 'SSE',
  }
  return map[t] || t
}

async function loadData() {
  loading.value = true
  try {
    clients.value = await listMCPClients()
  } catch (e: unknown) {
    ElMessage.error('Load failed: ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    loading.value = false
  }
}

async function toggleClient(client: MCPClientInfo) {
  try {
    const updated = await apiToggle(client.key)
    const idx = clients.value.findIndex((c) => c.key === client.key)
    if (idx >= 0) clients.value[idx] = updated
  } catch (e: unknown) {
    ElMessage.error('Toggle failed: ' + (e instanceof Error ? e.message : String(e)))
  }
}

async function confirmDelete(client: MCPClientInfo) {
  try {
    await ElMessageBox.confirm(
      t('settings.mcp.deleteConfirm', { name: client.name }),
      t('settings.mcp.deleteClient'),
      { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' },
    )
    await deleteMCPClient(client.key)
    clients.value = clients.value.filter((c) => c.key !== client.key)
    ElMessage.success(t('common.deleteSuccess'))
  } catch (e: unknown) {
    if (e !== 'cancel' && (e as any) !== 'cancel') {
      ElMessage.error(t('common.deleteFailed') + ': ' + (e instanceof Error ? e.message : String(e)))
    }
  }
}

// ── Create dialog ──
function openCreateDialog() {
  createJsonText.value = createPlaceholder
  createError.value = ''
  createDialogVisible.value = true
}

function parseCreateJson(text: string): Array<{ key: string; client: Record<string, any> }> {
  const obj = JSON.parse(text)
  // Standard format: { mcpServers: { key: {...} } }
  if (obj.mcpServers && typeof obj.mcpServers === 'object') {
    return Object.entries(obj.mcpServers).map(([key, val]) => ({
      key,
      client: { name: key, ...(val as Record<string, any>) },
    }))
  }
  // Single format: { key: "...", name: "...", command: "..." }
  if (typeof obj.key === 'string' && (obj.name || obj.command)) {
    const key = obj.key
    const { key: _k, ...rest } = obj
    return [{ key, client: { name: key, ...rest } }]
  }
  // Direct format: { key: {...} }
  const entries = Object.entries(obj)
  if (entries.length > 0 && typeof entries[0][1] === 'object') {
    return entries.map(([key, val]) => ({
      key,
      client: { name: key, ...(val as Record<string, any>) },
    }))
  }
  throw new Error(t('settings.mcp.invalidJson'))
}

async function handleCreate() {
  createError.value = ''
  creating.value = true
  try {
    const items = parseCreateJson(createJsonText.value)
    for (const item of items) {
      await createMCPClient({ client_key: item.key, client: item.client })
    }
    createDialogVisible.value = false
    ElMessage.success(t('common.createSuccess'))
    await loadData()
  } catch (e: unknown) {
    createError.value = e instanceof Error ? e.message : String(e)
  } finally {
    creating.value = false
  }
}

// ── Edit dialog ──
function openEditDialog(client: MCPClientInfo) {
  editingClient.value = client
  editError.value = ''
  // Build a clean JSON for editing (exclude masked env values concept — show as-is)
  const obj: Record<string, any> = {
    key: client.key,
    name: client.name,
    description: client.description,
    enabled: client.enabled,
  }
  if (client.transport === 'stdio') {
    obj.command = client.command
    obj.args = client.args
    if (client.cwd) obj.cwd = client.cwd
  } else {
    obj.transport = client.transport
    obj.url = client.url
    if (Object.keys(client.headers).length) obj.headers = client.headers
  }
  if (Object.keys(client.env).length) obj.env = client.env
  editJsonText.value = JSON.stringify(obj, null, 2)
  editDialogVisible.value = true
}

async function handleEdit() {
  if (!editingClient.value) return
  editError.value = ''
  saving.value = true
  try {
    const parsed = JSON.parse(editJsonText.value)
    // Remove key (immutable) before sending
    const { key: _k, ...updateData } = parsed
    await updateMCPClient(editingClient.value.key, updateData)
    editDialogVisible.value = false
    ElMessage.success(t('common.saveSuccess'))
    await loadData()
  } catch (e: unknown) {
    editError.value = e instanceof Error ? e.message : String(e)
  } finally {
    saving.value = false
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
.empty-state { text-align: center; padding: 60px 0; color: var(--text-4); font-size: 14px; }

/* ── Client Cards ── */
.clients-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.client-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 18px;
  transition: box-shadow var(--transition-fast), border-color var(--transition-fast);
}
.client-card:hover { box-shadow: var(--shadow-md); }
.client-card.enabled { border-color: var(--primary); }

.client-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 8px; }
.client-name-line { display: flex; align-items: center; gap: 8px; }
.client-icon { font-size: 18px; color: var(--primary); }
.client-name { font-size: 15px; font-weight: 600; color: var(--text-1); }

.transport-badge {
  font-size: 11px; font-weight: 500;
  padding: 1px 8px; border-radius: var(--radius-sm);
  border: 1px solid;
}
.badge-stdio { color: #22c55e; border-color: #bbf7d0; background: #f0fdf4; }
.badge-streamable_http { color: #3b82f6; border-color: #bfdbfe; background: #eff6ff; }
.badge-sse { color: #f59e0b; border-color: #fde68a; background: #fffbeb; }

.client-status { display: flex; align-items: center; gap: 4px; font-size: 11px; padding: 2px 7px; border-radius: var(--radius-sm); white-space: nowrap; }
.status-enabled { color: var(--success); background: var(--success-light); }
.status-disabled { color: var(--text-4); background: var(--bg); }
.dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; }

.client-desc { font-size: 12px; color: var(--text-3); margin-bottom: 8px; }

.client-actions {
  margin-top: 12px; border-top: 1px solid var(--border);
  padding-top: 10px; display: flex; gap: 4px; justify-content: flex-end;
}

/* ── Create/Edit Dialogs ── */
.format-hints { margin-bottom: 16px; }
.format-title { font-size: 14px; font-weight: 600; color: var(--text-1); margin-bottom: 8px; }
.format-list {
  list-style: disc; padding-left: 20px;
  font-size: 13px; color: var(--text-3);
}
.format-list li { margin-bottom: 4px; }
.format-list code {
  background: var(--bg);
  padding: 1px 6px; border-radius: var(--radius-sm);
  font-family: Consolas, monospace; font-size: 12px; color: var(--text-2);
}

.json-textarea :deep(.el-textarea__inner) {
  font-family: 'Fira Code', 'Cascadia Code', Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
  background: var(--bg);
  border-radius: var(--radius);
}

.json-error {
  margin-top: 8px;
  font-size: 12px; color: var(--error);
}

/* ── Dark mode badge overrides ── */
[data-theme="dark"] .badge-stdio { color: #4ade80; border-color: rgba(34,197,94,.3); background: rgba(34,197,94,.1); }
[data-theme="dark"] .badge-streamable_http { color: #60a5fa; border-color: rgba(59,130,246,.3); background: rgba(59,130,246,.1); }
[data-theme="dark"] .badge-sse { color: #fbbf24; border-color: rgba(245,158,11,.3); background: rgba(245,158,11,.1); }
</style>
