import { type Dispatch, type SetStateAction, useEffect, useMemo, useState } from 'react';
import { Play, RefreshCw, Save, Settings2, Square, X } from 'lucide-react';
import { api } from '../api';
import { SourceProgressCard, type UnitProgress } from '../components/SourceProgressCard';
import type { AnyConfig, JobEvent, JobSnapshot, PageKey, SourceAuthState } from '../types';

const sourceLabels: Record<string, string> = {
  wechat: '搜狗微信关键词',
  wechat_mp: '微信公众号账号',
  xiaohongshu: '小红书',
  zhihu: '知乎',
  google_news: 'Google News',
  aihot: 'AI HOT',
};

const JOB_POLL_INTERVAL_MS = 1500;
const AUTH_POLL_INTERVAL_MS = 2000;
const TERMINAL_JOB_STATUSES = new Set(['succeeded', 'failed', 'cancelled']);

function sleep(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

function sourceUnits(
  config: AnyConfig,
  source: string,
  status: UnitProgress['status'],
  unitEvents: Map<string, JobEvent>,
): UnitProgress[] {
  const unitStatus = status;
  const modeEnabled = (value: AnyConfig | undefined) => value?.enabled !== false;
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
    if (!modeEnabled(item)) return [];
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
    if (!modeEnabled(item)) return [];
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
      ...(modeEnabled(keyword) ? (keyword.keywords || []).map((name: string) => ({
        name,
        type: '关键词' as const,
        current: 0,
        max: keyword.max_results_per_keyword || 10,
        expectedMin: keyword.expected_min_results || 3,
        status: unitStatus,
      })) : []),
      ...(modeEnabled(account) ? (account.creator_urls || []).map((name: string) => ({
        name,
        type: '账号' as const,
        current: 0,
        max: account.max_results_per_account || 10,
        expectedMin: account.expected_min_results || 3,
        status: unitStatus,
      })) : []),
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
  return ['精选池'].map((name: string) => ({
    name,
    type: '来源' as const,
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
  onSaveConfig: (config: AnyConfig) => Promise<unknown>;
};

export function DashboardPage({
  config,
  events,
  isJobRunning,
  job,
  onEventsChange,
  onJobChange,
  onNavigate,
  onSaveConfig,
}: DashboardPageProps) {
  const [executionMode, setExecutionMode] = useState<'serial' | 'parallel'>(
    config.web?.default_execution_mode || 'parallel',
  );
  const [runMode, setRunMode] = useState<'collect_only' | 'collect_score_report'>(
    config.web?.default_run_mode || 'collect_score_report',
  );
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'warning' | 'error'>('success');
  const [isCancelling, setIsCancelling] = useState(false);
  const [authStates, setAuthStates] = useState<Record<string, SourceAuthState>>({});
  const [authError, setAuthError] = useState('');
  const [authCheckingAll, setAuthCheckingAll] = useState(false);
  const [loginModal, setLoginModal] = useState<SourceAuthState | null>(null);

  useEffect(() => {
    setExecutionMode(config.web?.default_execution_mode || 'parallel');
    setRunMode(config.web?.default_run_mode || 'collect_score_report');
  }, [config.web?.default_execution_mode, config.web?.default_run_mode]);

  useEffect(() => {
    if (!job || TERMINAL_JOB_STATUSES.has(job.status)) {
      setIsCancelling(false);
    }
  }, [job?.job_id, job?.status]);

  const enabledSources: string[] = config.enabled_sources || [];

  async function refreshAllAuthStates(showResultMessage = false) {
    setAuthError('');
    setAuthCheckingAll(true);
    try {
      const states = await api.getAuthStates();
      setAuthStates(Object.fromEntries(states.map((state) => [state.source, state])));
      if (showResultMessage) {
        setMessageType('success');
        setMessage('所有来源登录状态已重新检测。');
      }
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : String(err));
    } finally {
      setAuthCheckingAll(false);
    }
  }

  async function refreshSourceAuth(source: string) {
    setAuthStates((previous) => ({
      ...previous,
      [source]: {
        ...(previous[source] || {
          source,
          display_name: sourceLabels[source] || source,
          requires_login: true,
          label: '检测中',
          message: '正在检测登录状态。',
          login_url: '',
          checked_by: 'frontend',
        }),
        status: 'checking',
        label: '检测中',
      },
    }));
    try {
      const nextState = await api.getAuthState(source);
      setAuthStates((previous) => ({ ...previous, [source]: nextState }));
      if (loginModal?.source === source) setLoginModal(nextState);
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleAuthAction(source: string) {
    const currentState = authStates[source];
    if (!currentState) {
      try {
        const nextState = await api.getAuthState(source);
        setAuthStates((previous) => ({ ...previous, [source]: nextState }));
        if (nextState.requires_login) setLoginModal(nextState);
      } catch (err) {
        setAuthError(err instanceof Error ? err.message : String(err));
      }
      return;
    }
    if (!currentState.requires_login) return;
    setAuthError('');
    setLoginModal(currentState);
  }

  async function pollLoginNow() {
    if (!loginModal) return;
    setLoginModal({
      ...loginModal,
      status: 'checking',
      label: '检测中',
      message: '正在检测当前登录状态。',
    });
    try {
      const nextState = await api.pollSourceLogin(loginModal.source);
      setAuthStates((previous) => ({ ...previous, [loginModal.source]: nextState }));
      setLoginModal(nextState);
    } catch (err) {
      const errorText = err instanceof Error ? err.message : String(err);
      setAuthError(errorText);
      setLoginModal((current) => current ? {
        ...current,
        status: 'error',
        label: '检测失败',
        message: errorText,
      } : current);
    }
  }

  async function reopenLoginPage() {
    if (!loginModal) return;
    setAuthError('');
    setLoginModal({
      ...loginModal,
      status: 'checking',
      label: '打开中',
      message: '正在打开真实登录页。',
    });
    try {
      const nextState = await api.startSourceLogin(loginModal.source);
      setAuthStates((previous) => ({ ...previous, [loginModal.source]: nextState }));
      setLoginModal(nextState);
    } catch (err) {
      const errorText = err instanceof Error ? err.message : String(err);
      setAuthError(errorText);
      setLoginModal((current) => current ? {
        ...current,
        status: 'error',
        label: '打开失败',
        message: errorText,
      } : current);
    }
  }

  async function finishLogin() {
    if (!loginModal) return;
    try {
      const nextState = await api.finishSourceLogin(loginModal.source);
      setAuthStates((previous) => ({ ...previous, [loginModal.source]: nextState }));
      if (nextState.status === 'online' || nextState.status === 'not_required') {
        setLoginModal(null);
        setMessageType('success');
        setMessage(`${nextState.display_name} 登录状态已保存。`);
      } else {
        setLoginModal(nextState);
      }
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    void refreshAllAuthStates();
  }, [enabledSources.join('|')]);

  useEffect(() => {
    if (!loginModal || loginModal.status !== 'login_waiting') return;
    const timer = window.setInterval(async () => {
      try {
        const nextState = await api.pollSourceLogin(loginModal.source);
        setAuthStates((previous) => ({ ...previous, [loginModal.source]: nextState }));
        setLoginModal(nextState);
      } catch (err) {
        setAuthError(err instanceof Error ? err.message : String(err));
      }
    }, AUTH_POLL_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [loginModal?.source, loginModal?.status]);

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
    setMessage('');
    setIsCancelling(false);
    onEventsChange([]);
    void refreshAllAuthStates();
    try {
      const created = await api.createJob(runMode, executionMode);
      onJobChange(created);
      let eventCursor = 0;
      let latestJob = created;
      while (!TERMINAL_JOB_STATUSES.has(latestJob.status)) {
        const nextEvents = await api.getJobEvents(created.job_id, eventCursor);
        if (nextEvents.length > 0) {
          eventCursor += nextEvents.length;
          onEventsChange((previous) => [...previous, ...nextEvents]);
        }
        latestJob = await api.getJob(created.job_id);
        onJobChange(latestJob);
        if (!TERMINAL_JOB_STATUSES.has(latestJob.status)) {
          await sleep(JOB_POLL_INTERVAL_MS);
        }
      }
      const remainingEvents = await api.getJobEvents(created.job_id, eventCursor);
      if (remainingEvents.length > 0) {
        onEventsChange((previous) => [...previous, ...remainingEvents]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function cancelJob() {
    if (!job || !isJobRunning || job.cancel_requested) return;
    setError('');
    setMessage('');
    setIsCancelling(true);
    try {
      const nextJob = await api.cancelJob(job.job_id);
      onJobChange(nextJob);
      setMessageType('warning');
      setMessage('已发出取消请求，当前采集步骤结束后会停止。');
    } catch (err) {
      setIsCancelling(false);
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function saveRunDefaults() {
    setMessage('');
    if (isJobRunning) {
      setMessageType('warning');
      setMessage('任务运行中，先不要保存默认运行方式；等当前任务完成后再保存。');
      return;
    }
    try {
      const nextConfig = structuredClone(config);
      nextConfig.web = {
        ...(nextConfig.web || {}),
        default_execution_mode: executionMode,
        default_run_mode: runMode,
      };
      await onSaveConfig(nextConfig);
      setMessageType('success');
      setMessage('已保存为默认运行方式');
    } catch (err) {
      setMessageType('error');
      setMessage(err instanceof Error ? err.message : String(err));
    }
  }

  const displayJobStatus = job?.cancel_requested && isJobRunning ? '取消中' : job?.status || '未运行';

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
          <button className="ghost-btn" type="button" disabled={isJobRunning} onClick={saveRunDefaults}>
            <Save size={16} />保存默认
          </button>
          <button className="primary-btn" type="button" disabled={isJobRunning} onClick={startJob}>
            <Play size={16} />{isJobRunning ? '任务运行中' : '开始抓取'}
          </button>
          {isJobRunning && (
            <button
              className="danger-btn"
              type="button"
              disabled={isCancelling || Boolean(job?.cancel_requested)}
              onClick={cancelJob}
            >
              <Square size={16} />{isCancelling || job?.cancel_requested ? '取消中' : '取消任务'}
            </button>
          )}
        </div>
      </section>

      {error && <div className="alert error">{error}</div>}
      {authError && <div className="alert error">{authError}</div>}
      {message && <div className={`alert ${messageType}`}>{message}</div>}
      {loginModal && (
        <div className="modal-backdrop">
          <section className="login-modal">
            <div className="section-head compact">
              <div>
                <p className="eyebrow">login</p>
                <h3>{loginModal.display_name} 登录检测</h3>
              </div>
              <button className="ghost-btn" type="button" onClick={() => setLoginModal(null)}>
                <X size={16} />关闭
              </button>
            </div>
            <p className="subtle small">{loginModal.message}</p>
            <div className="login-live-panel">
              <div className={`login-status-banner ${loginModal.status}`}>
                <span>当前状态</span>
                <strong>{loginModal.label}</strong>
              </div>
              <strong>{loginModal.status === 'login_waiting' ? '真实登录页已打开' : '当前登录状态'}</strong>
              <ol className="login-step-list">
                <li>“立即检测”只检查当前状态，不会打开或关闭浏览器。</li>
                <li>“重新打开登录页”才会弹出真实平台登录页。</li>
                <li>登录页打开后不会因为已登录自动关闭，您可以先在平台页切换账号。</li>
                <li>确认账号无误后，点“完成并保存状态”，才会关闭登录窗口并刷新为绿色在线。</li>
              </ol>
            </div>
            <div className="login-actions">
              <button className="ghost-btn" type="button" onClick={pollLoginNow}>
                <RefreshCw size={16} />立即检测
              </button>
              <button className="ghost-btn" type="button" onClick={reopenLoginPage}>
                <Play size={16} />重新打开登录页
              </button>
              <button className="primary-btn" type="button" onClick={finishLogin}>
                <Save size={16} />完成并保存状态
              </button>
            </div>
            <p className="login-note">检测和保存已经拆开：检测只告诉有没有，保存才会收口并关闭登录窗口。</p>
          </section>
        </div>
      )}

      <section className="metrics-grid">
        <div className="metric-card"><span>启用来源</span><strong>{enabledSources.length}</strong></div>
        <div className="metric-card"><span>执行模式</span><strong>{executionMode === 'parallel' ? '并行' : '串行'}</strong></div>
        <div className="metric-card"><span>打分状态</span><strong>{config.scoring?.enabled && runMode === 'collect_score_report' ? '开启' : '关闭'}</strong></div>
        <div className="metric-card"><span>当前任务</span><strong>{displayJobStatus}</strong></div>
      </section>

      <div className="section-head">
        <div>
          <p className="eyebrow">progress</p>
          <h2>来源进度</h2>
        </div>
        <div className="hero-actions">
          <button
            className="ghost-btn"
            type="button"
            disabled={authCheckingAll}
            onClick={() => void refreshAllAuthStates(true)}
          >
            <RefreshCw className={authCheckingAll ? 'spin' : ''} size={16} />
            {authCheckingAll ? '检测中' : '一键检测登录'}
          </button>
          <button className="ghost-btn" type="button" onClick={() => onNavigate('sources')}><Settings2 size={16} />配置来源</button>
        </div>
      </div>

      <section className="source-grid">
        {enabledSources.map((source) => {
          const event = eventBySource.get(source);
          const sourceStatus = (event?.status as UnitProgress['status']) || 'idle';
          const status = job?.status === 'cancelled' && sourceStatus === 'running' ? 'cancelled' : sourceStatus;
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
              authState={authStates[source]}
              onAuthAction={() => void handleAuthAction(source)}
            />
          );
        })}
      </section>
    </div>
  );
}
