import React from 'react';

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionLabel,
  onAction
}) => {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-14 text-center rounded-xl border border-dashed border-line bg-surface">
      <div
        className="w-12 h-12 rounded-xl border border-line hatch mb-4"
        aria-hidden="true"
      />
      <h3 className="text-sm font-semibold text-ink mb-1.5">{title}</h3>
      <p className="text-xs text-muted max-w-sm leading-relaxed mb-5">{description}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-3.5 py-1.5 rounded-lg border border-line bg-canvas text-xs font-medium text-ink hover:border-mint hover:text-mint transition cursor-pointer"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};
