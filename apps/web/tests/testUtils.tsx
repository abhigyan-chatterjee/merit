import React from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../src/store/AuthContext';
import { ProgressProvider } from '../src/store/ProgressContext';

export function renderHookForTest<T>(hook: () => T): { result: { current: T } } {
  const result: { current: T } = { current: undefined as unknown as T };
  const Probe: React.FC = () => {
    result.current = hook();
    return null;
  };
  render(
    <AuthProvider>
      <ProgressProvider>
        <MemoryRouter>
          <Probe />
        </MemoryRouter>
      </ProgressProvider>
    </AuthProvider>
  );
  return { result };
}
