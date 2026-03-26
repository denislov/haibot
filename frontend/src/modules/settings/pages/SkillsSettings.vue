<template>
  <div class="page">
    <div class="page-header">
      <div><h1 class="page-title">{{ $t('settings.skills.title') }}</h1><p class="page-desc">{{ $t('settings.skills.desc') }}</p></div>
      <div class="header-actions">
        <el-button @click="openUploadDialog">
          <el-icon><Upload /></el-icon>{{ $t('settings.skills.uploadSkill') }}
        </el-button>
        <el-button @click="openImportDialog">
          <el-icon><Link /></el-icon>{{ $t('settings.skills.importSkill') }}
        </el-button>
        <el-button type="primary" @click="createDialogVisible = true"><el-icon><Plus /></el-icon>{{ $t('settings.skills.createSkill') }}</el-button>
      </div>
    </div>

    <input
      ref="uploadInputRef"
      type="file"
      accept=".zip,application/zip,application/x-zip-compressed,application/octet-stream"
      class="hidden-file-input"
      @change="handleZipSelected"
    >

    <div v-if="loading" class="loading-state"><el-icon class="is-loading"><Loading /></el-icon></div>

    <div v-else class="skills-grid">
      <div v-for="skill in skills" :key="skill.name" class="skill-card" :class="{ enabled: skill.enabled }" @click="openDetail(skill)">
        <div class="skill-main-header">
          <div class="skill-title-block">
            <span class="skill-icon-wrapper">
              <span v-if="getCustomEmoji(skill)">{{ getCustomEmoji(skill) }}</span>
              <el-icon v-else class="default-icon"><Document /></el-icon>
            </span>
            <span class="skill-name">{{ skill.name }}</span>
          </div>
          <span class="skill-status" :class="skill.enabled ? 'on' : 'off'">
            <span class="dot" />
            {{ skill.enabled ? $t('common.enabled') : $t('common.disabled') }}
          </span>
        </div>

        <div class="skill-section">
          <div class="section-label">Description</div>
          <div class="info-box skill-desc">{{ skill.description || 'No description provided.' }}</div>
        </div>

        <div class="skill-section">
          <div class="section-label">Source</div>
          <span class="badge" :class="'badge-' + (skill.source || 'builtin')">{{ skill.source || 'builtin' }}</span>
        </div>

        <div class="skill-section">
          <div class="section-label">Path</div>
          <div class="info-box path-box">{{ skill.path }}</div>
        </div>

        <div class="skill-card-footer" @click.stop>
          <el-button v-if="skill.enabled" link type="primary" @click="toggleSkill(skill, false)">{{ $t('common.disable') }}</el-button>
          <el-button v-else link type="primary" @click="toggleSkill(skill, true)">{{ $t('common.enable') }}</el-button>
          <el-button v-if="skill.source !== 'builtin'" link type="danger" @click="handleDelete(skill)">{{ $t('common.delete') || 'Delete' }}</el-button>
        </div>
      </div>
    </div>

    <!-- Detail drawer -->
    <div v-if="detailSkill" class="drawer-mask" @click.self="closeDetail">
      <div class="detail-drawer">
        <div class="drawer-header">
          <span class="drawer-title">{{ detailSkill.source === 'builtin' ? $t('settings.skills.viewSkill') : $t('settings.skills.editSkill') }}</span>
          <button class="drawer-close" @click="closeDetail"><el-icon><Close /></el-icon></button>
        </div>
        <div class="drawer-body">
          <div class="field-group"><label>Name</label><div class="field-readonly">{{ detailSkill.name }}</div></div>
          <div class="field-group content-group">
            <div class="content-header">
              <label>{{ $t('settings.skills.content') }}</label>
              <div class="content-tabs">
                <button class="tab-btn" :class="{ active: contentTab === 'edit' }" @click="contentTab = 'edit'">{{ $t('settings.skills.content') }}</button>
                <button class="tab-btn" :class="{ active: contentTab === 'preview' }" @click="contentTab = 'preview'">{{ $t('settings.skills.preview') }}</button>
              </div>
            </div>
            <textarea v-if="contentTab === 'edit'" v-model="editContent" class="content-editor" :readonly="detailSkill.source === 'builtin'" spellcheck="false" />
            <div v-else class="content-preview md-content" v-html="renderMarkdownWithFrontMatter(editContent)" />
          </div>
        </div>
        <div class="drawer-footer">
          <el-button @click="closeDetail">{{ $t('common.close') }}</el-button>
          <el-button v-if="detailSkill.source !== 'builtin'" type="primary" :loading="saving" @click="saveSkill">{{ $t('common.save') }}</el-button>
        </div>
      </div>
    </div>

    <!-- Create dialog -->
    <el-dialog v-model="createDialogVisible" :title="$t('settings.skills.createSkill')" width="560px" destroy-on-close>
      <el-form :model="createForm" label-position="top">
        <el-form-item :label="$t('settings.skills.skillName')" required><el-input v-model="createForm.name" placeholder="my_skill" /></el-form-item>
        <el-form-item label="SKILL.md" required><el-input v-model="createForm.content" type="textarea" :rows="8" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="creating" @click="doCreate">{{ $t('common.create') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="uploadDialogVisible" :title="$t('settings.skills.uploadSkill')" width="560px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item :label="$t('settings.skills.zipFile')" required>
          <div class="upload-file-row">
            <el-input :model-value="uploadForm.file?.name || ''" :placeholder="$t('settings.skills.noFileSelected')" readonly />
            <el-button @click="triggerZipSelect">{{ $t('settings.skills.selectZip') }}</el-button>
          </div>
          <p class="dialog-hint">{{ $t('settings.skills.uploadHint') }}</p>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="uploadForm.enable">{{ $t('settings.skills.enableAfterImport') }}</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="uploadForm.overwrite">{{ $t('settings.skills.overwriteExisting') }}</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">{{ $t('settings.skills.uploadSkill') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDialogVisible" :title="$t('settings.skills.importSkill')" width="560px" destroy-on-close>
      <el-form :model="importForm" label-position="top">
        <el-form-item :label="$t('settings.skills.skillUrl')" required>
          <el-input v-model="importForm.bundleUrl" :placeholder="$t('settings.skills.skillUrlPlaceholder')" />
          <p class="dialog-hint">{{ $t('settings.skills.importHint') }}</p>
        </el-form-item>
        <el-form-item :label="$t('settings.skills.version')">
          <el-input v-model="importForm.version" :placeholder="$t('settings.skills.versionPlaceholder')" />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="importForm.enable">{{ $t('settings.skills.enableAfterImport') }}</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="importForm.overwrite">{{ $t('settings.skills.overwriteExisting') }}</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="importing" @click="submitImport">{{ $t('settings.skills.importSkill') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import yaml from 'js-yaml'
import { Document, Plus, Loading, Close, Upload, Link } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { renderMarkdownWithFrontMatter } from '@/utils/useMarkdown'
import { listSkills, enableSkill, disableSkill, deleteSkill, createSkill, updateSkill, uploadSkillZip, installFromHub } from '@/api/skills'
import { useSettingsStore } from '@/stores/settings'
import type { SkillSpec } from '@/types'

const { t } = useI18n()
const settingsStore = useSettingsStore()
const skills = ref<SkillSpec[]>([])
const loading = ref(false)
const creating = ref(false)
const saving = ref(false)
const uploading = ref(false)
const importing = ref(false)
const createDialogVisible = ref(false)
const uploadDialogVisible = ref(false)
const importDialogVisible = ref(false)
const detailSkill = ref<SkillSpec | null>(null)
const editContent = ref('')
const contentTab = ref<'edit' | 'preview'>('edit')
const uploadInputRef = ref<HTMLInputElement | null>(null)
const createForm = reactive({ name: '', content: '' })
const uploadForm = reactive({
  file: null as File | null,
  enable: true,
  overwrite: false,
})
const importForm = reactive({
  bundleUrl: '',
  version: '',
  enable: true,
  overwrite: false,
})

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

async function loadSkills() {
  if (!settingsStore.selectedAgentId) return
  loading.value = true
  try { skills.value = await listSkills() }
  catch (e: unknown) { ElMessage.error(getErrorMessage(e)) }
  finally { loading.value = false }
}

async function toggleSkill(skill: SkillSpec, enable: boolean) {
  try { enable ? await enableSkill(skill.name) : await disableSkill(skill.name); await loadSkills() }
  catch (e: unknown) { ElMessage.error(getErrorMessage(e)) }
}

async function handleDelete(skill: SkillSpec) {
  try {
    await ElMessageBox.confirm(`Delete "${skill.name}"?`, 'Confirm', { type: 'warning' })
    await deleteSkill(skill.name); if (detailSkill.value?.name === skill.name) closeDetail(); await loadSkills()
  } catch { /* cancelled */ }
}

async function doCreate() {
  if (!createForm.name.trim() || !createForm.content.trim()) return
  creating.value = true
  try { await createSkill({ name: createForm.name, content: createForm.content }); createDialogVisible.value = false; createForm.name = ''; createForm.content = ''; await loadSkills() }
  catch (e: unknown) { ElMessage.error(getErrorMessage(e)) }
  finally { creating.value = false }
}

function openDetail(skill: SkillSpec) { detailSkill.value = skill; editContent.value = skill.content; contentTab.value = 'edit' }
function closeDetail() { detailSkill.value = null }

async function saveSkill() {
  if (!detailSkill.value) return
  saving.value = true
  try { await updateSkill({ name: detailSkill.value.name, content: editContent.value }); ElMessage.success('Saved') }
  catch (e: unknown) { ElMessage.error(getErrorMessage(e)) }
  finally { saving.value = false }
}

function resetUploadForm() {
  uploadForm.file = null
  uploadForm.enable = true
  uploadForm.overwrite = false
  if (uploadInputRef.value) uploadInputRef.value.value = ''
}

function openUploadDialog() {
  resetUploadForm()
  uploadDialogVisible.value = true
}

function triggerZipSelect() {
  uploadInputRef.value?.click()
}

function handleZipSelected(event: Event) {
  const target = event.target as HTMLInputElement
  uploadForm.file = target.files?.[0] ?? null
}

async function submitUpload() {
  if (!uploadForm.file) {
    ElMessage.warning(t('settings.skills.selectZipFirst'))
    return
  }
  uploading.value = true
  try {
    const result = await uploadSkillZip(uploadForm.file, {
      enable: uploadForm.enable,
      overwrite: uploadForm.overwrite,
    })
    uploadDialogVisible.value = false
    resetUploadForm()
    ElMessage.success(t('settings.skills.uploadSuccess', { count: result.count }))
    await loadSkills()
  } catch (e: unknown) {
    ElMessage.error(getErrorMessage(e))
  } finally {
    uploading.value = false
  }
}

function resetImportForm() {
  importForm.bundleUrl = ''
  importForm.version = ''
  importForm.enable = true
  importForm.overwrite = false
}

function openImportDialog() {
  resetImportForm()
  importDialogVisible.value = true
}

function isValidHttpUrl(value: string): boolean {
  try {
    const url = new URL(value)
    return url.protocol === 'http:' || url.protocol === 'https:'
  } catch {
    return false
  }
}

async function submitImport() {
  const bundleUrl = importForm.bundleUrl.trim()
  if (!isValidHttpUrl(bundleUrl)) {
    ElMessage.warning(t('settings.skills.invalidSkillUrl'))
    return
  }

  importing.value = true
  try {
    const result = await installFromHub({
      bundle_url: bundleUrl,
      version: importForm.version.trim(),
      enable: importForm.enable,
      overwrite: importForm.overwrite,
    })
    importDialogVisible.value = false
    resetImportForm()
    ElMessage.success(t('settings.skills.importSuccess', { name: result.name }))
    await loadSkills()
  } catch (e: unknown) {
    ElMessage.error(getErrorMessage(e))
  } finally {
    importing.value = false
  }
}

function getCustomEmoji(skill: SkillSpec): string | null {
  try {
    if (skill.content) {
      const match = skill.content.match(/^---\r?\n([\s\S]*?)\r?\n---/)
      if (match && match[1]) {
        const metadataObj = yaml.load(match[1]) as any
        if (metadataObj?.metadata?.haibot?.emoji) {
          return metadataObj.metadata.haibot.emoji
        }
      }
    }
  } catch (e) {
    // disregard parse errors
  }
  return null
}

onMounted(() => {
  if (settingsStore.selectedAgentId) loadSkills()
})

watch(
  () => settingsStore.selectedAgentId,
  (agentId) => {
    if (agentId) loadSkills()
    else skills.value = []
  },
)
</script>

<style scoped>
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text-1); }
.page-desc { font-size: 13px; color: var(--text-3); margin-top: 4px; }
.loading-state { display: flex; justify-content: center; padding: 60px 0; color: var(--text-4); font-size: 24px; }
.skills-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.skill-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 18px; cursor: pointer; transition: box-shadow var(--transition-fast); display: flex; flex-direction: column; gap: 14px; }
.skill-card:hover { box-shadow: var(--shadow-md); }
.skill-card.enabled { border-color: var(--primary); }

.skill-main-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
.skill-title-block { display: flex; align-items: center; gap: 10px; }
.skill-icon-wrapper { font-size: 20px; color: var(--primary); display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; background: var(--primary-light, rgba(59,130,246,0.1)); border-radius: 6px; }
.default-icon { color: var(--primary); font-size: 18px; }
.skill-name { font-size: 16px; font-weight: 600; color: var(--text-1); }

.skill-status { display: flex; align-items: center; gap: 4px; font-size: 11px; padding: 2px 7px; border-radius: var(--radius-sm); white-space: nowrap; }
.skill-status.on { color: var(--success); }
.skill-status.off { color: var(--text-4); }
.skill-status .dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; }

