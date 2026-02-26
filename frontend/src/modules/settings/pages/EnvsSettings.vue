<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">{{ $t('settings.envs.title') }}</h1>
        <p class="page-desc">{{ $t('settings.envs.desc') }}</p>
      </div>
      <el-button type="primary" @click="addVar"><el-icon><Plus /></el-icon>{{ $t('settings.envs.addVar') }}</el-button>
    </div>

    <div v-if="loading" class="loading-state"><el-icon class="is-loading"><Loading /></el-icon></div>

    <div v-else-if="envVars.length === 0" class="empty-state">{{ $t('settings.envs.emptyState') }}</div>

    <div v-else class="env-card">
      <div v-for="(v, i) in envVars" :key="i" class="env-row">
        <el-input v-model="v.key" :placeholder="$t('settings.envs.varName')" class="key-input" />
        <el-input v-model="v.value" :placeholder="$t('settings.envs.value')" class="val-input" show-password />
        <el-button link type="danger" @click="removeVar(i)"><el-icon><Delete /></el-icon></el-button>
      </div>
      <div class="env-footer">
        <span class="var-count">{{ $t('settings.envs.count', { count: envVars.length }) }}</span>
        <el-button type="primary" :loading="saving" @click="saveVars">{{ $t('settings.envs.saveVars') }}</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listEnvs, saveEnvs } from '@/api/envs'
import type { EnvVar } from '@/types'

const envVars = ref<EnvVar[]>([])
const loading = ref(false)
const saving = ref(false)

async function loadEnvs() {
  loading.value = true
  try {
    const data = await listEnvs()
    envVars.value = data ?? []
  } catch (e: unknown) { ElMessage.error(String(e)) }
  finally { loading.value = false }
}

function addVar() { envVars.value.push({ key: '', value: '' }) }
function removeVar(i: number) { envVars.value.splice(i, 1) }

async function saveVars() {
  const empty = envVars.value.find(v => !v.key.trim())
  if (empty) { ElMessage.warning('Variable name cannot be empty'); return }
  saving.value = true
  try {
    const obj: Record<string, string> = {}
    envVars.value.forEach(v => { obj[v.key] = v.value })
    await saveEnvs(obj)
    ElMessage.success('Saved')
  } catch (e: unknown) { ElMessage.error(String(e)) }
  finally { saving.value = false }
}

onMounted(loadEnvs)
</script>

<style scoped>
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text-1); }
.page-desc { font-size: 13px; color: var(--text-3); margin-top: 4px; }
.loading-state { display: flex; justify-content: center; padding: 60px 0; color: var(--text-4); font-size: 24px; }
.empty-state { text-align: center; color: var(--text-4); padding: 60px 0; font-size: 14px; }
.env-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 16px; }
.env-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.key-input { width: 240px; }
.val-input { flex: 1; }
.env-footer { display: flex; align-items: center; justify-content: space-between; padding-top: 12px; border-top: 1px solid var(--border); }
.var-count { font-size: 13px; color: var(--text-3); }
</style>
