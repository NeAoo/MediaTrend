import { type Dispatch, type SetStateAction, useMemo, useState } from 'react';
import { Play, Settings2 } from 'lucide-react';
import { api } from '../api';
import { SourceProgressCard, type UnitProgress } from '../components/SourceProgressCard';
import type { AnyConfig, JobEvent, JobSnapshot, PageKey } from '../types';

const sourceLabels: Record<string, string> = {
  wechat: '搜狗微信关键词',
  wechat_mp: '微信公众号账号',
  xiaohongshu: '小红书',
  zhihu: '知乎',
  google_news: 'Google News',
  aihot: 'AI HOT',
};

function sourceUnits(
  config: AnyConfig,
  source: string,
  status: UnitProgress['status'],
  unitEvents: Map<string, JobEvent>,
): UnitProgress[] {
  const unitStatus = status;
  const withEvent = (unit: UnitProgress): UnitProgress => {
    const event = unitEvents.get(`${source}:${unit.type}:${unit.name}`);
    if (!event) return unit;
    return {
      ...unit,
      current: event.current_count ?? unit.current,
      max: event.max_count ?? unit.max,
      expectedMin: event.expected_min_count ?? unit.expectedMin,
      status: (event.status as UnitProgress['status']) || unit.status,
    };
  };
  if (source === 'wechat') {
    const item = config.wechat?.keyword_search || {};
    return (item.keywords || []).map((name: string) => ({
      name,
      type: '关键词',
      current: 0,
      max: item.max_results_per_keyword || 10,
      expectedMin: item.expected_min_results || 3,
      status: unitStatus,
    })).map(withEvent);
  }
  if (source === 'wechat_mp') {
    const item = config.wechat?.account_crawl || {};
    return (item.accounts || []).map((name: string) => ({
      name,
      type: '账号',
      current: 0,
      max: item.max_results_per_account || 10,
      expectedMin: item.expected_min_results || 3,
      status: unitStatus,
    })).map(withEvent);
  }
  if (source === 'xiaohongshu' || source === 'zhihu') {
    const sourceConfig = config[source] || {};
    const keyword = sourceConfig.keyword_search || {};
    const account = sourceConfig.account_crawl || {};
    return [
      ...(keyword.keywords || []).map((name: string) => ({
        name,
        type: '关键词' as const,
        current: 0,
        max: keyword.max_results_per_keyword || 10,
        expectedMin: keyword.expected_min_results || 3,
        status: unitStatus,
      })),
      ...(account.creator_urls || []).map((name: string) => ({
        name,
        type: '账号' as const,
        current: 0,
        max: account.max_results_per_account || 10,
        expectedMin: account.expected_min_results || 3,
        status: unitStatus,
      })),
    ].map(withEvent);
  }
  if (source === 'google_news') {
    const item = config.google_news || {};
    return (item.keywords || []).map((name: string) => ({
      name,
      type: '关键词',
      current: 0,
      max: item.max_results_per_keyword || 10,
      expectedMin: item.expected_min_results || 3,
      status: unitStatus,
    })).map(withEvent);
  }
  const item = config.aihot || {};
  const keywords = item.keywords?.length ? item.keywords : ['精选池'];
  return keywords.map((name: string) => ({
    name,
    type: '来源',
    current: 0,
    max: item.max_results_per_query || 50,
    expectedMin: item.expected_min_results || 3,
    status: unitStatus,
  })).map(withEvent);
}

type DashboardPageProps = {
  config: AnyConfig;
  events: JobEvent[];
  isJobRunning: boolean;
  job: JobSnapshot | null;
  onEventsChange: Dispatch<SetStateAction<JobEvent[]>>;
  onJobChange: (job: JobSnapshot | null) => void;
  onNavigate: (page: PageKey) => void;
};

