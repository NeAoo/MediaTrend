import { useEffect, useState } from 'react';
import type { AnyConfig } from '../types';

const DAY_HOURS = 24;
const DEFAULT_DAYS = 7;

const sourceLabels: Record<string, string> = {
  wechat: '微信',
  xiaohongshu: '小红书',
  zhihu: '知乎',
  google_news: 'Google News',
  aihot: 'AI HOT',
};

function lines(value: string[] | undefined) {
  return (value || []).join('\n');
}

function parseLines(value: string) {
  return value.split(/\r?\n/).map((item) => item.trim()).filter(Boolean);
}

function cloneConfig(config: AnyConfig) {
  return structuredClone(config);
}

function getNested(config: AnyConfig, path: string[]) {
  return path.reduce((obj, key) => obj?.[key], config);
}

function hoursToDays(maxHours: number | undefined, fallbackDays = DEFAULT_DAYS) {
  const hours = Number(maxHours);
  if (!Number.isFinite(hours) || hours <= 0) return fallbackDays;
  return Math.max(1, Math.ceil(hours / DAY_HOURS));
}

function periodToDays(period: string | undefined) {
  const text = String(period || '').trim().toLowerCase();
  const dayMatch = text.match(/^(\d+)d$/);
  if (dayMatch) return Math.max(1, Number.parseInt(dayMatch[1], 10));
  const hourMatch = text.match(/^(\d+)h$/);
  if (hourMatch) return hoursToDays(Number.parseInt(hourMatch[1], 10), 1);
  return DEFAULT_DAYS;
}

function isWechatSource(source: string) {
  return source === 'wechat' || source === 'wechat_mp';
}

function isSourceEnabled(config: AnyConfig, source: string) {
  const enabledSources = config.enabled_sources || [];
  if (isWechatSource(source)) {
    return enabledSources.includes('wechat') || enabledSources.includes('wechat_mp');
  }
  return enabledSources.includes(source);
}

function isModeEnabled(target: AnyConfig) {
  return target.enabled !== false;
}

function SectionTitle({
  title,
  kind,
  description,
  enabled,
  onToggle,
}: {
  title: string;
  kind: 'keyword' | 'account';
  description: string;
  enabled: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="subsection-head">
      <div>
        <span className={`mode-pill ${kind}`}>{kind === 'keyword' ? '关键词' : '账号'}</span>
        <h4>{title}</h4>
        <p>{description}</p>
      </div>
      <button className={`mini-toggle ${enabled ? 'on' : ''}`} title="点击切换该采集方式" type="button" onClick={onToggle}>
        {enabled ? '启用中 · 可关闭' : '已关闭 · 可启用'}
      </button>
    </div>
  );
}

function ListTextarea({
  value,
  onChange,
}: {
  value: string[] | undefined;
  onChange: (value: string[]) => void;
}) {
  const serializedValue = lines(value);
  const [text, setText] = useState(serializedValue);

  useEffect(() => {
    setText(serializedValue);
  }, [serializedValue]);

  return (
    <textarea
      className="list-textarea"
      value={text}
      onChange={(event) => {
        const nextText = event.target.value;
        setText(nextText);
        onChange(parseLines(nextText));
      }}
    />
  );
}

function NumberInput({
  label,
  value,
  onChange,
  min = 0,
  helper,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  helper?: string;
}) {
  const normalizedValue = Number.isFinite(Number(value)) ? String(value) : String(min);
  const [text, setText] = useState(normalizedValue);

  useEffect(() => {
    setText(normalizedValue);
  }, [normalizedValue]);

  const commit = (rawValue: string) => {
    if (rawValue.trim() === '') return;
    const parsedValue = Number.parseInt(rawValue, 10);
    if (!Number.isFinite(parsedValue)) return;
    onChange(Math.max(min, parsedValue));
  };

  return (
    <label className="field-inline">
      <span>{label}</span>
      <input
        inputMode="numeric"
        pattern="[0-9]*"
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
          if (!/^\d*$/.test(nextText)) return;
          setText(nextText);
          commit(nextText);
        }}
      />
      {helper && <small className="field-hint">{helper}</small>}
    </label>
  );
}

