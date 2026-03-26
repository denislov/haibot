<template>
  <div class="workspace-layout">
    <div class="file-panel">
      <div class="panel-header">
        <div class="panel-title-row">
          <span class="panel-title">{{ $t('settings.workspace.coreFiles') }}</span>
          <button class="refresh-btn" :class="{ spinning: refreshing }" @click="loadFiles" :disabled="!settingsStore.selectedAgentId">
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
import { listAgentFiles, readAgentFile, writeAgentFile, getSystemPromptFiles, updateSystemPromptFiles } from '@/api/agents'
import { useSettingsStore } from '@/stores/settings'
import type { MdFileInfo } from '@/types'

interface WorkspaceFile extends MdFileInfo {
  enabled: boolean
}

const settingsStore = useSettingsStore()
const displayFiles = ref<WorkspaceFile[]>([])
const selectedFile = ref<string | null>(null)
const editorContent = ref('')
const refreshing = ref(false)
const saving = ref(false)

async function loadFiles() {
  if (!settingsStore.selectedAgentId) return
  refreshing.value = true
  try {
    const allFiles = await listAgentFiles(settingsStore.selectedAgentId)
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
  if (!settingsStore.selectedAgentId) return
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
  if (!settingsStore.selectedAgentId) return
  selectedFile.value = file.filename
  try {
    const data = await readAgentFile(settingsStore.selectedAgentId, file.filename)
    editorContent.value = data.content
  } catch (e: unknown) {
    ElMessage.error(String(e))
  }
}

async function saveFile() {
  if (!settingsStore.selectedAgentId || !selectedFile.value) return
  saving.value = true
  try { await writeAgentFile(settingsStore.selectedAgentId, selectedFile.value, editorContent.value); ElMessage.success('Saved') }
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

onMounted(async () => {
  if (!settingsStore.loaded) await settingsStore.loadAgents()
  if (settingsStore.selectedAgentId) await loadFiles()
})
</script>

<style scoped>
.workspace-layout {
  display: flex;
  height: calc(100dvh - 64px);
  margin: -32px;
  background:
    radial-gradient(circle at top right, var(--surface-tint) 0, transparent 28%),
    linear-gradient(180deg, var(--bg) 0%, var(--bg-soft) 100%);
}
.file-panel {
  width: 292px;
  flex-shrink: 0;
  background:
    linear-gradient(180deg, var(--bg-sidebar) 0%, var(--bg-card) 100%);
  border-right: 1px solid var(--border);
  box-shadow: inset -1px 0 0 var(--surface-highlight);
  display: flex;
  flex-direction: column;
}
.panel-header { padding: 18px 18px 16px; border-bottom: 1px solid var(--border); }
.panel-title-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.panel-title { font-size: 14px; font-weight: 600; color: var(--text-1); }
.refresh-btn {
  display: flex; align-items: center; gap: 4px; border: none;
  background: var(--bg-soft); cursor: pointer; font-size: 12px;
  color: var(--text-3); padding: 6px 10px; border-radius: 999px;
  transition: background var(--transition-fast), color var(--transition-fast);
}
.refresh-btn:hover { background: var(--bg-card-elevated); color: var(--text-1); }
.refresh-btn.spinning .el-icon { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.panel-desc { font-size: 12px; color: var(--text-4); }
.file-list { flex: 1; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 10px; }
.file-card {
  display: flex; align-items: center; justify-content: space-between; padding: 13px 14px;
  background:
    linear-gradient(180deg, var(--surface-highlight) 0%, rgba(0, 0, 0, 0) 42px),
    linear-gradient(180deg, var(--bg-card-elevated) 0%, var(--bg-card) 100%);
  border: 1px solid var(--border); border-radius: var(--radius-lg); cursor: pointer;
  transition: all var(--transition-fast); gap: 12px;
}
.file-card:hover { border-color: rgba(99, 102, 241, 0.32); }
.file-card.active {
  border-color: rgba(99, 102, 241, 0.36);
  background:
    linear-gradient(180deg, rgba(99, 102, 241, 0.12) 0%, rgba(0, 0, 0, 0) 48px),
    linear-gradient(180deg, var(--bg-card-elevated) 0%, var(--bg-card) 100%);
}

.drag-handle { cursor: grab; display: flex; align-items: center; color: var(--text-4); font-size: 16px; padding: 4px; opacity: 0.5; transition: opacity var(--transition-fast); }
.file-card:hover .drag-handle { opacity: 1; }
.drag-handle:active { cursor: grabbing; }

.file-info-block { flex: 1; display: flex; flex-direction: column; gap: 4px; overflow: hidden; }
.file-name-row { display: flex; align-items: center; font-size: 14px; font-weight: 600; color: var(--text-1); }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--text-4); }
.status-dot.on { background: var(--success); }
.file-meta { font-size: 11px; color: var(--text-3); text-overflow: ellipsis; white-space: nowrap; overflow: hidden; }

.file-actions { display: flex; align-items: center; }

.editor-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(circle at top left, var(--surface-tint) 0, transparent 26%),
    linear-gradient(180deg, var(--bg) 0%, var(--bg-soft) 100%);
}
.editor-empty {
  flex: 1; display: flex; align-items: center; justify-content: center; color: var(--text-4);
}
.editor-empty span {
  padding: 16px 18px;
  border-radius: var(--radius-lg);
  border: 1px dashed var(--border);
  background: var(--bg-card);
  box-shadow: inset 0 1px 0 var(--surface-highlight);
}
.editor-topbar {
  display: flex; align-items: center; justify-content: space-between; padding: 14px 18px;
  background:
    linear-gradient(180deg, var(--surface-highlight) 0%, rgba(0, 0, 0, 0) 46px),
    linear-gradient(180deg, var(--bg-card-elevated) 0%, var(--bg-card) 100%);
  border-bottom: 1px solid var(--border);
}
.editor-filename { font-size: 13px; font-weight: 600; color: var(--text-2); letter-spacing: 0.01em; }
.editor-textarea {
  flex: 1; width: 100%; padding: 22px 24px; border: none; outline: none; resize: none;
  font-size: 13px; font-family: 'Fira Code', Consolas, monospace; line-height: 1.75;
  color: var(--text-1); background: transparent;
}

@media (max-width: 960px) {
  .workspace-layout {
    margin: -22px -18px -28px;
    height: auto;
    min-height: calc(100dvh - 64px);
    flex-direction: column;
  }
  .file-panel { width: 100%; }
  .editor-panel { min-height: 52vh; }
}
</style>
