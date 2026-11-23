import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DpTableVisualizer } from '../src/visualizers/DpTableVisualizer';
import { SlidingWindowVisualizer } from '../src/visualizers/SlidingWindowVisualizer';
import { ShortestPathVisualizer } from '../src/visualizers/ShortestPathVisualizer';

function step(times = 1) {
  for (let i = 0; i < times; i++) {
    fireEvent.click(screen.getByRole('button', { name: /^Step forward$/ }));
  }
}

describe('Milestone C Track 6 Part A visualizers', () => {
  it('renders all three workbenches', () => {
    const { unmount } = render(<DpTableVisualizer />);
    expect(screen.getByTestId('dp-table-workbench')).toBeInTheDocument();
    unmount();
    const { unmount: u2 } = render(<SlidingWindowVisualizer />);
    expect(screen.getByTestId('sliding-window-workbench')).toBeInTheDocument();
    u2();
    render(<ShortestPathVisualizer />);
    expect(screen.getByTestId('shortest-path-workbench')).toBeInTheDocument();
  });

  it('DpTableVisualizer switches LCS / Knapsack / Edit presets and steps', () => {
    const { container } = render(<DpTableVisualizer />);
    expect(container.textContent).toMatch(/ABCBDA/);
    step(2);
    const afterStep = container.textContent ?? '';

    fireEvent.click(screen.getByRole('button', { name: '0/1 Knapsack' }));
    expect(container.textContent).toMatch(/Max value|Capacity/);
    step(3);
    expect(container.textContent).not.toBe(afterStep);

    fireEvent.click(screen.getByRole('button', { name: 'Edit Distance' }));
    expect(container.textContent).toMatch(/HORSE/);
    step(3);

    fireEvent.click(screen.getByRole('button', { name: 'LCS' }));
    for (let i = 0; i < 60; i++) {
      fireEvent.click(screen.getByRole('button', { name: /^Step forward$/ }));
    }
    expect(container.textContent).toMatch(/LCS =/);
  });

  it('SlidingWindowVisualizer switches Longest / Fixed / Two Pointers and steps', () => {
    const { container } = render(<SlidingWindowVisualizer />);
    expect(container.textContent).toMatch(/abcabcbb/);
    step(2);

    fireEvent.click(screen.getByRole('button', { name: 'Fixed Window' }));
    expect(container.textContent).toMatch(/Window Sum|k \(2\.\.5\)/);
    step(2);

    fireEvent.click(screen.getByRole('button', { name: 'Two Pointers' }));
    expect(container.textContent).toMatch(/Target/);
    step(2);
    expect(container.textContent).toMatch(/arr\[0\]/);

    fireEvent.click(screen.getByRole('button', { name: 'Longest Substring' }));
    for (let i = 0; i < 20; i++) {
      fireEvent.click(screen.getByRole('button', { name: /^Step forward$/ }));
    }
    expect(container.textContent).toMatch(/Done\. Longest/);
  });

  it('ShortestPathVisualizer switches Dijkstra / Bellman-Ford and graph presets', () => {
    const { container } = render(<ShortestPathVisualizer />);
    expect(screen.getByTestId('shortest-path-svg')).toBeInTheDocument();
    step(3);
    expect(container.textContent).toMatch(/Settle vertex|Relax/);

    fireEvent.click(screen.getByRole('button', { name: 'Negative-Weight Network' }));
    expect(screen.getByText(/Dijkstra requires non-negative edge weights/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Bellman-Ford' }));
    expect(screen.queryByText(/Dijkstra requires non-negative edge weights/)).toBeNull();
    step(5);
    expect(container.textContent).toMatch(/Pass 1/);

    fireEvent.click(screen.getByRole('button', { name: 'Dijkstra' }));
    fireEvent.click(screen.getByRole('button', { name: 'Standard Network' }));
    step(2);
    expect(container.textContent).toMatch(/Dijkstra/);
  });
});
