import { useEffect, useState } from 'react';
import { FlaskConical, Save } from 'lucide-react';
import { api } from '../api';
import { PromptEditor } from '../components/PromptEditor';
import type { AnyConfig } from '../types';

export function ScoringPage({
  config,
  maskedApiKey,
  hasApiKey,
  isJobRunning,
  onSaveConfig,
}: {
  config: AnyConfig;
  maskedApiKey: string;
  hasApiKey: boolean;
  isJobRunning: boolean;
  onSaveConfig: (config: AnyConfig, apiKey?: string) => Promise<unknown>;
}) {
  const [draft, setDraft] = useState<AnyConfig>(() => structuredClone(config));
  const [apiKey, setApiKey] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [userPrompt, setUserPrompt] = useState('');
  const [warnings, setWarnings] = useState<string[]>([]);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'warning' | 'error'>('success');

  useEffect(() => {
    api.getPrompts().then((response) => {
      setSystemPrompt(response.system_prompt);
      setUserPrompt(response.user_prompt);
      setWarnings(response.warnings);
    }).catch((err) => {
      setMessageType('error');
      setMessage(err instanceof Error ? err.message : String(err));
    });
  }, []);

  const scoring = draft.scoring || {};
  const updateScoring = (key: string, value: unknown) => {
    setDraft((previous) => ({
      ...previous,
      scoring: {
        ...(previous.scoring || {}),
        [key]: value,
      },
    }));
  };

  async function save() {
    setMessage('');
    if (isJobRunning) {
      setMessageType('warning');
      setMessage('任务运行中，先不要保存打分配置或 prompt；等当前任务完成后再保存。');
      return;
    }
    try {
      await onSaveConfig(draft, apiKey || undefined);
      const promptResponse = await api.savePrompts(systemPrompt, userPrompt);
      setWarnings(promptResponse.warnings);
      setMessageType('success');
      setMessage('打分配置、密钥和 prompt 已保存');
    } catch (err) {
      setMessageType('error');
      setMessage(err instanceof Error ? err.message : String(err));
    }
  }

  async function testConnection() {
    setMessage('');
    try {
      const result = await api.testScoring();
      setMessageType('success');
      setMessage(`连接正常：${result.model}，可见模型 ${result.available_count} 个`);
    } catch (err) {
      setMessageType('error');
      setMessage(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <div className="stack">
      <div className="section-head">
        <div>
          <p className="eyebrow">scoring</p>
          <h1>打分模型</h1>
          <p className="subtle">关闭后只采集和合并 JSON；开启后会调用模型生成评分报告。</p>
        </div>
        <div className="hero-actions">
          <button className="ghost-btn" type="button" onClick={testConnection}><FlaskConical size={16} />测试连接</button>
          <button className="primary-btn" type="button" disabled={isJobRunning} onClick={save}>
            <Save size={16} />{isJobRunning ? '任务运行中' : '保存'}
          </button>
        </div>
      </div>
      {message && <div className={`alert ${messageType}`}>{message}</div>}
      {warnings.length > 0 && <div className="alert warning">{warnings.join('；')}</div>}
      <section className="form-panel">
        <div className="form-grid">
          <label className="field-inline"><span>打分开关</span><button className={`toggle ${scoring.enabled ? 'on' : ''}`} type="button" onClick={() => updateScoring('enabled', !scoring.enabled)}>{scoring.enabled ? '开启' : '关闭'}</button></label>
          <label className="field-inline"><span>Base URL</span><input value={scoring.base_url || ''} onChange={(event) => updateScoring('base_url', event.target.value)} /></label>
          <label className="field-inline"><span>Model</span><input value={scoring.model || ''} onChange={(event) => updateScoring('model', event.target.value)} /></label>
          <label className="field-inline"><span>API Key</span><input type="password" placeholder={hasApiKey ? maskedApiKey : '未配置'} value={apiKey} onChange={(event) => setApiKey(event.target.value)} /></label>
          <label className="field-inline"><span>Timeout</span><input type="number" value={scoring.timeout_seconds || 120} onChange={(event) => updateScoring('timeout_seconds', Number(event.target.value))} /></label>
          <label className="field-inline"><span>Retries</span><input type="number" value={scoring.max_retries || 0} onChange={(event) => updateScoring('max_retries', Number(event.target.value))} /></label>
          <label className="field-inline"><span>Max Tokens</span><input type="number" value={scoring.max_completion_tokens || 0} onChange={(event) => updateScoring('max_completion_tokens', Number(event.target.value))} /></label>
          <label className="field-inline"><span>Workers</span><input type="number" value={scoring.workers || 1} onChange={(event) => updateScoring('workers', Number(event.target.value))} /></label>
          <label className="field-inline"><span>Reasoning</span><input value={scoring.reasoning_effort || ''} onChange={(event) => updateScoring('reasoning_effort', event.target.value)} /></label>
        </div>
      </section>
      <section className="prompt-grid">
        <PromptEditor label="System Prompt" value={systemPrompt} onChange={setSystemPrompt} minRows={8} />
        <PromptEditor label="User Prompt Template" value={userPrompt} onChange={setUserPrompt} minRows={22} />
      </section>
    </div>
  );
}
