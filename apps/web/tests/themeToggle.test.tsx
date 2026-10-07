import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeToggle } from '../src/components/ThemeToggle';
import { ProgressProvider } from '../src/store/ProgressContext';

function renderToggle() {
  return render(
    <ProgressProvider>
      <ThemeToggle />
    </ProgressProvider>,
  );
}

describe('ThemeToggle', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('starts in dark mode', () => {
    renderToggle();
    const toggle = screen.getByRole('switch', { name: /Switch to light theme/i });
    expect(toggle).toHaveAttribute('aria-checked', 'false');
  });

  it('switches to light mode and persists the choice', () => {
    renderToggle();
    fireEvent.click(screen.getByRole('switch', { name: /Switch to light theme/i }));

    const toggle = screen.getByRole('switch', { name: /Switch to dark theme/i });
    expect(toggle).toHaveAttribute('aria-checked', 'true');
    expect(window.localStorage.getItem('merit_theme_v1')).toContain('light');
  });

  it('respects a stored theme on load', () => {
    window.localStorage.setItem('merit_theme_v1', JSON.stringify('light'));
    renderToggle();
    expect(screen.getByRole('switch', { name: /Switch to dark theme/i })).toHaveAttribute(
      'aria-checked',
      'true',
    );
  });
});
