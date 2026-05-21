import { useEffect, useState } from 'react';
import { FlaskConical, Save } from 'lucide-react';
import { api } from '../api';
import { PromptEditor } from '../components/PromptEditor';
import type { AnyConfig } from '../types';

function NumberTextInput({
  label,
  value,
  onChange,
  min = 0,
  allowDecimal = false,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  allowDecimal?: boolean;
}) {
  const normalizedValue = Number.isFinite(Number(value)) ? String(value) : String(min);
  const [text, setText] = useState(normalizedValue);

  useEffect(() => {
    setText(normalizedValue);
  }, [normalizedValue]);

  const commit = (rawValue: string) => {
    if (rawValue.trim() === '') return;
    const parsedValue = allowDecimal ? Number.parseFloat(rawValue) : Number.parseInt(rawValue, 10);
    if (!Number.isFinite(parsedValue)) return;
    onChange(Math.max(min, parsedValue));
  };

  return (
    <label className="field-inline">
      <span>{label}</span>
      <input
        inputMode="decimal"
        value={text}
        onBlur={() => {
          if (text.trim() === '') {
            setText(normalizedValue);
            return;
          }
          commit(text);
        }}
        onChange={(event) => {
          const nextText = event.target.value;
          const pattern = allowDecimal ? /^\d*\.?\d*$/ : /^\d*$/;
          if (!pattern.test(nextText)) return;
          setText(nextText);
          commit(nextText);
        }}
      />
    </label>
  );
}

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
  const [scoringSystemPrompt, setScoringSystemPrompt] = useState('');
  const [scoringUserPrompt, setScoringUserPrompt] = useState('');
  const [scoringWarnings, setScoringWarnings] = useState<string[]>([]);
  const [hotrankSystemPrompt, setHotrankSystemPrompt] = useState('');
  const [hotrankUserPrompt, setHotrankUserPrompt] = useState('');
  const [hotrankWarnings, setHotrankWarnings] = useState<string[]>([]);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'warning' | 'error'>('success');

  useEffect(() => {
    Promise.all([api.getPrompts(), api.getHotrankPrompts()])
      .then(([scoringPromptResponse, hotrankPromptResponse]) => {
        setScoringSystemPrompt(scoringPromptResponse.system_prompt);
        setScoringUserPrompt(scoringPromptResponse.user_prompt);
        setScoringWarnings(scoringPromptResponse.warnings);
        setHotrankSystemPrompt(hotrankPromptResponse.system_prompt);
        setHotrankUserPrompt(hotrankPromptResponse.user_prompt);
        setHotrankWarnings(hotrankPromptResponse.warnings);
      }).catch((err) => {
        setMessageType('error');
        setMessage(err instanceof Error ? err.message : String(err));
      });
  }, []);

  const scoring = draft.scoring || {};
  const hotrankClassification = draft.hotrank?.ai_classification || {};
  const updateScoring = (key: string, value: unknown) => {
    setDraft((previous) => ({
      ...previous,
      scoring: {
        ...(previous.scoring || {}),
        [key]: value,
      },
    }));
  };
  const updateHotrankClassification = (key: string, value: unknown) => {
    setDraft((previous) => ({
      ...previous,
      hotrank: {
        ...(previous.hotrank || {}),
        ai_classification: {
          ...(previous.hotrank?.ai_classification || {}),
          [key]: value,
        },
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
      const [scoringPromptResponse, hotrankPromptResponse] = await Promise.all([
        api.savePrompts(scoringSystemPrompt, scoringUserPrompt),
        api.saveHotrankPrompts(hotrankSystemPrompt, hotrankUserPrompt),
      ]);
      setScoringWarnings(scoringPromptResponse.warnings);
      setHotrankWarnings(hotrankPromptResponse.warnings);
      setMessageType('success');
      setMessage('模型配置、密钥和两套 prompt 已保存');
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
          <p className="eyebrow">models</p>
          <h1>模型配置</h1>
          <p className="subtle">正文打分和全网热榜分类分开配置；API Key 共用 .env 里的 LLM_API_KEY。</p>
        </div>
        <div className="hero-actions">
          <button className="ghost-btn" type="button" onClick={testConnection}><FlaskConical size={16} />测试连接</button>
          <button className="primary-btn" type="button" disabled={isJobRunning} onClick={save}>
            <Save size={16} />{isJobRunning ? '任务运行中' : '保存'}
          </button>
        </div>
      </div>
      {message && <div className={`alert ${messageType}`}>{message}</div>}
      {scoringWarnings.length > 0 && <div className="alert warning">正文打分 Prompt：{scoringWarnings.join('；')}</div>}
      {hotrankWarnings.length > 0 && <div className="alert warning">热榜分类 Prompt：{hotrankWarnings.join('；')}</div>}
      <section className="form-panel">
        <div className="section-head compact model-section-head">
          <div>
            <p className="eyebrow">scoring</p>
            <h2>正文内容打分模型</h2>
            <p className="subtle small">采集完成后，对每篇候选内容做综合评分并生成评分报告。</p>
          </div>
        </div>
        <div className="form-grid">
          <label className="field-inline"><span>打分开关</span><button className={`toggle ${scoring.enabled ? 'on' : ''}`} type="button" onClick={() => updateScoring('enabled', !scoring.enabled)}>{scoring.enabled ? '开启' : '关闭'}</button></label>
          <label className="field-inline"><span>Base URL</span><input value={scoring.base_url || ''} onChange={(event) => updateScoring('base_url', event.target.value)} /></label>
          <label className="field-inline"><span>Model</span><input value={scoring.model || ''} onChange={(event) => updateScoring('model', event.target.value)} /></label>
          <label className="field-inline"><span>API Key</span><input type="password" placeholder={hasApiKey ? maskedApiKey : '未配置'} value={apiKey} onChange={(event) => setApiKey(event.target.value)} /></label>
          <NumberTextInput label="Timeout" value={scoring.timeout_seconds ?? 120} min={10} allowDecimal onChange={(value) => updateScoring('timeout_seconds', value)} />
          <NumberTextInput label="Retries" value={scoring.max_retries ?? 0} onChange={(value) => updateScoring('max_retries', value)} />
          <NumberTextInput label="Max Tokens" value={scoring.max_completion_tokens ?? 0} onChange={(value) => updateScoring('max_completion_tokens', value)} />
          <NumberTextInput label="Workers" value={scoring.workers ?? 1} min={1} onChange={(value) => updateScoring('workers', value)} />
          <label className="field-inline"><span>Reasoning</span><input value={scoring.reasoning_effort || ''} onChange={(event) => updateScoring('reasoning_effort', event.target.value)} /></label>
        </div>
      </section>
      <section className="form-panel">
        <div className="section-head compact model-section-head">
          <div>
            <p className="eyebrow">hotrank</p>
            <h2>全网热榜分类模型</h2>
            <p className="subtle small">只在“全网热榜”页刷新时使用，用来把聚合趋势分到主题类目。</p>
          </div>
        </div>
        <div className="form-grid">
          <label className="field-inline">
            <span>分类开关</span>
            <button
              className={`toggle ${hotrankClassification.enabled ? 'on' : ''}`}
              type="button"
              onClick={() => updateHotrankClassification('enabled', !hotrankClassification.enabled)}
            >
              {hotrankClassification.enabled ? '开启' : '关闭'}
            </button>
          </label>
          <label className="field-inline">
            <span>Base URL</span>
            <input
              value={hotrankClassification.base_url || ''}
              onChange={(event) => updateHotrankClassification('base_url', event.target.value)}
            />
          </label>
          <label className="field-inline">
            <span>Model</span>
            <input
              value={hotrankClassification.model || ''}
              onChange={(event) => updateHotrankClassification('model', event.target.value)}
            />
          </label>
          <NumberTextInput
            label="Timeout"
            value={hotrankClassification.timeout_seconds ?? 120}
            min={10}
            allowDecimal
            onChange={(value) => updateHotrankClassification('timeout_seconds', value)}
          />
          <NumberTextInput
            label="Retries"
            value={hotrankClassification.max_retries ?? 1}
            onChange={(value) => updateHotrankClassification('max_retries', value)}
          />
          <NumberTextInput
            label="Max Tokens"
            value={hotrankClassification.max_completion_tokens ?? 80}
            onChange={(value) => updateHotrankClassification('max_completion_tokens', value)}
          />
          <NumberTextInput
            label="Workers"
            value={hotrankClassification.workers ?? 32}
            min={1}
            onChange={(value) => updateHotrankClassification('workers', value)}
          />
          <label className="field-inline">
            <span>Reasoning</span>
            <input
              value={hotrankClassification.reasoning_effort || ''}
              onChange={(event) => updateHotrankClassification('reasoning_effort', event.target.value)}
            />
          </label>
          <label className="field-inline">
            <span>API Key</span>
            <input disabled value={hasApiKey ? maskedApiKey : '未配置'} />
            <span className="field-hint">和正文打分共用上方 API Key，不单独保存第二份密钥。</span>
          </label>
        </div>
      </section>
      <section className="form-panel prompt-section-panel">
        <div className="section-head compact model-section-head">
          <div>
            <p className="eyebrow">scoring prompt</p>
            <h2>正文打分 Prompt</h2>
            <p className="subtle small">用于采集后给候选正文打综合分，产出评分报告。</p>
          </div>
        </div>
        <div className="prompt-grid">
          <PromptEditor label="打分 System Prompt" value={scoringSystemPrompt} onChange={setScoringSystemPrompt} minRows={8} />
          <PromptEditor label="打分 User Prompt Template" value={scoringUserPrompt} onChange={setScoringUserPrompt} minRows={22} />
        </div>
      </section>
      <section className="form-panel prompt-section-panel">
        <div className="section-head compact model-section-head">
          <div>
            <p className="eyebrow">hotrank prompt</p>
            <h2>热榜内容分类 Prompt</h2>
            <p className="subtle small">只服务“全网热榜”的主题分类，不参与正文打分。</p>
          </div>
        </div>
        <div className="prompt-grid">
          <PromptEditor label="分类 System Prompt" value={hotrankSystemPrompt} onChange={setHotrankSystemPrompt} minRows={10} />
          <PromptEditor label="分类 User Prompt Template" value={hotrankUserPrompt} onChange={setHotrankUserPrompt} minRows={14} />
        </div>
      </section>
    </div>
  );
}
