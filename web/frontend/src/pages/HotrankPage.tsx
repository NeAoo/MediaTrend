import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, BarChart3, Clock3, ExternalLink, Layers3, RefreshCw } from 'lucide-react';
import { hotrankApi } from '../hotrankApi';
import type { HotrankRunStatus, HotrankSnapshot, HotrankThemeSearch, HotrankTrendTopic } from '../hotrankTypes';

const CHANNEL_OPTIONS = [
  { id: 1, name: '微博' },
  { id: 2, name: '知乎' },
  { id: 3, name: '百度' },
  { id: 4, name: '抖音' },
  { id: 5, name: '头条' },
  { id: 7, name: 'B站' },
];

const SCORE_PART_LABELS: Record<string, string> = {
  rank: '排名',
  hot: '热度',
  cross_platform: '跨平台',
  freshness: '新鲜度',
};

type ThemeTrendSummary = {
  category: string;
  totalScore: number;
  topicCount: number;
  evidenceCount: number;
  topSearches: HotrankThemeSearch[];
};

export function HotrankPage() {
  const [selectedChannels, setSelectedChannels] = useState<number[]>(CHANNEL_OPTIONS.map((item) => item.id));
  const [snapshot, setSnapshot] = useState<HotrankSnapshot | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [runStatus, setRunStatus] = useState<HotrankRunStatus | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let ignore = false;
    async function loadLatest() {
      setInitialLoading(true);
      setError('');
      try {
        const response = await hotrankApi.getLatest();
        if (!ignore) {
          setSnapshot(response.snapshot);
        }
      } catch (err) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!ignore) {
          setInitialLoading(false);
        }
      }
    }
    void loadLatest();
    return () => {
      ignore = true;
    };
  }, []);

  const maxScore = useMemo(() => {
    return Math.max(1, ...((snapshot?.top_trends || []).map((topic) => topic.trend_score)));
  }, [snapshot]);

  const platformCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const topic of snapshot?.top_trends || []) {
      for (const evidence of topic.evidence) {
        counts.set(evidence.channel_name, (counts.get(evidence.channel_name) || 0) + 1);
      }
    }
    return Array.from(counts.entries()).sort((left, right) => right[1] - left[1]);
  }, [snapshot]);

  const themeSummaries = useMemo(() => {
    if (snapshot?.theme_summaries?.length) {
      return snapshot.theme_summaries.map((summary) => ({
        category: summary.category,
        totalScore: summary.total_score,
        topicCount: summary.topic_count,
        evidenceCount: summary.evidence_count,
        topSearches: summary.top_searches,
      })).slice(0, 5);
    }
    const grouped = new Map<string, ThemeTrendSummary>();
    for (const topic of snapshot?.top_trends || []) {
      const category = topic.category || '其它';
      const current = grouped.get(category) || {
        category,
        totalScore: 0,
        topicCount: 0,
        evidenceCount: 0,
        topSearches: [],
      };
      current.totalScore += topic.trend_score;
      current.topicCount += 1;
      current.evidenceCount += topic.evidence_count;
      current.topSearches.push(topicToThemeSearch(topic));
      grouped.set(category, current);
    }
    return Array.from(grouped.values())
      .map((summary) => ({
        ...summary,
        totalScore: Number(summary.totalScore.toFixed(2)),
        topSearches: summary.topSearches
          .sort((left, right) => right.trend_score - left.trend_score)
          .slice(0, 3),
      }))
      .sort((left, right) => (
        right.totalScore - left.totalScore
        || right.topicCount - left.topicCount
        || right.evidenceCount - left.evidenceCount
        || left.category.localeCompare(right.category, 'zh-CN')
      ))
      .slice(0, 5);
  }, [snapshot]);

  const maxThemeScore = useMemo(() => {
    return Math.max(1, ...themeSummaries.map((theme) => theme.totalScore));
  }, [themeSummaries]);

  async function refreshHotrank() {
    setRefreshing(true);
    setRunStatus(null);
    setError('');
    try {
      let status = await hotrankApi.startRun({
        channel_ids: selectedChannels,
        limit: 10,
      });
      setRunStatus(status);
      while (!['succeeded', 'failed'].includes(status.status)) {
        await delay(1200);
        status = await hotrankApi.getRunStatus(status.run_id);
        setRunStatus(status);
      }
      if (status.status === 'failed') {
        throw new Error(status.error || '热榜刷新失败');
      }
      if (status.snapshot) {
        setSnapshot(status.snapshot);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRefreshing(false);
    }
  }

  function toggleChannel(channelId: number) {
    setSelectedChannels((current) => {
      if (current.includes(channelId)) {
        return current.length === 1 ? current : current.filter((id) => id !== channelId);
      }
      return [...current, channelId].sort((left, right) => left - right);
    });
  }

  return (
    <div className="stack hotrank-page">
      <section className="hero-panel hotrank-hero">
        <div>
          <p className="eyebrow">CimiData Hotrank</p>
          <h1>全网热榜</h1>
          <p className="subtle">
            {snapshot ? `最近快照 ${formatDateTime(snapshot.created_at)}，聚合 ${snapshot.channels_succeeded.length} 个平台。` : '暂无热榜快照。'}
          </p>
        </div>
        <div className="hero-actions hotrank-actions">
          <div className="channel-toggle-group" aria-label="热榜渠道">
            {CHANNEL_OPTIONS.map((channel) => (
              <button
                aria-pressed={selectedChannels.includes(channel.id)}
                className={`mini-toggle ${selectedChannels.includes(channel.id) ? 'on' : ''}`}
                key={channel.id}
                onClick={() => toggleChannel(channel.id)}
                type="button"
              >
                {channel.name}
              </button>
            ))}
          </div>
          <button className="primary-btn" disabled={refreshing} onClick={refreshHotrank} type="button">
            <RefreshCw className={refreshing ? 'spin' : ''} size={17} />
            {refreshing ? '刷新中' : '刷新热榜'}
          </button>
        </div>
      </section>

      {error && <div className="alert error">{error}</div>}
      {!refreshing && snapshot?.warnings.map((warning) => (
        <div className="alert warning" key={warning}>
          <AlertTriangle size={16} />
          {warning}
        </div>
      ))}
      {runStatus && <HotrankRunProgress status={runStatus} />}

      {initialLoading && <div className="loading-line">读取热榜快照中...</div>}

      {!initialLoading && !snapshot && (
        <section className="empty-state hotrank-empty">
          <strong>暂无快照</strong>
          <button className="primary-btn" disabled={refreshing} onClick={refreshHotrank} type="button">
            <RefreshCw className={refreshing ? 'spin' : ''} size={17} />
            刷新热榜
          </button>
        </section>
      )}

      {snapshot && (
        <>
          <section className="metrics-grid hotrank-metrics">
            <MetricCard label="平台" value={`${snapshot.channels_succeeded.length}/${snapshot.channels_requested.length}`} />
            <MetricCard label="原始条目" value={String(snapshot.raw_item_count)} />
            <MetricCard label="趋势主题" value={String(snapshot.top_trends.length)} />
            <MetricCard label="失败渠道" value={String(snapshot.channels_failed.length)} tone={snapshot.channels_failed.length ? 'red' : 'green'} />
          </section>

          <section className="hotrank-main-panel theme-trend-panel">
            <div className="section-head compact">
              <div>
                <p className="eyebrow">Theme Pulse</p>
                <h2>当前主题热度</h2>
              </div>
              <span className="status-pill running">
                <BarChart3 size={14} />
                Top 5
              </span>
            </div>
            <div className="theme-bar-list">
              {themeSummaries.map((theme, index) => (
                <ThemeTrendRow
                  index={index}
                  key={theme.category}
                  maxScore={maxThemeScore}
                  theme={theme}
                />
              ))}
            </div>
          </section>

          <section className="hotrank-layout">
            <div className="hotrank-main-panel">
              <div className="section-head compact">
                <div>
                  <p className="eyebrow">Top 10</p>
                  <h2>当前搜索趋势</h2>
                </div>
                <span className="status-pill running">
                  <Clock3 size={14} />
                  {formatDateTime(snapshot.created_at)}
                </span>
              </div>
              <div className="trend-chart-list">
                {snapshot.top_trends.map((topic, index) => (
                  <TrendRow key={topic.id} index={index} maxScore={maxScore} topic={topic} />
                ))}
              </div>
            </div>

            <aside className="hotrank-side-panel">
              <div className="side-block">
                <h3>平台覆盖</h3>
                <div className="platform-list">
                  {platformCounts.map(([name, count]) => (
                    <div className="platform-row" key={name}>
                      <span>{name}</span>
                      <strong>{count}</strong>
                    </div>
                  ))}
                </div>
              </div>
              <div className="side-block">
                <h3>分类分布</h3>
                <div className="category-list">
                  {Object.entries(snapshot.category_counts).map(([category, count]) => (
                    <div className="category-row" key={category}>
                      <span>{category}</span>
                      <strong>{count}</strong>
                    </div>
                  ))}
                </div>
              </div>
            </aside>
          </section>

          <section className="hotrank-main-panel">
            <div className="section-head compact">
              <div>
                <p className="eyebrow">Evidence</p>
                <h2>来源明细</h2>
              </div>
              <span className="status-pill succeeded">
                <Layers3 size={14} />
                {snapshot.top_trends.reduce((total, topic) => total + topic.evidence_count, 0)}
              </span>
            </div>
            <div className="evidence-topic-list">
              {snapshot.top_trends.map((topic, index) => (
                <details className="evidence-topic" key={topic.id}>
                  <summary>
                    <span>{index + 1}</span>
                    <strong>{topic.title}</strong>
                    <em>{topic.platform_count} 平台</em>
                  </summary>
                  <div className="evidence-grid">
                    {topic.evidence.map((item) => (
                      <a className="evidence-card" href={item.url || '#'} key={`${item.channel_id}-${item.rank}-${item.title}`} rel="noreferrer" target="_blank">
                        <span className="status-pill">{item.channel_name} #{item.rank}</span>
                        <strong>{item.title}</strong>
                        <small>{formatHotValue(item.hot_value, item.hot)}</small>
                        <ExternalLink size={14} />
                      </a>
                    ))}
                  </div>
                </details>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function MetricCard({ label, value, tone }: { label: string; value: string; tone?: 'green' | 'red' }) {
  return (
    <div className={`metric-card hotrank-metric ${tone || ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function HotrankRunProgress({ status }: { status: HotrankRunStatus }) {
  const percent = Math.round((status.progress || 0) * 100);
  const isClassifying = status.status === 'classifying';
  return (
    <section className="hotrank-run-progress">
      <div className="run-progress-head">
        <div>
          <p className="eyebrow">Run Progress</p>
          <h3>{status.message || statusLabel(status.status)}</h3>
        </div>
        <strong>{percent}%</strong>
      </div>
      <div className="run-progress-track">
        <div className="run-progress-fill" style={{ width: `${Math.max(2, percent)}%` }} />
      </div>
      <div className="run-progress-meta">
        <span>状态：{statusLabel(status.status)}</span>
        {isClassifying && <span>分类：{status.classified_topics}/{status.total_topics}</span>}
        {status.estimated_seconds_remaining !== null && status.estimated_seconds_remaining !== undefined && (
          <span>预计剩余：{formatDuration(status.estimated_seconds_remaining)}</span>
        )}
        <span>任务：{status.run_id}</span>
      </div>
      {status.error && <div className="alert error">{status.error}</div>}
    </section>
  );
}

function TrendRow({ topic, index, maxScore }: { topic: HotrankTrendTopic; index: number; maxScore: number }) {
  const width = `${Math.max(8, Math.round((topic.trend_score / maxScore) * 100))}%`;
  return (
    <article className="trend-chart-row">
      <div className="trend-chart-rank">{index + 1}</div>
      <div className="trend-chart-main">
        <div className="trend-chart-head">
          <div>
            <strong>{topic.title}</strong>
            <span>{topic.category}</span>
          </div>
          <em>{topic.trend_score.toFixed(1)}</em>
        </div>
        <div className="trend-bar-track">
          <div className="trend-bar-fill" style={{ width }} />
        </div>
        <div className="trend-meta">
          <span>{topic.platform_count} 平台</span>
          <span>{topic.evidence_count} 条证据</span>
          <span>{formatHotValue(topic.total_hot_value, '')}</span>
        </div>
        <div className="score-parts">
          {Object.entries(topic.score_parts).map(([key, value]) => (
            <span key={key}>
              {SCORE_PART_LABELS[key] || key} {Math.round(value)}
            </span>
          ))}
        </div>
      </div>
    </article>
  );
}

function ThemeTrendRow({
  theme,
  index,
  maxScore,
}: {
  theme: ThemeTrendSummary;
  index: number;
  maxScore: number;
}) {
  const width = `${Math.max(8, Math.round((theme.totalScore / maxScore) * 100))}%`;
  return (
    <article className="theme-bar-card">
      <div className="theme-bar-head">
        <span>{String(index + 1).padStart(2, '0')}</span>
        <strong>{theme.category}</strong>
        <em>{theme.topicCount} 个趋势 · {theme.evidenceCount} 条证据</em>
        <b>{theme.totalScore.toFixed(1)}</b>
      </div>
      <div className="theme-bar-track">
        <div className="theme-bar-fill" style={{ width }} />
      </div>
      <div className="theme-topic-list">
        {theme.topSearches.map((topic, topicIndex) => (
          <span key={topic.id}>
            <em>{topicIndex + 1}</em>
            {topic.title}
          </span>
        ))}
      </div>
    </article>
  );
}

function topicToThemeSearch(topic: HotrankTrendTopic): HotrankThemeSearch {
  return {
    id: topic.id,
    title: topic.title,
    trend_score: topic.trend_score,
    platform_count: topic.platform_count,
    evidence_count: topic.evidence_count,
    total_hot_value: topic.total_hot_value,
  };
}

function formatHotValue(value: number | null | undefined, fallback: string) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value <= 0) {
    return fallback || '-';
  }
  if (value >= 100_000_000) {
    return `${(value / 100_000_000).toFixed(1)}亿`;
  }
  if (value >= 10_000) {
    return `${(value / 10_000).toFixed(1)}万`;
  }
  return new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 0 }).format(value);
}

function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return '-';
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(parsed);
}

function statusLabel(status: HotrankRunStatus['status']) {
  const labels: Record<HotrankRunStatus['status'], string> = {
    queued: '排队中',
    fetching: '拉取热榜',
    classifying: 'AI 分类',
    saving: '保存快照',
    succeeded: '已完成',
    failed: '失败',
  };
  return labels[status];
}

function formatDuration(seconds: number) {
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return '马上完成';
  }
  if (seconds < 60) {
    return `${Math.ceil(seconds)} 秒`;
  }
  const minutes = Math.floor(seconds / 60);
  const restSeconds = Math.ceil(seconds % 60);
  return `${minutes} 分 ${String(restSeconds).padStart(2, '0')} 秒`;
}

function delay(ms: number) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}
