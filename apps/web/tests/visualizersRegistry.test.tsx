import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
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
  it('has exactly 17 defined visualizers in curriculum', () => {
    expect(VISUALIZERS.length).toBe(17);
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
    'dp-table': 'dp-table-workbench',
    'sliding-window': 'sliding-window-workbench',
    'shortest-path': 'shortest-path-workbench',
    'union-find': 'union-find-workbench',
    trie: 'trie-workbench',
  };

  for (const [id, testId] of Object.entries(visualizerWorkbenchTestIds)) {
    it(`renders dedicated workbench for "${id}" with testId "${testId}"`, () => {
      const { unmount } = renderVisualizer(id);
      expect(screen.getByTestId(testId)).toBeInTheDocument();
      // Ensure a dedicated workbench renders instead of the NotFound fallback
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

  it('union-find: union merges sets and cycle preset reports a redundant edge', () => {
    const { unmount } = renderVisualizer('union-find');
    expect(screen.getByTestId('union-find-workbench')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Union(u, v)'));
    expect(screen.getByText(/merged/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText('Find(x) & Compress'));
    expect(screen.getByTestId('union-find-workbench')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Cycle Detection Demo'));
    expect(screen.getAllByText(/Cycle detected/i).length).toBeGreaterThanOrEqual(1);
    unmount();
  });

  it('trie: inserting then searching a word reports terminal membership', () => {
    const { unmount } = renderVisualizer('trie');
    expect(screen.getByTestId('trie-workbench')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/word/i), { target: { value: 'care' } });
    fireEvent.click(screen.getByText('Insert Word'));
    expect(screen.getAllByText(/Inserted "care"/i).length).toBeGreaterThanOrEqual(1);
    fireEvent.click(screen.getByText('Search Word'));
    expect(screen.getByText(/Found "care"/i)).toBeInTheDocument();
    unmount();
  });

  it('trie: prefix autocomplete lists matching words', () => {
    const { unmount } = renderVisualizer('trie');
    fireEvent.change(screen.getByLabelText(/word/i), { target: { value: 'ca' } });
    fireEvent.click(screen.getByText('StartsWith Prefix'));
    expect(screen.getAllByText(/3 match\(es\)/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByTestId('trie-matches')).toBeInTheDocument();
    unmount();
  });
});
