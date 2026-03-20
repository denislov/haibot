import api from './index'
import type { CronJobSpec, CronJobView } from '@/types'

export const listJobs = () =>
  api.get<CronJobSpec[]>('/cron/jobs').then((r) => r.data)

export const getJob = (id: string) =>
  api.get<CronJobView>(`/cron/jobs/${id}`).then((r) => r.data)

export const createJob = (data: Omit<CronJobSpec, 'id'>) =>
  api.post<CronJobSpec>('/cron/jobs', data).then((r) => r.data)

export const updateJob = (id: string, data: CronJobSpec) =>
  api.put<CronJobSpec>(`/cron/jobs/${id}`, data).then((r) => r.data)

export const deleteJob = (id: string) =>
  api.delete<{ deleted: boolean }>(`/cron/jobs/${id}`).then((r) => r.data)

export const pauseJob = (id: string) =>
  api.post<{ paused: boolean }>(`/cron/jobs/${id}/pause`).then((r) => r.data)

export const resumeJob = (id: string) =>
  api.post<{ resumed: boolean }>(`/cron/jobs/${id}/resume`).then((r) => r.data)

export const runJob = (id: string) =>
  api.post<{ started: boolean }>(`/cron/jobs/${id}/run`).then((r) => r.data)

export const getJobState = (id: string) =>
  api.get(`/cron/jobs/${id}/state`).then((r) => r.data)
