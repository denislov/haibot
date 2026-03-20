<template>
  <div class="workspace-layout">
    <div class="file-panel">
      <div class="panel-header">
        <div class="panel-title-row">
          <span class="panel-title">{{ $t('settings.workspace.coreFiles') }}</span>
          <button class="refresh-btn" :class="{ spinning: refreshing }" @click="loadFiles">
            <el-icon><Refresh /></el-icon>{{ $t('common.refresh') }}
          </button>
        </div>
        <p class="panel-desc">{{ $t('settings.workspace.coreFilesDesc') }}</p>
      </div>
      <div class="file-list">
        <div v-for="file in files" :key="file.filename" class="file-item"
          :class="{ active: selectedFile === file.filename }" @click="selectFile(file)">
          <div class="file-info">
            <span class="file-name">{{ file.filename }}</span>
            <span class="file-meta">{{ formatSize(file.size) }}</span>
          </div>
        </div>
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
import { listAgentFiles, readAgentFile, writeAgentFile } from '@/api/workspace'
import type { MdFileInfo } from '@/types'

const files = ref<MdFileInfo[]>([])
const selectedFile = ref<string | null>(null)
const editorContent = ref('')
const refreshing = ref(false)
const saving = ref(false)

async function loadFiles() {
  refreshing.value = true
  try { files.value = await listAgentFiles() }
  catch (e: unknown) { ElMessage.error(String(e)) }
  finally { refreshing.value = false }
}

async function selectFile(file: MdFileInfo) {
  selectedFile.value = file.filename
  try { editorContent.value = await readAgentFile(file.filename) }
  catch (e: unknown) { ElMessage.error(String(e)) }
}

async function saveFile() {
  if (!selectedFile.value) return
  saving.value = true
  try { await writeAgentFile(selectedFile.value, editorContent.value); ElMessage.success('Saved') }
  catch (e: unknown) { ElMessage.error(String(e)) }
  finally { saving.value = false }
}

function formatSize(b: number) {
  if (b < 1024) return b + ' B'
  return (b / 1024).toFixed(1) + ' KB'
}

onMounted(loadFiles)
</script>

<style scoped>
.workspace-layout { display: flex; height: calc(100vh - 56px); margin: -28px; }
.file-panel { width: 280px; flex-shrink: 0; background: var(--bg-sidebar); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
.panel-header { padding: 16px; border-bottom: 1px solid var(--border); }
.panel-title-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.panel-title { font-size: 14px; font-weight: 600; color: var(--text-1); }
.refresh-btn { display: flex; align-items: center; gap: 4px; border: none; background: none; cursor: pointer; font-size: 12px; color: var(--text-3); padding: 4px 8px; border-radius: var(--radius-sm); }
.refresh-btn:hover { background: var(--bg); }
.refresh-btn.spinning .el-icon { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.panel-desc { font-size: 12px; color: var(--text-4); }
.file-list { flex: 1; overflow-y: auto; padding: 8px; }
.file-item { padding: 10px 12px; border-radius: var(--radius); cursor: pointer; margin-bottom: 2px; }
.file-item:hover { background: var(--bg); }
.file-item.active { background: var(--primary-light); }
.file-name { display: block; font-size: 13px; font-weight: 500; color: var(--text-1); }
.file-meta { font-size: 11px; color: var(--text-4); }
.editor-panel { flex: 1; display: flex; flex-direction: column; background: var(--bg); }
.editor-empty { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--text-4); }
.editor-topbar { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; background: var(--bg-card); border-bottom: 1px solid var(--border); }
.editor-filename { font-size: 13px; font-weight: 500; color: var(--text-2); }
.editor-textarea { flex: 1; width: 100%; padding: 16px; border: none; outline: none; resize: none; font-size: 13px; font-family: 'Fira Code', Consolas, monospace; line-height: 1.7; color: var(--text-1); background: var(--bg); }
</style>
