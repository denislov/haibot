<template>
  <div class="settings-page">
    <h2>{{ $t('settings.tokenUsage.title') }}</h2>
    <p class="desc">{{ $t('settings.tokenUsage.desc') }}</p>

    <!-- Date range picker + refresh -->
    <div class="toolbar">
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        :start-placeholder="$t('settings.tokenUsage.startDate') || '开始日期'"
        :end-placeholder="$t('settings.tokenUsage.endDate') || '结束日期'"
        value-format="YYYY-MM-DD"
        size="default"
        style="max-width: 320px"
      />
      <el-button type="primary" @click="fetchUsage">{{ $t('common.refresh') }}</el-button>
    </div>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="6" animated />
    </div>

    <template v-else-if="usage">
      <!-- Summary cards -->
      <div class="summary-cards">
        <div class="stat-card">
          <div class="stat-value">{{ formatNumber(usage.total_prompt_tokens) }}</div>
          <div class="stat-label">{{ $t('settings.tokenUsage.totalInput') }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ formatNumber(usage.total_completion_tokens) }}</div>
          <div class="stat-label">{{ $t('settings.tokenUsage.totalOutput') }}</div>
        </div>
      </div>

      <!-- By Model table -->
      <div class="table-card">
        <h3>{{ $t('settings.tokenUsage.byModel') }}</h3>
        <el-table :data="modelRows" stripe size="small">
          <el-table-column prop="provider_id" :label="$t('settings.tokenUsage.provider')" min-width="120" />
          <el-table-column prop="model" :label="$t('settings.tokenUsage.model')" min-width="160" />
          <el-table-column :label="$t('settings.tokenUsage.inputTokens')" min-width="120">
            <template #default="{ row }">{{ formatNumber(row.prompt_tokens) }}</template>
          </el-table-column>
          <el-table-column :label="$t('settings.tokenUsage.outputTokens')" min-width="120">
            <template #default="{ row }">{{ formatNumber(row.completion_tokens) }}</template>
          </el-table-column>
          <el-table-column :label="$t('settings.tokenUsage.callCount')" min-width="100">
            <template #default="{ row }">{{ row.call_count }}</template>
          </el-table-column>
        </el-table>
      </div>

      <!-- By Date table -->
      <div class="table-card">
        <h3>{{ $t('settings.tokenUsage.byDate') }}</h3>
        <el-table :data="dateRows" stripe size="small">
          <el-table-column prop="date" :label="$t('settings.tokenUsage.date')" min-width="120" />
          <el-table-column :label="$t('settings.tokenUsage.inputTokens')" min-width="140">
            <template #default="{ row }">{{ formatNumber(row.prompt_tokens) }}</template>
          </el-table-column>
          <el-table-column :label="$t('settings.tokenUsage.outputTokens')" min-width="140">
            <template #default="{ row }">{{ formatNumber(row.completion_tokens) }}</template>
          </el-table-column>
          <el-table-column :label="$t('settings.tokenUsage.callCount')" min-width="120">
            <template #default="{ row }">{{ row.call_count }}</template>
          </el-table-column>
        </el-table>
      </div>
    </template>

    <div v-else class="empty-state">
      <p>{{ $t('settings.tokenUsage.noData') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { getTokenUsage } from '@/api/token_usage'
import type { TokenUsageSummary } from '@/api/token_usage'

const { t } = useI18n()
const usage = ref<TokenUsageSummary | null>(null)
const loading = ref(true)

// Default date range: 30 days ago to today
const today = new Date()
const thirtyDaysAgo = new Date(today)
thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
const dateRange = ref<[string, string] | null>([
  thirtyDaysAgo.toISOString().slice(0, 10),
  today.toISOString().slice(0, 10),
])

// Transform by_model dict → array for el-table
const modelRows = computed(() => {
  if (!usage.value?.by_model) return []
  return Object.values(usage.value.by_model)
})

// Transform by_date dict → sorted array for el-table
const dateRows = computed(() => {
  if (!usage.value?.by_date) return []
  return Object.entries(usage.value.by_date)
    .map(([date, stats]) => ({ date, ...stats }))
    .sort((a, b) => a.date.localeCompare(b.date))
})

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(0) + 'K'
  return String(n)
}

async function fetchUsage() {
  loading.value = true
  try {
    const params: Record<string, string> = {}
    if (dateRange.value) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    usage.value = await getTokenUsage(params)
  } catch {
    ElMessage.error(t('common.loadFailed'))
  } finally {
    loading.value = false
  }
}

onMounted(fetchUsage)
</script>

<style scoped>
.settings-page h2 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-1);
  margin-bottom: 4px;
  letter-spacing: -0.02em;
}
.desc {
  color: var(--text-3);
  font-size: 13px;
  margin-bottom: 4px;
  max-width: 680px;
  line-height: 1.55;
}

.toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 4px;
  padding: 16px 18px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border);
  background:
    linear-gradient(180deg, var(--surface-highlight) 0%, rgba(0, 0, 0, 0) 48px),
    linear-gradient(180deg, var(--bg-card-elevated) 0%, var(--bg-card) 100%);
  box-shadow:
    inset 0 1px 0 var(--surface-highlight),
    0 18px 34px -26px var(--surface-shadow);
}

h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-1);
  margin-bottom: 12px;
}

.loading-state { max-width: 800px; }
.empty-state { color: var(--text-4); font-size: 14px; }

.summary-cards {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.stat-card {
  flex: 1;
  padding: 24px 22px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border);
  background:
    radial-gradient(circle at top right, var(--surface-tint) 0, transparent 34%),
    linear-gradient(180deg, var(--surface-highlight) 0%, rgba(0, 0, 0, 0) 54px),
    linear-gradient(180deg, var(--bg-card-elevated) 0%, var(--bg-card) 100%);
  text-align: left;
}

.stat-value {
  font-size: 30px;
  font-weight: 700;
  color: var(--text-1);
  margin-bottom: 4px;
  letter-spacing: -0.03em;
}

.stat-label {
  font-size: 13px;
  color: var(--text-3);
}

.table-card {
  padding: 20px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border);
  background:
    linear-gradient(180deg, var(--surface-highlight) 0%, rgba(0, 0, 0, 0) 54px),
    linear-gradient(180deg, var(--bg-card-elevated) 0%, var(--bg-card) 100%);
}

@media (max-width: 768px) {
  .summary-cards {
    grid-template-columns: 1fr;
  }
}
</style>
