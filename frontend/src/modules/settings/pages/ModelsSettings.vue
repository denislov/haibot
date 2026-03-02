<template>
  <div class="page">
    <section class="section">
      <h2 class="section-title">{{ $t('settings.models.providers') }}</h2>
      <p class="section-desc">{{ $t('settings.models.providersDesc') }}</p>

      <div v-if="loadingProviders" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
      </div>

      <div v-else class="providers-grid">
        <div
          v-for="provider in providers"
          :key="provider.id"
          class="provider-card"
          :class="{ authorized: provider.has_api_key }"
        >
          <div class="provider-header">
            <span class="provider-name">{{ provider.name }}</span>
            <span class="provider-status" :class="provider.has_api_key ? 'auth' : 'unauth'">
              <span class="dot" />
              {{ provider.has_api_key ? $t('settings.models.authorized') : $t('settings.models.unauthorized') }}
            </span>
          </div>
          <div class="provider-field">
            <span class="field-label">{{ $t('settings.models.baseUrl') }}</span>
            <span class="field-value">{{ provider.current_base_url || $t('settings.models.notSet') }}</span>
          </div>
          <div class="provider-field">
            <span class="field-label">{{ $t('settings.models.apiKey') }}</span>
            <span class="field-value">{{ provider.current_api_key || $t('settings.models.notSet') }}</span>
          </div>
          <div class="provider-actions">
            <el-button size="small" @click="openProviderEdit(provider)">
              <el-icon><EditPen /></el-icon>
              {{ $t('common.edit') }}
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">LLM</h2>
      <p class="section-desc">{{ $t('settings.models.llmDesc') }}</p>

      <div class="llm-card">
        <div class="llm-card-header">
          <span class="llm-card-title">{{ $t('settings.models.llmConfig') }}</span>
          <span v-if="activeModel.provider_id" class="active-badge">
            {{ $t('settings.models.active') }}: {{ activeModel.provider_id }} / {{ activeModel.model }}
          </span>
        </div>

        <div class="llm-form-row">
          <div class="llm-form-item">
            <label>{{ $t('settings.models.provider') }}</label>
            <el-select v-model="selectedProvider" :placeholder="$t('settings.models.selectProvider')" style="width: 100%" @change="onProviderChange">
              <el-option v-for="p in authorizedProviders" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </div>
          <div class="llm-form-item">
            <label>{{ $t('settings.models.model') }}</label>
            <el-select
              v-if="!selectedProvider || availableModels.length > 0"
              v-model="selectedModel"
              :placeholder="$t('settings.models.selectModel')"
              style="width: 100%"
              filterable
              allow-create
              default-first-option
            >
              <el-option v-for="m in availableModels" :key="m.id" :label="m.name" :value="m.id" />
            </el-select>
            <el-input
              v-else
              v-model="selectedModel"
              :placeholder="$t('settings.models.customModelId')"
            />
          </div>
        </div>

        <div class="llm-form-footer">
          <el-button type="primary" :loading="savingLLM" :disabled="!selectedProvider || !selectedModel" @click="saveLLM">
            {{ isSaved ? $t('common.saved') : $t('common.save') }}
          </el-button>
        </div>
      </div>
    </section>

    <el-dialog v-model="providerDialogVisible" :title="`${$t('common.edit')} ${editingProvider?.name}`" width="440px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item v-if="editingProvider?.allow_custom_base_url" :label="$t('settings.models.baseUrl')">
          <el-input v-model="providerForm.base_url" placeholder="http://localhost:11434/v1" />
        </el-form-item>
        <el-form-item :label="$t('settings.models.apiKey')">
          <el-input v-model="providerForm.api_key" show-password placeholder="sk-..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="providerDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="savingProvider" @click="saveProvider">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { listProviders, configureProvider, getActiveModel, setActiveModel } from '@/api/models'
import type { ProviderInfo, ModelInfo, ModelSlotConfig } from '@/types'

const providers = ref<ProviderInfo[]>([])
const loadingProviders = ref(false)
const activeModel = ref<ModelSlotConfig>({ provider_id: '', model: '' })
const selectedProvider = ref('')
const selectedModel = ref('')
const savingLLM = ref(false)
const isSaved = ref(false)
const providerDialogVisible = ref(false)
const editingProvider = ref<ProviderInfo | null>(null)
const providerForm = reactive({ api_key: '', base_url: '' })
const savingProvider = ref(false)

