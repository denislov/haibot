<template>
  <div class="contact-sidebar" :class="{ collapsed }">
    <!-- Header -->
    <div class="sidebar-header">
      <span class="sidebar-title">
        <span class="logo-hai">Hai</span><span class="logo-bot">Bot</span>
      </span>
      <button class="sidebar-toggle" @click="$emit('toggle')" :title="$t('chat.collapseSidebar')">
        <el-icon><Fold /></el-icon>
      </button>
    </div>

    <!-- Scrollable contact list -->
    <div class="cs-list">
      <!-- Agents section -->
      <div class="section-label">{{ $t('settings.agents.title') }}</div>
      <div
        v-for="agent in agents"
        :key="agent.id"
        class="cs-item"
        :class="{ active: selectedType === 'agent' && selectedId === agent.id }"
        @click="$emit('selectAgent', agent)"
      >
        <div class="avatar agent-avatar" :style="{ background: avatarColor(agent.id) }">
          {{ (agent.name.charAt(0) || '?').toUpperCase() }}
        </div>
        <span class="cs-item-name">{{ agent.name }}</span>
      </div>

      <!-- Group chats section -->
      <template v-if="groupChats.length > 0">
        <div class="section-label section-label--groups">{{ $t('chat.groupChats') }}</div>
        <div
          v-for="gc in groupChats"
          :key="gc.id"
          class="cs-item"
          :class="{ active: selectedType === 'group' && selectedId === gc.id }"
          @click="$emit('selectGroup', gc)"
        >
          <div class="avatar group-avatar">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          <span class="cs-item-name">{{ gc.name }}</span>
        </div>
      </template>
    </div>

    <!-- Footer -->
    <div class="sidebar-footer">
      <button class="footer-btn" @click="$emit('openSettings')" :title="$t('common.settings')">
        <el-icon><Setting /></el-icon>
        <span>{{ $t('common.settings') }}</span>
      </button>
      <button
        class="footer-btn theme-btn"
        @click="toggleTheme()"
        :title="isDark ? $t('theme.light') : $t('theme.dark')"
      >
        <el-icon v-if="isDark"><Sunny /></el-icon>
        <el-icon v-else><Moon /></el-icon>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AgentInfo } from '@/types'
import type { GroupChatConfig } from '@/types/group_chat'
import { useTheme } from '@/utils/useTheme'

const { isDark, toggleTheme } = useTheme()

defineProps<{
  agents: AgentInfo[]
  groupChats: GroupChatConfig[]
  selectedId: string | null
  selectedType: 'agent' | 'group' | null
  collapsed: boolean
}>()

defineEmits<{
  toggle: []
  selectAgent: [agent: AgentInfo]
  selectGroup: [gc: GroupChatConfig]
  openSettings: []
}>()

const AVATAR_COLORS = [
  '#5b5bd6',
  '#0ea5e9',
  '#10b981',
  '#f59e0b',
  '#ef4444',
  '#8b5cf6',
  '#ec4899',
  '#14b8a6',
]

function avatarColor(id: string): string {
  let hash = 0
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) & 0xffff
  return AVATAR_COLORS[hash % AVATAR_COLORS.length]
}
</script>

<style scoped>
.contact-sidebar {
  width: 220px;
  flex-shrink: 0;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width var(--transition-slow), opacity var(--transition-slow);
}

.contact-sidebar.collapsed {
  width: 0;
  opacity: 0;
  border-right: none;
  pointer-events: none;
  visibility: hidden;
}

/* Header */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 14px 10px;
  flex-shrink: 0;
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
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  cursor: pointer;
  color: var(--text-4);
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}
.sidebar-toggle:hover {
  background: var(--border);
  color: var(--text-2);
}

/* Scrollable list */
.cs-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 6px 8px;
}

/* Section labels */
.section-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 6px 8px 4px;
}

.section-label--groups {
  margin-top: 4px;
  border-top: 1px solid var(--border);
  padding-top: 10px;
}

/* Contact items */
.cs-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px;
  border-radius: var(--radius);
  cursor: pointer;
  transition: background var(--transition-fast);
  margin-bottom: 2px;
}
.cs-item:hover { background: var(--bg); }
.cs-item.active { background: var(--primary-light); }

/* Avatars */
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.agent-avatar {
  font-size: 13px;
  font-weight: 700;
  color: #ffffff;
}

.group-avatar {
  background: var(--border-strong);
  color: var(--text-2);
  font-size: 16px;
}

/* Item name */
.cs-item-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Footer */
.sidebar-footer {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 10px;
  border-top: 1px solid var(--border);
  margin-top: auto;
  flex-shrink: 0;
}

.footer-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px;
  border: none;
  background: none;
  cursor: pointer;
  color: var(--text-3);
  font-size: 13px;
  border-radius: var(--radius);
  transition: background var(--transition-fast), color var(--transition-fast);
}
.footer-btn:hover {
  background: var(--bg);
  color: var(--text-1);
}
.footer-btn .el-icon { font-size: 16px; }

.theme-btn {
  margin-left: auto;
  padding: 7px;
}
</style>
