<template>
  <div class="page">
    <!-- ═══════════════ LLM Section ═══════════════ -->
    <section class="section">
      <h2 class="section-title">LLM</h2>
      <p class="section-desc">{{ $t('settings.models.llmDesc') }}</p>

      <div class="llm-card">
        <div class="llm-card-header">
          <span class="llm-card-title">{{ $t('settings.models.llmConfig') }}</span>
          <span v-if="activeModel.provider_id" class="active-badge">
            {{ $t('settings.models.active') }}：{{ activeModel.provider_id }} / {{ activeModel.model }}
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
              <el-option v-for="m in availableModels" :key="m.id" :label="`${m.name} (${m.id})`" :value="m.id" />
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
            <el-icon v-if="isSaved"><Check /></el-icon>
            {{ isSaved ? $t('common.saved') : $t('common.save') }}
          </el-button>
        </div>
      </div>
    </section>

    <!-- ═══════════════ Providers Section ═══════════════ -->
    <section class="section">
      <div class="section-header-row">
        <div>
          <h2 class="section-title">{{ $t('settings.models.providers') }}</h2>
          <p class="section-desc">{{ $t('settings.models.providersDesc') }}</p>
        </div>
        <el-button type="primary" @click="openCreateProviderDialog">
          <el-icon><Plus /></el-icon>
          {{ $t('settings.models.addProvider') }}
        </el-button>
      </div>

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
            <div class="provider-name-line">
              <span class="provider-name">{{ provider.name }}</span>
              <span class="provider-type-badge" :class="provider.is_custom ? 'badge-custom' : (provider.is_local ? 'badge-local' : 'badge-builtin')">
                {{ provider.is_custom ? $t('settings.models.custom') : (provider.is_local ? $t('settings.models.local') : $t('settings.models.builtIn')) }}
              </span>
            </div>
            <span class="provider-status" :class="provider.has_api_key ? 'auth' : 'unauth'">
              <span class="dot" />
              {{ provider.has_api_key ? $t('settings.models.authorized') : $t('settings.models.unauthorized') }}
            </span>
          </div>

          <div v-if="!provider.is_local" class="provider-field">
            <span class="field-label">{{ $t('settings.models.baseUrl') }}:</span>
            <span class="field-value" :title="provider.current_base_url">{{ truncate(provider.current_base_url, 32) || $t('settings.models.notSet') }}</span>
          </div>
          <div v-if="!provider.is_local" class="provider-field">
            <span class="field-label">{{ $t('settings.models.apiKey') }}:</span>
            <span class="field-value">{{ provider.current_api_key || $t('settings.models.notSet') }}</span>
          </div>
          <div class="provider-field">
            <span class="field-label">{{ $t('settings.models.model') }}:</span>
            <span class="field-value">{{ provider.models.length }} {{ $t('settings.models.model') }}</span>
          </div>

          <div class="provider-actions">
            <el-button size="small" text type="primary" @click="openModelsDialog(provider)">
              <el-icon><Grid /></el-icon>
              {{ $t('settings.models.models') }}
            </el-button>
            <el-button v-if="!provider.is_local" size="small" text type="primary" @click="openProviderEdit(provider)">
              <el-icon><EditPen /></el-icon>
              {{ $t('settings.models.configure') }}
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════ Provider Edit Dialog ═══════════════ -->
    <el-dialog v-model="providerDialogVisible" :title="`${$t('common.edit')} ${editingProvider?.name}`" width="440px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item v-if="editingProvider && (editingProvider.is_custom || editingProvider.needs_base_url)" :label="$t('settings.models.baseUrl')">
          <el-input v-model="providerForm.base_url" placeholder="http://localhost:11434/v1" />
        </el-form-item>
        <el-form-item :label="$t('settings.models.apiKey')">
          <el-input v-model="providerForm.api_key" show-password placeholder="sk-..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="providerDialogVisible = false">{{ $t('common.cancel') }}</el-button>
          <el-button type="primary" :loading="savingProvider" @click="saveProvider">{{ $t('common.save') }}</el-button>
          <el-button v-if="editingProvider?.is_custom" type="danger" plain @click="confirmDeleteProvider">
            {{ $t('settings.models.deleteProvider') }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- ═══════════════ Create Custom Provider Dialog ═══════════════ -->
    <el-dialog v-model="createProviderDialogVisible" :title="$t('settings.models.addCustomProvider')" width="500px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item :label="$t('settings.models.providerId')" required>
          <el-input v-model="createProviderForm.id" :placeholder="$t('settings.models.providerIdPlaceholder')" />
          <div class="form-hint">{{ $t('settings.models.providerIdHint') }}</div>
        </el-form-item>
        <el-form-item :label="$t('settings.models.displayName')" required>
          <el-input v-model="createProviderForm.name" :placeholder="$t('settings.models.displayNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('settings.models.defaultBaseUrl')">
          <el-input v-model="createProviderForm.default_base_url" :placeholder="$t('settings.models.defaultBaseUrlPlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('settings.models.apiKeyPrefix')">
          <el-input v-model="createProviderForm.api_key_prefix" :placeholder="$t('settings.models.apiKeyPrefixPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createProviderDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="creatingProvider" :disabled="!createProviderForm.id || !createProviderForm.name" @click="createProvider">
          {{ $t('common.create') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- ═══════════════ Models Management Dialog ═══════════════ -->
    <el-dialog v-model="modelsDialogVisible" :title="`${modelsDialogProvider?.name} — ${$t('settings.models.manageModels')}`" width="560px" destroy-on-close>
      <div class="models-list">
        <div v-for="m in modelsDialogProvider?.models ?? []" :key="m.id" class="model-item">
          <div class="model-info">
            <span class="model-name">{{ m.name }}</span>
            <span class="model-id">{{ m.id }}</span>
          </div>
          <div class="model-actions">
            <span v-if="isExtraModel(m)" class="model-badge badge-user">{{ $t('settings.models.userAdded') }}</span>
            <span v-else class="model-badge badge-builtin">{{ $t('settings.models.builtIn') }}</span>
            <el-button
              v-if="isExtraModel(m)"
              size="small"
              type="danger"
              text
              :icon="Delete"
              @click="handleRemoveModel(m)"
            />
          </div>
        </div>
      </div>
      <div class="add-model-area" @click="showAddModelInput = true">
        <template v-if="!showAddModelInput">
          <el-icon><Plus /></el-icon>
          <span>{{ $t('settings.models.addModel') }}</span>
        </template>
        <div v-else class="add-model-form" @click.stop>
          <el-input v-model="newModelId" :placeholder="$t('settings.models.modelId')" size="small" style="flex: 1" />
          <el-input v-model="newModelName" :placeholder="$t('settings.models.modelName')" size="small" style="flex: 1" />
          <el-button type="primary" size="small" :disabled="!newModelId || !newModelName" :loading="addingModel" @click="handleAddModel">
            {{ $t('common.add') }}
          </el-button>
          <el-button size="small" @click.stop="showAddModelInput = false">{{ $t('common.cancel') }}</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Delete, EditPen, Grid, Loading, Plus } from '@element-plus/icons-vue'
import {
  listProviders,
  configureProvider,
  getActiveModel,
  setActiveModel,
  createCustomProvider as apiCreateCustomProvider,
  deleteCustomProvider as apiDeleteCustomProvider,
  addModel as apiAddModel,
  removeModel as apiRemoveModel,
} from '@/api/models'
import type { ProviderInfo, ModelInfo, ModelSlotConfig } from '@/types'

const providers = ref<ProviderInfo[]>([])
const loadingProviders = ref(false)
const activeModel = ref<ModelSlotConfig>({ provider_id: '', model: '' })
const selectedProvider = ref('')
const selectedModel = ref('')
const savingLLM = ref(false)
const isSaved = ref(false)

// ── Provider Edit ──
const providerDialogVisible = ref(false)
const editingProvider = ref<ProviderInfo | null>(null)
const providerForm = reactive({ api_key: '', base_url: '' })
const savingProvider = ref(false)

// ── Create Custom Provider ──
const createProviderDialogVisible = ref(false)
const createProviderForm = reactive({ id: '', name: '', default_base_url: '', api_key_prefix: '' })
const creatingProvider = ref(false)

// ── Models Management ──
const modelsDialogVisible = ref(false)
const modelsDialogProvider = ref<ProviderInfo | null>(null)
const showAddModelInput = ref(false)
const newModelId = ref('')
const newModelName = ref('')
const addingModel = ref(false)

const authorizedProviders = computed(() => providers.value.filter((p) => p.has_api_key))
const availableModels = computed<ModelInfo[]>(() => {
  const p = providers.value.find((p) => p.id === selectedProvider.value)
  return p?.models ?? []
})

function truncate(s: string, max: number): string {
  if (!s) return ''
  return s.length > max ? s.slice(0, max) + '…' : s
}

function isExtraModel(m: ModelInfo): boolean {
  if (!modelsDialogProvider.value) return false
  return modelsDialogProvider.value.extra_models.some((em) => em.id === m.id)
}

// ── Load Data ──
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

// ── Save LLM ──
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

// ── Provider Edit ──
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

async function confirmDeleteProvider() {
  if (!editingProvider.value) return
  try {
    await ElMessageBox.confirm(
      `确认删除自定义提供商 "${editingProvider.value.name}"？`,
      '删除确认',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' },
    )
    const result = await apiDeleteCustomProvider(editingProvider.value.id)
    providers.value = result
    providerDialogVisible.value = false
    ElMessage.success('Deleted')
  } catch (e: unknown) {
    if (e !== 'cancel' && (e as any) !== 'cancel') {
      ElMessage.error('Delete failed: ' + (e instanceof Error ? e.message : String(e)))
    }
  }
}

// ── Create Custom Provider ──
function openCreateProviderDialog() {
  createProviderForm.id = ''
  createProviderForm.name = ''
  createProviderForm.default_base_url = ''
  createProviderForm.api_key_prefix = ''
  createProviderDialogVisible.value = true
}

async function createProvider() {
  creatingProvider.value = true
  try {
    await apiCreateCustomProvider({
      id: createProviderForm.id,
      name: createProviderForm.name,
      default_base_url: createProviderForm.default_base_url || undefined,
      api_key_prefix: createProviderForm.api_key_prefix || undefined,
    })
    ElMessage.success('Created')
    createProviderDialogVisible.value = false
    await loadData()
  } catch (e: unknown) {
    ElMessage.error('Create failed: ' + (e instanceof Error ? e.message : String(e)))
  } finally { creatingProvider.value = false }
}

// ── Model Management ──
function openModelsDialog(p: ProviderInfo) {
  modelsDialogProvider.value = { ...p }
  showAddModelInput.value = false
  newModelId.value = ''
  newModelName.value = ''
  modelsDialogVisible.value = true
}

async function handleAddModel() {
  if (!modelsDialogProvider.value) return
  addingModel.value = true
  try {
    const updated = await apiAddModel(modelsDialogProvider.value.id, { id: newModelId.value, name: newModelName.value })
    modelsDialogProvider.value = updated
    // Sync providers list
    const idx = providers.value.findIndex((p) => p.id === updated.id)
    if (idx >= 0) providers.value[idx] = updated
    newModelId.value = ''
    newModelName.value = ''
    showAddModelInput.value = false
    ElMessage.success('Added')
  } catch (e: unknown) {
    ElMessage.error('Add failed: ' + (e instanceof Error ? e.message : String(e)))
  } finally { addingModel.value = false }
}

async function handleRemoveModel(m: ModelInfo) {
  if (!modelsDialogProvider.value) return
  try {
    const updated = await apiRemoveModel(modelsDialogProvider.value.id, m.id)
    modelsDialogProvider.value = updated
    const idx = providers.value.findIndex((p) => p.id === updated.id)
    if (idx >= 0) providers.value[idx] = updated
    ElMessage.success('Removed')
  } catch (e: unknown) {
    ElMessage.error('Remove failed: ' + (e instanceof Error ? e.message : String(e)))
  }
}

onMounted(loadData)
</script>

<style scoped>
.page { max-width: 960px; }
.section { margin-bottom: 36px; }
.section-title { font-size: 18px; font-weight: 700; color: var(--text-1); margin-bottom: 4px; }
.section-desc { font-size: 13px; color: var(--text-3); margin-bottom: 16px; }
.section-header-row { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 16px; }
.section-header-row .section-title { margin-bottom: 2px; }
.section-header-row .section-desc { margin-bottom: 0; }

.loading-state { display: flex; justify-content: center; padding: 40px 0; color: var(--text-4); font-size: 24px; }

/* ── Provider Cards ── */
.providers-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.provider-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 18px;
  transition: box-shadow var(--transition-fast), border-color var(--transition-fast);
}
.provider-card:hover { box-shadow: var(--shadow-md); }
.provider-card.authorized { border-color: var(--primary); }

.provider-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 12px; }
.provider-name-line { display: flex; align-items: center; gap: 8px; }
.provider-name { font-size: 15px; font-weight: 600; color: var(--text-1); }

