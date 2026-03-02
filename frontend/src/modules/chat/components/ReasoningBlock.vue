<template>
  <div class="reasoning-block">
    <button class="reasoning-header" @click="$emit('toggle')">
      <el-icon class="reasoning-icon"><ChatLineRound /></el-icon>
      <span class="reasoning-label">{{ $t('chat.thinking') }}</span>
      <el-icon class="reasoning-chevron" :class="{ open: expanded }"><ArrowDown /></el-icon>
    </button>
    <div v-if="expanded" class="reasoning-body">
      <MarkdownBlock class="reasoning-text" :text="text || ''" />
    </div>
  </div>
</template>

<script setup lang="ts">
import MarkdownBlock from './MarkdownBlock.vue'

defineProps<{
  text?: string
  expanded?: boolean
}>()

defineEmits<{ toggle: [] }>()
</script>

<style scoped>
.reasoning-block {
  border: 1px solid var(--primary-light);
  border-radius: var(--radius);
  overflow: hidden;
  background: var(--primary-light);
  font-size: 13px;
}

.reasoning-header {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 7px 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
  color: var(--primary);
  transition: background var(--transition-fast);
}
.reasoning-header:hover { background: var(--primary-light); }

.reasoning-icon { font-size: 13px; color: var(--primary); opacity: 0.7; }
.reasoning-label {
  flex: 1;
  font-size: 12px;
  font-weight: 500;
  color: var(--primary);
}

.reasoning-chevron {
  font-size: 12px !important;
  color: var(--primary);
  opacity: 0.5;
  transition: transform 0.2s;
}
.reasoning-chevron.open { transform: rotate(180deg); }

.reasoning-body {
  padding: 8px 12px 10px;
  border-top: 1px solid var(--primary-light);
}

.reasoning-text { font-size: 13px; color: var(--text-3); }
</style>
