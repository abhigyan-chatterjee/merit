import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { GraphVisualizer } from '../src/visualizers/GraphVisualizer';

const VIEWBOX_WIDTH = 420;
const VIEWBOX_HEIGHT = 350;

function mockBounds(left: number, top: number, width: number, height: number) {
  vi.spyOn(Element.prototype, 'getBoundingClientRect').mockReturnValue({
    left,
    top,
    right: left + width,
    bottom: top + height,
    width,
    height,
    x: left,
    y: top,
    toJSON: () => {},
  } as DOMRect);
}

function clickAtViewBoxPoint(left: number, top: number, width: number, height: number, x: number, y: number) {
  const scale = Math.min(width / VIEWBOX_WIDTH, height / VIEWBOX_HEIGHT);
  const offsetX = (width - VIEWBOX_WIDTH * scale) / 2;
  const offsetY = (height - VIEWBOX_HEIGHT * scale) / 2;
  const svg = screen.getByTestId('graph-svg');
  fireEvent.click(svg, {
    clientX: left + offsetX + x * scale,
    clientY: top + offsetY + y * scale,
  });
  return svg;
}

describe('Graph Visualizer Coordinates', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('maps client coordinates inside the letterboxed viewBox (1000x800)', () => {
    render(<GraphVisualizer />);
    mockBounds(100, 50, 1000, 800);

    const svg = clickAtViewBoxPoint(100, 50, 1000, 800, 385, 294);

    const circles = svg.querySelectorAll('circle');
    expect(circles.length).toBe(7);

    const lastCircle = circles[circles.length - 1];
    expect(Number(lastCircle.getAttribute('cx'))).toBeCloseTo(385, 0);
    expect(Number(lastCircle.getAttribute('cy'))).toBeCloseTo(294, 0);
  });

  it('accounts for horizontal letterboxing on a wide aspect ratio (800x320)', () => {
    render(<GraphVisualizer />);
    mockBounds(100, 50, 800, 320);

    const svg = clickAtViewBoxPoint(100, 50, 800, 320, 300, 160);

    const circles = svg.querySelectorAll('circle');
    expect(circles.length).toBe(7);

    const lastCircle = circles[circles.length - 1];
    expect(Number(lastCircle.getAttribute('cx'))).toBeCloseTo(300, 0);
    expect(Number(lastCircle.getAttribute('cy'))).toBeCloseTo(160, 0);
  });
});
