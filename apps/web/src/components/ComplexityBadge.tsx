import React from 'react';

interface ComplexityBadgeProps {
  label: string;
  value: string;
  variant?: 'mint' | 'violet' | 'amber';
}

export const ComplexityBadge: React.FC<ComplexityBadgeProps> = ({
  label,
  value,
  variant = 'mint'
}) => {
  const tone = {
    mint: 'text-mint',
    violet: 'text-violet',
    amber: 'text-amber'
  }[variant];

  return (
    <span className="inline-flex items-stretch rounded-md border border-line overflow-hidden bg-canvas">
      <span className="px-2 py-1 text-[9px] font-mono uppercase tracking-[0.14em] text-muted border-r border-line flex items-center">
        {label}
      </span>
      <span className={`px-2 py-1 text-[11px] font-mono font-bold tnum flex items-center ${tone}`}>
        {value}
      </span>
    </span>
  );
};
