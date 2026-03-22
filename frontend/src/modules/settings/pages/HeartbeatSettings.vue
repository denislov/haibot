<template>
  <div class="settings-page">
    <h2>{{ $t('settings.heartbeat.title') }}</h2>
    <p class="desc">{{ $t('settings.heartbeat.desc') }}</p>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="4" animated />
    </div>

    <template v-else>
      <div class="form-card">
        <!-- Enable toggle -->
        <div class="form-field">
          <div class="field-label">{{ $t('settings.heartbeat.enabled') }}</div>
          <el-switch v-model="form.enabled" />
        </div>

        <!-- Interval -->
        <div class="form-field">
          <div class="field-label required">{{ $t('settings.heartbeat.interval') }}</div>
          <div class="interval-row">
            <el-input-number
              v-model="intervalValue"
              :min="1"
              :max="999"
              controls-position="right"
              style="width: 120px"
            />
            <el-select v-model="intervalUnit" style="width: 160px">
              <el-option value="m" :label="$t('settings.heartbeat.minutes')" />
              <el-option value="h" :label="$t('settings.heartbeat.hours')" />
            </el-select>
          </div>
        </div>

        <!-- Target -->
        <div class="form-field">
          <div class="field-label required">{{ $t('settings.heartbeat.target') }}</div>
          <el-select v-model="form.target" style="max-width: 460px; width: 100%">
            <el-option value="main" :label="$t('settings.heartbeat.targetMain')" />
            <el-option value="last" :label="$t('settings.heartbeat.targetLast')" />
          </el-select>
        </div>

        <!-- Active hours -->
        <div class="form-field">
          <div class="field-label">{{ $t('settings.heartbeat.activeHours') }}</div>
          <el-switch v-model="activeHoursEnabled" />
        </div>

        <div v-if="activeHoursEnabled" class="time-range-row">
          <div class="time-field">
            <div class="field-sublabel">{{ $t('settings.heartbeat.startTime') }}</div>
            <el-time-picker
              v-model="activeStart"
              format="HH:mm"
              :placeholder="'08:00'"
              style="width: 160px"
            />
          </div>
          <div class="time-field">
            <div class="field-sublabel">{{ $t('settings.heartbeat.endTime') }}</div>
            <el-time-picker
              v-model="activeEnd"
              format="HH:mm"
              :placeholder="'22:00'"
              style="width: 160px"
            />
          </div>
        </div>

        <!-- Save button -->
        <div class="form-actions">
          <el-button type="primary" :loading="saving" @click="save">
            {{ $t('common.save') }}
          </el-button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import api from '@/api'

const { t } = useI18n()
const loading = ref(true)
const saving = ref(false)

const form = ref({
  enabled: false,
  every: '6h',
  target: 'main',
})

const activeHoursEnabled = ref(false)
const activeStart = ref<Date | null>(null)
const activeEnd = ref<Date | null>(null)

// Parse interval string "6h" / "30m" / "2h30m" into value + unit
const intervalValue = ref(6)
const intervalUnit = ref<'h' | 'm'>('h')

function parseEvery(every: string) {
  const hMatch = every.match(/(\d+)h/)
  const mMatch = every.match(/(\d+)m/)
  if (hMatch && !mMatch) {
    intervalValue.value = parseInt(hMatch[1])
    intervalUnit.value = 'h'
  } else if (mMatch && !hMatch) {
    intervalValue.value = parseInt(mMatch[1])
    intervalUnit.value = 'm'
  } else if (hMatch && mMatch) {
    // Convert to minutes
    intervalValue.value = parseInt(hMatch[1]) * 60 + parseInt(mMatch[1])
    intervalUnit.value = 'm'
  }
}

function buildEvery(): string {
  return `${intervalValue.value}${intervalUnit.value}`
}

function timeStringToDate(timeStr: string): Date {
  const [h, m] = timeStr.split(':').map(Number)
  const d = new Date()
  d.setHours(h, m, 0, 0)
  return d
}

function dateToTimeString(d: Date): string {
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
}

async function fetchConfig() {
  loading.value = true
  try {
    const res = await api.get('/config/heartbeat')
    const data = res.data
    form.value.enabled = data.enabled ?? false
    form.value.every = data.every ?? '6h'
    form.value.target = data.target ?? 'main'
    parseEvery(form.value.every)

    if (data.activeHours || data.active_hours) {
      const ah = data.activeHours || data.active_hours
      activeHoursEnabled.value = true
      activeStart.value = timeStringToDate(ah.start || '08:00')
      activeEnd.value = timeStringToDate(ah.end || '22:00')
    } else {
      activeHoursEnabled.value = false
      activeStart.value = timeStringToDate('08:00')
      activeEnd.value = timeStringToDate('22:00')
    }
  } catch {
    ElMessage.error(t('common.loadFailed'))
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const body: Record<string, unknown> = {
      enabled: form.value.enabled,
      every: buildEvery(),
      target: form.value.target,
    }
    if (activeHoursEnabled.value && activeStart.value && activeEnd.value) {
      body.activeHours = {
        start: dateToTimeString(activeStart.value),
        end: dateToTimeString(activeEnd.value),
      }
    } else {
      body.activeHours = null
    }
    await api.put('/config/heartbeat', body)
    ElMessage.success(t('common.saved'))
  } catch {
    ElMessage.error(t('common.saveFailed'))
  } finally {
    saving.value = false
  }
}

onMounted(fetchConfig)
</script>

<style scoped>
.settings-page h2 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-1);
  margin-bottom: 4px;
}
.desc {
  color: var(--text-3);
  font-size: 13px;
  margin-bottom: 20px;
  line-height: 1.6;
}
.loading-state { max-width: 600px; }

.form-card {
  max-width: 600px;
  padding: 24px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  background: var(--bg-card);
}

.form-field {
  margin-bottom: 20px;
}

.field-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-1);
  margin-bottom: 8px;
}
.field-label.required::after {
  content: ' *';
  color: var(--error);
}

.field-sublabel {
  font-size: 13px;
  color: var(--text-2);
  margin-bottom: 6px;
}

.interval-row {
  display: flex;
  gap: 12px;
}

.time-range-row {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 8px;
}
</style>
