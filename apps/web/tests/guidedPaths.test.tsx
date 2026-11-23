import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, within, fireEvent } from '@testing-library/react';
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

  it('lists every path with its progress', () => {
    renderAt('/learn', <GuidedPathsPage />, '/learn');
    expect(screen.getByRole('heading', { name: /Learning paths/i })).toBeInTheDocument();

    for (const path of LEARNING_PATHS) {
      const card = screen.getByRole('link', { name: new RegExp(path.title, 'i') });
      expect(within(card).getByText(/0%/)).toBeInTheDocument();
    }
  });

  it('badges the recommended path', () => {
    renderAt('/learn', <GuidedPathsPage />, '/learn');
    const card = screen.getByRole('link', { name: /Foundation/i });
    expect(within(card).getByText(/Start here/i)).toBeInTheDocument();
  });

  it('filters path cards by track tab', () => {
    renderAt('/learn', <GuidedPathsPage />, '/learn');

    fireEvent.click(screen.getByRole('button', { name: /^Foundational$/i }));
    expect(screen.getByRole('link', { name: /Foundation/i })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /^Targeted/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /TCS/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Infosys/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Mastery/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Product/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Placement & Company/i }));
    expect(screen.getByRole('link', { name: /^Targeted/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /TCS/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Infosys/i })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Foundation/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Mastery/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /^Specialised$/i }));
    expect(screen.getByRole('link', { name: /Mastery/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Product/i })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /^Targeted/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /^All$/i }));
    for (const path of LEARNING_PATHS) {
      expect(screen.getByRole('link', { name: new RegExp(path.title, 'i') })).toBeInTheDocument();
    }
  });

  it('shows a one-line blurb on each path card', () => {
    renderAt('/learn', <GuidedPathsPage />, '/learn');
    for (const path of LEARNING_PATHS) {
      const card = screen.getByRole('link', { name: new RegExp(path.title, 'i') });
      expect(within(card).getByText(path.blurb)).toBeInTheDocument();
    }
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

  it('appends path context with & when a mock step already has ?mock=true', () => {
    const targeted = LEARNING_PATHS.find((p) => p.id === 'targeted')!;
    const mockIdx = targeted.steps.findIndex((s) => s.type === 'mock');
    expect(mockIdx).toBeGreaterThan(-1);

    renderAt(`/learn/${targeted.id}`, <GuidedPathDetailPage />, '/learn/:id');

    const mockLink = screen.getByRole('link', {
      name: new RegExp(targeted.steps[mockIdx].title ?? 'mock', 'i'),
    });
    expect(mockLink).toHaveAttribute(
      'href',
      `/quiz/mixed?mock=true&path=${targeted.id}&step=${mockIdx}`,
    );
  });
});