export function SourceConfigEditor({
  source,
  config,
  onChange,
}: {
  source: string;
  config: AnyConfig;
  onChange: (config: AnyConfig) => void;
}) {
  const enabled = isSourceEnabled(config, source);
  const update = (mutator: (draft: AnyConfig) => void) => {
    const next = cloneConfig(config);
    mutator(next);
    onChange(next);
  };
  const toggle = () => update((draft) => {
    const enabledSources = new Set<string>(draft.enabled_sources || []);
    if (isWechatSource(source)) {
      if (enabledSources.has('wechat') || enabledSources.has('wechat_mp')) {
        enabledSources.delete('wechat');
        enabledSources.delete('wechat_mp');
      } else {
        const hasKeywords = Boolean(draft.wechat?.keyword_search?.keywords?.length);
        const hasAccounts = Boolean(draft.wechat?.account_crawl?.accounts?.length);
        if (hasKeywords) enabledSources.add('wechat');
        if (hasAccounts) enabledSources.add('wechat_mp');
        if (!hasKeywords && !hasAccounts) enabledSources.add('wechat');
      }
    } else if (enabledSources.has(source)) {
      enabledSources.delete(source);
    } else {
      enabledSources.add(source);
    }
    draft.enabled_sources = Array.from(enabledSources);
  });

  const renderDaysAndCountInputs = (
    target: AnyConfig,
    path: string[],
    maxCountKey: 'max_results_per_keyword' | 'max_results_per_query' | 'max_results_per_account',
    defaultMaxCount: number,
  ) => (
    <div className="form-grid">
      <NumberInput
        label="几天内"
        min={1}
        value={hoursToDays(target.time_range_hours?.max)}
        helper="1=最近24小时；2=最近48小时。"
        onChange={(value) => update((draft) => {
          const item = getNested(draft, path);
          item.time_range_hours = { ...(item.time_range_hours || {}), min: 0, max: value * DAY_HOURS };
        })}
      />
      <NumberInput
        label="最少篇数（不足就取实际数量）"
        value={target.expected_min_results ?? 3}
        helper="时间窗口内少于这个数时，不补假数据，取实际能抓到的 0/1/2 篇。"
        onChange={(value) => update((draft) => {
          const item = getNested(draft, path);
          item.expected_min_results = value;
        })}
      />
      <NumberInput
        label="最多篇数（超出按最新保留）"
        min={1}
        value={target[maxCountKey] ?? defaultMaxCount}
        helper="多于上限时，按发布时间从近到远保留到上限。"
        onChange={(value) => update((draft) => {
          const item = getNested(draft, path);
          item[maxCountKey] = value;
        })}
      />
    </div>
  );

  const renderKeywordBlock = (path: string[], label = '关键词') => {
    const target = getNested(config, path);
    if (!target) return null;
    const maxCountKey = 'max_results_per_query' in target ? 'max_results_per_query' : 'max_results_per_keyword';
    const modeEnabled = isModeEnabled(target);
    return (
      <div className={`form-section mode-card keyword ${modeEnabled ? '' : 'disabled'}`}>
        <SectionTitle
          title={label}
          kind="keyword"
          description="按关键词搜索内容，一行一个关键词。"
          enabled={modeEnabled}
          onToggle={() => update((draft) => {
            const item = getNested(draft, path);
            item.enabled = !isModeEnabled(item);
          })}
        />
        <label className="field-block">
          <span>每行一个</span>
          <ListTextarea value={target.keywords} onChange={(value) => update((draft) => {
            const item = getNested(draft, path);
            item.keywords = value;
          })} />
        </label>
        {renderDaysAndCountInputs(target, path, maxCountKey, 10)}
      </div>
    );
  };

  const renderAccountBlock = (path: string[], keyName: 'accounts' | 'creator_urls', label: string) => {
    const target = getNested(config, path);
    if (!target) return null;
    const modeEnabled = isModeEnabled(target);
    return (
      <div className={`form-section mode-card account ${modeEnabled ? '' : 'disabled'}`}>
        <SectionTitle
          title={label}
          kind="account"
          description="按固定账号抓取近期内容，一行一个账号或主页 URL。"
          enabled={modeEnabled}
          onToggle={() => update((draft) => {
            const item = getNested(draft, path);
            item.enabled = !isModeEnabled(item);
          })}
        />
        <label className="field-block">
          <span>每行一个</span>
          <ListTextarea value={target[keyName]} onChange={(value) => update((draft) => {
            const item = getNested(draft, path);
            item[keyName] = value;
          })} />
        </label>
        {renderDaysAndCountInputs(target, path, 'max_results_per_account', 10)}
      </div>
    );
  };

  const renderGoogleNewsBlock = () => {
    const target = config.google_news || {};
    return (
      <div className="form-section">
        <h4>Google News 关键词</h4>
        <label className="field-block">
          <span>每行一个</span>
          <ListTextarea value={target.keywords} onChange={(value) => update((draft) => {
            draft.google_news.keywords = value;
          })} />
        </label>
        <div className="form-grid">
          <NumberInput
            label="几天内"
            min={1}
            value={periodToDays(target.period)}
            helper="保存为 Google News RSS 的 Nd 时间段，例如 7 天内写成 7d。"
            onChange={(value) => update((draft) => {
              draft.google_news.period = `${value}d`;
            })}
          />
          <NumberInput label="最少篇数（不足就取实际数量）" value={target.expected_min_results ?? 3} onChange={(value) => update((draft) => {
            draft.google_news.expected_min_results = value;
          })} />
          <NumberInput label="最多篇数（超出按最新保留）" min={1} value={target.max_results_per_keyword ?? 20} onChange={(value) => update((draft) => {
            draft.google_news.max_results_per_keyword = value;
          })} />
          <label className="field-inline">
            <span>语言</span>
            <input value={target.language || 'zh-CN'} onChange={(event) => update((draft) => {
              draft.google_news.language = event.target.value;
            })} />
          </label>
          <label className="field-inline">
            <span>国家</span>
            <input value={target.country || 'CN'} onChange={(event) => update((draft) => {
              draft.google_news.country = event.target.value;
            })} />
          </label>
        </div>
      </div>
    );
  };

  const renderAihotBlock = () => {
    return (
      <div className="form-section">
        <h4>AI HOT 精选池</h4>
        <p className="subtle small">
          AI HOT 固定使用 selected 精选池，不再手动填关键词、分类或模式。
          是否参与本次采集只看右上角来源开关。
        </p>
      </div>
    );
  };

  return (
    <section className="config-editor">
      <div className="section-head compact">
        <div>
          <p className="eyebrow">source</p>
          <h3>{sourceLabels[source] || source}</h3>
        </div>
        <button className={`toggle ${enabled ? 'on' : ''}`} title="点击切换来源启用状态" type="button" onClick={toggle}>
          {enabled ? '已启用 · 点击关闭' : '已关闭 · 点击启用'}
        </button>
      </div>
      {source === 'wechat' && (
        <>
          {renderKeywordBlock(['wechat', 'keyword_search'], '关键词')}
          {renderAccountBlock(['wechat', 'account_crawl'], 'accounts', '对标公众号账号')}
        </>
      )}
      {source === 'xiaohongshu' && (
        <>
          {renderKeywordBlock(['xiaohongshu', 'keyword_search'])}
          {renderAccountBlock(['xiaohongshu', 'account_crawl'], 'creator_urls', '对标账号主页 URL')}
        </>
      )}
      {source === 'zhihu' && (
        <>
          {renderKeywordBlock(['zhihu', 'keyword_search'])}
          {renderAccountBlock(['zhihu', 'account_crawl'], 'creator_urls', '对标用户主页 URL')}
        </>
      )}
      {source === 'google_news' && renderGoogleNewsBlock()}
      {source === 'aihot' && renderAihotBlock()}
    </section>
  );
}
