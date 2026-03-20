<template>
  <div class="tc-block">
    <div
      class="tc-header"
      :class="{ 'tc-loading': loading }"
      @click="!loading && $emit('toggle')"
    >
      <el-icon class="tc-icon spin-icon" v-if="loading"><Loading /></el-icon>
      <el-icon class="tc-icon" v-else-if="toolType === 'mcp_call'"><Connection /></el-icon>
      <el-icon class="tc-icon" v-else><Tools /></el-icon>
      <span class="tc-name">{{ toolName || toolType }}</span>
      <span v-if="loading" class="tc-running">{{ $t('chat.running') }}</span>
      <el-icon v-else class="tc-chevron" :class="{ open: expanded }"><ArrowDown /></el-icon>
    </div>

    <div v-if="!loading && expanded" class="tc-body">
      <!-- Input -->
      <div class="tc-section">
        <div class="tc-section-hd">
          <span class="tc-section-label">Input</span>
          <button class="tc-copy" title="Copy" @click.stop="copy(toolArgs)">
            <el-icon><CopyDocument /></el-icon>
          </button>
        </div>
        <div class="tc-code-wrap">
          <table class="tc-code-table">
            <tbody v-html="renderJsonCode(toolArgs)" />
          </table>
        </div>
      </div>
      <!-- Output -->
      <div v-if="toolOutput !== undefined" class="tc-section">
        <div class="tc-section-hd">
          <span class="tc-section-label">Output</span>
          <button class="tc-copy" title="Copy" @click.stop="copy(toolOutput)">
            <el-icon><CopyDocument /></el-icon>
          </button>
        </div>
        <div class="tc-code-wrap">
          <table class="tc-code-table">
            <tbody v-html="renderJsonCode(toolOutput)" />
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { renderJsonCode } from '@/utils/useMarkdown'

defineProps<{
  toolType?: string
  toolName?: string
  toolArgs?: string
  toolOutput?: string
  expanded?: boolean
  loading?: boolean
}>()

defineEmits<{ toggle: [] }>()

function copy(raw: string | undefined) {
  if (!raw) return
  let text: string
  try { text = JSON.stringify(JSON.parse(raw), null, 2) } catch { text = raw }
  navigator.clipboard.writeText(text).then(() => ElMessage.success('已复制'))
}
</script>

<style scoped>
.tc-block {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  background: var(--bg-card);
  font-size: 13px;
  width: 100%;
}

.tc-header {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 9px 14px;
  cursor: pointer;
  user-select: none;
  transition: background var(--transition-fast);
}
.tc-header:hover { background: var(--bg); }
.tc-header.tc-loading { cursor: default; }
.tc-header.tc-loading:hover { background: var(--bg-card); }

.tc-icon { font-size: 14px; color: var(--text-3); flex-shrink: 0; }
.spin-icon { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.tc-name {
  flex: 1;
  font-weight: 600;
  font-size: 13px;
  color: var(--text-1);
  font-family: 'Fira Code', 'Cascadia Code', Consolas, monospace;
}

.tc-running { font-size: 11px; color: var(--text-4); font-style: italic; }

.tc-chevron {
  font-size: 12px !important;
  color: var(--text-4);
  transition: transform 0.2s;
}
.tc-chevron.open { transform: rotate(180deg); }

.tc-body { border-top: 1px solid var(--border); }

.tc-section {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}
.tc-section:last-child { border-bottom: none; }

.tc-section-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.tc-section-label { font-size: 12px; font-weight: 600; color: var(--text-2); }

.tc-copy {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px; height: 24px;
  border: none; background: none;
  cursor: pointer; color: var(--text-4);
  border-radius: var(--radius-sm);
  font-size: 13px;
  transition: background var(--transition-fast), color var(--transition-fast);
}
.tc-copy:hover { background: var(--border); color: var(--text-2); }

.tc-code-wrap {
  overflow-x: auto;
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}

.tc-code-table {
  border-collapse: collapse;
  width: 100%;
  font-family: 'Fira Code', 'Cascadia Code', Consolas, monospace;
  font-size: 12.5px;
  line-height: 1.6;
}

:deep(.tc-code-table .ln) {
  padding: 0 12px 0 10px;
  color: var(--text-4);
  text-align: right;
  vertical-align: top;
  white-space: nowrap;
  user-select: none;
  min-width: 28px;
  border-right: 1px solid var(--border);
  background: var(--bg);
}

:deep(.tc-code-table .lc) {
  padding: 0 14px 0 10px;
  white-space: pre;
  vertical-align: top;
  color: var(--text-1);
}

/* Light mode hljs token colors */
:deep(.tc-code-table .hljs-attr)        { color: #0550ae; }
:deep(.tc-code-table .hljs-string)      { color: #cf222e; }
:deep(.tc-code-table .hljs-number)      { color: #0a3069; }
:deep(.tc-code-table .hljs-literal)     { color: #8250df; }
:deep(.tc-code-table .hljs-punctuation) { color: var(--text-1); }

/* Dark mode hljs token colors */
[data-theme="dark"] :deep(.tc-code-table .hljs-attr)        { color: #79c0ff; }
[data-theme="dark"] :deep(.tc-code-table .hljs-string)      { color: #a5d6ff; }
[data-theme="dark"] :deep(.tc-code-table .hljs-number)      { color: #79c0ff; }
[data-theme="dark"] :deep(.tc-code-table .hljs-literal)     { color: #d2a8ff; }
[data-theme="dark"] :deep(.tc-code-table .hljs-punctuation) { color: var(--text-1); }
</style>
