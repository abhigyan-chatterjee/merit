import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ControlBar } from '../src/components/ControlBar';
import { TreeVisualizer } from '../src/visualizers/TreeVisualizer';

describe('ControlBar step controls (regression: Step/Back must work)', () => {
  it('calls onStepForward and onStepBack when clicked', () => {
    const fwd = vi.fn();
    const back = vi.fn();
    render(
      <ControlBar
        isPlaying={false}
        onPlayPause={() => {}}
        onStepForward={fwd}
        onStepBack={back}
        onReset={() => {}}
        onRandomize={() => {}}
        speed={1}
        onSpeedChange={() => {}}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /step forward/i }));
    expect(fwd).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: /step back/i }));
    expect(back).toHaveBeenCalledTimes(1);
  });

  it('still supports the legacy onStep prop (graph/sorting)', () => {
    const step = vi.fn();
    render(
      <ControlBar
        isPlaying={false}
        onPlayPause={() => {}}
        onStep={step}
        onReset={() => {}}
        onRandomize={() => {}}
        speed={1}
        onSpeedChange={() => {}}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /step forward/i }));
    expect(step).toHaveBeenCalledTimes(1);
  });

  it('disables stepping while playing', () => {
    const fwd = vi.fn();
    render(
      <ControlBar
        isPlaying
        onPlayPause={() => {}}
        onStepForward={fwd}
        onReset={() => {}}
        onRandomize={() => {}}
        speed={1}
        onSpeedChange={() => {}}
      />
    );

    expect(screen.getByRole('button', { name: /step forward/i })).toBeDisabled();
  });

  it('advances binary-tree traversal frames via the Step button', () => {
    const { container } = render(<TreeVisualizer variant="binary-tree" />);
    const before = container.textContent ?? '';
    expect(before).toMatch(/Starting inorder/);

    fireEvent.click(screen.getByRole('button', { name: /step forward/i }));
    fireEvent.click(screen.getByRole('button', { name: /step forward/i }));

    expect(container.textContent).not.toBe(before);
    expect(container.textContent).toMatch(/Visited node/);
  });

  it('exposes the exact e2e smoke label contract (Step forward / Step back)', () => {
    render(
      <ControlBar
        isPlaying={false}
        onPlayPause={() => {}}
        onStepForward={vi.fn()}
        onStepBack={vi.fn()}
        onReset={() => {}}
        onRandomize={() => {}}
        speed={1}
        onSpeedChange={() => {}}
      />
    );
    // The e2e smoke spec queries getByLabel('Step forward'). Keep the
    // accessible name an exact, stable contract rather than relying on
    // fragile substring matching against "Step forward one frame".
    expect(screen.getByRole('button', { name: /^Step forward$/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Step back$/ })).toBeInTheDocument();
  });
});
