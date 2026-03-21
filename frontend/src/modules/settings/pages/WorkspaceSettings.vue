<template>
  <div class="workspace-layout">
    <div class="file-panel">
      <div class="agent-selector-wrapper">
        <span class="selector-label">{{ $t('settings.agents.title') }}</span>
        <el-select v-model="selectedAgentId" :placeholder="$t('settings.agents.displayNamePlaceholder') || 'Select Agent'" @change="onAgentChange" style="width: 100%" size="small">
          <el-option v-for="agent in agents" :key="agent.id" :label="agent.name" :value="agent.id" />
        </el-select>
      </div>
      <div class="panel-header">
        <div class="panel-title-row">
          <span class="panel-title">{{ $t('settings.workspace.coreFiles') }}</span>
          <button class="refresh-btn" :class="{ spinning: refreshing }" @click="loadFiles" :disabled="!selectedAgentId">
            <el-icon><Refresh /></el-icon>{{ $t('common.refresh') }}
          </button>
        </div>
        <p class="panel-desc">{{ $t('settings.workspace.coreFilesDesc') }}</p>
      </div>
      <div class="file-list">
        <draggable v-model="displayFiles" item-key="filename" handle=".drag-handle" @end="syncPrompts">
          <template #item="{ element }">
            <div class="file-card" :class="{ active: selectedFile === element.filename }" @click="selectFile(element)">
              <div class="drag-handle">
                <el-icon><MoreFilled /></el-icon>
              </div>
              <div class="file-info-block">
                <div class="file-name-row">
                  <span class="status-dot" :class="{ on: element.enabled }" />
                  <span class="file-name" style="margin-left: 6px;">{{ element.filename }}</span>
                </div>
                <div class="file-meta">
                  {{ formatSize(element.size) }} · {{ formatTimeOffset(element.modified_time) }}
                </div>
              </div>
              <div class="file-actions" @click.stop>
                <el-switch v-model="element.enabled" @change="onToggle" />
              </div>
            </div>
          </template>
        </draggable>
      </div>
    </div>
    <div class="editor-panel">
      <div v-if="!selectedFile" class="editor-empty">
        <span>{{ $t('settings.workspace.selectFile') }}</span>
      </div>
      <template v-else>
        <div class="editor-topbar">
          <span class="editor-filename">{{ selectedFile }}</span>
          <el-button size="small" :loading="saving" type="primary" @click="saveFile">
            {{ $t('common.save') }}
          </el-button>
        </div>
        <textarea v-model="editorContent" class="editor-textarea" spellcheck="false" />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import draggable from 'vuedraggable'
import { MoreFilled, Refresh } from '@element-plus/icons-vue'
import { listAgents, listAgentFiles, readAgentFile, writeAgentFile, getSystemPromptFiles, updateSystemPromptFiles } from '@/api/agents'
import { setAgentHeader } from '@/api/index'
import type { AgentSummary, MdFileInfo } from '@/types'

interface WorkspaceFile extends MdFileInfo {
  enabled: boolean
}

const agents = ref<AgentSummary[]>([])
const selectedAgentId = ref<string>('')
const displayFiles = ref<WorkspaceFile[]>([])
const selectedFile = ref<string | null>(null)
const editorContent = ref('')
const refreshing = ref(false)
const saving = ref(false)

async function loadAgents() {
  try {
    agents.value = await listAgents()
    if (agents.value.length > 0) {
      selectedAgentId.value = agents.value[0].id
      await loadFiles()
    }
  } catch (e: unknown) {
    ElMessage.error(String(e))
  }
}

function onAgentChange() {
  selectedFile.value = null
  editorContent.value = ''
  displayFiles.value = []
  if (selectedAgentId.value) setAgentHeader(selectedAgentId.value)
  loadFiles()
}

async function loadFiles() {
  if (!selectedAgentId.value) return
  refreshing.value = true
  try {
    const allFiles = await listAgentFiles(selectedAgentId.value)
    const enabledNames = await getSystemPromptFiles()
    
    const mapped: WorkspaceFile[] = []
    // Add enabled files in the specific order returned by the backend
    for (const name of enabledNames) {
      const found = allFiles.find(f => f.filename === name)
      if (found) { mapped.push({ ...found, enabled: true }) }
    }
    // Add remaining files disabled
    for (const f of allFiles) {
      if (!enabledNames.includes(f.filename)) {
        mapped.push({ ...f, enabled: false })
      }
    }
    displayFiles.value = mapped
  }
  catch (e: unknown) { ElMessage.error(String(e)) }
  finally { refreshing.value = false }
}

