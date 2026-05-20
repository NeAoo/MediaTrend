import { useEffect, useState } from 'react';
import { api } from '../api';
import type { ReportFile } from '../types';

export function ReportsPage() {
  const [reports, setReports] = useState<ReportFile[]>([]);

  useEffect(() => {
    api.listReports().then(setReports).catch(() => setReports([]));
  }, []);

  return (
    <div className="stack">
      <div className="section-head"><div><p className="eyebrow">reports</p><h1>结果报告</h1></div></div>
      <section className="table-panel">
        <table>
          <thead><tr><th>文件</th><th>大小</th><th>路径</th><th>更新时间</th></tr></thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.path}>
                <td>{report.name}</td>
                <td>{Math.round(report.size / 1024)} KB</td>
                <td>{report.path}</td>
                <td>{new Date(report.updated_at * 1000).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
