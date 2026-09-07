import React from 'react';

interface ProgressRingProps {
  completed: number;
  total: number;
  size?: number;
  strokeWidth?: number;
}

export const ProgressRing: React.FC<ProgressRingProps> = ({
  completed,
  total,
  size = 128,
  strokeWidth = 8
}) => {
  const radius = (size - strokeWidth) / 2 - 6;
  const circumference = 2 * Math.PI * radius;
  const percentage = total > 0 ? Math.min(100, Math.round((completed / total) * 100)) : 0;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;
  const center = size / 2;

  // Gauge ticks every 30°
  const ticks = Array.from({ length: 12 }, (_, i) => {
    const angle = (i * 30 * Math.PI) / 180;
    const outer = size / 2 - 1;
    const inner = size / 2 - 5;
    return {
      x1: center + Math.cos(angle) * inner,
      y1: center + Math.sin(angle) * inner,
      x2: center + Math.cos(angle) * outer,
      y2: center + Math.sin(angle) * outer,
      lit: (i / 12) * 100 < percentage
    };
  });

  return (
    <div
      className="relative inline-flex items-center justify-center shrink-0"
      style={{ width: size, height: size }}
      role="img"
      aria-label={`${percentage} percent complete, ${completed} of ${total}`}
    >
      <svg width={size} height={size} className="-rotate-90">
        {ticks.map((t, i) => (
          <line
            key={i}
            x1={t.x1}
            y1={t.y1}
            x2={t.x2}
            y2={t.y2}
            stroke={t.lit ? 'var(--c-mint)' : 'var(--c-line)'}
            strokeWidth={1.5}
            strokeLinecap="round"
          />
        ))}
        <circle
          cx={center}
          cy={center}
          r={radius}
          stroke="var(--c-line)"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        <circle
          cx={center}
          cy={center}
          r={radius}
          stroke="var(--c-mint)"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
          style={{ transition: 'stroke-dashoffset 400ms cubic-bezier(0.16,1,0.3,1)' }}
        />
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold font-mono text-ink tnum leading-none tracking-tight">
          {percentage}
          <span className="text-sm text-muted">%</span>
        </span>
        <span className="text-[10px] font-mono text-muted tnum mt-1">
          {completed}/{total}
        </span>
      </div>
    </div>
  );
};
