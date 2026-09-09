import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AdminPage } from '../src/pages/AdminPage';
import { AuthProvider } from '../src/store/AuthContext';
import * as apiModule from '../src/utils/api';

describe('AdminPage Component (Phase 9)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('rejects non-admin student users with access warning', async () => {
    vi.spyOn(apiModule.authApi, 'getMe').mockResolvedValue({
      id: 'usr-student',
      email: 'student@test.com',
      display_name: 'Student User',
      displayName: 'Student User',
      role: 'student',
      created_at: '2026-09-01T00:00:00Z',
      last_login_at: null,
    });

    render(
      <AuthProvider>
        <MemoryRouter>
          <AdminPage />
        </MemoryRouter>
      </AuthProvider>
    );

    expect(
      await screen.findByText(/Administrative Privileges Required/i)
    ).toBeInTheDocument();
    expect(screen.queryByText(/Admin Control Center/i)).not.toBeInTheDocument();
  });

  it('allows authorized admins to view stats and approve items in review queue', async () => {
    vi.spyOn(apiModule.authApi, 'getMe').mockResolvedValue({
      id: 'usr-admin',
      email: 'admin@test.com',
      display_name: 'Admin Lead',
      displayName: 'Admin Lead',
      role: 'admin',
      created_at: '2026-09-01T00:00:00Z',
      last_login_at: null,
    });

    vi.spyOn(apiModule.adminApi, 'getStats').mockResolvedValue({
      users_count: 42,
      total_submissions: 150,
      ac_submissions: 120,
      ac_rate_pct: 80.0,
      total_quiz_attempts: 75,
      verified_questions: 831,
      draft_questions: 2,
      verified_problems: 30,
      draft_problems: 0,
    });

    vi.spyOn(apiModule.adminApi, 'getReviewQueue').mockResolvedValue([
      {
        id: 'draft-q-1',
        topic: 'dynamic-programming',
        difficulty: 'medium',
        prompt: 'Draft question on optimal substructure in matrix chain multiplication',
        options: ['O(n^3)', 'O(n^2)', 'O(n)', 'O(2^n)'],
        correct_index: 0,
        explanation: 'Standard matrix chain multiplication dynamic programming runs in O(n^3).',
        source: 'curated',
      },
    ]);

    const reviewSpy = vi
      .spyOn(apiModule.adminApi, 'reviewQuestion')
      .mockResolvedValue({ status: 'verified' });

    render(
      <AuthProvider>
        <MemoryRouter>
          <AdminPage />
        </MemoryRouter>
      </AuthProvider>
    );

    // Header and stats rendered. AdminPage loads stats asynchronously in
    // useEffect, so wait for the async fetch to resolve first.
    expect(await screen.findByText(/Admin Control Center/i)).toBeInTheDocument();
    expect(await screen.findByText('Registered Users')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument(); // users count
    expect(screen.getByText('831')).toBeInTheDocument(); // verified questions

    // Switch to Review Queue tab
    fireEvent.click(screen.getByText(/Review Queue/i));

    // Question in review queue should appear
    expect(
      await screen.findByText(/Draft question on optimal substructure/i)
    ).toBeInTheDocument();

    // Click Approve & Verify
    const approveBtn = screen.getByText(/Approve & Verify/i);
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(reviewSpy).toHaveBeenCalledWith(
        'draft-q-1',
        'approved',
        expect.stringContaining('Reviewed by')
      );
    });
  });
});
