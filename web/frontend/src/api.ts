import type { AnyConfig, ConfigResponse, JobEvent, JobSnapshot, PromptResponse, ReportFile, SourceAuthState, SystemStatus } from './types';

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || detail.message || `请求失败：${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  getConfig: () => request<ConfigResponse>('/api/config'),
  saveConfig: (config: AnyConfig, apiKey?: string) =>
    request<ConfigResponse>('/api/config', {
      method: 'PUT',
      body: JSON.stringify({ config, api_key: apiKey }),
    }),
  getPrompts: () => request<PromptResponse>('/api/prompts'),
  savePrompts: (systemPrompt: string, userPrompt: string) =>
    request<PromptResponse>('/api/prompts', {
      method: 'PUT',
      body: JSON.stringify({ system_prompt: systemPrompt, user_prompt: userPrompt }),
    }),
  getHotrankPrompts: () => request<PromptResponse>('/api/hotrank/prompts'),
  saveHotrankPrompts: (systemPrompt: string, userPrompt: string) =>
    request<PromptResponse>('/api/hotrank/prompts', {
      method: 'PUT',
      body: JSON.stringify({ system_prompt: systemPrompt, user_prompt: userPrompt }),
    }),
  testScoring: () => request<{ ok: boolean; model: string; available_count: number }>('/api/scoring/test', { method: 'POST' }),
  createJob: (runMode: 'collect_only' | 'collect_score_report', executionMode: 'serial' | 'parallel') =>
    request<JobSnapshot>('/api/jobs', {
      method: 'POST',
      body: JSON.stringify({ run_mode: runMode, execution_mode: executionMode }),
    }),
  cancelJob: (jobId: string) => request<JobSnapshot>(`/api/jobs/${jobId}/cancel`, { method: 'POST' }),
  listJobs: () => request<JobSnapshot[]>('/api/jobs'),
  getJob: (jobId: string) => request<JobSnapshot>(`/api/jobs/${jobId}`),
  getJobEvents: (jobId: string, start = 0) => request<JobEvent[]>(`/api/jobs/${jobId}/events?start=${start}`),
  getAuthStates: () => request<SourceAuthState[]>('/api/auth/sources'),
  getAuthState: (source: string) => request<SourceAuthState>(`/api/auth/sources/${source}`),
  startSourceLogin: (source: string) => request<SourceAuthState>(`/api/auth/sources/${source}/login`, { method: 'POST' }),
  pollSourceLogin: (source: string) => request<SourceAuthState>(`/api/auth/sources/${source}/login`),
  finishSourceLogin: (source: string) => request<SourceAuthState>(`/api/auth/sources/${source}/login/finish`, { method: 'POST' }),
  listReports: () => request<ReportFile[]>('/api/reports'),
  getSystem: () => request<SystemStatus>('/api/system'),
};
