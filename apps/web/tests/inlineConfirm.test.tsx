import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { InlineConfirm } from '../src/components/ui/InlineConfirm';

describe('InlineConfirm (D-ux)', () => {
  it('focuses the cancel button on open', () => {
    render(
      <InlineConfirm
        title="Discard?"
        confirmLabel="Discard"
        cancelLabel="Cancel"
        onConfirm={() => {}}
        onCancel={() => {}}
      />
    );
    expect(screen.getByRole('button', { name: /cancel/i })).toHaveFocus();
  });

  it('calls onCancel on Escape', () => {
    const onCancel = vi.fn();
    render(
      <InlineConfirm
        title="Discard?"
        confirmLabel="Discard"
        cancelLabel="Cancel"
        onConfirm={() => {}}
        onCancel={onCancel}
      />
    );
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onCancel).toHaveBeenCalled();
  });

  it('calls onConfirm when confirm button clicked', () => {
    const onConfirm = vi.fn();
    render(
      <InlineConfirm
        title="Discard?"
        confirmLabel="Discard"
        cancelLabel="Cancel"
        onConfirm={onConfirm}
        onCancel={() => {}}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: /discard/i }));
    expect(onConfirm).toHaveBeenCalled();
  });
});