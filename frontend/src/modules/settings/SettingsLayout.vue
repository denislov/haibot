<template>
  <div class="settings-layout">
    <!-- Left nav -->
    <aside class="settings-nav">
      <div class="nav-header">
        <button class="back-btn" @click="router.push('/chat')">
          <el-icon><ArrowLeft /></el-icon>
          <span>{{ $t('common.back') }}</span>
        </button>
      </div>

      <!-- Agent selector -->
      <div class="agent-switcher">
        <el-select
          v-model="settingsStore.selectedAgentId"
          size="small"
          style="width: 100%"
          @change="onAgentChange"
        >
          <el-option
            v-for="agent in settingsStore.agents"
            :key="agent.id"
            :label="agent.name"
            :value="agent.id"
          />
        </el-select>
      </div>

      <nav class="nav-list">
        <template v-for="group in navGroups" :key="group.key">
          <div class="nav-group">
            <button class="nav-group-header" @click="toggleGroup(group.key)">
              <el-icon><component :is="group.icon" /></el-icon>
              <span class="nav-group-label">{{ group.label }}</span>
              <el-icon class="nav-group-arrow" :class="{ collapsed: collapsedGroups[group.key] }"><ArrowUp /></el-icon>
            </button>
            <div v-show="!collapsedGroups[group.key]" class="nav-group-items">
              <router-link
                v-for="item in group.items"
                :key="item.path"
                :to="'/settings/' + item.path"
                class="nav-item"
              >
                <el-icon><component :is="item.icon" /></el-icon>
                <span>{{ item.label }}</span>
              </router-link>
            </div>
          </div>
        </template>
      </nav>

      <!-- Theme & Language at bottom -->
      <div class="nav-footer">
        <div class="footer-row">
          <el-icon v-if="isDark"><Moon /></el-icon>
          <el-icon v-else><Sunny /></el-icon>
          <el-select
            :model-value="themeMode"
            size="small"
            style="width: 100px"
            @change="setTheme"
          >
            <el-option value="light" :label="$t('theme.light')" />
            <el-option value="dark" :label="$t('theme.dark')" />
            <el-option value="system" :label="$t('theme.system')" />
          </el-select>
        </div>
        <div class="footer-row">
          <el-icon><Globe /></el-icon>
          <el-select
            :model-value="locale"
            size="small"
            style="width: 100px"
            @change="changeLocale"
          >
            <el-option value="zh-CN" :label="$t('language.zhCN')" />
            <el-option value="en" :label="$t('language.en')" />
          </el-select>
        </div>
      </div>
    </aside>

    <!-- Right content -->
    <main class="settings-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useTheme } from '@/utils/useTheme'
import { setLocale } from '@/i18n'
import { useSettingsStore } from '@/stores/settings'

const router = useRouter()
const { t, locale } = useI18n()
const { isDark, themeMode, setTheme } = useTheme()
const settingsStore = useSettingsStore()

function changeLocale(val: string) {
  setLocale(val as 'zh-CN' | 'en')
}

// Collapsible groups — all expanded by default
const collapsedGroups = reactive<Record<string, boolean>>({
  control: false,
  agent: false,
  settings: false,
})

function toggleGroup(key: string) {
  collapsedGroups[key] = !collapsedGroups[key]
}

function onAgentChange() {
  // The store's watch already updates the X-Agent-Id header.
  // Reload the current page by emitting a route replace to force re-fetch.
  const currentPath = router.currentRoute.value.fullPath
  router.replace('/settings').then(() => router.replace(currentPath))
}

const navGroups = computed(() => [
  {
    key: 'control',
    label: t('settings.navGroup.control'),
    icon: 'Promotion',
    items: [
      { path: 'channels', label: t('settings.channels.title'), icon: 'Connection' },
      { path: 'sessions', label: t('settings.sessions.title'), icon: 'UserFilled' },
      { path: 'crons', label: t('settings.crons.title'), icon: 'AlarmClock' },
      { path: 'heartbeat', label: t('settings.heartbeat.title'), icon: 'Odometer' },
      { path: 'group-chats', label: t('settings.groupChats.title'), icon: 'ChatDotRound' },
    ],
  },
  {
    key: 'agent',
    label: t('settings.navGroup.agent'),
    icon: 'Lightning',
    items: [
      { path: 'workspace', label: t('settings.workspace.title'), icon: 'Suitcase' },
      { path: 'skills', label: t('settings.skills.title'), icon: 'MagicStick' },
      { path: 'tools', label: t('settings.tools.title'), icon: 'SetUp' },
      { path: 'mcp', label: t('settings.mcp.title'), icon: 'Link' },
      { path: 'running-config', label: t('settings.runningConfig.title'), icon: 'Setting' },
    ],
  },
  {
    key: 'settings',
    label: t('settings.navGroup.settings'),
    icon: 'Setting',
    items: [
      { path: 'agents', label: t('settings.agents.title'), icon: 'Avatar' },
      { path: 'models', label: t('settings.models.title'), icon: 'Box' },
      { path: 'envs', label: t('settings.envs.title'), icon: 'Setting' },
      { path: 'security', label: t('settings.security.title'), icon: 'Lock' },
      { path: 'token-usage', label: t('settings.tokenUsage.title'), icon: 'DataAnalysis' },
    ],
  },
])

onMounted(() => {
  if (!settingsStore.loaded) {
    settingsStore.loadAgents()
  }
})
</script>

<style scoped>
.settings-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--bg);
}

/* ── Nav ── */
.settings-nav {
  width: 240px;
  flex-shrink: 0;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 16px 12px;
}

.nav-header { margin-bottom: 12px; }

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: none; background: none;
  cursor: pointer; color: var(--text-3);
  font-size: 13px;
  border-radius: var(--radius);
  transition: background var(--transition-fast);
}
.back-btn:hover { background: var(--bg); color: var(--text-1); }
.back-btn .el-icon { font-size: 14px; }

/* ── Agent switcher ── */
.agent-switcher {
  padding: 0 4px;
  margin-bottom: 16px;
}

/* ── Nav groups ── */
.nav-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-group {
  margin-bottom: 4px;
}

.nav-group-header {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 8px 10px;
  border: none;
  background: none;
  cursor: pointer;
  color: var(--primary-text);
  font-size: 13px;
  font-weight: 600;
  border-radius: var(--radius);
  transition: background var(--transition-fast);
}
.nav-group-header:hover { background: var(--bg); }
.nav-group-header .el-icon:first-child { font-size: 15px; }

.nav-group-label { flex: 1; text-align: left; }

.nav-group-arrow {
  font-size: 12px !important;
  color: var(--text-4);
  transition: transform 0.2s;
}
.nav-group-arrow.collapsed { transform: rotate(180deg); }

.nav-group-items {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding-left: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: var(--radius);
  color: var(--text-2);
  text-decoration: none;
  font-size: 13px;
  transition: background var(--transition-fast);
}
.nav-item:hover { background: var(--bg); }
.nav-item.router-link-active {
  background: var(--primary-light);
  color: var(--primary-text);
  font-weight: 500;
}
.nav-item .el-icon { font-size: 15px; }

.nav-footer {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.footer-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 8px;
  color: var(--text-3);
}
.footer-row .el-icon { font-size: 15px; }

/* ── Content ── */
.settings-content {
  flex: 1;
  overflow-y: auto;
  padding: 28px;
}
</style>