const authorizedProviders = computed(() => providers.value.filter((p) => p.has_api_key))
const availableModels = computed<ModelInfo[]>(() => {
  const p = providers.value.find((p) => p.id === selectedProvider.value)
  return p?.models ?? []
})

async function loadData() {
  loadingProviders.value = true
  try {
    const [provData, activeData] = await Promise.all([listProviders(), getActiveModel()])
    providers.value = provData
    activeModel.value = activeData.active_llm
    selectedProvider.value = activeData.active_llm.provider_id
    selectedModel.value = activeData.active_llm.model
  } catch (e: unknown) {
    ElMessage.error('Load failed: ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    loadingProviders.value = false
  }
}

function onProviderChange() { selectedModel.value = ''; isSaved.value = false }

async function saveLLM() {
  const model = selectedModel.value
  if (!model) return
  savingLLM.value = true
  try {
    const res = await setActiveModel({ provider_id: selectedProvider.value, model })
    activeModel.value = res.active_llm
    isSaved.value = true
    ElMessage.success('Saved')
    setTimeout(() => { isSaved.value = false }, 3000)
  } catch (e: unknown) {
    ElMessage.error('Save failed: ' + (e instanceof Error ? e.message : String(e)))
  } finally { savingLLM.value = false }
}

function openProviderEdit(p: ProviderInfo) {
  editingProvider.value = p
  providerForm.api_key = ''
  providerForm.base_url = p.current_base_url || ''
  providerDialogVisible.value = true
}

async function saveProvider() {
  if (!editingProvider.value) return
  savingProvider.value = true
  try {
    await configureProvider(editingProvider.value.id, {
      api_key: providerForm.api_key || undefined,
      base_url: providerForm.base_url || undefined,
    })
    ElMessage.success('Saved')
    providerDialogVisible.value = false
    await loadData()
  } catch (e: unknown) {
    ElMessage.error('Save failed: ' + (e instanceof Error ? e.message : String(e)))
  } finally { savingProvider.value = false }
}

onMounted(loadData)
</script>

<style scoped>
.page { max-width: 900px; }
.section { margin-bottom: 36px; }
.section-title { font-size: 18px; font-weight: 700; color: var(--text-1); margin-bottom: 4px; }
.section-desc { font-size: 13px; color: var(--text-3); margin-bottom: 16px; }
.loading-state { display: flex; justify-content: center; padding: 40px 0; color: var(--text-4); font-size: 24px; }
.providers-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
.provider-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 16px; transition: box-shadow var(--transition-fast); }
.provider-card:hover { box-shadow: var(--shadow-md); }
.provider-card.authorized { border-color: var(--primary); }
.provider-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.provider-name { font-size: 15px; font-weight: 600; color: var(--text-1); }
.provider-status { display: flex; align-items: center; gap: 4px; font-size: 11px; padding: 2px 7px; border-radius: var(--radius-sm); }
.provider-status.auth { color: var(--success); background: var(--success-light); }
.provider-status.unauth { color: var(--text-4); background: var(--bg); }
.dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; }
.provider-field { display: flex; flex-direction: column; gap: 2px; margin-bottom: 6px; }
.field-label { font-size: 11px; color: var(--text-4); }
.field-value { font-size: 12px; color: var(--text-2); word-break: break-all; font-family: Consolas, monospace; }
.provider-actions { margin-top: 12px; border-top: 1px solid var(--border); padding-top: 10px; }
.llm-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 20px; }
.llm-card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.llm-card-title { font-size: 14px; font-weight: 600; color: var(--text-1); }
.active-badge { font-size: 12px; color: var(--success); background: var(--success-light); padding: 2px 10px; border-radius: var(--radius-sm); }
.llm-form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.llm-form-item { display: flex; flex-direction: column; gap: 6px; }
.llm-form-item label { font-size: 13px; color: var(--text-2); font-weight: 500; }
.llm-form-footer { display: flex; justify-content: flex-end; }
</style>
