<template>
  <div ref="messagesEl" class="chat-window" @scroll.passive="onScroll">
    <div class="chat-content-track content-track">
      <div v-if="messages.length === 0" class="chat-empty-state">
        <p>{{ $t('chat.emptyState') }}</p>
      </div>
      <template v-else>
        <MessageBubble
          v-for="(msg, idx) in messages"
          :key="msg.id"
          :message="msg"
          :is-last="msg.role === 'assistant' && isLastAssistant(idx)"
          :is-streaming="streaming"
          :allow-regenerate="allowRegenerate"
          @regenerate="$emit('regenerate')"
        />
      </template>
    </div>

    <!-- Scroll to bottom button -->
    <Transition name="fade-btn">
      <button
        v-if="!isNearBottom && messages.length > 0"
        class="scroll-bottom-btn"
        :title="$t('chat.scrollToBottom')"
        @click="scrollToBottom()"
      >
        <el-icon><ArrowDown /></el-icon>
      </button>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import type { DisplayMessage } from '@/types'
import MessageBubble from './MessageBubble.vue'

const props = defineProps<{
  messages: DisplayMessage[]
  streaming?: boolean
  allowRegenerate?: boolean
}>()

defineEmits<{ regenerate: [] }>()

const messagesEl = ref<HTMLDivElement | null>(null)
const isNearBottom = ref(true)
const SCROLL_THRESHOLD = 80 // px from bottom to be considered "at bottom"

function onScroll() {
  if (!messagesEl.value) return
  const { scrollTop, scrollHeight, clientHeight } = messagesEl.value
  isNearBottom.value = scrollHeight - scrollTop - clientHeight < SCROLL_THRESHOLD
}

function isLastAssistant(idx: number): boolean {
  for (let i = props.messages.length - 1; i >= 0; i--) {
    if (props.messages[i].role === 'assistant') return i === idx
  }
  return false
}

/** Always scrolls to bottom — use for history loads and initial render. */
function scrollToBottom() {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTo({ top: messagesEl.value.scrollHeight, behavior: 'smooth' })
      isNearBottom.value = true
    }
  })
}

/** Only scrolls if the user hasn't scrolled up — use during streaming. */
function scrollIfNearBottom() {
  if (isNearBottom.value) scrollToBottom()
}

// Force-scroll when a new message turn is added (count changes)
watch(() => props.messages.length, scrollToBottom)

defineExpose({ scrollToBottom, scrollIfNearBottom })
</script>

<style scoped>
.chat-window {
  flex: 1;
  overflow-y: auto;
  padding: 24px 16px;
  position: relative;
}

/* Centered content track — responsive width (breakpoints in style.css) */
.chat-content-track {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.chat-empty-state {
  padding: 120px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-4);
  font-size: 14px;
}

/* ── Scroll to bottom button ── */
.scroll-bottom-btn {
  position: sticky;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--bg-card);
  cursor: pointer;
  color: var(--text-3);
  box-shadow: var(--shadow-md);
  transition: background var(--transition-fast), color var(--transition-fast);
  z-index: 10;
}
.scroll-bottom-btn:hover {
  background: var(--bg);
  color: var(--text-1);
}

.fade-btn-enter-active,
.fade-btn-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.fade-btn-enter-from,
.fade-btn-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(8px);
}
</style>