.provider-type-badge {
  font-size: 11px; font-weight: 500;
  padding: 1px 8px; border-radius: var(--radius-sm);
  border: 1px solid;
}
.badge-builtin { color: #22c55e; border-color: #bbf7d0; background: #f0fdf4; }
.badge-custom { color: #7c3aed; border-color: #ddd6fe; background: #f5f3ff; }
.badge-local { color: #f59e0b; border-color: #fde68a; background: #fffbeb; }

.provider-status { display: flex; align-items: center; gap: 4px; font-size: 11px; padding: 2px 7px; border-radius: var(--radius-sm); white-space: nowrap; }
.provider-status.auth { color: var(--success); background: var(--success-light); }
.provider-status.unauth { color: var(--text-4); background: var(--bg); }
.dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; }

.provider-field { display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px; }
.field-label { font-size: 12px; color: var(--text-4); white-space: nowrap; }
.field-value { font-size: 12px; color: var(--text-2); word-break: break-all; font-family: Consolas, monospace; }

.provider-actions {
  margin-top: 12px; border-top: 1px solid var(--border);
  padding-top: 10px; display: flex; gap: 8px; justify-content: flex-end;
}

/* ── LLM Card ── */
.llm-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 20px; }
.llm-card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; justify-content: space-between; }
.llm-card-title { font-size: 14px; font-weight: 600; color: var(--text-1); }
.active-badge { font-size: 12px; color: var(--success); background: var(--success-light); padding: 2px 10px; border-radius: var(--radius-sm); }
.llm-form-row { display: grid; grid-template-columns: 1fr 1.5fr; gap: 16px; margin-bottom: 16px; }
.llm-form-item { display: flex; flex-direction: column; gap: 6px; }
.llm-form-item label { font-size: 13px; color: var(--text-2); font-weight: 500; }
.llm-form-footer { display: flex; justify-content: flex-end; }

