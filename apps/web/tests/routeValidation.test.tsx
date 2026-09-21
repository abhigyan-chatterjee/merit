import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppRoutes } from '../src/routes';
import { ProgressProvider } from '../src/store/ProgressContext';

function mockGuestFetch() {
  vi.spyOn(global, 'fetch').mockImplementation(async (url) => {
    const u = String(url);
    if (u.includes('/auth/me') || u.includes('/auth/refresh')) {
      return new Response(
        JSON.stringify({ error: { code: 'UNAUTHORIZED', message: 'Not logged in' } }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      );
    }
    if (u.includes('/api/v1/paths/')) {
      return new Response(JSON.stringify({ detail: { code: 'PATH_NOT_FOUND' } }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    if (u.includes('/api/v1/problems/')) {
      return new Response(JSON.stringify({ detail: { code: 'PROBLEM_NOT_FOUND' } }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    return new Response(JSON.stringify({}), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  });
}

function renderWithRouter(initialEntry: string) {
  return render(
    <ProgressProvider>
      <MemoryRouter initialEntries={[initialEntry]}>
        <AppRoutes />
      </MemoryRouter>
    </ProgressProvider>
  );
}

describe('Route Validation & 404 Handling (D5)', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
    mockGuestFetch();
  });

  it('renders NotFound for unknown visualizer id', async () => {
    renderWithRouter('/visualizers/non-existent-visualizer-xyz');
    // Lazy route chunks can be slow to resolve under full-suite load.
    expect(await screen.findByTestId('not-found-page', {}, { timeout: 10000 })).toBeInTheDocument();
    expect(screen.getByText(/Visualizer Not Found/i)).toBeInTheDocument();
  });

  it('renders NotFound for mismatching problem slug and topic', async () => {
    // two-sum belongs to 'arrays-hashing', not 'graphs'
    renderWithRouter('/problems/graphs/two-sum');
    expect(await screen.findByTestId('not-found-page', {}, { timeout: 10000 })).toBeInTheDocument();
    expect(screen.getByText(/Problem Not Found/i)).toBeInTheDocument();
  });

  it('renders NotFound for unknown problem slug', async () => {
    renderWithRouter('/problems/arrays-hashing/not-a-real-problem');
    expect(await screen.findByTestId('not-found-page', {}, { timeout: 10000 })).toBeInTheDocument();
    expect(screen.getByText(/Problem Not Found/i)).toBeInTheDocument();
  });

  it('serves a live quiz instead of 404 for exam topics like aptitude (spaced-recall links)', async () => {
    renderWithRouter('/quiz/aptitude');
    await waitFor(
      () => {
        expect(screen.queryByTestId('not-found-page')).not.toBeInTheDocument();
      },
      { timeout: 10000 }
    );
    // Guest with no static bank for aptitude: honest empty-state, never a 404.
    expect(await screen.findByText('No Questions Available', {}, { timeout: 10000 })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Aptitude/i })).toBeInTheDocument();
  }, 20000);

  it('serves a live quiz instead of 404 for unknown quiz topic', async () => {
    renderWithRouter('/quiz/unknown-quantum-computing-topic');
    await waitFor(
      () => {
        expect(screen.queryByTestId('not-found-page')).not.toBeInTheDocument();
      },
      { timeout: 10000 }
    );
    expect(await screen.findByText('No Questions Available', {}, { timeout: 10000 })).toBeInTheDocument();
  }, 20000);

  it('renders NotFound for unknown guided path id', async () => {
    renderWithRouter('/learn/unknown-alien-path');
    expect(await screen.findByTestId('not-found-page', {}, { timeout: 10000 })).toBeInTheDocument();
    expect(screen.getByText(/Learning Path Not Found/i)).toBeInTheDocument();
  });

  it('recovery link points to the live /learn catalog route (not the dead /paths)', async () => {
    renderWithRouter('/learn/unknown-alien-path');
    expect(await screen.findByTestId('not-found-page', {}, { timeout: 10000 })).toBeInTheDocument();

    // The recovery link must target the live catalog route.
    const recovery = screen.getByRole('link', { name: /All Guided Paths/i });
    expect(recovery).toHaveAttribute('href', '/learn');

    // Clicking it must render the catalog, not another 404.
    fireEvent.click(recovery);
    expect(
      await screen.findByRole('heading', { name: /Learning paths/i }, { timeout: 10000 })
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Foundation/i })).toBeInTheDocument();
    expect(screen.queryByTestId('not-found-page')).not.toBeInTheDocument();
  });

  it('renders NotFound for random unmatched route', async () => {
    renderWithRouter('/some/completely/random/route');
    expect(await screen.findByTestId('not-found-page', {}, { timeout: 10000 })).toBeInTheDocument();
  });

  it('renders the privacy policy and terms pages', async () => {
    renderWithRouter('/privacy');
    expect(await screen.findByRole('heading', { name: 'Privacy Policy' })).toBeInTheDocument();

    renderWithRouter('/terms');
    expect(await screen.findByRole('heading', { name: 'Terms of Service' })).toBeInTheDocument();
  });

  it('renders real problem when topic and slug match', async () => {
    renderWithRouter('/problems/arrays-hashing/two-sum');
    await waitFor(() => {
      expect(screen.queryByTestId('not-found-page')).not.toBeInTheDocument();
    });
    expect(screen.getAllByText('Two Sum').length).toBeGreaterThanOrEqual(1);
  });

  it('renders editorial + further reading on a PAF problem page', async () => {
    // two-sum is legacy (no editorial); assert on a PAF problem instead.
    renderWithRouter('/problems/stack/asteroid-collision');
    await waitFor(() => {
      expect(screen.queryByTestId('not-found-page')).not.toBeInTheDocument();
    });
    expect(screen.getByText('Colliding Asteroids')).toBeInTheDocument();
    // Editorial accordion header is always visible for PAF problems; body is collapsed.
    expect(screen.getByRole('heading', { name: /Editorial/i })).toBeInTheDocument();
    expect(screen.queryByText(/left-moving rock duel/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Editorial/i }));
    expect(await screen.findByText(/left-moving rock duel/i)).toBeInTheDocument();
    expect(screen.getByText(/pushed and popped at most once/i)).toBeInTheDocument();
    // Further reading: at least one outbound link, max 3, safe attributes.
    const readingHeading = screen.getByRole('heading', { name: /Further reading/i });
    const section = readingHeading.closest('div')!.parentElement!;
    const links = Array.from(section.querySelectorAll('a'));
    expect(links.length).toBeGreaterThanOrEqual(1);
    expect(links.length).toBeLessThanOrEqual(3);
    for (const link of links) {
      expect(link).toHaveAttribute('target', '_blank');
      expect(link.getAttribute('rel')).toMatch(/noreferrer/);
    }
  });
});
