import { describe, it, expect, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { React, useState } from 'react';
import { useDialogFocus } from '../src/hooks/useDialogFocus';

function Probe({ label }: { label: string }) {
  const [open, setOpen] = useState(true);
  // A fresh inline closure per parent render is exactly the case the hook must
  // survive: Navbar/Footer/CodeRunner all pass inline onClose.
  const ref = useDialogFocus<HTMLDivElement>(open, () => setOpen(false));
  return (
    <>
      <button data-testid="origin">{label}</button>
      {open && (
        <>
          <button data-testid="decoy" onClick={() => {}}>
            decoy
          </button>
          <div ref={ref} role="dialog" aria-modal="true">
            <button data-testid="inside" onClick={() => {}}>
              inside
            </button>
            <button data-testid="close" onClick={() => setOpen(false)}>
              close
            </button>
          </div>
        </>
      )}
    </>
  );
}

describe('useDialogFocus', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('re-renders with inline onClose do not steal focus, and close returns it to the opener', async () => {
    vi.useFakeTimers();
    const { rerender } = render(<Probe label="opener" />);

    // The hook defers focus via rAF.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(30);
    });
    expect(document.activeElement?.textContent).toBe('inside');

    // User work inside, then a parent-button click re-renders, then another
    // parent re-render — all while the dialog stays open. Same component, new
    // inline closures each time (the actual Navbar/Footer/CodeRunner shape).
    await act(async () => {
      fireEvent.click(screen.getByTestId('inside'));
      rerender(<Probe label="opener" />);
      await vi.advanceTimersByTimeAsync(30);
      rerender(<Probe label="opener" />);
      await vi.advanceTimersByTimeAsync(30);
    });
    expect(document.activeElement?.textContent).toBe('inside');

    fireEvent.click(screen.getByTestId('close'));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(30);
    });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    // Focus returns to the original opener, not whatever was focused mid-dialog.
    expect(document.activeElement?.textContent).toBe('opener');
  }, 10000);
});
