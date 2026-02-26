<template>
  <div class="page">
    <div class="page-header">
      <div><h1 class="page-title">{{ $t('settings.skills.title') }}</h1><p class="page-desc">{{ $t('settings.skills.desc') }}</p></div>
      <el-button type="primary" @click="createDialogVisible = true"><el-icon><Plus /></el-icon>{{ $t('settings.skills.createSkill') }}</el-button>
    </div>

    <div v-if="loading" class="loading-state"><el-icon class="is-loading"><Loading /></el-icon></div>

    <div v-else class="skills-grid">
      <div v-for="skill in skills" :key="skill.name" class="skill-card" :class="{ enabled: skill.enabled }" @click="openDetail(skill)">
        <div class="skill-card-header">
          <span class="skill-name">{{ skill.name }}</span>
          <span class="skill-status" :class="skill.enabled ? 'on' : 'off'">{{ skill.enabled ? $t('common.enabled') : $t('common.disabled') }}</span>
        </div>
        <div class="skill-meta">{{ $t('settings.skills.source') }}: {{ skill.source || 'builtin' }}</div>
        <div class="skill-card-footer" @click.stop>
          <el-button v-if="skill.enabled" size="small" @click="toggleSkill(skill, false)">{{ $t('common.disable') }}</el-button>
          <el-button v-else size="small" type="primary" @click="toggleSkill(skill, true)">{{ $t('common.enable') }}</el-button>
          <el-button v-if="skill.source !== 'builtin'" size="small" type="danger" link @click="handleDelete(skill)"><el-icon><Delete /></el-icon></el-button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { renderMarkdownWithFrontMatter } from '@/utils/useMarkdown'
import { listSkills, enableSkill, disableSkill, deleteSkill, createSkill, updateSkill } from '@/api/skills'
import type { SkillSpec } from '@/types'

const skills = ref<SkillSpec[]>([])
const loading = ref(false)
const creating = ref(false)
const saving = ref(false)
const createDialogVisible = ref(false)
const detailSkill = ref<SkillSpec | null>(null)
const editContent = ref('')
const contentTab = ref<'edit' | 'preview'>('edit')
const createForm = reactive({ name: '', content: '' })

async function loadSkills() {
  loading.value = true
  try { skills.value = await listSkills() }
  catch (e: unknown) { ElMessage.error(String(e)) }
  finally { loading.value = false }
}

async function toggleSkill(skill: SkillSpec, enable: boolean) {
  try { enable ? await enableSkill(skill.name) : await disableSkill(skill.name); await loadSkills() }
  catch (e: unknown) { ElMessage.error(String(e)) }
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
  catch (e: unknown) { ElMessage.error(String(e)) }
  finally { creating.value = false }
}

function openDetail(skill: SkillSpec) { detailSkill.value = skill; editContent.value = skill.content; contentTab.value = 'edit' }
function closeDetail() { detailSkill.value = null }

async function saveSkill() {
  if (!detailSkill.value) return
  saving.value = true
  try { await updateSkill(detailSkill.value.name, editContent.value); ElMessage.success('Saved') }
  catch (e: unknown) { ElMessage.error(String(e)) }
  finally { saving.value = false }
}

onMounted(loadSkills)
</script>

<style scoped>
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text-1); }
.page-desc { font-size: 13px; color: var(--text-3); margin-top: 4px; }
.loading-state { display: flex; justify-content: center; padding: 60px 0; color: var(--text-4); font-size: 24px; }
.skills-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
.skill-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 16px; cursor: pointer; transition: box-shadow var(--transition-fast); }
.skill-card:hover { box-shadow: var(--shadow-md); }
.skill-card.enabled { border-color: var(--primary); }
.skill-card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.skill-name { font-size: 13px; font-weight: 600; color: var(--text-1); }
.skill-status { font-size: 11px; padding: 2px 7px; border-radius: var(--radius-sm); }
.skill-status.on { color: var(--success); background: var(--success-light); }
.skill-status.off { color: var(--text-4); background: var(--bg); }
.skill-meta { font-size: 12px; color: var(--text-3); }
.skill-card-footer { display: flex; justify-content: flex-end; gap: 6px; margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--border); }
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
</style>
