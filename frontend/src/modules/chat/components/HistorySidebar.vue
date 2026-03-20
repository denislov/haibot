<template>
  <div class="history-sidebar" :class="{ collapsed }">
    <!-- Header -->
    <div class="hs-header">
      <span class="hs-title">{{ $t('chat.history') }}</span>
      <button class="hs-toggle" @click="$emit('toggle')" :title="$t('chat.collapseSidebar')">
        <el-icon><Fold /></el-icon>
      </button>
    </div>

    <!-- Scrollable list -->
    <div class="hs-list">
      <!-- Empty state -->
      <div v-if="groups.length === 0" class="hs-empty">
        {{ $t('chat.noHistory') }}
      </div>

      <!-- Grouped chat list -->
      <template v-else>
        <template v-for="group in groups" :key="group.label">
          <div class="hs-divider">{{ group.label }}</div>
          <div
            v-for="chat in group.chats"
            :key="chat.id"
            class="hs-item"
            :class="{ active: activeChatId === chat.id, 'is-group': !!chat.meta?.group_id }"
            @click="$emit('selectChat', chat)"
          >
            <div class="hs-item-inner">
              <div class="hs-item-name">{{ chat.name }}</div>
              <div v-if="chat.meta?.preview" class="hs-item-preview">{{ chat.meta?.preview }}</div>
            </div>
            <el-dropdown
              trigger="click"
              @command="(cmd: string) => $emit('chatAction', cmd, chat)"
              @click.stop
            >
              <el-icon class="hs-more"><More /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="rename">{{ $t('chat.rename') }}</el-dropdown-item>
                  <el-dropdown-item command="delete" class="danger-item">{{ $t('common.delete') }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ChatSpec } from '@/types'

const { t, locale } = useI18n()

const props = defineProps<{
  chats: ChatSpec[]
  activeChatId: string | null
  collapsed: boolean
}>()

defineEmits<{
  toggle: []
  selectChat: [chat: ChatSpec]
  chatAction: [cmd: string, chat: ChatSpec]
}>()

interface Group {
  label: string
  chats: ChatSpec[]
}

const groups = computed((): Group[] => {
  const sorted = [...props.chats]
    .filter((c) => !c.meta?._isTemp)
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())

  if (sorted.length === 0) return []

  const now = new Date()
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const ms7 = 7 * 24 * 60 * 60 * 1000
  const ms30 = 30 * 24 * 60 * 60 * 1000

  const buckets = new Map<string, ChatSpec[]>()

  function bucketLabel(chat: ChatSpec): string {
    const d = new Date(chat.updated_at)
    const startOfDay = new Date(d.getFullYear(), d.getMonth(), d.getDate())
    const diff = startOfToday.getTime() - startOfDay.getTime()
    if (diff <= 0) return t('chat.timeToday')
    if (diff <= ms7) return t('chat.time7days')
    if (diff < ms30) return t('chat.time30days')
    return d.toLocaleDateString(locale.value, { year: 'numeric', month: 'long' })
  }

  for (const chat of sorted) {
    const label = bucketLabel(chat)
    if (!buckets.has(label)) buckets.set(label, [])
    buckets.get(label)!.push(chat)
  }

  return [...buckets.entries()].map(([label, chats]) => ({ label, chats }))
})

</script>

<style scoped>
.history-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: var(--bg-sidebar);
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width var(--transition-slow), opacity var(--transition-slow);
}

.history-sidebar.collapsed {
  width: 0;
  opacity: 0;
  border-left: none;
  pointer-events: none;
  visibility: hidden;
}

.hs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 14px 10px;
  flex-shrink: 0;
}

.hs-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-2);
}

.hs-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  cursor: pointer;
  color: var(--text-4);
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}

.hs-toggle:hover {
  background: var(--border);
  color: var(--text-2);
}

.hs-toggle :deep(.el-icon) {
  transform: rotate(180deg);
}

.hs-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 6px 8px;
}

.hs-empty {
  padding: 24px 8px;
  text-align: center;
  font-size: 12px;
  color: var(--text-4);
}

.hs-divider {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-4);
  padding: 10px 8px 4px;
  letter-spacing: 0.3px;
}

.hs-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 7px 8px;
  border-radius: var(--radius);
  cursor: pointer;
  transition: background var(--transition-fast);
  margin-bottom: 1px;
}

.hs-item:hover {
  background: var(--bg);
}

.hs-item.active {
  background: var(--primary-light);
}

.hs-item.is-group {
  border-left: 2px solid var(--primary);
  padding-left: 6px;
}

.hs-item-inner {
  flex: 1;
  min-width: 0;
}

.hs-item-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hs-item-preview {
  font-size: 11px;
  color: var(--text-4);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.hs-more {
  flex-shrink: 0;
  color: var(--text-4);
  font-size: 16px;
  padding: 2px;
  border-radius: 4px;
  cursor: pointer;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.hs-item:hover .hs-more,
.hs-item.active .hs-more {
  opacity: 1;
}

.hs-more:hover {
  color: var(--text-2);
  background: var(--border);
}

:deep(.danger-item) {
  color: var(--error) !important;
}
</style>
