import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DashboardPage } from '../src/pages/DashboardPage';
import { ProgressProvider } from '../src/store/ProgressContext';

describe('DashboardPage Honest Initial State (D7)', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('renders fresh user dashboard with 0s and "Start your first problem" CTA', () => {
    render(
      <ProgressProvider>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </ProgressProvider>
    );

    // Assert 0 problems solved, 0 in progress, 0d streak
    expect(screen.getAllByText('0/30').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('0d')).toBeInTheDocument();
    expect(screen.getAllByText(/Start your first problem/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/No assessment scores recorded yet/i)).toBeInTheDocument();
  });
});
