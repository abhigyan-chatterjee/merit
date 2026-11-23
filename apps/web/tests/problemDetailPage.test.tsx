import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProblemDetailPage } from '../src/pages/ProblemDetailPage';
import { ProgressProvider } from '../src/store/ProgressContext';

const STORAGE_KEY = 'merit_store_v1';

function renderProblem(path = '/problems/arrays-hashing/two-sum') {
  return render(
    <ProgressProvider>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/problems/:topic/:slug" element={<ProblemDetailPage />} />
        </Routes>
      </MemoryRouter>
    </ProgressProvider>,
  );
}

function stored(): Record<string, unknown> {
  return JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? '{}');
}

describe('ProblemDetailPage', () => {
  beforeEach(() => {
    window.localStorage.clear();
    // The embedded CodeRunner fetches submission history on mount; a
    // guest gets 401. Stub fetch so the page settles without network.
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: async () => ({ error: { code: 'UNAUTHENTICATED', message: 'no session' } }),
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the problem statement and metadata', () => {
    renderProblem();
    expect(screen.getByRole('heading', { name: 'Two Sum' })).toBeInTheDocument();
    expect(screen.getByText('Hash Map / Complement')).toBeInTheDocument();
    expect(screen.getByLabelText('Problem Status')).toHaveValue('Todo');
    expect(screen.getByText(/Given an array of integers nums/i)).toBeInTheDocument();
  });

  it('persists a status change to storage', () => {
    renderProblem();
    fireEvent.change(screen.getByLabelText('Problem Status'), { target: { value: 'Done' } });
    expect((stored().progress as Record<string, string>)['two-sum']).toBe('Done');
  });

  it('toggles the bookmark', () => {
    renderProblem();
    fireEvent.click(screen.getByRole('button', { name: 'Bookmark problem' }));
    expect(stored().bookmarks).toContain('two-sum');
  });

  it('saves revision notes once the typing pause elapses', async () => {
    renderProblem();
    const box = screen.getByPlaceholderText(/Write down edge cases/i);
    fireEvent.change(box, { target: { value: 'complement via hash map' } });

    // The textarea echoes immediately; the write is debounced.
    expect(box).toHaveValue('complement via hash map');
    expect((stored().notes as Record<string, string> | undefined)?.['two-sum']).toBeUndefined();

    await waitFor(() =>
      expect((stored().notes as Record<string, string>)['two-sum']).toBe(
        'complement via hash map',
      ),
    );
  });

  it('reveals hints only when asked', () => {
    renderProblem();
    expect(screen.queryByText(/Hint #1/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Progressive Algorithmic Hints/i }));
    expect(screen.getByText(/Hint #1/)).toBeInTheDocument();
  });

  it('shows a reference solution when a tab is chosen', () => {
    renderProblem();
    fireEvent.click(screen.getByRole('button', { name: /Brute Force/i }));
    // The solution panel renders its Big-O annotation and code block.
    expect(screen.getByText(/Reference Solutions & Big-O/i)).toBeInTheDocument();
    expect(document.querySelector('pre')).not.toBeNull();
  });

  it('links to further reading', () => {
    renderProblem();
    expect(screen.getByText(/Further reading/i)).toBeInTheDocument();
  });

  it('links company badges to the company-filtered list', () => {
    renderProblem();
    expect(screen.getByRole('link', { name: 'TCS', exact: true })).toHaveAttribute(
      'href',
      '/problems?company=TCS',
    );
    expect(screen.getByRole('link', { name: 'Infosys', exact: true })).toHaveAttribute(
      'href',
      '/problems?company=Infosys',
    );
  });

  it('expands all companies beyond six via +N more', () => {
    renderProblem();
    // Two Sum has 7 companies: 6 badges plus the expansion control.
    expect(screen.queryByRole('link', { name: 'Goldman Sachs', exact: true })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '+1 more' }));
    expect(screen.getByRole('link', { name: 'Goldman Sachs', exact: true })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Show less' }));
    expect(screen.queryByRole('link', { name: 'Goldman Sachs', exact: true })).not.toBeInTheDocument();
  });

  it('does not offer expansion for six or fewer companies', () => {
    renderProblem('/problems/stack/baseball-game');
    expect(screen.getByRole('link', { name: 'Turing', exact: true })).toHaveAttribute(
      'href',
      '/problems?company=Turing',
    );
    expect(screen.queryByRole('button', { name: /\+\d+ more/ })).not.toBeInTheDocument();
  });

  it('renders not-found for an unknown slug', () => {
    renderProblem('/problems/arrays-hashing/does-not-exist');
    expect(screen.getByText(/Problem Not Found/i)).toBeInTheDocument();
  });
});