/* ── Dialogs ── */
.form-hint { font-size: 12px; color: var(--text-4); margin-top: 4px; }
.dialog-footer { display: flex; gap: 8px; justify-content: flex-end; }

/* ── Models Dialog ── */
.models-list { border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.model-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
}
.model-item:last-child { border-bottom: none; }
.model-info { display: flex; flex-direction: column; gap: 2px; }
.model-name { font-size: 14px; font-weight: 600; color: var(--text-1); }
.model-id { font-size: 12px; color: var(--text-4); font-family: Consolas, monospace; }
.model-actions { display: flex; align-items: center; gap: 8px; }
.model-badge { font-size: 11px; font-weight: 500; padding: 1px 8px; border-radius: var(--radius-sm); border: 1px solid; }
.badge-user { color: #22c55e; border-color: #bbf7d0; background: #f0fdf4; }

.add-model-area {
  margin-top: 14px;
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  padding: 14px;
  display: flex; align-items: center; justify-content: center; gap: 6px;
  cursor: pointer; color: var(--text-3); font-size: 13px;
  transition: border-color var(--transition-fast), color var(--transition-fast);
}
.add-model-area:hover { border-color: var(--primary); color: var(--primary); }
.add-model-form { display: flex; gap: 8px; width: 100%; align-items: center; }

/* ── Dark mode badge overrides ── */
[data-theme="dark"] .badge-builtin { color: #4ade80; border-color: rgba(34,197,94,.3); background: rgba(34,197,94,.1); }
[data-theme="dark"] .badge-custom { color: #a78bfa; border-color: rgba(124,58,237,.3); background: rgba(124,58,237,.1); }
[data-theme="dark"] .badge-local { color: #fbbf24; border-color: rgba(245,158,11,.3); background: rgba(245,158,11,.1); }
[data-theme="dark"] .badge-user { color: #4ade80; border-color: rgba(34,197,94,.3); background: rgba(34,197,94,.1); }
</style>