export function DashboardPage({
  config,
  events,
  isJobRunning,
  job,
  onEventsChange,
  onJobChange,
  onNavigate,
}: DashboardPageProps) {
  const [executionMode, setExecutionMode] = useState<'serial' | 'parallel'>('parallel');
  const [runMode, setRunMode] = useState<'collect_only' | 'collect_score_report'>('collect_score_report');
  const [error, setError] = useState('');

  const enabledSources: string[] = config.enabled_sources || [];
  const eventBySource = useMemo(() => {
    const map = new Map<string, JobEvent>();
    events.forEach((event) => {
      if (event.source && event.unit_type === 'source' && event.unit_name === event.source) {
        map.set(event.source, event);
      }
    });
    return map;
  }, [events]);
  const eventByUnit = useMemo(() => {
    const map = new Map<string, JobEvent>();
    events.forEach((event) => {
      if (!event.source || !event.unit_type || !event.unit_name || event.unit_name === event.source) return;
      const typeLabel = event.unit_type === 'keyword' ? '关键词' : event.unit_type === 'account' ? '账号' : '来源';
      map.set(`${event.source}:${typeLabel}:${event.unit_name}`, event);
    });
    return map;
  }, [events]);

  async function startJob() {
    if (isJobRunning) {
      setError('已有任务正在运行，等当前任务完成后再开始新的抓取。');
      return;
    }
    setError('');
    onEventsChange([]);
    try {
      const created = await api.createJob(runMode, executionMode);
      onJobChange(created);
      const source = new EventSource(`/api/jobs/${created.job_id}/stream`);
      source.onmessage = (message) => {
        const event = JSON.parse(message.data) as JobEvent;
        onEventsChange((previous) => [...previous, event]);
      };
      source.addEventListener('done', (message) => {
        onJobChange(JSON.parse((message as MessageEvent).data));
        source.close();
      });
      source.onerror = () => {
        source.close();
      };
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <div className="stack">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">workspace</p>
          <h1>AITrend 采集控制台</h1>
          <p className="subtle">配置默认写回根目录 config.yaml；任务可以串行或按来源并行执行。</p>
        </div>
        <div className="hero-actions">
          <div className="segmented">
            <button className={executionMode === 'parallel' ? 'active' : ''} disabled={isJobRunning} onClick={() => setExecutionMode('parallel')} type="button">并行</button>
            <button className={executionMode === 'serial' ? 'active' : ''} disabled={isJobRunning} onClick={() => setExecutionMode('serial')} type="button">串行</button>
          </div>
          <div className="segmented">
            <button className={runMode === 'collect_score_report' ? 'active' : ''} disabled={isJobRunning} onClick={() => setRunMode('collect_score_report')} type="button">采集+打分</button>
            <button className={runMode === 'collect_only' ? 'active' : ''} disabled={isJobRunning} onClick={() => setRunMode('collect_only')} type="button">只采集</button>
          </div>
          <button className="primary-btn" type="button" disabled={isJobRunning} onClick={startJob}>
            <Play size={16} />{isJobRunning ? '任务运行中' : '开始抓取'}
          </button>
        </div>
      </section>

      {error && <div className="alert error">{error}</div>}

      <section className="metrics-grid">
        <div className="metric-card"><span>启用来源</span><strong>{enabledSources.length}</strong></div>
        <div className="metric-card"><span>执行模式</span><strong>{executionMode === 'parallel' ? '并行' : '串行'}</strong></div>
        <div className="metric-card"><span>打分状态</span><strong>{config.scoring?.enabled && runMode === 'collect_score_report' ? '开启' : '关闭'}</strong></div>
        <div className="metric-card"><span>当前任务</span><strong>{job?.status || '未运行'}</strong></div>
      </section>

      <div className="section-head">
        <div>
          <p className="eyebrow">progress</p>
          <h2>来源进度</h2>
        </div>
        <button className="ghost-btn" type="button" onClick={() => onNavigate('sources')}><Settings2 size={16} />配置来源</button>
      </div>

      <section className="source-grid">
        {enabledSources.map((source) => {
          const event = eventBySource.get(source);
          const status = (event?.status as UnitProgress['status']) || 'idle';
          const progress = event?.progress !== undefined ? event.progress * 100 : 0;
          const current = event?.current_count || 0;
          return (
            <SourceProgressCard
              key={source}
              sourceName={sourceLabels[source] || source}
              progress={status === 'succeeded' ? 100 : progress}
              status={status}
              eta={status === 'running' ? '正在采集，预计随来源响应动态变化' : status === 'succeeded' ? '已完成' : '等待开始'}
              units={sourceUnits(config, source, status, eventByUnit)}
            />
          );
        })}
      </section>
    </div>
  );
}
