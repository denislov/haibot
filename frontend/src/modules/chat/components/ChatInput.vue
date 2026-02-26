<template>
  <div class="input-area">
    <div class="input-track">
      <div class="input-box-wrap">
        <textarea
          ref="textareaEl"
          :value="modelValue"
          class="chat-textarea"
          :placeholder="$t('chat.inputPlaceholder')"
          rows="1"
          @input="onInput"
          @keydown.enter.exact.prevent="$emit('send')"
        />
        <div class="input-footer">
          <span class="char-count">{{ (modelValue || '').length }}/10000</span>
          <button v-if="streaming" class="stop-btn" :title="$t('chat.stop')" @click="$emit('stop')">
            <el-icon><VideoPause /></el-icon>
          </button>
          <button v-else class="send-btn" :disabled="!(modelValue || '').trim()" @click="$emit('send')">
            <el-icon><Promotion /></el-icon>
          </button>
        </div>
      </div>
      <div class="chat-tagline">{{ $t('chat.tagline') }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

const props = defineProps<{
  modelValue: string
  streaming: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  send: []
  stop: []
}>()

const textareaEl = ref<HTMLTextAreaElement | null>(null)

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

defineExpose({ focus: () => textareaEl.value?.focus() })
</script>

<style scoped>
.input-area {
  flex-shrink: 0;
  padding: 0 16px 12px;
  background: transparent;
}

/* Same centered track as ChatWindow */
.input-track {
  max-width: 768px;
  margin: 0 auto;
}

@media (min-width: 1200px) {
  .input-track { max-width: 800px; }
}
@media (min-width: 1600px) {
  .input-track { max-width: 860px; }
}

.input-box-wrap {
  position: relative;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-shadow: var(--shadow-sm);
}
.input-box-wrap:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(91, 91, 214, 0.08);
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

.input-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 4px 8px 8px;
  gap: 8px;
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
