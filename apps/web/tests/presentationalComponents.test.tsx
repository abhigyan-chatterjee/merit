import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ComplexityBadge } from '../src/components/ComplexityBadge';
import { EmptyState } from '../src/components/EmptyState';
import { ProgressRing } from '../src/components/ProgressRing';
import { SpeedControl } from '../src/components/SpeedControl';

describe('ComplexityBadge', () => {
  it('renders the label and value', () => {
    render(<ComplexityBadge label="avg" value="O(n log n)" />);
    expect(screen.getByText('avg')).toBeInTheDocument();
    expect(screen.getByText('O(n log n)')).toBeInTheDocument();
  });

  it('applies the variant tone', () => {
    render(<ComplexityBadge label="space" value="O(1)" variant="violet" />);
    expect(screen.getByText('O(1)')).toHaveClass('text-violet');
  });
});

describe('EmptyState', () => {
  it('renders title and description without an action', () => {
    render(<EmptyState title="Nothing here" description="Add something to get started." />);
    expect(screen.getByText('Nothing here')).toBeInTheDocument();
    expect(screen.getByText('Add something to get started.')).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('invokes the action when provided', () => {
    const onAction = vi.fn();
    render(
      <EmptyState
        title="Nothing here"
        description="Add something."
        actionLabel="Create"
        onAction={onAction}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Create' }));
    expect(onAction).toHaveBeenCalledTimes(1);
  });
});

describe('ProgressRing', () => {
  it('reports 0 percent for an empty tally', () => {
    render(<ProgressRing completed={0} total={10} />);
    expect(screen.getByRole('img', { name: /0 percent complete, 0 of 10/i })).toBeInTheDocument();
  });

  it('computes the rounded percentage', () => {
    render(<ProgressRing completed={5} total={10} />);
    expect(screen.getByRole('img', { name: /50 percent complete, 5 of 10/i })).toBeInTheDocument();
  });

  it('clamps at 100 percent', () => {
    render(<ProgressRing completed={20} total={10} />);
    expect(screen.getByRole('img', { name: /100 percent complete, 20 of 10/i })).toBeInTheDocument();
  });

  it('treats a zero total as 0 percent instead of dividing by zero', () => {
    render(<ProgressRing completed={0} total={0} />);
    expect(screen.getByRole('img', { name: /0 percent complete, 0 of 0/i })).toBeInTheDocument();
  });
});

describe('SpeedControl', () => {
  it('reflects the current speed', () => {
    render(<SpeedControl speed={1} onChange={vi.fn()} />);
    const slider = screen.getByLabelText('Animation speed multiplier');
    expect(slider).toHaveValue('1');
    expect(slider).toHaveAttribute('aria-valuetext', '1 times');
  });

  it('reports slider changes as numbers', () => {
    const onChange = vi.fn();
    render(<SpeedControl speed={1} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText('Animation speed multiplier'), {
      target: { value: '1.5' },
    });
    expect(onChange).toHaveBeenCalledWith(1.5);
  });

  it('sets the speed from a preset', () => {
    const onChange = vi.fn();
    render(<SpeedControl speed={1} onChange={onChange} />);
    fireEvent.click(screen.getByRole('button', { name: 'Set speed to 2x' }));
    expect(onChange).toHaveBeenCalledWith(2);
  });
});
