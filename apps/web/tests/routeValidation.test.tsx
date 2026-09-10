import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
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

  it('renders NotFound for unknown quiz topic', async () => {
    renderWithRouter('/quiz/unknown-quantum-computing-topic');
    expect(await screen.findByTestId('not-found-page', {}, { timeout: 10000 })).toBeInTheDocument();
    expect(screen.getByText(/Quiz Not Found/i)).toBeInTheDocument();
  });

  it('renders NotFound for unknown guided path id', async () => {
    renderWithRouter('/learn/unknown-alien-path');
    expect(await screen.findByTestId('not-found-page', {}, { timeout: 10000 })).toBeInTheDocument();
    expect(screen.getByText(/Learning Path Not Found/i)).toBeInTheDocument();
  });

  it('renders NotFound for random unmatched route', async () => {
    renderWithRouter('/some/completely/random/route');
    expect(await screen.findByTestId('not-found-page', {}, { timeout: 10000 })).toBeInTheDocument();
  });

  it('renders real problem when topic and slug match', async () => {
    renderWithRouter('/problems/arrays-hashing/two-sum');
    await waitFor(() => {
      expect(screen.queryByTestId('not-found-page')).not.toBeInTheDocument();
    });
    expect(screen.getAllByText('Two Sum').length).toBeGreaterThanOrEqual(1);
  });
});
