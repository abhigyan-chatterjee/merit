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

  it('shows Suggested label when query is empty', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));
    expect(screen.getByText('Suggested')).toBeInTheDocument();
  });

  it('shows results count when typed', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));
    const input = screen.getByPlaceholderText(/search structures/i);
    fireEvent.change(input, { target: { value: 'heap' } });
    expect(screen.getByText(/result/i)).toBeInTheDocument();
  });

  it('ArrowDown moves active row', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));
    const input = screen.getByPlaceholderText(/search structures/i);
    fireEvent.change(input, { target: { value: 'heap' } });

    const options = screen.getAllByRole('option');
    expect(options.length).toBeGreaterThan(1);
    expect(options[0]).toHaveAttribute('aria-selected', 'true');
    expect(input).toHaveAttribute('aria-activedescendant', options[0].id);

    fireEvent.keyDown(input, { key: 'ArrowDown', code: 'ArrowDown' });

    expect(options[0]).toHaveAttribute('aria-selected', 'false');
    expect(options[1]).toHaveAttribute('aria-selected', 'true');
    expect(input).toHaveAttribute('aria-activedescendant', options[1].id);
  });

  it('match-quality: exact title match ranks above blurb match', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));
    const input = screen.getByPlaceholderText(/search structures/i);
    // 'heap' matches the visualizer title and problems only via their pattern.
    fireEvent.change(input, { target: { value: 'heap' } });
    const options = screen.getAllByRole('option');
    expect(options[0]).toHaveTextContent('Min / Max Binary Heap');
    expect(options[0]).toHaveTextContent('Visualizer');
    expect(options.findIndex((o) => o.textContent?.includes('Problem'))).toBeGreaterThan(0);

    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    expect(mockNavigate).toHaveBeenCalledWith('/visualizers/heap');
  });

  it('finds and navigates to targeted exam when searching', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));
    const input = screen.getByPlaceholderText(/search structures/i);
    fireEvent.change(input, { target: { value: 'TCS NQT' } });

    const examOption = screen.getByRole('option', { name: /TCS NQT & Digital Mock/i });
    expect(examOption).toBeInTheDocument();
    expect(screen.getByText('Exam')).toBeInTheDocument();

    fireEvent.click(examOption);
    expect(mockNavigate).toHaveBeenCalledWith('/exams/tcs-nqt');
  });

  it('finds and navigates to quiz topic when searching', () => {
    renderNavbar();
    fireEvent.click(screen.getByRole('button', { name: /open global search/i }));
    const input = screen.getByPlaceholderText(/search structures/i);
    fireEvent.change(input, { target: { value: 'SQL' } });

    expect(screen.getByText(/SQL & Databases/i)).toBeInTheDocument();
    expect(screen.getByText('Quiz')).toBeInTheDocument();

    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    expect(mockNavigate).toHaveBeenCalledWith('/quiz/sql');
  });
});
