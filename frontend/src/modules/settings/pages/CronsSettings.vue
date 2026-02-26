<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">{{ $t('settings.crons.title') }}</h1>
        <p class="page-desc">{{ $t('settings.crons.desc') }}</p>
      </div>
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon>{{ $t('settings.crons.createJob') }}</el-button>
    </div>
    <div v-if="loading" class="loading-state"><el-icon class="is-loading"><Loading /></el-icon></div>
    <div v-else class="jobs-list">
      <div v-for="job in jobs" :key="job.spec.id" class="job-card" @click="openEdit(job)">
        <div class="job-header">
          <span class="job-name">{{ job.spec.name }}</span>
          <span class="job-status" :class="job.spec.enabled ? 'on' : 'off'">{{ job.spec.enabled ? $t('common.enabled') : $t('common.disabled') }}</span>
        </div>
        <div class="job-meta">
          <span class="mono">{{ job.spec.schedule.cron }}</span>
          <span v-if="job.state.next_run_at" class="dot-sep">·</span>
          <span v-if="job.state.next_run_at">Next: {{ new Date(job.state.next_run_at).toLocaleString() }}</span>
        </div>
        <div class="job-actions" @click.stop>
          <el-switch :model-value="job.spec.enabled" size="small" @change="toggleJob(job)" />
          <el-button size="small" link @click.stop="triggerJob(job)"><el-icon><VideoPlay /></el-icon>{{ $t('settings.crons.run') }}</el-button>
          <el-button size="small" link type="danger" @click.stop="handleDelete(job)"><el-icon><Delete /></el-icon></el-button>
        </div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="editingJob ? $t('settings.crons.editJob') : $t('settings.crons.createJob')" width="520px" destroy-on-close>
      <el-form :model="form" label-position="top">
        <el-form-item :label="$t('settings.crons.jobName')" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item :label="$t('settings.crons.cronExpr')" required>
          <el-input v-model="form.cron" placeholder="0 9 * * *" />
          <div class="form-hint">{{ $t('settings.crons.cronHint') }}</div>
        </el-form-item>
        <el-form-item :label="$t('settings.crons.timezone')"><el-input v-model="form.timezone" placeholder="Asia/Shanghai" /></el-form-item>
        <el-form-item :label="$t('settings.crons.taskType')">
          <el-radio-group v-model="form.task_type">
            <el-radio value="text">{{ $t('settings.crons.textMessage') }}</el-radio>
            <el-radio value="agent">{{ $t('settings.crons.agentQuery') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.task_type === 'text'" :label="$t('settings.crons.messageContent')"><el-input v-model="form.text" type="textarea" :rows="3" /></el-form-item>
        <el-form-item v-else :label="$t('settings.crons.queryContent')"><el-input v-model="form.queryInput" type="textarea" :rows="3" :placeholder="$t('settings.crons.queryPlaceholder')" /></el-form-item>
        <el-form-item :label="$t('settings.crons.channel')">
          <el-select v-model="form.channel" style="width: 100%">
            <el-option v-for="ch in ['console','dingtalk','feishu','qq','discord','imessage']" :key="ch" :value="ch" :label="ch" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="save">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listJobs, createJob, updateJob, deleteJob, pauseJob, resumeJob, runJob } from '@/api/crons'
import type { CronJobView, CronJobSpec } from '@/types'

const jobs = ref<CronJobView[]>([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editingJob = ref<CronJobView | null>(null)
const form = reactive({ name: '', cron: '', timezone: 'Asia/Shanghai', task_type: 'text' as 'text' | 'agent', text: '', queryInput: '', channel: 'console' })

async function loadJobs() {
  loading.value = true
  try { jobs.value = await listJobs() } catch (e: unknown) { ElMessage.error(String(e)) }
  finally { loading.value = false }
}

function openCreate() { editingJob.value = null; Object.assign(form, { name: '', cron: '', timezone: 'Asia/Shanghai', task_type: 'text', text: '', queryInput: '', channel: 'console' }); dialogVisible.value = true }

function openEdit(job: CronJobView) {
  editingJob.value = job
  Object.assign(form, { name: job.spec.name, cron: job.spec.schedule.cron, timezone: job.spec.schedule.timezone, task_type: job.spec.task_type, text: job.spec.text || '', queryInput: (job.spec.request?.input as string) || '', channel: job.spec.dispatch.channel })
  dialogVisible.value = true
}

function buildSpec(): Partial<CronJobSpec> {
  return {
    name: form.name,
    schedule: { type: 'cron', cron: form.cron, timezone: form.timezone },
    task_type: form.task_type,
    text: form.task_type === 'text' ? form.text : undefined,
    request: form.task_type === 'agent' ? { input: form.queryInput } : undefined,
    dispatch: { type: 'channel', channel: form.channel, target: { user_id: 'cron', session_id: '' }, mode: 'final', meta: {} },
    runtime: { max_concurrency: 1, timeout_seconds: 300, misfire_grace_seconds: 60 },
  }
}

async function save() {
  if (!form.name.trim()) { ElMessage.warning('Name required'); return }
  saving.value = true
  try {
    if (editingJob.value) await updateJob(editingJob.value.spec.id, buildSpec() as CronJobSpec)
    else await createJob(buildSpec() as CronJobSpec)
    dialogVisible.value = false; await loadJobs()
  } catch (e: unknown) { ElMessage.error(String(e)) }
  finally { saving.value = false }
}

async function toggleJob(job: CronJobView) {
  try { job.spec.enabled ? await pauseJob(job.spec.id) : await resumeJob(job.spec.id); await loadJobs() }
  catch (e: unknown) { ElMessage.error(String(e)) }
}

async function triggerJob(job: CronJobView) {
  try { await runJob(job.spec.id); ElMessage.success('Triggered') }
  catch (e: unknown) { ElMessage.error(String(e)) }
}

async function handleDelete(job: CronJobView) {
  try {
    await ElMessageBox.confirm(`Delete "${job.spec.name}"?`, 'Confirm', { type: 'warning' })
    await deleteJob(job.spec.id); await loadJobs()
  } catch { /* cancelled */ }
}

onMounted(loadJobs)
</script>

<style scoped>
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text-1); }
.page-desc { font-size: 13px; color: var(--text-3); margin-top: 4px; }
.loading-state { display: flex; justify-content: center; padding: 60px 0; color: var(--text-4); font-size: 24px; }
.jobs-list { display: flex; flex-direction: column; gap: 12px; }
.job-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 16px; cursor: pointer; transition: box-shadow var(--transition-fast); }
.job-card:hover { box-shadow: var(--shadow-md); }
.job-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.job-name { font-size: 14px; font-weight: 600; color: var(--text-1); }
.job-status { font-size: 11px; padding: 2px 7px; border-radius: var(--radius-sm); }
.job-status.on { color: var(--success); background: var(--success-light); }
.job-status.off { color: var(--text-4); background: var(--bg); }
.job-meta { font-size: 12px; color: var(--text-3); margin-bottom: 10px; }
.mono { font-family: 'Fira Code', Consolas, monospace; }
.dot-sep { margin: 0 6px; }
.job-actions { display: flex; align-items: center; gap: 12px; padding-top: 10px; border-top: 1px solid var(--border); }
.form-hint { font-size: 11px; color: var(--text-4); margin-top: 4px; }
</style>
