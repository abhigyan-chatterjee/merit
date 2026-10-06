import { describe, it, expect, beforeEach, vi, act } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { StrictMode } from 'react';
import { LandingPage } from '../src/pages/LandingPage';
import { AuthProvider } from '../src/store/AuthContext';
import { ProgressProvider } from '../src/store/ProgressContext';

describe('LandingPage live sort demo', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.useFakeTimers();
  });

  const mount = () =>
    render(
      <StrictMode>
        <AuthProvider>
          <ProgressProvider>
            <MemoryRouter>
              <LandingPage />
            </MemoryRouter>
          </ProgressProvider>
        </AuthProvider>
      </StrictMode>
    );

  it('counts real swaps instead of staying pinned at 0', async () => {
    mount();
    expect(screen.getByText(/\[0,1\] · 0 swaps/)).toBeInTheDocument();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5 * 220);
    });
    const counters = screen
      .getAllByText(/swaps/)
      .map((node) => node.textContent ?? '');
    expect(counters.some((t) => /^[0-9,\[\]]* · [1-9] swaps/.test(t))).toBe(true);
  }, 15000);
});
