export type HotrankTrendEvidence = {
  channel_id: number;
  channel_name: string;
  rank: number;
  title: string;
  url: string;
  hot: string;
  hot_value: number | null;
  hot_tag: string;
  summary: string;
  created_at: string | null;
};

export type HotrankTrendTopic = {
  id: string;
  title: string;
  category: string;
  trend_score: number;
  platform_count: number;
  evidence_count: number;
  total_hot_value: number;
  latest_created_at: string | null;
  channels: string[];
  score_parts: Record<string, number>;
  evidence: HotrankTrendEvidence[];
};

export type HotrankThemeSearch = {
  id: string;
  title: string;
  trend_score: number;
  platform_count: number;
  evidence_count: number;
  total_hot_value: number;
};

export type HotrankThemeSummary = {
  category: string;
  total_score: number;
  topic_count: number;
  evidence_count: number;
  top_searches: HotrankThemeSearch[];
};

export type HotrankSnapshot = {
  run_id: string;
  created_at: string;
  source: string;
  channels_requested: number[];
  channels_succeeded: number[];
  channels_failed: number[];
  raw_item_count: number;
  top_trends: HotrankTrendTopic[];
  theme_summaries?: HotrankThemeSummary[];
  category_counts: Record<string, number>;
  warnings: string[];
  errors: string[];
};

export type HotrankLatestResponse = {
  snapshot: HotrankSnapshot | null;
};

export type HotrankRunRequest = {
  channel_ids?: number[];
  limit?: number;
};

export type HotrankRunResponse = {
  snapshot: HotrankSnapshot;
};

export type HotrankRunStatusValue =
  | 'queued'
  | 'fetching'
  | 'classifying'
  | 'saving'
  | 'succeeded'
  | 'failed';

export type HotrankRunStatus = {
  run_id: string;
  status: HotrankRunStatusValue;
  message: string;
  progress: number;
  channel_ids: number[];
  limit: number;
  total_topics: number;
  classified_topics: number;
  estimated_seconds_remaining: number | null;
  snapshot: HotrankSnapshot | null;
  error: string;
  warnings: string[];
  created_at: string;
  updated_at: string;
};
