import React, { useEffect, useRef } from 'react';
import { ComplexityBadge } from './ComplexityBadge';

interface PseudoCodePanelProps {
  title: string;
  lines: string[];
  activeLine?: number;
  timeComplexity: string;
  spaceComplexity: string;
  logs: string[];
}

export const PseudoCodePanel: React.FC<PseudoCodePanelProps> = ({
  title,
  lines,
  activeLine,
  timeComplexity,
  spaceComplexity,
  logs
}) => {
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs.length]);

  const visibleLogs = logs.slice(-40);

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* ---- Pseudocode ---- */}
      <div className="rounded-xl border border-line bg-surface overflow-hidden">
        <div className="flex items-center justify-between gap-2 px-4 h-9 border-b border-line">
          <span className="inline-flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.16em] text-muted truncate">
            <span className="w-1 h-1 rounded-full bg-mint shrink-0" />
            {title}
          </span>
        </div>

        <div className="font-mono text-[11px] leading-relaxed py-1.5 bg-canvas">
          {lines.map((line, index) => {
            const isActive = activeLine === index;
            return (
              <div
                key={index}
                className={`group relative flex items-stretch transition-colors duration-150 ${
                  isActive ? 'bg-mint/10' : ''
                }`}
              >
                {/* active marker */}
                <span
                  className={`w-0.5 shrink-0 ${isActive ? 'bg-mint' : 'bg-transparent'}`}
                  aria-hidden="true"
                />
                {/* gutter */}
                <span
                  className={`w-8 shrink-0 select-none text-right pr-2 py-1 tnum ${
                    isActive ? 'text-mint' : 'text-muted'
                  }`}
                >
                  {index + 1}
                </span>
                <pre
                  className={`flex-1 py-1 pr-3 whitespace-pre overflow-x-auto ${
                    isActive ? 'text-mint font-semibold' : 'text-muted'
                  }`}
                >
                  {line}
                </pre>
              </div>
            );
          })}
        </div>

        <div className="flex flex-wrap items-center gap-1.5 px-3 py-2.5 border-t border-line">
          <ComplexityBadge label="Time" value={timeComplexity} variant="mint" />
          <ComplexityBadge label="Space" value={spaceComplexity} variant="violet" />
        </div>
      </div>

      {/* ---- Operation log ---- */}
      <div className="flex-1 flex flex-col rounded-xl border border-line bg-surface overflow-hidden min-h-[190px]">
        <div className="flex items-center justify-between px-4 h-9 border-b border-line">
          <span className="inline-flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.16em] text-muted">
            <span className="w-1 h-1 rounded-full bg-violet" />
            Operation log
          </span>
          <span className="text-[10px] font-mono text-muted tnum">{logs.length} ops</span>
        </div>

        <div
          ref={logRef}
          className="flex-1 overflow-y-auto max-h-[220px] bg-canvas font-mono text-[11px] divide-y divide-line/60"
        >
          {visibleLogs.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center gap-2 py-8 px-4 text-center">
              <span className="w-8 h-8 rounded-lg border border-line hatch" aria-hidden="true" />
              <p className="text-[11px] text-muted">
                Press <span className="text-mint">Play</span> or{' '}
                <span className="text-mint">Step</span> to trace execution
              </p>
            </div>
          ) : (
            visibleLogs.map((log, i) => {
              const n = logs.length - visibleLogs.length + i + 1;
              const isLast = i === visibleLogs.length - 1;
              return (
                <div
                  key={i}
                  className={`flex items-start gap-2.5 px-3 py-1.5 ${
                    isLast ? 'bg-mint/[0.07]' : ''
                  }`}
                >
                  <span className="text-muted tnum shrink-0 w-7 text-right">{n}</span>
                  <span className={`shrink-0 ${isLast ? 'text-mint' : 'text-muted'}`}>›</span>
                  <span className={isLast ? 'text-ink' : 'text-muted'}>{log}</span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
