import { CheckCircle2, CircleDashed, Loader2, LogIn, RefreshCw, ShieldCheck, Square, TriangleAlert, WifiOff } from 'lucide-react';
import { ProgressBar } from './ProgressBar';
import type { SourceAuthState } from '../types';

export type UnitProgress = {
  name: string;
  type: '关键词' | '账号' | '来源';
  current: number;
  max: number;
  expectedMin: number;
  status: 'idle' | 'running' | 'succeeded' | 'failed' | 'cancelled';
};

function statusIcon(status: UnitProgress['status']) {
  if (status === 'running') return <Loader2 className="spin" size={16} />;
  if (status === 'succeeded') return <CheckCircle2 size={16} />;
  if (status === 'failed') return <TriangleAlert size={16} />;
  if (status === 'cancelled') return <Square size={16} />;
  return <CircleDashed size={16} />;
}

function authIcon(status: SourceAuthState['status']) {
  if (status === 'online' || status === 'not_required') return <ShieldCheck size={14} />;
  if (status === 'offline' || status === 'error') return <WifiOff size={14} />;
  if (status === 'login_waiting') return <LogIn size={14} />;
  return <RefreshCw className="spin" size={14} />;
}

export function SourceProgressCard({
  sourceName,
  progress,
  status,
  eta,
  units,
  authState,
  onAuthAction,
}: {
  sourceName: string;
  progress: number;
  status: UnitProgress['status'];
  eta: string;
  units: UnitProgress[];
  authState?: SourceAuthState;
  onAuthAction?: () => void;
}) {
  const tone = status === 'failed' ? 'red' : status === 'succeeded' ? 'green' : status === 'running' ? 'blue' : status === 'cancelled' ? 'amber' : 'gray';
  const authStatus = authState?.status || 'checking';
  const authDisabled = authState?.status === 'not_required' || !onAuthAction;
  return (
    <section className="source-progress-card">
      <div className="source-progress-head">
        <div>
          <span className={`status-pill ${status}`}>{statusIcon(status)}{status}</span>
          <h3>{sourceName}</h3>
        </div>
        <div className="source-progress-side">
          {authState && (
            <button
              className={`auth-badge ${authStatus}`}
              disabled={authDisabled}
              title={authState.message}
              type="button"
              onClick={onAuthAction}
            >
              {authIcon(authStatus)}{authState.label}
            </button>
          )}
          <div className="metric-num">{Math.round(progress)}%</div>
        </div>
      </div>
      <ProgressBar value={progress} tone={tone} />
      <div className="eta-line">{eta}</div>
      <div className="unit-list">
        {units.map((unit) => {
          const unitProgress = unit.max > 0 ? Math.min(100, (unit.current / unit.max) * 100) : 0;
          const low = unit.expectedMin > 0 && unit.status === 'succeeded' && unit.current < unit.expectedMin;
          return (
            <div className="unit-row" key={`${unit.type}-${unit.name}`}>
              <span>{unit.type}</span>
              <strong>{unit.name}</strong>
              <em className={low ? 'low' : ''}>{unit.current}/{unit.max}</em>
              <ProgressBar value={unit.status === 'running' ? Math.max(12, unitProgress) : unitProgress} tone={low ? 'amber' : tone} />
            </div>
          );
        })}
      </div>
    </section>
  );
}