.skill-section { display: flex; flex-direction: column; gap: 4px; }
.section-label { font-size: 12px; color: var(--text-3); }

.info-box { background: var(--bg); padding: 10px 12px; border-radius: 6px; font-size: 13px; color: var(--text-2); border: 1px solid var(--border); }
.skill-desc {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.5;
}
.path-box {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: 'Fira Code', 'Cascadia Code', Consolas, monospace;
  font-size: 12px;
}

.badge { font-size: 11px; padding: 2px 8px; border-radius: var(--radius-sm); border: 1px solid; display: inline-block; width: fit-content; }
.badge-builtin { color: #8b5cf6; border-color: #ddd6fe; background: #f5f3ff; }
.badge-customized { color: #3b82f6; border-color: #bfdbfe; background: #eff6ff; }
[data-theme="dark"] .badge-builtin { color: #a78bfa; border-color: rgba(139,92,246,.3); background: rgba(139,92,246,.1); }
[data-theme="dark"] .badge-customized { color: #60a5fa; border-color: rgba(59,130,246,.3); background: rgba(59,130,246,.1); }

.header-actions { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.skill-card-footer { display: flex; justify-content: flex-end; gap: 12px; border-top: 1px solid var(--border); padding-top: 12px; margin-top: auto; }
.drawer-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 2000; display: flex; justify-content: flex-end; }
.detail-drawer { width: 520px; height: 100%; background: var(--bg-card); display: flex; flex-direction: column; box-shadow: -4px 0 24px rgba(0,0,0,0.12); animation: slideIn 0.22s ease; }
@keyframes slideIn { from { transform: translateX(100%); } }
.drawer-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border); }
.drawer-title { font-size: 15px; font-weight: 600; color: var(--text-1); }
.drawer-close { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border: none; background: none; cursor: pointer; color: var(--text-4); border-radius: var(--radius-sm); }
.drawer-body { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.field-group { display: flex; flex-direction: column; gap: 6px; }
.field-group label { font-size: 13px; font-weight: 500; color: var(--text-2); }
.field-readonly { padding: 7px 10px; background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius); font-size: 13px; color: var(--text-2); }
.content-group { flex: 1; }
.content-header { display: flex; align-items: center; justify-content: space-between; }
.content-tabs { display: flex; border: 1px solid var(--border); border-radius: var(--radius-sm); overflow: hidden; }
.tab-btn { padding: 3px 10px; font-size: 12px; border: none; background: var(--bg-card); cursor: pointer; color: var(--text-3); }
.tab-btn:first-child { border-right: 1px solid var(--border); }
.tab-btn.active { background: var(--primary); color: white; }
.content-editor { width: 100%; min-height: 320px; padding: 10px; border: 1px solid var(--border); border-radius: var(--radius); font-family: 'Fira Code', Consolas, monospace; font-size: 12px; line-height: 1.6; color: var(--text-1); background: var(--bg); resize: vertical; outline: none; box-sizing: border-box; }
.content-editor:focus { border-color: var(--primary); background: var(--bg-card); }
.content-preview { min-height: 320px; padding: 12px; border: 1px solid var(--border); border-radius: var(--radius); background: var(--bg-card); overflow-y: auto; font-size: 13px; }
.drawer-footer { padding: 14px 20px; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; gap: 8px; }
.hidden-file-input { display: none; }
.upload-file-row { display: flex; gap: 12px; width: 100%; }
.upload-file-row :deep(.el-input) { flex: 1; }
.dialog-hint { margin: 8px 0 0; font-size: 12px; line-height: 1.5; color: var(--text-3); }

@media (max-width: 768px) {
  .page-header { flex-direction: column; gap: 16px; }
  .header-actions { width: 100%; }
  .upload-file-row { flex-direction: column; }
  .detail-drawer { width: min(100%, 520px); }
}
</style>
