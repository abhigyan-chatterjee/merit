import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { VisualizerDetailPage } from '../src/pages/VisualizerDetailPage';
import { ProgressProvider } from '../src/store/ProgressContext';
import { VISUALIZERS } from '../src/data/curriculum';

function renderVisualizer(id: string) {
  return render(
    <ProgressProvider>
      <MemoryRouter initialEntries={[`/visualizers/${id}`]}>
        <Routes>
          <Route path="/visualizers/:id" element={<VisualizerDetailPage />} />
        </Routes>
      </MemoryRouter>
    </ProgressProvider>
  );
}

describe('Visualizers Registry & Dedicated Components (D1/D10)', () => {
  it('has exactly 12 defined visualizers in curriculum', () => {
    expect(VISUALIZERS.length).toBe(12);
  });

  const visualizerWorkbenchTestIds: Record<string, string> = {
    array: 'array-workbench',
    'linked-list': 'linkedlist-workbench',
    stack: 'stack-workbench',
    queue: 'queue-workbench',
    'binary-tree': 'tree-svg',
    bst: 'tree-svg',
    heap: 'tree-svg',
    hashmap: 'hashmap-workbench',
    searching: 'searching-workbench',
    'recursion-tree': 'recursion-workbench',
    graph: 'graph-svg',
  };

  for (const [id, testId] of Object.entries(visualizerWorkbenchTestIds)) {
    it(`renders dedicated workbench for "${id}" with testId "${testId}"`, () => {
      const { unmount } = renderVisualizer(id);
      expect(screen.getByTestId(testId)).toBeInTheDocument();
      // Ensure it does not render generic fallback LinearVisualizer or NotFound
      expect(screen.queryByTestId('not-found-page')).not.toBeInTheDocument();
      unmount();
    });
  }

  it('renders sorting visualizer with comparison counters', () => {
    const { unmount } = renderVisualizer('sorting');
    expect(screen.getByRole('heading', { name: /Sorting Algorithms/i })).toBeInTheDocument();
    expect(screen.getByText(/Comparisons/i)).toBeInTheDocument();
    unmount();
  });
});
