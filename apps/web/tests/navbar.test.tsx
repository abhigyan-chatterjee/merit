import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Navbar } from '../src/components/Navbar';
import { ProgressProvider } from '../src/store/ProgressContext';
import { AuthProvider } from '../src/store/AuthContext';
import * as apiModule from '../src/utils/api';

const mockNavigate = vi.hoisted(() => vi.fn());
vi.mock('react-router-dom', async (importOriginal) => ({
  ...(await importOriginal()),
  useNavigate: () => mockNavigate,
}));

function renderNavbar() {
  return render(
    <ProgressProvider>
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    </ProgressProvider>
  );
}

describe('Navbar search Enter-to-jump (D-search)', () => {
  beforeEach(() => {
    window.localStorage.clear();
    mockNavigate.mockReset();
  });

  it('pressing Enter opens the first matching result (paths take priority)', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));

    const input = screen.getByPlaceholderText(/search structures/i);
    fireEvent.change(input, { target: { value: 'foundation' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    expect(mockNavigate).toHaveBeenCalledWith('/learn/foundation');
  });

  it('pressing Enter with no results does not navigate', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));

    const input = screen.getByPlaceholderText(/search structures/i);
    fireEvent.change(input, { target: { value: 'zzz-no-such-term-xyz' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('shows Suggested label when query is empty', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));
    expect(screen.getByText('Suggested')).toBeInTheDocument();
  });

  it('shows results count when typed', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));
    const input = screen.getByPlaceholderText(/search structures/i);
    fireEvent.change(input, { target: { value: 'heap' } });
    expect(screen.getByText(/result/i)).toBeInTheDocument();
  });

  it('ArrowDown moves active row', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));
    const input = screen.getByPlaceholderText(/search structures/i);
    fireEvent.change(input, { target: { value: 'heap' } });

    const options = screen.getAllByRole('option');
    expect(options.length).toBeGreaterThan(1);
    expect(options[0]).toHaveAttribute('aria-selected', 'true');
    expect(input).toHaveAttribute('aria-activedescendant', options[0].id);

    fireEvent.keyDown(input, { key: 'ArrowDown', code: 'ArrowDown' });

    expect(options[0]).toHaveAttribute('aria-selected', 'false');
    expect(options[1]).toHaveAttribute('aria-selected', 'true');
    expect(input).toHaveAttribute('aria-activedescendant', options[1].id);
  });

  it('match-quality: exact title match ranks above blurb match', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));
    const input = screen.getByPlaceholderText(/search structures/i);
    // 'heap' matches the visualizer title and problems only via their pattern.
    fireEvent.change(input, { target: { value: 'heap' } });
    const options = screen.getAllByRole('option');
    expect(options[0]).toHaveTextContent('Min / Max Binary Heap');
    expect(options[0]).toHaveTextContent('Visualizer');
    expect(options.findIndex((o) => o.textContent?.includes('Problem'))).toBeGreaterThan(0);

    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    expect(mockNavigate).toHaveBeenCalledWith('/visualizers/heap');
  });

  it('finds and navigates to targeted exam when searching', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));
    const input = screen.getByPlaceholderText(/search structures/i);
    fireEvent.change(input, { target: { value: 'TCS NQT' } });

    const examOption = screen.getByRole('option', { name: /TCS NQT & Digital Mock/i });
    expect(examOption).toBeInTheDocument();
    expect(screen.getByText('Exam')).toBeInTheDocument();

    fireEvent.click(examOption);
    expect(mockNavigate).toHaveBeenCalledWith('/exams/tcs-nqt');
  });

  it('finds and navigates to quiz topic when searching', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));
    const input = screen.getByPlaceholderText(/search structures/i);
    fireEvent.change(input, { target: { value: 'SQL' } });

    expect(screen.getByText(/SQL & Databases/i)).toBeInTheDocument();
    expect(screen.getByText('Quiz')).toBeInTheDocument();

    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    expect(mockNavigate).toHaveBeenCalledWith('/quiz/sql');
  });
});

describe('Navbar due badge', () => {
  beforeEach(() => {
    window.localStorage.clear();
    mockNavigate.mockReset();
    vi.restoreAllMocks();
  });

  const student = {
    id: 'usr-1',
    email: 'student@test.com',
    display_name: 'Test Student',
    displayName: 'Test Student',
    role: 'student',
    created_at: '2026-09-01T00:00:00Z',
    last_login_at: null,
  };

  const summaryWithDue = (due: number) => ({
    solved_count: 0,
    doing_count: 0,
    total_problems: 10,
    current_streak: 1,
    activity_days: {},
    progress: {},
    notes: {},
    bookmarks: [],
    visited_visualizers: [],
    has_imported_local: true,
    due_today_count: due,
  });

  function renderSignedNavbar(due: number) {
    vi.spyOn(apiModule.authApi, 'getMe').mockResolvedValue(student);
    vi.spyOn(apiModule.progressApi, 'getSummary').mockResolvedValue(summaryWithDue(due) as never);
    return render(
      <AuthProvider>
        <ProgressProvider>
          <MemoryRouter>
            <Navbar />
          </MemoryRouter>
        </ProgressProvider>
      </AuthProvider>
    );
  }

  it('renders amber due badge linking to /review when signed in with due items', async () => {
    renderSignedNavbar(3);
    const badge = await screen.findByRole('link', { name: '3 due for review today' });
    expect(badge).toHaveAttribute('href', '/review');
    expect(badge).toHaveTextContent('due');
    expect(badge).toHaveTextContent('3');
  });

  it('does not render due badge when count is 0', async () => {
    renderSignedNavbar(0);
    await waitFor(() => expect(screen.getByRole('link', { name: /Sign In|Learning streak/i })).toBeInTheDocument());
    expect(screen.queryByRole('link', { name: /due for review today/ })).not.toBeInTheDocument();
  });

  it('does not render due badge when signed out', () => {
    renderNavbar();
    expect(screen.queryByRole('link', { name: /due for review today/ })).not.toBeInTheDocument();
  });

  it('finds Spaced Review Deck when searching review', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));
    const input = screen.getByPlaceholderText(/search structures/i);
    fireEvent.change(input, { target: { value: 'review' } });
    expect(screen.getByText('Spaced Review Deck')).toBeInTheDocument();
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    expect(mockNavigate).toHaveBeenCalledWith('/review');
  });

  it('includes dedicated Interview tab in navigation and global search', () => {
    renderNavbar();
    const links = screen.getAllByRole('link', { name: 'Interview' });
    expect(links.length).toBeGreaterThanOrEqual(1);
    expect(links[0]).toHaveAttribute('href', '/interview');

    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));
    const input = screen.getByPlaceholderText(/search structures/i);
    fireEvent.change(input, { target: { value: 'interview' } });
    expect(screen.getByText('AI Mock Interview Portal')).toBeInTheDocument();
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    expect(mockNavigate).toHaveBeenCalledWith('/interview');
  });
});
