import { useState } from 'react';
import { Save } from 'lucide-react';
import { SourceConfigEditor } from '../components/SourceConfigEditor';
import type { AnyConfig } from '../types';

const sources = ['wechat', 'wechat_mp', 'xiaohongshu', 'zhihu', 'google_news', 'aihot'];

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
  const [activeSource, setActiveSource] = useState(config.enabled_sources?.[0] || 'google_news');
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
      await onSave(draft);
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
              {source}
            </button>
          ))}
        </aside>
        <SourceConfigEditor source={activeSource} config={draft} onChange={setDraft} />
      </div>
    </div>
  );
}
