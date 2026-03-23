<template>
  <div class="message-row" :class="message.role">
    <!-- User message -->
    <template v-if="message.role === 'user'">
      <div class="msg-user">
        <div class="msg-sender-label">You</div>
        <!-- Attachments -->
        <div v-if="message.attachments?.length" class="msg-attachments">
          <template v-for="att in message.attachments" :key="att.url">
            <a
              v-if="att.type.startsWith('image/')"
              :href="att.url"
              target="_blank"
              class="msg-att-img-link"
            >
              <img :src="att.url" :alt="att.name" class="msg-att-img" />
            </a>
            <span v-else class="msg-att-file">
              <el-icon><Document /></el-icon>
              {{ att.name }}
            </span>
          </template>
        </div>
        <MarkdownBlock
          v-if="message.blocks[0]?.text"
          class="msg-user-markdown"
          :text="message.blocks[0]?.text || ''"
        />
      </div>
    </template>

    <!-- Assistant message -->
    <template v-else>
      <!-- Agent name badge (always shown) -->
      <div class="agent-name-badge">
        {{ message.agentName || 'Assistant' }}
      </div>
      <div class="msg-assistant" :class="{ 'group-agent': message.agentId }">
        <!-- Typing indicator (waiting for first content) -->
        <div v-if="message.streaming && message.blocks.length === 0" class="typing-indicator">
          <span class="dot" /><span class="dot" /><span class="dot" />
        </div>

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
            :streaming="message.streaming"
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

        <!-- Action bar -->
        <div v-if="!message.streaming && hasContent" class="msg-actions" :class="{ 'always-visible': isLast }">
          <button class="action-btn" :title="$t('common.copy')" @click="copyMessage">
            <el-icon v-if="!copied"><CopyDocument /></el-icon>
            <el-icon v-else><Select /></el-icon>
          </button>
          <button
            v-if="isLast && !isStreaming"
            class="action-btn"
            :title="$t('chat.regenerate')"
            @click="$emit('regenerate')"
          >
            <el-icon><RefreshRight /></el-icon>
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
  isLast?: boolean
  isStreaming?: boolean
}>()

defineEmits<{ regenerate: [] }>()

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
@keyframes messageEntryFade {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-row {
  display: flex;
  flex-direction: column;
  animation: messageEntryFade var(--transition-message) both;
}

/* ── User message ── */
.msg-user {
  align-self: flex-end;
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: fit-content;
  max-width: min(720px, calc(100% - 56px));
  margin-left: 56px;
  background: var(--bg-user-message);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  font-size: 15px;
  line-height: 1.6;
  word-break: break-word;
}

.msg-user :deep(.md-content) {
  color: inherit;
}

.msg-user :deep(.md-content > *:first-child) {
  margin-top: 0;
}

.msg-user :deep(.md-content > *:last-child) {
  margin-bottom: 0;
}

.msg-sender-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-4);
  text-align: right;
}

/* ── User attachments ── */
.msg-attachments {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.msg-att-img-link { display: inline-block; }
.msg-att-img {
  max-width: 200px;
  max-height: 200px;
  border-radius: 8px;
  object-fit: cover;
  cursor: pointer;
  transition: opacity var(--transition-fast);
}
.msg-att-img:hover { opacity: 0.85; }

.msg-att-file {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 12px;
  color: var(--text-2);
}

/* ── Assistant message ── */
.msg-assistant {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
}

/* ── Typing indicator ── */
@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-4);
  animation: typingBounce 1.2s infinite;
}
.typing-indicator .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator .dot:nth-child(3) { animation-delay: 0.4s; }

/* ── Action bar ── */
.msg-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s;
  padding-top: 2px;
}
.msg-actions.always-visible { opacity: 1; }
.message-row:hover .msg-actions,
.message-row:focus-within .msg-actions { opacity: 1; }

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
  color: var(--el-color-primary, var(--primary));
  margin-bottom: 4px;
  padding-left: 2px;
  opacity: 0.85;
}

.msg-assistant.group-agent {
  border-left: 2px solid var(--el-color-primary-light-5, var(--primary-light));
  padding-left: 8px;
}
</style>
