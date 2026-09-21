import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Navbar } from '../src/components/Navbar';
import { ProgressProvider } from '../src/store/ProgressContext';

const mockNavigate = vi.hoisted(() => vi.fn());
vi.mock('react-router-dom', async (importOriginal) => ({
  ...(await importOriginal()),
  useNavigate: () => mockNavigate,
}));

function renderNavbar() {
  return render(
    <ProgressProvider>
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    </ProgressProvider>
  );
}

describe('Navbar search Enter-to-jump (D-search)', () => {
  beforeEach(() => {
    window.localStorage.clear();
    mockNavigate.mockReset();
  });

  it('pressing Enter opens the first matching result (paths take priority)', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));

    const input = screen.getByPlaceholderText(/search structures/i);
    fireEvent.change(input, { target: { value: 'foundation' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    expect(mockNavigate).toHaveBeenCalledWith('/learn/foundation');
  });

  it('pressing Enter with no results does not navigate', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));

    const input = screen.getByPlaceholderText(/search structures/i);
    fireEvent.change(input, { target: { value: 'zzz-no-such-term-xyz' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
