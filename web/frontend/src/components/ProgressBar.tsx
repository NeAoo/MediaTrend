export function ProgressBar({ value, tone = 'blue' }: { value: number; tone?: 'blue' | 'green' | 'amber' | 'red' | 'gray' }) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="progress-track" aria-label={`进度 ${Math.round(clamped)}%`}>
      <div className={`progress-fill ${tone}`} style={{ width: `${clamped}%` }} />
    </div>
  );
}
