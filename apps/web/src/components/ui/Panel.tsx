import React from 'react';

interface PanelProps {
  children: React.ReactNode;
  /** Small uppercase mono label rendered in the panel's header rail */
  label?: string;
  /** Right-aligned content inside the header rail */
  action?: React.ReactNode;
  /** Draws drafting-style corner brackets on the panel */
  bracket?: boolean;
  /** Removes inner padding (for tables / canvases that bleed to the edge) */
  flush?: boolean;
  className?: string;
  as?: 'div' | 'section' | 'article';
}

/**
 * Panel — the core surface of MERIT.
 * A dense, hairline-bordered instrument card with an optional header rail
 * and drafting-table corner brackets.
 */
export const Panel: React.FC<PanelProps> = ({
  children,
  label,
  action,
  bracket = false,
  flush = false,
  className = '',
  as: Tag = 'div'
}) => {
  return (
    <Tag
      className={`relative rounded-xl border border-line bg-surface ${
        bracket ? 'bracketed' : ''
      } ${className}`}
    >
      {(label || action) && (
        <div className="flex items-center justify-between gap-3 px-4 h-9 border-b border-line">
          {label && (
            <span className="inline-flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.14em] text-muted">
              <span className="w-1 h-1 rounded-full bg-mint" />
              {label}
            </span>
          )}
          {action && <div className="flex items-center gap-2">{action}</div>}
        </div>
      )}
      <div className={flush ? '' : 'p-4'}>{children}</div>
    </Tag>
  );
};
