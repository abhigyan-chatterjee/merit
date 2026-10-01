import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ErrorBoundary } from '../src/components/ErrorBoundary';

function Boom(): React.ReactElement {
  throw new Error('forced finish-pass crash');
}

describe('ErrorBoundary', () => {
  it('shows recovery UI and keeps the document usable when a child throws', () => {
    // Suppress the expected React error logging for this deliberate throw.
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>
    );

    // Recovery copy is present.
    expect(screen.getByText(/failed to render/i)).toBeInTheDocument();
    expect(screen.getByText(/still loaded/i)).toBeInTheDocument();
    // A reference the user can quote in a bug report.
    expect(screen.getByText(/^ref /)).toBeInTheDocument();
    // Two ways out, not a dead end.
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reload/i })).toBeInTheDocument();

    spy.mockRestore();
  });

  it('renders children untouched when nothing throws', () => {
    render(
      <ErrorBoundary>
        <p>all good</p>
      </ErrorBoundary>
    );
    expect(screen.getByText('all good')).toBeInTheDocument();
    expect(screen.queryByText(/failed to render/i)).not.toBeInTheDocument();
  });
});
