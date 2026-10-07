import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { GuidedPathsPage } from '../src/pages/GuidedPathsPage';
import { GuidedPathDetailPage } from '../src/pages/GuidedPathDetailPage';
import { ProgressProvider } from '../src/store/ProgressContext';
import { LEARNING_PATHS } from '../src/data/learningPaths';
import { EMPTY_INITIAL_STATE } from '../src/store/schema';

const STORAGE_KEY = 'merit_store_v1';
const FOUNDATION = LEARNING_PATHS.find((p) => p.id === 'foundation')!;

function renderAt(path: string, element: React.ReactElement, route: string) {
  return render(
    <ProgressProvider>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path={route} element={element} />
        </Routes>
      </MemoryRouter>
    </ProgressProvider>,
  );
}

describe('guided paths', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('lists every path with its step count and progress', () => {
    renderAt('/learn', <GuidedPathsPage />, '/learn');
    expect(screen.getByRole('heading', { name: /Learning paths/i })).toBeInTheDocument();

    for (const path of LEARNING_PATHS) {
      const card = screen.getByRole('link', { name: new RegExp(path.title, 'i') });
      expect(within(card).getByText(new RegExp(`${path.steps.length} steps`))).toBeInTheDocument();
      expect(within(card).getByText(/0 \d+ complete|0\/\d+ complete/)).toBeInTheDocument();
    }
  });

  it('badges the recommended path', () => {
    renderAt('/learn', <GuidedPathsPage />, '/learn');
    const card = screen.getByRole('link', { name: /Foundation/i });
    expect(within(card).getByText(/Start here/i)).toBeInTheDocument();
  });

  it('shows not-found for an unknown path id', () => {
    renderAt('/learn/no-such-path', <GuidedPathDetailPage />, '/learn/:id');
    expect(screen.getByText(/Learning Path Not Found/i)).toBeInTheDocument();
  });

  it('renders the fallback path with its steps', () => {
    renderAt(`/learn/${FOUNDATION.id}`, <GuidedPathDetailPage />, '/learn/:id');
    expect(screen.getByRole('heading', { name: /Foundation/i })).toBeInTheDocument();
    expect(screen.getByText(new RegExp(`/${FOUNDATION.steps.length} complete`))).toBeInTheDocument();
  });

  it('agrees with the list card on done/total and percent', () => {
    // One problem step marked done. Both surfaces must count it identically —
    // the shared-rule invariant for path progress.
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ ...EMPTY_INITIAL_STATE, progress: { 'two-sum': 'Done' } }),
    );
    const expectedDone = 1;
    const expectedPct = Math.round((expectedDone / FOUNDATION.steps.length) * 100);

    const expectedText = `${expectedDone}/${FOUNDATION.steps.length} complete`;
    const expectedPctText = `${expectedPct}%`;

    const list = renderAt('/learn', <GuidedPathsPage />, '/learn');
    const card = screen.getByRole('link', { name: /Foundation/i });
    // The card renders "<n> steps · <done>/<total> complete", so match loosely.
    expect(within(card).getByText(new RegExp(expectedText))).toBeInTheDocument();
    expect(within(card).getByText(expectedPctText)).toBeInTheDocument();
    list.unmount();

    renderAt(`/learn/${FOUNDATION.id}`, <GuidedPathDetailPage />, '/learn/:id');
    expect(screen.getByText(expectedText)).toBeInTheDocument();
    expect(screen.getByText(expectedPctText)).toBeInTheDocument();
  });

  it('does not fetch the server path for a guest, keeping counting local', async () => {
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({}),
    });
    vi.stubGlobal('fetch', fetchSpy);

    renderAt(`/learn/${FOUNDATION.id}`, <GuidedPathDetailPage />, '/learn/:id');

    expect(screen.getByText(new RegExp(`/${FOUNDATION.steps.length} complete`))).toBeInTheDocument();
    const pathCalls = fetchSpy.mock.calls.filter((c) => String(c[0]).includes('/paths/'));
    expect(pathCalls).toHaveLength(0);
  });
});
