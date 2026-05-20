import { useEffect, useState } from 'react';
import { api } from '../api';
import type { SystemStatus } from '../types';

export function SystemStatusPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    api.getSystem().then(setStatus).catch(() => setStatus(null));
  }, []);

  return (
    <div className="stack">
      <div className="section-head"><div><p className="eyebrow">system</p><h1>系统状态</h1></div></div>
      <section className="detail-grid">
        <div><span>项目根目录</span><strong>{status?.project_root}</strong></div>
        <div><span>配置文件</span><strong>{status?.config_path}</strong></div>
        <div><span>环境变量</span><strong>{status?.env_path}</strong></div>
        <div><span>任务目录</span><strong>{status?.jobs_root}</strong></div>
        <div><span>API Key</span><strong>{status?.has_api_key ? '已配置' : '未配置'}</strong></div>
        <div><span>启用来源</span><strong>{status?.enabled_sources.join(', ')}</strong></div>
      </section>
    </div>
  );
}
