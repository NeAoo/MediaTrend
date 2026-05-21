import { useState } from 'react';
import { Save } from 'lucide-react';
import { SourceConfigEditor } from '../components/SourceConfigEditor';
import type { AnyConfig } from '../types';

const sources = ['wechat', 'xiaohongshu', 'zhihu', 'google_news', 'aihot'];
const sourceLabels: Record<string, string> = {
  wechat: '微信',
  xiaohongshu: '小红书',
  zhihu: '知乎',
  google_news: 'Google News',
  aihot: 'AI HOT',
};

function normalizeActiveSource(source: string | undefined) {
  if (source === 'wechat_mp') return 'wechat';
  return source && sources.includes(source) ? source : 'google_news';
}

function normalizeConfigBeforeSave(config: AnyConfig) {
  const next = structuredClone(config);
  const enabledSources = new Set<string>(next.enabled_sources || []);
  const modeEnabled = (value: AnyConfig | undefined) => value?.enabled !== false;
  const hasActiveCreatorSource = (source: 'xiaohongshu' | 'zhihu') => {
    const sourceConfig = next[source] || {};
    const keywordActive = (
      modeEnabled(sourceConfig.keyword_search)
      && Boolean(sourceConfig.keyword_search?.keywords?.length)
    );
    const accountActive = (
      modeEnabled(sourceConfig.account_crawl)
      && Boolean(sourceConfig.account_crawl?.creator_urls?.length)
    );
    return keywordActive || accountActive;
  };

  const hasWechatEnabled = enabledSources.has('wechat') || enabledSources.has('wechat_mp');
  if (hasWechatEnabled) {
    enabledSources.delete('wechat');
    enabledSources.delete('wechat_mp');
    if (
      modeEnabled(next.wechat?.keyword_search)
      && next.wechat?.keyword_search?.keywords?.length
    ) enabledSources.add('wechat');
    if (
      modeEnabled(next.wechat?.account_crawl)
      && next.wechat?.account_crawl?.accounts?.length
    ) enabledSources.add('wechat_mp');
  }

  for (const creatorSource of ['xiaohongshu', 'zhihu'] as const) {
    if (enabledSources.has(creatorSource) && !hasActiveCreatorSource(creatorSource)) {
      enabledSources.delete(creatorSource);
    }
  }

  if (next.aihot) {
    next.aihot.mode = 'selected';
    next.aihot.keywords = [];
    next.aihot.categories = [];
  }
  next.enabled_sources = Array.from(enabledSources);
  return next;
}

export function SourcesPage({
  config,
  isJobRunning,
  onSave,
}: {
  config: AnyConfig;
  isJobRunning: boolean;
  onSave: (config: AnyConfig) => Promise<unknown>;
}) {
  const [draft, setDraft] = useState<AnyConfig>(() => structuredClone(config));
  const [activeSource, setActiveSource] = useState(normalizeActiveSource(config.enabled_sources?.[0]));
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'warning' | 'error'>('success');

  async function save() {
    setMessage('');
    if (isJobRunning) {
      setMessageType('warning');
      setMessage('任务运行中，先不要保存配置；等当前任务完成后再写回 config.yaml。');
      return;
    }
    try {
      const normalizedDraft = normalizeConfigBeforeSave(draft);
      await onSave(normalizedDraft);
      setDraft(normalizedDraft);
      setMessageType('success');
      setMessage('已写回根目录 config.yaml');
    } catch (err) {
      setMessageType('error');
      setMessage(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <div className="stack">
      <div className="section-head">
        <div>
          <p className="eyebrow">config.yaml</p>
          <h1>来源配置</h1>
          <p className="subtle">这里保存后会直接成为命令行和 Web 任务的默认配置。</p>
        </div>
        <button className="primary-btn" type="button" disabled={isJobRunning} onClick={save}>
          <Save size={16} />{isJobRunning ? '任务运行中' : '保存配置'}
        </button>
      </div>
      {message && <div className={`alert ${messageType}`}>{message}</div>}
      <div className="source-layout">
        <aside className="source-tabs">
          {sources.map((source) => (
            <button className={activeSource === source ? 'active' : ''} key={source} onClick={() => setActiveSource(source)} type="button">
              {sourceLabels[source] || source}
            </button>
          ))}
        </aside>
        <SourceConfigEditor source={activeSource} config={draft} onChange={setDraft} />
      </div>
    </div>
  );
}
