<template>
  <div class="chat-sidebar" :class="{ collapsed }">
    <!-- Header -->
    <div class="sidebar-header">
      <span class="sidebar-title">
        <span class="logo-hai">Hai</span><span class="logo-bot">Bot</span>
      </span>
      <button class="sidebar-toggle" @click="$emit('toggle')">
        <el-icon><Fold /></el-icon>
      </button>
    </div>

    <!-- New chat button -->
    <button class="new-chat-btn" @click="$emit('newChat')">
      <el-icon><Plus /></el-icon>
      {{ $t('chat.newChat') }}
    </button>

    <!-- Chat list -->
    <div class="chat-items">
      <div
        v-for="chat in chats"
        :key="chat.id"
        class="chat-item"
        :class="{ active: activeChatId === chat.id }"
        @click="$emit('selectChat', chat)"
      >
        <div class="chat-item-content">
          <div class="chat-item-name">{{ chat.name }}</div>
          <div class="chat-item-preview">{{ getPreview(chat) }}</div>
        </div>
        <el-dropdown
          trigger="click"
          @command="(cmd: string) => $emit('chatAction', cmd, chat)"
          @click.stop
        >
          <el-icon class="chat-item-more"><More /></el-icon>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="rename">{{ $t('chat.rename') }}</el-dropdown-item>
              <el-dropdown-item command="delete" class="danger-item">{{ $t('common.delete') }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- Bottom bar: settings + theme -->
    <div class="sidebar-footer">
      <button class="footer-btn" @click="$emit('openSettings')" :title="$t('common.settings')">
        <el-icon><Setting /></el-icon>
        <span>{{ $t('common.settings') }}</span>
      </button>
      <button class="footer-btn theme-btn" @click="toggleTheme()" :title="isDark ? $t('theme.light') : $t('theme.dark')">
        <el-icon v-if="isDark"><Sunny /></el-icon>
        <el-icon v-else><Moon /></el-icon>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ChatSpec } from '@/types'
import { useTheme } from '@/utils/useTheme'

const { isDark, toggleTheme } = useTheme()

defineProps<{
  chats: ChatSpec[]
  activeChatId: string | null
  collapsed: boolean
}>()

defineEmits<{
  toggle: []
  newChat: []
  selectChat: [chat: ChatSpec]
  chatAction: [cmd: string, chat: ChatSpec]
  openSettings: []
}>()

function getPreview(chat: ChatSpec): string {
  return (chat.meta?.preview as string) || ''
}
</script>

<style scoped>
.chat-sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width var(--transition-slow), opacity var(--transition-slow);
}
.chat-sidebar.collapsed {
  width: 0;
  opacity: 0;
  border-right: none;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 14px 10px;
}

.sidebar-title {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.5px;
}
.logo-hai { color: var(--primary); }
.logo-bot { color: var(--text-1); }

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px; height: 28px;
  border: none; background: none;
  cursor: pointer; color: var(--text-4);
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}
.sidebar-toggle:hover { background: var(--border); color: var(--text-2); }

.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin: 0 10px 10px;
  padding: 8px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-size: 13px; font-weight: 500;
  cursor: pointer;
  transition: background var(--transition-fast);
}
.new-chat-btn:hover { background: var(--primary-hover); }

.chat-items {
  flex: 1;
  overflow-y: auto;
  padding: 0 6px 8px;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px;
  border-radius: var(--radius);
  cursor: pointer;
  transition: background var(--transition-fast);
  margin-bottom: 2px;
}
.chat-item:hover { background: var(--bg); }
.chat-item.active { background: var(--primary-light); }

.chat-item-content { flex: 1; min-width: 0; }
.chat-item-name {
  font-size: 13px; font-weight: 500; color: var(--text-1);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.chat-item-preview {
  font-size: 12px; color: var(--text-4);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  margin-top: 2px;
}

.chat-item-more {
  flex-shrink: 0; color: var(--text-4);
  font-size: 16px; padding: 2px;
  border-radius: 4px; cursor: pointer;
  opacity: 0;
  transition: opacity var(--transition-fast);
}
.chat-item:hover .chat-item-more,
.chat-item.active .chat-item-more { opacity: 1; }
.chat-item-more:hover { color: var(--text-2); background: var(--border); }

/* Footer */
.sidebar-footer {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 10px;
  border-top: 1px solid var(--border);
}

.footer-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px;
  border: none; background: none;
  cursor: pointer;
  color: var(--text-3);
  font-size: 13px;
  border-radius: var(--radius);
  transition: background var(--transition-fast), color var(--transition-fast);
}
.footer-btn:hover { background: var(--bg); color: var(--text-1); }
.footer-btn .el-icon { font-size: 16px; }

.theme-btn { margin-left: auto; padding: 7px; }

:deep(.danger-item) { color: var(--error) !important; }
</style>
