import React from 'react';

interface SectionLabelProps {
  /** Two-digit section index, e.g. "01" */
  index?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

/**
 * SectionLabel — numbered datasheet-style section heading with a
 * hairline rule that runs to the end of the container.
 */
export const SectionLabel: React.FC<SectionLabelProps> = ({
  index,
  title,
  description,
  action
}) => {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        {index && (
          <span className="font-mono text-[10px] tracking-[0.2em] text-mint shrink-0">
            {index}
          </span>
        )}
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted shrink-0">
          {title}
        </span>
        <span className="flex-1 h-px bg-line" />
        {action}
      </div>
      {description && (
        <p className="text-xs text-muted max-w-2xl leading-relaxed">{description}</p>
      )}
    </div>
  );
};
