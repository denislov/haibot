<template>
  <div class="page">
    <section class="section">
      <h2 class="section-title">{{ $t('settings.runningConfig.title') }}</h2>
      <p class="section-desc">{{ $t('settings.runningConfig.desc') }}</p>

      <div class="card" v-loading="loading">
        <label class="card-title">{{ $t('settings.runningConfig.reactAgent') }}</label>
        
        <div class="form-row">
          <label>{{ $t('settings.runningConfig.agentLanguage') }} <el-icon class="info-icon"><InfoFilled /></el-icon></label>
          <el-select v-model="agentLanguage" style="width: 100%">
            <el-option label="中文" value="zh" />
            <el-option label="English" value="en" />
            <el-option label="Русский" value="ru" />
          </el-select>
        </div>

        <div class="form-row mt-4">
          <label>{{ $t('settings.runningConfig.userTimezone') }} <el-icon class="info-icon"><InfoFilled /></el-icon></label>
          <el-select v-model="userTimezone" style="width: 100%" filterable allow-create>
            <el-option label="Asia/Shanghai (UTC+8)" value="Asia/Shanghai" />
            <el-option label="UTC" value="UTC" />
            <el-option label="America/New_York (UTC-5)" value="America/New_York" />
            <el-option label="America/Los_Angeles (UTC-8)" value="America/Los_Angeles" />
          </el-select>
        </div>

        <div class="form-row mt-4">
          <label>{{ $t('settings.runningConfig.maxIters') }} <el-icon class="info-icon"><InfoFilled /></el-icon> <span class="required">*</span></label>
          <el-input-number v-model="form.max_iters" :min="1" :max="1000" style="width: 100%" controls-position="right" />
        </div>
      </div>
      
      <div class="card mt-6" v-loading="loading">
        <label class="card-title">{{ $t('settings.runningConfig.contextManagement') }}</label>
        
        <div class="form-row">
          <label>{{ $t('settings.runningConfig.maxInputLength') }} <el-icon class="info-icon"><InfoFilled /></el-icon> <span class="required">*</span></label>
          <el-input-number v-model="form.max_input_length" :min="1000" style="width: 100%" controls-position="right" />
        </div>

        <div class="form-row slider-row mt-4">
          <label>{{ $t('settings.runningConfig.contextCompressionRatio') }} <el-icon class="info-icon"><InfoFilled /></el-icon> <span class="required">*</span></label>
          <el-slider v-model="form.memory_compact_ratio" :min="0" :max="1" :step="0.01" />
        </div>

        <div class="form-row mt-4">
          <label>{{ $t('settings.runningConfig.contextCompressionThreshold') }} <el-icon class="info-icon"><InfoFilled /></el-icon></label>
          <el-input :model-value="compressionThreshold" readonly disabled />
        </div>

        <div class="form-row slider-row mt-4">
          <label>{{ $t('settings.runningConfig.contextKeepRatio') }} <el-icon class="info-icon"><InfoFilled /></el-icon> <span class="required">*</span></label>
          <el-slider v-model="form.memory_reserve_ratio" :min="0" :max="1" :step="0.01" />
        </div>

        <div class="form-row mt-4">
          <label>{{ $t('settings.runningConfig.contextKeepThreshold') }} <el-icon class="info-icon"><InfoFilled /></el-icon></label>
          <el-input :model-value="keepThreshold" readonly disabled />
        </div>

        <div class="form-row slider-row mt-4">
          <label>{{ $t('settings.runningConfig.toolResultRecentN') }} <el-icon class="info-icon"><InfoFilled /></el-icon> <span class="required">*</span></label>
          <el-slider v-model="form.tool_result_compact_recent_n" :min="1" :max="10" />
        </div>

        <div class="form-row mt-4">
          <label>{{ $t('settings.runningConfig.maxCharsBeyondN') }} <el-icon class="info-icon"><InfoFilled /></el-icon> <span class="required">*</span></label>
          <el-input-number v-model="form.tool_result_compact_old_threshold" :min="0" style="width: 100%" controls-position="right" />
        </div>

        <div class="form-row mt-4">
          <label>{{ $t('settings.runningConfig.maxCharsWithinN') }} <el-icon class="info-icon"><InfoFilled /></el-icon> <span class="required">*</span></label>
          <el-input-number v-model="form.tool_result_compact_recent_threshold" :min="0" style="width: 100%" controls-position="right" />
        </div>

        <div class="form-row slider-row mt-4">
          <label>{{ $t('settings.runningConfig.toolFileRetentionDays') }} <el-icon class="info-icon"><InfoFilled /></el-icon> <span class="required">*</span></label>
          <el-slider v-model="form.tool_result_compact_retention_days" :min="1" :max="30" />
        </div>
      </div>

      <div class="actions">
        <el-button @click="loadData">{{ $t('common.refresh') }}</el-button>
        <el-button type="primary" :loading="saving" @click="saveData">{{ $t('common.save') }}</el-button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { 
  getRunningConfig, 
  updateRunningConfig, 
  getAgentLanguage,
  updateAgentLanguage,
  getUserTimezone,
  updateUserTimezone
} from '@/api/config'
import type { AgentsRunningConfig } from '@/types'

const loading = ref(false)
const saving = ref(false)
const form = ref<AgentsRunningConfig>({})
const agentLanguage = ref('')
const userTimezone = ref('')

const formatNumber = (num: number) => num ? num.toLocaleString() : '0'

const compressionThreshold = computed(() => {
  if (!form.value.max_input_length || !form.value.memory_compact_ratio) return '0'
  return formatNumber(Math.floor(form.value.max_input_length * form.value.memory_compact_ratio))
})

const keepThreshold = computed(() => {
  if (!form.value.max_input_length || !form.value.memory_reserve_ratio) return '0'
  return formatNumber(Math.floor(form.value.max_input_length * form.value.memory_reserve_ratio))
})

async function loadData() {
  loading.value = true
  try {
    const configResp = await getRunningConfig()
    const langResp = await getAgentLanguage()
    const tzResp = await getUserTimezone()
    
    form.value = configResp || {}
    console.log(form.value.tool_result_compact_recent_n)
    agentLanguage.value = langResp.language || 'zh'
    userTimezone.value = tzResp.timezone || 'Asia/Shanghai'
  } catch(e: any) {
    ElMessage.error('Load failed: ' + e.message)
  } finally {
    loading.value = false
  }
}

async function saveData() {
  saving.value = true
  try {
    await updateRunningConfig(form.value)
    await updateAgentLanguage(agentLanguage.value)
    await updateUserTimezone(userTimezone.value)
    ElMessage.success('Saved successfully')
  } catch(e: any) {
    ElMessage.error('Save failed: ' + e.message)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page { max-width: 960px; }
.section { margin-bottom: 36px; }
.section-title { font-size: 18px; font-weight: 700; color: var(--text-1); margin-bottom: 4px; }
.section-desc { font-size: 13px; color: var(--text-3); margin-bottom: 16px; }

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
  display: flex;
  flex-direction: column;
}
.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-1);
  margin-bottom: 20px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.slider-row {
  padding: 0 10px;
}
.form-row label {
  font-size: 13px;
  color: var(--text-2);
  display: flex;
  align-items: center;
  gap: 6px;
}
.info-icon {
  color: var(--text-4);
  font-size: 14px;
  cursor: help;
}
.required {
  color: var(--danger);
}
.mt-4 { margin-top: 20px; }
.mt-6 { margin-top: 24px; }

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}
</style>
