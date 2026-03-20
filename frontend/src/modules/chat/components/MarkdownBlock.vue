<template>
  <div class="md-content" v-html="renderedHtml" />
</template>

<script setup lang="ts">
import { computed, toRef } from 'vue'
import { refThrottled } from '@vueuse/core'
import { renderMarkdown } from '@/utils/useMarkdown'

const props = defineProps<{
  text: string
}>()

const textRef = toRef(props, 'text')
// Throttle updates to 60ms to prevent heavy markdown parsing from blocking the main thread during stream
const throttledText = refThrottled(textRef, 60)

const renderedHtml = computed(() => {
  return renderMarkdown(throttledText.value || '')
})
</script>
