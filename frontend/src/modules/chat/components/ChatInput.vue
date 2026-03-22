<template>
  <div class="input-area">
    <div class="input-track content-track">
      <div
        class="input-box-wrap"
        :class="{ dragging: isDragging }"
        @dragover.prevent="isDragging = true"
        @dragenter.prevent="isDragging = true"
        @dragleave="isDragging = false"
        @drop.prevent="onDrop"
      >
        <textarea
          ref="textareaEl"
          :value="modelValue"
          class="chat-textarea"
          :placeholder="$t('chat.inputPlaceholder')"
          rows="1"
          @input="onInput"
          @keydown.enter.exact.prevent="$emit('send')"
          @paste="onPaste"
        />
        <!-- Attachment preview bar -->
        <div v-if="attachments.length > 0" class="attachment-bar">
          <div v-for="att in attachments" :key="att.id" class="att-item">
            <img v-if="att.previewUrl" :src="att.previewUrl" class="att-thumb" />
            <span v-else class="att-file-chip">
              <el-icon><Document /></el-icon>
              <span class="att-file-name">{{ att.name }}</span>
            </span>
            <span v-if="att.uploading" class="att-spinner">
              <el-icon class="spin"><Loading /></el-icon>
            </span>
            <span v-if="att.error" class="att-error-dot" />
            <button class="att-remove" @click="$emit('removeAttachment', att.id)">&times;</button>
          </div>
        </div>
        <div class="input-footer">
          <div class="footer-left">
            <button class="attach-btn" :title="$t('chat.attachFile')" @click="fileInput?.click()">
              <el-icon><Paperclip /></el-icon>
            </button>
            <input
              ref="fileInput"
              type="file"
              multiple
              accept="image/*,application/pdf,.txt,.md,.csv,.json,.yaml,.yml,.xml"
              class="hidden-file-input"
              @change="onFileSelect"
            />
          </div>
          <div class="footer-right">
            <span class="char-count">{{ (modelValue || '').length }}/10000</span>
            <button v-if="streaming" class="stop-btn" :title="$t('chat.stop')" @click="$emit('stop')">
              <el-icon><VideoPause /></el-icon>
            </button>
            <button v-else class="send-btn" :disabled="!(modelValue || '').trim() && attachments.length === 0" @click="$emit('send')">
              <el-icon><Promotion /></el-icon>
            </button>
          </div>
        </div>
      </div>
      <div class="chat-tagline">{{ $t('chat.tagline') }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { FileAttachment } from '@/types'

const props = defineProps<{
  modelValue: string
  streaming: boolean
  attachments: FileAttachment[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  send: []
  stop: []
  addFiles: [files: File[]]
  removeAttachment: [id: string]
}>()

const textareaEl = ref<HTMLTextAreaElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)

function onInput(e: Event) {
  const target = e.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
  autoResize()
}

function autoResize() {
  if (textareaEl.value) {
    textareaEl.value.style.height = 'auto'
    textareaEl.value.style.height = Math.min(textareaEl.value.scrollHeight, 200) + 'px'
  }
}

// Reset height when value is cleared
watch(() => props.modelValue, (val) => {
  if (!val) {
    nextTick(autoResize)
  }
})

function onFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) {
    emit('addFiles', Array.from(input.files))
    input.value = ''
  }
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  if (e.dataTransfer?.files.length) {
    emit('addFiles', Array.from(e.dataTransfer.files))
  }
}

function onPaste(e: ClipboardEvent) {
  const files = e.clipboardData?.files
  if (files?.length) {
    e.preventDefault()
    emit('addFiles', Array.from(files))
  }
}

defineExpose({ focus: () => textareaEl.value?.focus() })
</script>

<style scoped>
.input-area {
  flex-shrink: 0;
  padding: 0 16px 12px;
  background: transparent;
}

/* Same centered track as ChatWindow — breakpoints in style.css */
.input-track { }

.input-box-wrap {
  position: relative;
  border: 1px solid var(--border);
  border-radius: 24px;
  background: var(--bg-card);
  overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-shadow: var(--shadow-sm);
}
.input-box-wrap:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(91, 91, 214, 0.08), var(--shadow-sm);
}
.input-box-wrap.dragging {
  border-color: var(--primary);
  background: var(--primary-light);
}

.chat-textarea {
  width: 100%;
  min-height: 44px;
  max-height: 200px;
  padding: 12px 16px 4px;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-1);
  background: transparent;
  font-family: inherit;
}

/* ── Attachment preview bar ── */
.attachment-bar {
  display: flex;
  gap: 8px;
  padding: 8px 16px;
  overflow-x: auto;
}

.att-item {
  position: relative;
  flex-shrink: 0;
}

.att-thumb {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid var(--border);
}

.att-file-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-2);
  max-width: 120px;
}

.att-file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.att-spinner {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.6);
  border-radius: 6px;
}
[data-theme="dark"] .att-spinner { background: rgba(0,0,0,0.4); }

.att-spinner .spin {
  animation: att-spin 1s linear infinite;
  font-size: 16px;
  color: var(--primary);
}
@keyframes att-spin { to { transform: rotate(360deg); } }

.att-error-dot {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--error);
}

.att-remove {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: none;
  background: var(--text-4);
  color: white;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity var(--transition-fast);
}
.att-item:hover .att-remove { opacity: 1; }

/* ── Footer ── */
.input-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px 8px;
}

.footer-left {
  display: flex;
  align-items: center;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.attach-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  color: var(--text-3);
  font-size: 18px;
  transition: background var(--transition-fast), color var(--transition-fast);
}
.attach-btn:hover {
  background: var(--bg);
  color: var(--text-1);
}

.hidden-file-input {
  display: none;
}

.char-count { font-size: 11px; color: var(--text-4); }

.send-btn, .stop-btn {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  border: none; border-radius: 50%;
  cursor: pointer;
  transition: background var(--transition-fast), opacity var(--transition-fast);
}
.send-btn { background: var(--primary); color: white; }
.send-btn:hover { background: var(--primary-hover); }
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.stop-btn { background: var(--error-light); color: var(--error); }
.stop-btn:hover { opacity: 0.8; }
.send-btn .el-icon, .stop-btn .el-icon { font-size: 16px; }

.chat-tagline {
  text-align: center;
  font-size: 11px;
  color: var(--text-4);
  margin-top: 6px;
}
</style>
