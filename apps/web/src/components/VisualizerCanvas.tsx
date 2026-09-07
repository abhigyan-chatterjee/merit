import React from 'react';

interface VisualizerCanvasProps {
  children: React.ReactNode;
  metrics?: { label: string; value: number | string; color?: string }[];
  legend?: { label: string; color: string }[];
}

/** Small crosshair drawn in each corner of the stage. */
const Crosshair: React.FC<{ className: string }> = ({ className }) => (
  <svg
    viewBox="0 0 12 12"
    className={`absolute w-3 h-3 text-line pointer-events-none ${className}`}
    aria-hidden="true"
  >
    <path d="M6 0v12M0 6h12" stroke="currentColor" strokeWidth="1" />
  </svg>
);

export const VisualizerCanvas: React.FC<VisualizerCanvasProps> = ({
  children,
  metrics = [],
  legend = [
    { label: 'Idle', color: 'var(--c-steel)' },
    { label: 'Comparing', color: 'var(--c-amber)' },
    { label: 'Writing', color: 'var(--c-rose)' },
    { label: 'Settled', color: 'var(--c-mint)' }
  ]
}) => {
  return (
    <div className="flex flex-col w-full rounded-xl border border-line bg-surface overflow-hidden">
      {/* ---- Metric rail ---- */}
      {metrics.length > 0 && (
        <div className="flex items-stretch divide-x divide-line border-b border-line overflow-x-auto">
          {metrics.map((m, i) => (
            <div key={i} className="px-4 py-2.5 min-w-0 shrink-0">
              <div className="text-[9px] font-mono uppercase tracking-[0.16em] text-muted whitespace-nowrap">
                {m.label}
              </div>
              <div
                className="text-sm font-mono font-bold tnum truncate max-w-[22ch]"
                style={{ color: m.color || 'var(--c-ink)' }}
              >
                {m.value}
              </div>
            </div>
          ))}
          <div className="flex-1 hatch opacity-30 min-w-6" aria-hidden="true" />
        </div>
      )}

      {/* ---- Stage ---- */}
      <div className="relative flex-1 flex items-center justify-center p-5 min-h-[340px] bg-canvas blueprint-grid overflow-auto">
        <Crosshair className="top-1.5 left-1.5" />
        <Crosshair className="top-1.5 right-1.5" />
        <Crosshair className="bottom-1.5 left-1.5" />
        <Crosshair className="bottom-1.5 right-1.5" />
        <div className="relative w-full">{children}</div>
      </div>

      {/* ---- Legend rail ---- */}
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 px-4 py-2 border-t border-line">
        <span className="text-[9px] font-mono uppercase tracking-[0.16em] text-muted">Legend</span>
        {legend.map((item, idx) => (
          <div key={idx} className="flex items-center gap-1.5">
            <span
              className="w-2.5 h-2.5 rounded-[2px] border border-line"
              style={{ backgroundColor: item.color }}
            />
            <span className="text-[10px] font-mono text-muted">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
