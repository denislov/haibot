<template>
  <div ref="messagesEl" class="chat-window">
    <div class="chat-content-track">
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

function scrollToBottom() {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    }
  })
}

// Auto-scroll when messages change
watch(() => props.messages.length, scrollToBottom)

defineExpose({ scrollToBottom })
</script>

<style scoped>
.chat-window {
  flex: 1;
  overflow-y: auto;
  padding: 24px 16px;
}

/* Centered content track — responsive width like GPT */
.chat-content-track {
  max-width: 768px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Responsive: wider margins on larger screens */
@media (min-width: 1200px) {
  .chat-content-track { max-width: 800px; }
}
@media (min-width: 1600px) {
  .chat-content-track { max-width: 860px; }
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
