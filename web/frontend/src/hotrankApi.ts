import { request } from './api';
import type { HotrankLatestResponse, HotrankRunRequest, HotrankRunResponse, HotrankRunStatus } from './hotrankTypes';

export const hotrankApi = {
  getLatest: () => request<HotrankLatestResponse>('/api/hotrank/latest'),
  run: (payload: HotrankRunRequest) =>
    request<HotrankRunResponse>('/api/hotrank/runs', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  startRun: (payload: HotrankRunRequest) =>
    request<HotrankRunStatus>('/api/hotrank/runs/async', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getRunStatus: (runId: string) => request<HotrankRunStatus>(`/api/hotrank/runs/${runId}`),
};
