<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">{{ $t('settings.channels.title') }}</h1>
        <p class="page-desc">{{ $t('settings.channels.desc') }}</p>
      </div>
    </div>

    <div v-if="loading" class="loading-state"><el-icon class="is-loading"><Loading /></el-icon></div>

    <div v-else class="channels-grid">
      <div v-for="ch in channelList" :key="ch.key" class="channel-card" :class="{ enabled: ch.config.enabled }" @click="openEdit(ch)">
        <div class="card-header-row">
          <div class="status-dot" :class="ch.config.enabled ? 'on' : 'off'" />
          <span class="status-label">{{ ch.config.enabled ? $t('common.enabled') : $t('common.disabled') }}</span>
          <span class="channel-badge">{{ ch.label }}</span>
        </div>
        <div class="card-name">{{ ch.displayName }}</div>
        <div class="card-meta">{{ $t('settings.channels.botPrefix') }}：{{ ch.config.bot_prefix || $t('settings.models.notSet') }}</div>
        <div class="card-hint">{{ $t('settings.channels.clickToEdit') }}</div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="`${$t('common.edit')} ${editingChannel?.displayName}`" width="480px" destroy-on-close>
      <el-form v-if="editingChannel" :model="editForm" label-position="top">
        <el-form-item :label="$t('common.enable')">
          <el-switch v-model="editForm.enabled" />
        </el-form-item>
        <el-form-item :label="$t('settings.channels.botPrefix')">
          <el-input v-model="editForm.bot_prefix" placeholder="@bot" />
        </el-form-item>
        <template v-if="editingChannel.key === 'dingtalk'">
          <el-form-item label="Client ID"><el-input v-model="editForm.client_id" /></el-form-item>
          <el-form-item label="Client Secret"><el-input v-model="editForm.client_secret" show-password /></el-form-item>
        </template>
        <template v-if="editingChannel.key === 'feishu'">
          <el-form-item label="App ID"><el-input v-model="editForm.app_id" /></el-form-item>
          <el-form-item label="App Secret"><el-input v-model="editForm.app_secret" show-password /></el-form-item>
          <el-form-item label="Encrypt Key"><el-input v-model="editForm.encrypt_key" show-password /></el-form-item>
          <el-form-item label="Verification Token"><el-input v-model="editForm.verification_token" /></el-form-item>
          <el-form-item label="Media Dir"><el-input v-model="editForm.media_dir" /></el-form-item>
        </template>
        <template v-if="editingChannel.key === 'qq'">
          <el-form-item label="App ID"><el-input v-model="editForm.app_id" /></el-form-item>
          <el-form-item label="Client Secret"><el-input v-model="editForm.client_secret" show-password /></el-form-item>
        </template>
        <template v-if="editingChannel.key === 'discord'">
          <el-form-item label="Bot Token"><el-input v-model="editForm.bot_token" show-password /></el-form-item>
          <el-form-item label="HTTP Proxy"><el-input v-model="editForm.http_proxy" /></el-form-item>
        </template>
        <template v-if="editingChannel.key === 'imessage'">
          <el-form-item label="DB Path"><el-input v-model="editForm.db_path" /></el-form-item>
          <el-form-item label="Poll Interval (sec)"><el-input-number v-model="editForm.poll_sec" :min="0.5" :step="0.5" /></el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="saveChannel">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listChannels, updateChannel } from '@/api/channels'
import type { AnyChannelConfig } from '@/types'

interface ChannelEntry { key: string; displayName: string; label: string; config: AnyChannelConfig }

const CHANNEL_META: Record<string, { displayName: string; label: string }> = {
  console: { displayName: 'Console', label: 'Console' },
  feishu: { displayName: 'Feishu', label: 'Feishu' },
  dingtalk: { displayName: 'DingTalk', label: 'DingTalk' },
  imessage: { displayName: 'iMessage', label: 'iMessage' },
  discord: { displayName: 'Discord', label: 'Discord' },
  qq: { displayName: 'QQ', label: 'QQ' },
}

const loading = ref(false)
const channelList = ref<ChannelEntry[]>([])
const dialogVisible = ref(false)
const editingChannel = ref<ChannelEntry | null>(null)
const editForm = ref<Record<string, unknown>>({})
const saving = ref(false)

async function loadChannels() {
  loading.value = true
  try {
    const data = await listChannels()
    channelList.value = Object.entries(data).map(([key, config]) => ({
      key, displayName: CHANNEL_META[key]?.displayName ?? key, label: CHANNEL_META[key]?.label ?? key, config,
    }))
  } catch (e: unknown) { ElMessage.error('Load failed: ' + (e instanceof Error ? e.message : String(e)))
  } finally { loading.value = false }
}

function openEdit(ch: ChannelEntry) {
  editingChannel.value = ch
  editForm.value = { ...ch.config } as Record<string, unknown>
  dialogVisible.value = true
}

async function saveChannel() {
  if (!editingChannel.value) return
  saving.value = true
  try {
    await updateChannel(editingChannel.value.key, editForm.value as unknown as AnyChannelConfig)
    ElMessage.success('Saved')
    dialogVisible.value = false
    await loadChannels()
  } catch (e: unknown) { ElMessage.error('Save failed: ' + (e instanceof Error ? e.message : String(e)))
  } finally { saving.value = false }
}

onMounted(loadChannels)
</script>

<style scoped>
.page-header { margin-bottom: 24px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text-1); }
.page-desc { font-size: 13px; color: var(--text-3); margin-top: 4px; }
.loading-state { display: flex; justify-content: center; padding: 60px 0; color: var(--text-4); font-size: 24px; }
.channels-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
.channel-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 16px; cursor: pointer; transition: box-shadow var(--transition-fast), border-color var(--transition-fast); }
.channel-card:hover { box-shadow: var(--shadow-md); }
.channel-card.enabled { border-color: var(--primary); }
.card-header-row { display: flex; align-items: center; gap: 6px; margin-bottom: 10px; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.status-dot.on { background: var(--success); }
.status-dot.off { background: var(--text-4); }
.status-label { font-size: 12px; color: var(--text-3); flex: 1; }
.channel-badge { font-size: 11px; color: var(--primary); background: var(--primary-light); padding: 2px 7px; border-radius: var(--radius-sm); font-weight: 500; }
.card-name { font-size: 16px; font-weight: 600; color: var(--text-1); margin-bottom: 6px; }
.card-meta { font-size: 12px; color: var(--text-3); margin-bottom: 4px; }
.card-hint { font-size: 12px; color: var(--text-4); margin-top: 8px; }
</style>
