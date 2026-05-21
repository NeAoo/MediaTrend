import { useEffect, useState } from 'react';
import { Activity, BarChart3, Database, FileText, Gauge, Settings2, TrendingUp } from 'lucide-react';
import { api } from './api';
import { TopNav } from './components/TopNav';
import { DashboardPage } from './pages/DashboardPage';
import { SourcesPage } from './pages/SourcesPage';
import { ScoringPage } from './pages/ScoringPage';
import { HotrankPage } from './pages/HotrankPage';
import { HistoryPage } from './pages/HistoryPage';
import { ReportsPage } from './pages/ReportsPage';
import { SystemStatusPage } from './pages/SystemStatusPage';
import type { AnyConfig, ConfigResponse, JobEvent, JobSnapshot, PageKey } from './types';

const pageRoutes: Record<PageKey, string> = {
  dashboard: '/',
  sources: '/sources',
  scoring: '/scoring',
  hotrank: '/hotrank',
  history: '/history',
  reports: '/reports',
  system: '/system',
};

const navItems = [
  { key: 'dashboard' as PageKey, label: '主工作台', icon: Gauge },
  { key: 'sources' as PageKey, label: '来源配置', icon: Database },
  { key: 'scoring' as PageKey, label: '打分模型', icon: Settings2 },
  { key: 'hotrank' as PageKey, label: '全网热榜', icon: TrendingUp },
  { key: 'history' as PageKey, label: '任务历史', icon: Activity },
  { key: 'reports' as PageKey, label: '结果报告', icon: FileText },
  { key: 'system' as PageKey, label: '系统状态', icon: BarChart3 },
];

function pageFromPath(pathname: string): PageKey {
  const normalizedPath = pathname.replace(/\/+$/, '') || '/';
  const matched = Object.entries(pageRoutes).find(([, path]) => path === normalizedPath);
  return (matched?.[0] as PageKey | undefined) || 'dashboard';
}

export function App() {
  const [page, setPage] = useState<PageKey>(() => pageFromPath(window.location.pathname));
  const [configResponse, setConfigResponse] = useState<ConfigResponse | null>(null);
  const [job, setJob] = useState<JobSnapshot | null>(null);
  const [events, setEvents] = useState<JobEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function refreshConfig() {
    setLoading(true);
    setError('');
    try {
      setConfigResponse(await api.getConfig());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function saveConfig(config: AnyConfig, apiKey?: string) {
    const saved = await api.saveConfig(config, apiKey);
    setConfigResponse(saved);
    return saved;
  }

  useEffect(() => {
    void refreshConfig();
  }, []);

  useEffect(() => {
    function handlePopState() {
      setPage(pageFromPath(window.location.pathname));
    }
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  function handlePageChange(nextPage: PageKey) {
    setPage(nextPage);
    const nextPath = pageRoutes[nextPage];
    if (window.location.pathname !== nextPath) {
      window.history.pushState({}, '', nextPath);
    }
  }

  const config = configResponse?.config || {};
  const isJobRunning = job?.status === 'queued' || job?.status === 'running';

  return (
    <div className="app-shell">
      <TopNav items={navItems} active={page} onChange={handlePageChange} />
      <main className="page-frame">
        {error && <div className="alert error">{error}</div>}
        {loading && <div className="loading-line">读取配置中...</div>}
        {!loading && page === 'dashboard' && (
          <DashboardPage
            config={config}
            events={events}
            isJobRunning={isJobRunning}
            job={job}
            onEventsChange={setEvents}
            onJobChange={setJob}
            onNavigate={handlePageChange}
            onSaveConfig={saveConfig}
          />
        )}
        {!loading && page === 'sources' && (
          <SourcesPage config={config} isJobRunning={isJobRunning} onSave={saveConfig} />
        )}
        {!loading && page === 'scoring' && (
          <ScoringPage
            config={config}
            isJobRunning={isJobRunning}
            maskedApiKey={configResponse?.masked_api_key || ''}
            hasApiKey={configResponse?.has_api_key || false}
            onSaveConfig={saveConfig}
          />
        )}
        {!loading && page === 'hotrank' && <HotrankPage />}
        {!loading && page === 'history' && <HistoryPage />}
        {!loading && page === 'reports' && <ReportsPage />}
        {!loading && page === 'system' && <SystemStatusPage />}
      </main>
    </div>
  );
}
