<template>
  <div class="settings-layout">
    <!-- Left nav -->
    <aside class="settings-nav" :class="{ 'mobile-open': isMobile && mobileNavOpen }">
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
                @click="handleNavItemClick"
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
        <div v-if="authStore.enabled" class="account-box">
          <div class="account-label">
            {{ authStore.isAuthenticated ? authStore.username : $t('auth.localBypass') }}
          </div>
          <div class="account-hint">
            {{
              authStore.isAuthenticated
                ? $t('settings.security.accountDesc')
                : $t('auth.localBypassDesc')
            }}
          </div>
          <div class="account-actions">
            <el-button size="small" text @click="openAccountSettings">
              {{ authStore.isAuthenticated ? $t('settings.security.account') : $t('auth.signIn') }}
            </el-button>
            <el-button
              v-if="authStore.isAuthenticated"
              size="small"
              text
              type="danger"
              @click="authStore.logout"
            >
              {{ $t('auth.logout') }}
            </el-button>
          </div>
        </div>
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

    <div
      v-if="isMobile && mobileNavOpen"
      class="nav-backdrop"
      @click="closeMobileNav"
    />

    <!-- Right content -->
    <main class="settings-content">
      <div v-if="isMobile" class="settings-mobile-bar">
        <button class="mobile-bar-btn" @click="toggleMobileNav">
          <el-icon><Operation /></el-icon>
        </button>
        <div class="mobile-bar-title">{{ $t('settings.title') }}</div>
        <div class="mobile-bar-actions">
          <button class="mobile-bar-btn" @click="router.push('/chat')">
            <el-icon><ArrowLeft /></el-icon>
          </button>
        </div>
      </div>
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useMediaQuery } from '@vueuse/core'
import { useTheme } from '@/utils/useTheme'
import { setLocale } from '@/i18n'
import { useSettingsStore } from '@/stores/settings'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const { t, locale } = useI18n()
const { isDark, themeMode, setTheme } = useTheme()
const settingsStore = useSettingsStore()
const authStore = useAuthStore()
const isMobile = useMediaQuery('(max-width: 960px)')
const mobileNavOpen = ref(false)

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

function openAccountSettings() {
  if (isMobile.value) mobileNavOpen.value = false
  router.push({
    path: '/settings/security',
    query: { tab: 'account' },
  })
}

function closeMobileNav() {
  mobileNavOpen.value = false
}

function toggleMobileNav() {
  mobileNavOpen.value = !mobileNavOpen.value
}

function handleNavItemClick() {
  if (isMobile.value) {
    mobileNavOpen.value = false
  }
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

watch(isMobile, (mobile) => {
  if (!mobile) {
    mobileNavOpen.value = false
  }
})
</script>

<style scoped>
.settings-layout {
  display: flex;
  height: 100dvh;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, var(--surface-tint) 0, transparent 26%),
    linear-gradient(180deg, var(--bg) 0%, var(--bg-soft) 100%);
}

/* ── Nav ── */
.settings-nav {
  width: 240px;
  flex-shrink: 0;
  background:
    linear-gradient(180deg, var(--bg-sidebar) 0%, var(--bg-card) 100%);
  border-right: 1px solid var(--border);
  box-shadow: inset -1px 0 0 var(--surface-highlight);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 18px 12px;
  backdrop-filter: blur(18px);
}

.nav-backdrop {
  position: fixed;
  inset: 0;
  z-index: 109;
  background: rgba(8, 10, 18, 0.42);
  backdrop-filter: blur(4px);
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
  transition: background var(--transition-fast), color var(--transition-fast);
}
.nav-group-header:hover { background: var(--bg-soft); color: var(--text-1); }
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
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: var(--radius);
  border: 1px solid transparent;
  color: var(--text-2);
  text-decoration: none;
  font-size: 13px;
  transition:
    background var(--transition-fast),
    border-color var(--transition-fast),
    transform var(--transition-fast),
    box-shadow var(--transition-fast);
}
.nav-item:hover {
  background: var(--bg-card-elevated);
  border-color: var(--border);
  box-shadow: 0 10px 24px -18px var(--surface-shadow);
  transform: translateX(2px);
}
.nav-item.router-link-active {
  background:
    linear-gradient(180deg, var(--primary-light) 0%, rgba(0, 0, 0, 0) 100%),
    var(--bg-card-elevated);
  color: var(--primary-text);
  font-weight: 500;
  border-color: rgba(99, 102, 241, 0.18);
  box-shadow:
    inset 0 1px 0 var(--surface-highlight),
    0 16px 28px -20px var(--surface-shadow);
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

.account-box {
  padding: 10px 12px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  background:
    linear-gradient(180deg, var(--surface-highlight) 0%, rgba(0, 0, 0, 0) 40px),
    linear-gradient(180deg, var(--bg-card-elevated) 0%, var(--bg-card) 100%);
  box-shadow: inset 0 1px 0 var(--surface-highlight);
}

.account-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-1);
}

.account-hint {
  margin-top: 4px;
  font-size: 11px;
  line-height: 1.45;
  color: var(--text-3);
}

.account-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
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
  position: relative;
  padding: 32px;
}

.settings-mobile-bar {
  display: none;
}

.settings-content::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 82% 0%, var(--surface-tint) 0, transparent 24%),
    radial-gradient(circle at 12% 12%, var(--surface-highlight) 0, transparent 18%);
  pointer-events: none;
}

.settings-content > * {
  position: relative;
  z-index: 1;
}

@media (max-width: 960px) {
  .settings-layout {
    position: relative;
  }

  .settings-nav {
    position: fixed;
    z-index: 120;
    inset: 0 auto 0 0;
    width: min(84vw, 320px);
    height: 100dvh;
    padding-top: calc(18px + var(--safe-top));
    padding-bottom: calc(18px + var(--safe-bottom));
    transform: translateX(-100%);
    transition: transform var(--transition-slow);
    box-shadow: var(--shadow-lg);
  }

  .settings-nav.mobile-open {
    transform: translateX(0);
  }

  .settings-content {
    padding:
      calc(12px + var(--safe-top))
      calc(14px + var(--safe-right))
      calc(22px + var(--safe-bottom))
      calc(14px + var(--safe-left));
  }

  .settings-mobile-bar {
    position: sticky;
    top: calc(-12px - var(--safe-top));
    z-index: 30;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 0 -14px 14px;
    padding:
      calc(10px + var(--safe-top))
      calc(14px + var(--safe-right))
      10px
      calc(14px + var(--safe-left));
    background:
      linear-gradient(180deg, var(--surface-highlight) 0%, rgba(0, 0, 0, 0) 52px),
      linear-gradient(180deg, var(--bg-card-elevated) 0%, var(--bg-card) 100%);
    border-bottom: 1px solid var(--border);
    backdrop-filter: blur(18px);
  }

  .mobile-bar-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--text-1);
    letter-spacing: -0.02em;
  }

  .mobile-bar-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .mobile-bar-btn {
    width: 34px;
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: var(--bg-card);
    color: var(--text-2);
    box-shadow: var(--shadow-sm);
    cursor: pointer;
  }

  .settings-nav:not(.mobile-open) {
    pointer-events: none;
  }
}
</style>
