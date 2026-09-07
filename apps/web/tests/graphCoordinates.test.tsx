import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { GraphVisualizer } from '../src/visualizers/GraphVisualizer';

describe('Graph Visualizer Coordinates (D3)', () => {
  it('correctly maps client coordinates to viewBox units (0..420, 0..350)', () => {
    const { container } = render(<GraphVisualizer />);
    const svg = screen.getByTestId('graph-svg');
    expect(svg).toBeInTheDocument();

    vi.spyOn(Element.prototype, 'getBoundingClientRect').mockReturnValue({
      left: 100,
      top: 50,
      right: 1100,
      bottom: 850,
      width: 1000,
      height: 800,
      x: 100,
      y: 50,
      toJSON: () => {},
    } as DOMRect);

    // Click at 90% width (100 + 900 = 1000) and 84% height (50 + 672 = 722)
    // 90% of 420 = 378, 84% of 350 = 294
    fireEvent.click(svg!, {
      clientX: 1000,
      clientY: 722,
    });

    // Verify a circle was added with viewBox coordinates within [0, 420] and [0, 350]
    const circles = container.querySelectorAll('circle');
    // Default nodes: 5 nodes. We expect 6 nodes now.
    expect(circles.length).toBeGreaterThanOrEqual(6);

    const lastCircle = circles[circles.length - 1];
    const cx = Number(lastCircle.getAttribute('cx'));
    const cy = Number(lastCircle.getAttribute('cy'));

    expect(cx).toBeGreaterThanOrEqual(0);
    expect(cx).toBeLessThanOrEqual(420);
    expect(cy).toBeGreaterThanOrEqual(0);
    expect(cy).toBeLessThanOrEqual(350);

    // Specifically around 378 and 294
    expect(cx).toBeCloseTo(378, -1);
    expect(cy).toBeCloseTo(294, -1);
  });
});
