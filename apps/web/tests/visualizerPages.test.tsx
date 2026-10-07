import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { VisualizersListPage } from '../src/pages/VisualizersListPage';
import { VisualizerDetailPage } from '../src/pages/VisualizerDetailPage';
import { ProgressProvider } from '../src/store/ProgressContext';
import { VISUALIZERS } from '../src/data/curriculum';

const STORAGE_KEY = 'merit_store_v1';

function renderList() {
  return render(
    <ProgressProvider>
      <MemoryRouter initialEntries={['/visualizers']}>
        <Routes>
          <Route path="/visualizers" element={<VisualizersListPage />} />
        </Routes>
      </MemoryRouter>
    </ProgressProvider>,
  );
}

function renderDetail(id: string) {
  return render(
    <ProgressProvider>
      <MemoryRouter initialEntries={[`/visualizers/${id}`]}>
        <Routes>
          <Route path="/visualizers/:id" element={<VisualizerDetailPage />} />
        </Routes>
      </MemoryRouter>
    </ProgressProvider>,
  );
}

describe('VisualizersListPage', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('lists every visualizer', () => {
    renderList();
    expect(screen.getByRole('heading', { name: /Twelve interactive structures/i })).toBeInTheDocument();
    // Each card carries the visualizer title and its own "Open workbench" link.
    for (const vis of VISUALIZERS) {
      expect(screen.getByText(vis.title)).toBeInTheDocument();
    }
    expect(screen.getAllByRole('link', { name: /Open workbench/i })).toHaveLength(
      VISUALIZERS.length,
    );
  });

  it('filters by category', () => {
    renderList();
    fireEvent.click(screen.getByRole('button', { name: /^Algorithms/ }));

    expect(screen.getByText('Sorting Algorithms')).toBeInTheDocument();
    // 'Static & Dynamic Array' is a Linear item, so it drops out.
    expect(screen.queryByText('Static & Dynamic Array')).not.toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: /Open workbench/i }).length).toBeLessThan(
      VISUALIZERS.length,
    );
  });

  it('toggles a bookmark and persists it', () => {
    renderList();
    fireEvent.click(screen.getByRole('button', { name: /Add bookmark for Sorting Algorithms/i }));
    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? '{}');
    expect(stored.bookmarks).toContain('sorting');
  });
});

describe('VisualizerDetailPage', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('renders not-found for an unknown id', () => {
    renderDetail('no-such-visualizer');
    expect(screen.getByText(/Visualizer Not Found/i)).toBeInTheDocument();
  });

  it('renders the workbench for a known id', () => {
    renderDetail('sorting');
    expect(screen.getByRole('heading', { name: /Sorting Algorithms/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Back to all visualizers/i })).toBeInTheDocument();
  });
});
