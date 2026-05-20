import { useEffect, useState } from 'react';
import { api } from '../api';
import type { JobSnapshot } from '../types';

export function HistoryPage() {
  const [jobs, setJobs] = useState<JobSnapshot[]>([]);

  useEffect(() => {
    api.listJobs().then(setJobs).catch(() => setJobs([]));
  }, []);

  return (
    <div className="stack">
      <div className="section-head"><div><p className="eyebrow">jobs</p><h1>任务历史</h1></div></div>
      <section className="table-panel">
        <table>
          <thead><tr><th>任务</th><th>状态</th><th>模式</th><th>事件</th><th>更新时间</th></tr></thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.job_id}>
                <td>{job.job_id}</td>
                <td><span className={`status-pill ${job.status}`}>{job.status}</span></td>
                <td>{job.execution_mode} / {job.run_mode}</td>
                <td>{job.events_count}</td>
                <td>{job.updated_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
