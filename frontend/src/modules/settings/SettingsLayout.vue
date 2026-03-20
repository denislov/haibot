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
      <h2 class="nav-title">{{ $t('common.settings') }}</h2>
      <nav class="nav-list">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="'/settings/' + item.path"
          class="nav-item"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
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
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useTheme } from '@/utils/useTheme'
import { setLocale } from '@/i18n'

const router = useRouter()
const { t, locale } = useI18n()
const { isDark, themeMode, setTheme } = useTheme()

function changeLocale(val: string) {
  setLocale(val as 'zh-CN' | 'en')
}

const navItems = computed(() => [
  { path: 'models', label: t('settings.models.title'), icon: 'Box' },
  { path: 'mcp', label: t('settings.mcp.title'), icon: 'Link' },
  { path: 'agents', label: t('settings.agents.title'), icon: 'Avatar' },
  { path: 'channels', label: t('settings.channels.title'), icon: 'Connection' },
  { path: 'sessions', label: t('settings.sessions.title'), icon: 'UserFilled' },
  { path: 'workspace', label: t('settings.workspace.title'), icon: 'Suitcase' },
  { path: 'skills', label: t('settings.skills.title'), icon: 'MagicStick' },
  { path: 'envs', label: t('settings.envs.title'), icon: 'Setting' },
  { path: 'crons', label: t('settings.crons.title'), icon: 'AlarmClock' },
  { path: 'group-chats', label: t('settings.groupChats.title'), icon: 'ChatDotRound' },
])
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

.nav-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-1);
  padding: 0 8px;
  margin-bottom: 12px;
}

.nav-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
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
