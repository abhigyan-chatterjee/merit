import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProblemListPage } from '../src/pages/ProblemListPage';
import { ProgressProvider } from '../src/store/ProgressContext';
import { PROBLEMS } from '../src/data/problems';

const STORAGE_KEY = 'merit_store_v1';

function renderList(topic = 'arrays-hashing') {
  return render(
    <ProgressProvider>
      <MemoryRouter initialEntries={[`/problems/${topic}`]}>
        <Routes>
          <Route path="/problems/:topic" element={<ProblemListPage />} />
        </Routes>
      </MemoryRouter>
    </ProgressProvider>,
  );
}

/** The topic accordion carries aria-expanded; tag chips carry aria-pressed. */
function topicToggle(container: HTMLElement, label: string): HTMLButtonElement {
  const found = Array.from(
    container.querySelectorAll<HTMLButtonElement>('button[aria-expanded]'),
  ).find((btn) => btn.textContent?.includes(label));
  if (!found) throw new Error(`no topic accordion for ${label}`);
  return found;
}

function stored(): Record<string, unknown> {
  return JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? '{}');
}

describe('ProblemListPage', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('renders the catalog header with the full problem count', () => {
    renderList();
    expect(screen.getByRole('heading', { name: /Master the patterns/i })).toBeInTheDocument();
    expect(screen.getByText(`0/${PROBLEMS.length}`)).toBeInTheDocument();
  });

  it('expands the routed topic so its problems are listed', () => {
    const { container } = renderList('arrays-hashing');
    // The topic accordion for the route is open by default.
    expect(topicToggle(container, 'Arrays & Hashing')).toHaveAttribute(
      'aria-expanded',
      'true',
    );
    expect(screen.getByRole('link', { name: 'Two Sum', exact: true })).toBeInTheDocument();
  });

  it('filters by search query', () => {
    renderList('arrays-hashing');
    expect(screen.getByText(new RegExp(`Showing ${PROBLEMS.length} of ${PROBLEMS.length}`))).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Search problems'), {
      target: { value: 'two sum' },
    });

    // Fewer than the full set remain, and the match is still listed.
    expect(
      screen.queryByText(new RegExp(`Showing ${PROBLEMS.length} of ${PROBLEMS.length}`)),
    ).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Two Sum', exact: true })).toBeInTheDocument();
  });

  it('collapses a topic on click', () => {
    const { container } = renderList('arrays-hashing');
    const toggle = topicToggle(container, 'Arrays & Hashing');
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    expect(
      screen.queryByRole('link', { name: 'Two Sum', exact: true }),
    ).not.toBeInTheDocument();
  });

  it('toggles a bookmark from the list and persists it', () => {
    renderList('arrays-hashing');
    fireEvent.click(screen.getByRole('button', { name: 'Add bookmark for Two Sum', exact: true }));
    expect(stored().bookmarks).toContain('two-sum');
    expect(
      screen.getByRole('button', { name: 'Remove bookmark for Two Sum', exact: true }),
    ).toHaveAttribute('aria-pressed', 'true');
  });

  it('reflects solved progress from storage', () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ progress: { 'two-sum': 'Done' } }),
    );
    renderList('arrays-hashing');
    expect(screen.getByText(`1/${PROBLEMS.length}`)).toBeInTheDocument();
    expect(screen.getByLabelText('Solved')).toBeInTheDocument();
  });
});
