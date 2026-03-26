<template>
  <div class="media-block">
    <a
      v-if="kind === 'image' && url"
      :href="url"
      target="_blank"
      rel="noreferrer"
      class="media-block__image-link"
    >
      <img :src="url" :alt="name || 'Image output'" class="media-block__image" />
    </a>

    <audio
      v-else-if="kind === 'audio' && url"
      class="media-block__player"
      controls
      preload="metadata"
      :src="url"
    />

    <video
      v-else-if="kind === 'video' && url"
      class="media-block__video"
      controls
      preload="metadata"
      :src="url"
    />

    <div v-if="name || formatLabel" class="media-block__meta">
      <span v-if="name" class="media-block__name">{{ name }}</span>
      <span v-if="formatLabel" class="media-block__format">{{ formatLabel }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  kind: 'image' | 'audio' | 'video'
  url?: string
  format?: string
  name?: string
}>()

const formatLabel = computed(() => props.format?.toUpperCase() || '')
</script>

<style scoped>
.media-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.media-block__image-link {
  display: inline-flex;
  width: fit-content;
  max-width: 100%;
}

.media-block__image {
  display: block;
  max-width: min(100%, 420px);
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--bg-soft);
  object-fit: cover;
}

.media-block__player,
.media-block__video {
  width: min(100%, 420px);
  max-width: 100%;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--bg-soft);
}

.media-block__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--text-3);
}

.media-block__name {
  font-weight: 600;
  color: var(--text-2);
}

.media-block__format {
  padding: 2px 6px;
  border-radius: 999px;
  background: var(--bg);
  border: 1px solid var(--border);
}
</style>
