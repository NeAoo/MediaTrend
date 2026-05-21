export type AnyConfig = Record<string, any>;

export type PageKey = 'dashboard' | 'sources' | 'scoring' | 'hotrank' | 'history' | 'reports' | 'system';

export type ConfigResponse = {
  config: AnyConfig;
  masked_api_key: string;
  has_api_key: boolean;
};

export type PromptResponse = {
  system_prompt: string;
  user_prompt: string;
  warnings: string[];
};

export type JobSnapshot = {
  job_id: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled';
  run_mode: 'collect_only' | 'collect_score_report';
  execution_mode: 'serial' | 'parallel';
  created_at: string;
  updated_at: string;
  cancel_requested: boolean;
  events_count: number;
  artifacts: Record<string, any>;
  errors: string[];
  warnings: string[];
};

export type JobEvent = {
  job_id: string;
  type: string;
  message: string;
  source?: string;
  unit_type?: 'source' | 'keyword' | 'account' | 'stage';
  unit_name?: string;
  status?: string;
  current_count?: number;
  max_count?: number;
  expected_min_count?: number;
  progress?: number;
  created_at: string;
};

export type SourceAuthState = {
  source: string;
  display_name: string;
  requires_login: boolean;
  status: 'not_required' | 'online' | 'offline' | 'login_waiting' | 'checking' | 'error';
  label: string;
  message: string;
  login_url: string;
  checked_by: string;
};

export type SystemStatus = {
  project_root: string;
  config_path: string;
  env_path: string;
  jobs_root: string;
  has_api_key: boolean;
  enabled_sources: string[];
};

export type ReportFile = {
  name: string;
  path: string;
  size: number;
  updated_at: number;
};
