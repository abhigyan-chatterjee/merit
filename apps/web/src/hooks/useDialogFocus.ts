import { useEffect, useRef } from 'react';

const FOCUSABLE =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * useDialogFocus — the dialog focus contract.
 *
 * On open: marks everything outside the dialog `inert` so pointer and
 * keyboard focus cannot reach the background, moves focus to the first
 * focusable control inside, and traps Tab within the dialog. On close:
 * clears `inert` and returns focus to whatever opened it.
 *
 * Without all three parts the dialog is a lie: a role is a promise of a
 * full keyboard model, and an `aria-modal` overlay that lets Tab walk
 * out the back is worse than no dialog at all.
 */
export function useDialogFocus<T extends HTMLElement>(
  isOpen: boolean,
  onClose: () => void
) {
  const ref = useRef<T>(null);
  const returnFocusTo = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    returnFocusTo.current = document.activeElement as HTMLElement | null;

    const dialog = ref.current;
    if (!dialog) return;

    const moveFocusIn = () => {
      const first = dialog.querySelector<HTMLElement>(FOCUSABLE);
      (first ?? dialog).focus();
    };

    // Defer one frame so the dialog is painted before focus lands.
    const raf = requestAnimationFrame(moveFocusIn);

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
        return;
      }
      if (e.key !== 'Tab') return;

      const items = [...dialog.querySelectorAll<HTMLElement>(FOCUSABLE)].filter(
        (el) => el.offsetParent !== null || el === document.activeElement
      );
      if (items.length === 0) {
        e.preventDefault();
        return;
      }

      const first = items[0];
      const last = items[items.length - 1];
      const active = document.activeElement as HTMLElement | null;

      if (e.shiftKey && (active === first || !dialog.contains(active))) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && active === last) {
        e.preventDefault();
        first.focus();
      }
    };

    // Background goes inert so nothing behind the overlay is reachable. The
    // dialog usually renders *inside* the app shell (via a navbar), so the
    // whole shell cannot be inerted. Instead walk up from the dialog and
    // inert every sibling that does not contain it.
    const inerted: HTMLElement[] = [];
    let node: HTMLElement | null = dialog;
    while (node && node !== document.body) {
      const parent: HTMLElement | null = node.parentElement;
      if (!parent) break;
      for (const sibling of Array.from(parent.children)) {
        if (sibling === node || !(sibling instanceof HTMLElement)) continue;
        if (sibling.hasAttribute('inert')) continue;
        sibling.setAttribute('inert', '');
        inerted.push(sibling);
      }
      node = parent;
    }

    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    document.addEventListener('keydown', handleKeyDown, true);

    return () => {
      cancelAnimationFrame(raf);
      document.removeEventListener('keydown', handleKeyDown, true);
      inerted.forEach((el) => el.removeAttribute('inert'));
      document.body.style.overflow = prevOverflow;
      returnFocusTo.current?.focus?.();
    };
  }, [isOpen, onClose]);

  return ref;
}
