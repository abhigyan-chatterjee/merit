import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Footer } from '../src/components/Footer';
import { PseudoCodePanel } from '../src/components/PseudoCodePanel';
import { VisualizerCanvas } from '../src/components/VisualizerCanvas';

describe('Footer', () => {
  it('renders the link columns', () => {
    render(
      <MemoryRouter>
        <Footer />
      </MemoryRouter>,
    );
    for (const column of ['Visualize', 'Learn', 'Assess', 'Legal']) {
      expect(screen.getByRole('heading', { name: column })).toBeInTheDocument();
    }
    expect(screen.getByRole('link', { name: 'Guided paths' })).toHaveAttribute('href', '/learn');
    expect(screen.getByRole('link', { name: 'Privacy policy' })).toHaveAttribute(
      'href',
      '/privacy',
    );
  });

  it('opens the feedback dialog from the bug report button', () => {
    render(
      <MemoryRouter>
        <Footer />
      </MemoryRouter>,
    );
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Report Bug \/ Feedback/i }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });
});

describe('PseudoCodePanel', () => {
  it('numbers the pseudocode lines and defaults the title', () => {
    render(<PseudoCodePanel lines={['if (a < b)', '  swap(a, b)']} />);
    expect(screen.getByText('Algorithm Logic')).toBeInTheDocument();
    expect(screen.getByText('if (a < b)')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('shows the complexity badges', () => {
    render(<PseudoCodePanel timeComplexity="O(n log n)" spaceComplexity="O(1)" />);
    expect(screen.getByText('O(n log n)')).toBeInTheDocument();
    expect(screen.getByText('O(1)')).toBeInTheDocument();
  });

  it('prompts for input when the log is empty', () => {
    render(<PseudoCodePanel lines={['x']} logs={[]} />);
    expect(screen.getByText(/to trace execution/i)).toBeInTheDocument();
    expect(screen.getByText('0 ops')).toBeInTheDocument();
  });

  it('lists operation log entries and their count', () => {
    render(<PseudoCodePanel lines={['x']} logs={['push(5)', 'pop()']} />);
    expect(screen.getByText('push(5)')).toBeInTheDocument();
    expect(screen.getByText('pop()')).toBeInTheDocument();
    expect(screen.getByText('2 ops')).toBeInTheDocument();
  });
});

describe('VisualizerCanvas', () => {
  it('renders its children inside the stage', () => {
    render(
      <VisualizerCanvas>
        <span>stage-content</span>
      </VisualizerCanvas>,
    );
    expect(screen.getByText('stage-content')).toBeInTheDocument();
  });

  it('renders the metric rail when metrics are given', () => {
    render(
      <VisualizerCanvas metrics={[{ label: 'Comparisons', value: 12 }]}>
        <div />
      </VisualizerCanvas>,
    );
    expect(screen.getByText('Comparisons')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
  });

  it('renders the default legend', () => {
    render(
      <VisualizerCanvas>
        <div />
      </VisualizerCanvas>,
    );
    for (const label of ['Idle', 'Comparing', 'Writing', 'Settled']) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });
});
