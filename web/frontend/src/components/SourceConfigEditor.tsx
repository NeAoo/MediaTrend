import type { AnyConfig } from '../types';

const sourceLabels: Record<string, string> = {
  wechat: '搜狗微信关键词',
  wechat_mp: '微信公众号账号',
  xiaohongshu: '小红书',
  zhihu: '知乎',
  google_news: 'Google News',
  aihot: 'AI HOT',
};

function lines(value: string[] | undefined) {
  return (value || []).join('\n');
}

function parseLines(value: string) {
  return value.split('\n').map((item) => item.trim()).filter(Boolean);
}

function cloneConfig(config: AnyConfig) {
  return structuredClone(config);
}

function NumberInput({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return (
    <label className="field-inline">
      <span>{label}</span>
      <input type="number" min={0} value={value ?? 0} onChange={(event) => onChange(Number(event.target.value))} />
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
  const enabled = (config.enabled_sources || []).includes(source);
  const update = (mutator: (draft: AnyConfig) => void) => {
    const next = cloneConfig(config);
    mutator(next);
    onChange(next);
  };
  const toggle = () => update((draft) => {
    const enabledSources = new Set<string>(draft.enabled_sources || []);
    if (enabledSources.has(source)) enabledSources.delete(source);
    else enabledSources.add(source);
    draft.enabled_sources = Array.from(enabledSources);
  });

  const renderKeywordBlock = (path: string[], label = '关键词') => {
    const target = path.reduce((obj, key) => obj?.[key], config);
    if (!target) return null;
    return (
      <div className="form-section">
        <h4>{label}</h4>
        <label className="field-block">
          <span>每行一个</span>
          <textarea value={lines(target.keywords)} onChange={(event) => update((draft) => {
            const item = path.reduce((obj, key) => obj[key], draft);
            item.keywords = parseLines(event.target.value);
          })} />
        </label>
        <div className="form-grid">
          <NumberInput label="时间下限(小时)" value={target.time_range_hours?.min ?? 0} onChange={(value) => update((draft) => {
            const item = path.reduce((obj, key) => obj[key], draft);
            item.time_range_hours = { ...(item.time_range_hours || {}), min: value };
          })} />
          <NumberInput label="时间上限(小时)" value={target.time_range_hours?.max ?? 168} onChange={(value) => update((draft) => {
            const item = path.reduce((obj, key) => obj[key], draft);
            item.time_range_hours = { ...(item.time_range_hours || {}), max: value };
          })} />
          <NumberInput label="最少预期" value={target.expected_min_results ?? 3} onChange={(value) => update((draft) => {
            const item = path.reduce((obj, key) => obj[key], draft);
            item.expected_min_results = value;
          })} />
          <NumberInput label="最多篇数" value={target.max_results_per_keyword ?? target.max_results_per_query ?? 10} onChange={(value) => update((draft) => {
            const item = path.reduce((obj, key) => obj[key], draft);
            if ('max_results_per_query' in item) item.max_results_per_query = value;
            else item.max_results_per_keyword = value;
          })} />
        </div>
      </div>
    );
  };

  const renderAccountBlock = (path: string[], keyName: 'accounts' | 'creator_urls', label: string) => {
    const target = path.reduce((obj, key) => obj?.[key], config);
    if (!target) return null;
    return (
      <div className="form-section">
        <h4>{label}</h4>
        <label className="field-block">
          <span>每行一个</span>
          <textarea value={lines(target[keyName])} onChange={(event) => update((draft) => {
            const item = path.reduce((obj, key) => obj[key], draft);
            item[keyName] = parseLines(event.target.value);
          })} />
        </label>
        <div className="form-grid">
          <NumberInput label="时间下限(小时)" value={target.time_range_hours?.min ?? 0} onChange={(value) => update((draft) => {
            const item = path.reduce((obj, key) => obj[key], draft);
            item.time_range_hours = { ...(item.time_range_hours || {}), min: value };
          })} />
          <NumberInput label="时间上限(小时)" value={target.time_range_hours?.max ?? 168} onChange={(value) => update((draft) => {
            const item = path.reduce((obj, key) => obj[key], draft);
            item.time_range_hours = { ...(item.time_range_hours || {}), max: value };
          })} />
          <NumberInput label="最少预期" value={target.expected_min_results ?? 3} onChange={(value) => update((draft) => {
            const item = path.reduce((obj, key) => obj[key], draft);
            item.expected_min_results = value;
          })} />
          <NumberInput label="最多篇数" value={target.max_results_per_account ?? 10} onChange={(value) => update((draft) => {
            const item = path.reduce((obj, key) => obj[key], draft);
            item.max_results_per_account = value;
          })} />
        </div>
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
          <textarea value={lines(target.keywords)} onChange={(event) => update((draft) => {
            draft.google_news.keywords = parseLines(event.target.value);
          })} />
        </label>
        <div className="form-grid">
          <label className="field-inline">
            <span>时间窗口</span>
            <input value={target.period || '7d'} onChange={(event) => update((draft) => {
              draft.google_news.period = event.target.value;
            })} />
          </label>
          <NumberInput label="最少预期" value={target.expected_min_results ?? 3} onChange={(value) => update((draft) => {
            draft.google_news.expected_min_results = value;
          })} />
          <NumberInput label="最多篇数" value={target.max_results_per_keyword ?? 20} onChange={(value) => update((draft) => {
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
    const target = config.aihot || {};
    return (
      <div className="form-section">
        <h4>AI HOT 查询</h4>
        <label className="field-block">
          <span>关键词，每行一个；为空时使用精选池</span>
          <textarea value={lines(target.keywords)} onChange={(event) => update((draft) => {
            draft.aihot.keywords = parseLines(event.target.value);
          })} />
        </label>
        <label className="field-block">
          <span>分类，每行一个：ai-models / ai-products / industry / paper / tip</span>
          <textarea value={lines(target.categories)} onChange={(event) => update((draft) => {
            draft.aihot.categories = parseLines(event.target.value);
          })} />
        </label>
        <div className="form-grid">
          <label className="field-inline">
            <span>模式</span>
            <input value={target.mode || 'selected'} onChange={(event) => update((draft) => {
              draft.aihot.mode = event.target.value;
            })} />
          </label>
          <NumberInput label="最少预期" value={target.expected_min_results ?? 3} onChange={(value) => update((draft) => {
            draft.aihot.expected_min_results = value;
          })} />
          <NumberInput label="最多篇数" value={target.max_results_per_query ?? 50} onChange={(value) => update((draft) => {
            draft.aihot.max_results_per_query = value;
          })} />
          <label className="field-inline">
            <span>Base URL</span>
            <input value={target.base_url || ''} onChange={(event) => update((draft) => {
              draft.aihot.base_url = event.target.value;
            })} />
          </label>
        </div>
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
        <button className={`toggle ${enabled ? 'on' : ''}`} type="button" onClick={toggle}>
          {enabled ? '已启用' : '已关闭'}
        </button>
      </div>
      {source === 'wechat' && renderKeywordBlock(['wechat', 'keyword_search'])}
      {source === 'wechat_mp' && renderAccountBlock(['wechat', 'account_crawl'], 'accounts', '公众号账号')}
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
