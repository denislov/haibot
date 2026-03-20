<template>
  <div class="message-row" :class="message.role">
    <!-- User message -->
    <template v-if="message.role === 'user'">
      <div class="msg-bubble user-bubble">
        <span>{{ message.blocks[0]?.text || '' }}</span>
      </div>
    </template>

    <!-- Assistant message -->
    <template v-else>
      <!-- Agent name badge for group chat -->
      <div v-if="message.agentName" class="agent-name-badge">
        {{ message.agentName }}
      </div>
      <div class="msg-assistant" :class="{ 'group-agent': message.agentId }">
        <div v-for="(block, bi) in message.blocks" :key="bi" class="msg-block">
          <!-- Text -->
          <MarkdownBlock
            v-if="block.kind === 'text' && block.text"
            :text="block.text"
          />

          <!-- Reasoning -->
          <ReasoningBlock
            v-else-if="block.kind === 'reasoning'"
            :text="block.text"
            :expanded="block.expanded"
            @toggle="block.expanded = !block.expanded"
          />

          <!-- Tool call -->
          <ToolCallBlock
            v-else-if="block.kind === 'tool_call'"
            :tool-type="block.toolType"
            :tool-name="block.toolName"
            :tool-args="block.toolArgs"
            :tool-output="block.toolOutput"
            :expanded="block.expanded"
            :loading="block.loading"
            @toggle="block.expanded = !block.expanded"
          />
        </div>

        <!-- Streaming cursor -->
        <span v-if="message.streaming" class="streaming-cursor" />

        <!-- Action bar (copy button) — shown on hover -->
        <div v-if="!message.streaming && hasContent" class="msg-actions">
          <button class="action-btn" :title="$t('common.copy')" @click="copyMessage">
            <el-icon v-if="!copied"><CopyDocument /></el-icon>
            <el-icon v-else><Select /></el-icon>
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { DisplayMessage } from '@/types'
import ReasoningBlock from './ReasoningBlock.vue'
import ToolCallBlock from './ToolCallBlock.vue'
import MarkdownBlock from './MarkdownBlock.vue'

const props = defineProps<{
  message: DisplayMessage
}>()

const copied = ref(false)

const hasContent = computed(() =>
  props.message.blocks.some((b) => b.kind === 'text' && b.text?.trim())
)

function copyMessage() {
  const textBlocks = props.message.blocks
    .filter((b) => b.kind === 'text' && b.text)
    .map((b) => b.text)
    .join('\n\n')
  if (!textBlocks) return
  navigator.clipboard.writeText(textBlocks).then(() => {
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }).catch(() => {
    ElMessage.error('Copy failed')
  })
}
</script>

<style scoped>
.message-row { display: flex; }
.message-row.user { justify-content: flex-end; }
.message-row.assistant { justify-content: flex-start; }

.msg-bubble {
  max-width: 80%;
  padding: 10px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}
.user-bubble {
  background: var(--primary);
  color: white;
  border-bottom-right-radius: 4px;
}

.msg-assistant {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
}

/* Action bar — appears below last text block on hover / focus */
.msg-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s;
  padding-top: 2px;
}
.message-row:hover .msg-actions,
.message-row:focus-within .msg-actions { opacity: 1; }

/* Touch devices: always show action bar (no hover available) */
@media (hover: none) {
  .msg-actions { opacity: 1; }
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px; height: 28px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-card);
  cursor: pointer;
  color: var(--text-3);
  font-size: 14px;
  transition: background var(--transition-fast), color var(--transition-fast), border-color var(--transition-fast);
}
.action-btn:hover {
  background: var(--bg);
  color: var(--text-1);
  border-color: var(--text-4);
}

.streaming-cursor {
  display: inline-block;
  width: 8px;
  height: 15px;
  background: var(--primary);
  border-radius: 1px;
  animation: blink 1s step-end infinite;
  vertical-align: text-bottom;
  margin-left: 2px;
}
@keyframes blink { 50% { opacity: 0; } }

.agent-name-badge {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-color-primary);
  margin-bottom: 4px;
  padding-left: 2px;
  opacity: 0.85;
}

.msg-assistant.group-agent {
  border-left: 2px solid var(--el-color-primary-light-5);
  padding-left: 8px;
}
</style>
