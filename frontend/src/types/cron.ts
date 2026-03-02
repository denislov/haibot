// ── Cron ─────────────────────────────────────────────────────────────────────
export interface ScheduleSpec {
  type: 'cron'
  cron: string
  timezone: string
}

export interface DispatchTarget {
  user_id: string
  session_id: string
}

export interface DispatchSpec {
  type: 'channel'
  channel: string
  target: DispatchTarget
  mode: 'stream' | 'final'
  meta: Record<string, unknown>
}

export interface JobRuntimeSpec {
  max_concurrency: number
  timeout_seconds: number
  misfire_grace_seconds: number
}

export interface CronJobRequest {
  input: object
  session_id?: string
  user_id?: string
}

export interface CronJobSpec {
  id: string
  name: string
  enabled: boolean
  schedule: ScheduleSpec
  task_type: 'text' | 'agent'
  text?: string
  request?: CronJobRequest
  dispatch: DispatchSpec
  runtime: JobRuntimeSpec
  meta: Record<string, unknown>
}

export interface CronJobState {
  next_run_at?: string
  last_run_at?: string
  last_status?: 'success' | 'error' | 'running' | 'skipped'
  last_error?: string
}

export interface CronJobView {
  spec: CronJobSpec
  state: CronJobState
}