async function syncPrompts() {
  if (!selectedAgentId.value) return
  const enabledNames = displayFiles.value.filter(f => f.enabled).map(f => f.filename)
  try {
    await updateSystemPromptFiles(enabledNames)
  } catch (e: unknown) {
    ElMessage.error('Failed to sync sequence: ' + String(e))
  }
}

function onToggle() {
  // Visually sink disabled files to the bottom
  displayFiles.value.sort((a, b) => (a.enabled === b.enabled ? 0 : a.enabled ? -1 : 1))
  syncPrompts()
}

async function selectFile(file: WorkspaceFile) {
  if (!selectedAgentId.value) return
  selectedFile.value = file.filename
  try {
    const data = await readAgentFile(selectedAgentId.value, file.filename)
    editorContent.value = data.content
  } catch (e: unknown) {
    ElMessage.error(String(e))
  }
}

async function saveFile() {
  if (!selectedAgentId.value || !selectedFile.value) return
  saving.value = true
  try { await writeAgentFile(selectedAgentId.value, selectedFile.value, editorContent.value); ElMessage.success('Saved') }
  catch (e: unknown) { ElMessage.error(String(e)) }
  finally { saving.value = false }
}

function formatSize(b: number) {
  if (b < 1024) return b + ' B'
  return (b / 1024).toFixed(1) + ' KB'
}

function formatTimeOffset(isoTime: string) {
  if (!isoTime) return 'NaNd ago'
  const time = new Date(isoTime).getTime()
  if (isNaN(time)) return 'NaNd ago'
  const diffMs = Date.now() - time
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  if (days === 0) {
    const hours = Math.floor(diffMs / (1000 * 60 * 60))
    if (hours === 0) return 'Just now'
    return `${hours}h ago`
  }
  return `${days}d ago`
}

onMounted(loadAgents)
</script>

<style scoped>
.workspace-layout { display: flex; height: calc(100vh - 56px); margin: -28px; }
.file-panel { width: 280px; flex-shrink: 0; background: var(--bg-sidebar); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
.agent-selector-wrapper { padding: 12px 16px; border-bottom: 1px solid var(--border); background: var(--bg-card); }
.selector-label { display: block; font-size: 12px; font-weight: 500; color: var(--text-3); margin-bottom: 6px; }
.panel-header { padding: 16px; border-bottom: 1px solid var(--border); }
.panel-title-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.panel-title { font-size: 14px; font-weight: 600; color: var(--text-1); }
.refresh-btn { display: flex; align-items: center; gap: 4px; border: none; background: none; cursor: pointer; font-size: 12px; color: var(--text-3); padding: 4px 8px; border-radius: var(--radius-sm); }
.refresh-btn:hover { background: var(--bg); }
.refresh-btn.spinning .el-icon { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.panel-desc { font-size: 12px; color: var(--text-4); }
.file-list { flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.file-card { display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); cursor: pointer; transition: all var(--transition-fast); gap: 12px; }
.file-card:hover { border-color: var(--primary); }
.file-card.active { border-color: var(--primary); background: var(--primary-light); }

.drag-handle { cursor: grab; display: flex; align-items: center; color: var(--text-4); font-size: 16px; padding: 4px; opacity: 0.5; transition: opacity var(--transition-fast); }
.file-card:hover .drag-handle { opacity: 1; }
.drag-handle:active { cursor: grabbing; }

.file-info-block { flex: 1; display: flex; flex-direction: column; gap: 4px; overflow: hidden; }
.file-name-row { display: flex; align-items: center; font-size: 14px; font-weight: 600; color: var(--text-1); }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--text-4); }
.status-dot.on { background: var(--success); }
.file-meta { font-size: 11px; color: var(--text-3); text-overflow: ellipsis; white-space: nowrap; overflow: hidden; }

.file-actions { display: flex; align-items: center; }

.editor-panel { flex: 1; display: flex; flex-direction: column; background: var(--bg); }
.editor-empty { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--text-4); }
.editor-topbar { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; background: var(--bg-card); border-bottom: 1px solid var(--border); }
.editor-filename { font-size: 13px; font-weight: 500; color: var(--text-2); }
.editor-textarea { flex: 1; width: 100%; padding: 16px; border: none; outline: none; resize: none; font-size: 13px; font-family: 'Fira Code', Consolas, monospace; line-height: 1.7; color: var(--text-1); background: var(--bg); }
</style>
