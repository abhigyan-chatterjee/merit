import React, { useEffect, useRef } from 'react';

interface InlineConfirmProps {
  title: string;
  body?: string;
  confirmLabel: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * InlineConfirm — an unstyled-thread, non-blocking confirmation rendered in
 * place of the trigger. Used by destructive resets. Esc cancels; Enter
 * activates whichever button currently has focus (Cancel is focused on open).
 * The parent is responsible for restoring focus to the trigger after close.
 */
export const InlineConfirm: React.FC<InlineConfirmProps> = ({
  title,
  body,
  confirmLabel,
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
}) => {
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    cancelRef.current?.focus();
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onCancel();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onCancel]);

  return (
    <div
      role="group"
      aria-label={title}
      className="inline-flex flex-wrap items-center gap-2 px-2 py-1 rounded-lg border border-rose/40 bg-rose/10"
    >
      <span className="text-xs font-medium text-ink">{title}</span>
      {body && <span className="text-[11px] text-muted">{body}</span>}
      <button
        ref={cancelRef}
        type="button"
        onClick={onCancel}
        className="px-2.5 py-1 rounded border border-line bg-surface text-xs font-mono text-muted hover:text-ink transition cursor-pointer"
      >
        {cancelLabel}
      </button>
      <button
        type="button"
        onClick={onConfirm}
        className="px-2.5 py-1 rounded border border-rose/40 bg-rose/10 text-xs font-mono text-rose hover:bg-rose/20 transition cursor-pointer"
      >
        {confirmLabel}
      </button>
    </div>
  );
};