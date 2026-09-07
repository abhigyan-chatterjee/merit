import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppRoutes } from '../src/routes';
import { ProgressProvider } from '../src/store/ProgressContext';

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
  it('renders NotFound for unknown visualizer id', () => {
    renderWithRouter('/visualizers/non-existent-visualizer-xyz');
    expect(screen.getByTestId('not-found-page')).toBeInTheDocument();
    expect(screen.getByText(/Visualizer Not Found/i)).toBeInTheDocument();
  });

  it('renders NotFound for mismatching problem slug and topic', () => {
    // two-sum belongs to 'arrays', not 'graphs'
    renderWithRouter('/problems/graphs/two-sum');
    expect(screen.getByTestId('not-found-page')).toBeInTheDocument();
    expect(screen.getByText(/Problem Not Found/i)).toBeInTheDocument();
  });

  it('renders NotFound for unknown problem slug', () => {
    renderWithRouter('/problems/arrays/not-a-real-problem');
    expect(screen.getByTestId('not-found-page')).toBeInTheDocument();
    expect(screen.getByText(/Problem Not Found/i)).toBeInTheDocument();
  });

  it('renders NotFound for unknown quiz topic', () => {
    renderWithRouter('/quiz/unknown-quantum-computing-topic');
    expect(screen.getByTestId('not-found-page')).toBeInTheDocument();
    expect(screen.getByText(/Quiz Not Found/i)).toBeInTheDocument();
  });

  it('renders NotFound for unknown guided path id', () => {
    renderWithRouter('/learn/unknown-alien-path');
    expect(screen.getByTestId('not-found-page')).toBeInTheDocument();
    expect(screen.getByText(/Learning Path Not Found/i)).toBeInTheDocument();
  });

  it('renders NotFound for random unmatched route', () => {
    renderWithRouter('/some/completely/random/route');
    expect(screen.getByTestId('not-found-page')).toBeInTheDocument();
  });

  it('renders real problem when topic and slug match', () => {
    renderWithRouter('/problems/arrays/two-sum');
    expect(screen.queryByTestId('not-found-page')).not.toBeInTheDocument();
    expect(screen.getByText('Two Sum')).toBeInTheDocument();
  });
});
