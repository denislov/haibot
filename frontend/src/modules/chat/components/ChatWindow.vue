<template>
  <div ref="messagesEl" class="chat-window" @scroll.passive="onScroll">
    <div class="chat-content-track content-track">
      <div v-if="messages.length === 0" class="chat-empty-state">
        <p>{{ $t('chat.emptyState') }}</p>
      </div>
      <template v-else>
        <MessageBubble
          v-for="msg in messages"
          :key="msg.id"
          :message="msg"
        />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import type { DisplayMessage } from '@/types'
import MessageBubble from './MessageBubble.vue'

const props = defineProps<{
  messages: DisplayMessage[]
}>()

const messagesEl = ref<HTMLDivElement | null>(null)
const isNearBottom = ref(true)
const SCROLL_THRESHOLD = 80 // px from bottom to be considered "at bottom"

function onScroll() {
  if (!messagesEl.value) return
  const { scrollTop, scrollHeight, clientHeight } = messagesEl.value
  isNearBottom.value = scrollHeight - scrollTop - clientHeight < SCROLL_THRESHOLD
}

/** Always scrolls to bottom — use for history loads and initial render. */
function scrollToBottom() {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight
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
</style>
