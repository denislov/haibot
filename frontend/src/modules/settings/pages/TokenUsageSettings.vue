<template>
  <div class="settings-page">
    <h2>{{ $t('settings.tokenUsage.title') }}</h2>
    <p class="desc">{{ $t('settings.tokenUsage.desc') }}</p>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="6" animated />
    </div>

    <template v-else-if="usage">
      <!-- Summary cards -->
      <div class="summary-cards">
        <div class="stat-card">
          <div class="stat-label">{{ $t('settings.tokenUsage.totalInput') }}</div>
          <div class="stat-value">{{ formatNumber(usage.total_input_tokens) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ $t('settings.tokenUsage.totalOutput') }}</div>
          <div class="stat-value">{{ formatNumber(usage.total_output_tokens) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ $t('settings.tokenUsage.totalCost') }}</div>
          <div class="stat-value">${{ usage.total_cost.toFixed(4) }}</div>
        </div>
      </div>

      <!-- By Model table -->
      <h3>{{ $t('settings.tokenUsage.byModel') }}</h3>
      <el-table :data="usage.by_model" stripe size="small" style="max-width: 700px">
        <el-table-column prop="model" :label="$t('settings.tokenUsage.model')" />
        <el-table-column prop="provider" :label="$t('settings.tokenUsage.provider')" width="120" />
        <el-table-column :label="$t('settings.tokenUsage.inputTokens')" width="100">
          <template #default="{ row }">{{ formatNumber(row.input_tokens) }}</template>
        </el-table-column>
        <el-table-column :label="$t('settings.tokenUsage.outputTokens')" width="100">
          <template #default="{ row }">{{ formatNumber(row.output_tokens) }}</template>
        </el-table-column>
        <el-table-column :label="$t('settings.tokenUsage.cost')" width="90">
          <template #default="{ row }">${{ row.cost.toFixed(4) }}</template>
        </el-table-column>
      </el-table>

      <!-- By Date table -->
      <h3 style="margin-top: 24px">{{ $t('settings.tokenUsage.byDate') }}</h3>
      <el-table :data="usage.by_date" stripe size="small" style="max-width: 700px">
        <el-table-column prop="date" :label="$t('settings.tokenUsage.date')" width="120" />
        <el-table-column :label="$t('settings.tokenUsage.inputTokens')" width="120">
          <template #default="{ row }">{{ formatNumber(row.input_tokens) }}</template>
        </el-table-column>
        <el-table-column :label="$t('settings.tokenUsage.outputTokens')" width="120">
          <template #default="{ row }">{{ formatNumber(row.output_tokens) }}</template>
        </el-table-column>
        <el-table-column :label="$t('settings.tokenUsage.cost')" width="90">
          <template #default="{ row }">${{ row.cost.toFixed(4) }}</template>
        </el-table-column>
      </el-table>
    </template>

    <div v-else class="empty-state">
      <p>{{ $t('settings.tokenUsage.noData') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { getTokenUsage } from '@/api/token_usage'
import type { TokenUsageSummary } from '@/api/token_usage'

const { t } = useI18n()
const usage = ref<TokenUsageSummary | null>(null)
const loading = ref(true)

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}

async function fetchUsage() {
  loading.value = true
  try {
    usage.value = await getTokenUsage()
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
  font-size: 20px;
  font-weight: 700;
  color: var(--text-1);
  margin-bottom: 4px;
}
.desc {
  color: var(--text-3);
  font-size: 13px;
  margin-bottom: 20px;
}
h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-1);
  margin-bottom: 12px;
}

.loading-state { max-width: 700px; }
.empty-state { color: var(--text-4); font-size: 14px; }

.summary-cards {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.stat-card {
  flex: 1;
  max-width: 200px;
  padding: 16px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--bg-card);
}

.stat-label {
  font-size: 12px;
  color: var(--text-3);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-1);
}
</style>
