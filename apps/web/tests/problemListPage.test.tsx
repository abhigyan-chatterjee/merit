import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
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

function renderListAt(entry: string, routePath: string) {
  return render(
    <ProgressProvider>
      <MemoryRouter initialEntries={[entry]}>
        <Routes>
          <Route path={routePath} element={<ProblemListPage />} />
        </Routes>
      </MemoryRouter>
    </ProgressProvider>,
  );
}

/** The pill row next to a filter label (Tags / Companies / Difficulty / Status). */
function filterRow(label: RegExp): HTMLElement {
  return screen.getByText(label).parentElement as HTMLElement;
}

function pill(row: HTMLElement, name: string | RegExp): HTMLButtonElement {
  return within(row).getByRole('button', { name }) as HTMLButtonElement;
}

describe('ProblemListPage', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('renders the catalog header with the full problem count', () => {
    renderList();
    expect(screen.getByRole('heading', { name: /^Problems$/i })).toBeInTheDocument();
    expect(screen.getByText(`${PROBLEMS.length} problems · 0 done · 0 starred`)).toBeInTheDocument();
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
    expect(screen.getByText(new RegExp(`${PROBLEMS.length} / ${PROBLEMS.length}`))).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Search problems'), {
      target: { value: 'two sum' },
    });

    // Fewer than the full set remain, and the match is still listed.
    expect(
      screen.queryByText(new RegExp(`${PROBLEMS.length} / ${PROBLEMS.length}`)),
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

  it('filters by company pill and shows Clear filters', () => {
    renderList('arrays-hashing');
    const row = filterRow(/^Companies$/);
    fireEvent.click(pill(row, /TCS/));
    expect(pill(row, /TCS/)).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('link', { name: 'Two Sum', exact: true })).toBeInTheDocument();
    // Baseball Scorebook (stack) is not asked by TCS, so it drops out.
    expect(
      screen.queryByRole('link', { name: 'Baseball Scorebook', exact: true }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Clear filters' })).toBeInTheDocument();
  });

  it('allows collapsing a topic accordion while a company filter is active', () => {
    const { container } = renderList('arrays-hashing');
    fireEvent.click(pill(filterRow(/^Companies$/), /TCS/));
    const toggle = topicToggle(container, 'Arrays & Hashing');
    expect(toggle).toHaveAttribute('aria-expanded', 'true');

    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    expect(
      screen.queryByRole('link', { name: 'Two Sum', exact: true }),
    ).not.toBeInTheDocument();

    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
  });

  it('pre-filters from ?company= on mount', () => {
    renderListAt('/problems?company=TCS', '/problems');
    expect(pill(filterRow(/^Companies$/), /TCS/)).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('link', { name: 'Two Sum', exact: true })).toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: 'Baseball Scorebook', exact: true }),
    ).not.toBeInTheDocument();
  });

  it('filters by difficulty', () => {
    renderList('arrays-hashing');
    fireEvent.click(pill(filterRow(/^Difficulty$/), 'Easy'));
    expect(pill(filterRow(/^Difficulty$/), 'Easy')).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('link', { name: 'Two Sum', exact: true })).toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: 'First Missing Positive', exact: true }),
    ).not.toBeInTheDocument();
  });

  it('filters by Done status', () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ progress: { 'two-sum': 'Done' } }),
    );
    renderList('arrays-hashing');
    fireEvent.click(pill(filterRow(/^Status$/), 'Done'));
    expect(screen.getByRole('link', { name: 'Two Sum', exact: true })).toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: 'Contains Duplicate', exact: true }),
    ).not.toBeInTheDocument();
  });

  it('filters by Starred status', () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ bookmarks: ['two-sum'] }));
    renderList('arrays-hashing');
    fireEvent.click(pill(filterRow(/^Status$/), 'Starred'));
    expect(screen.getByRole('link', { name: 'Two Sum', exact: true })).toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: 'Contains Duplicate', exact: true }),
    ).not.toBeInTheDocument();
  });

  it('matches search against company names', () => {
    renderList('arrays-hashing');
    // 'Turing' appears only in Baseball Scorebook's company list, not in its
    // title or pattern.
    fireEvent.change(screen.getByLabelText('Search problems'), {
      target: { value: 'Turing' },
    });
    expect(screen.getByRole('link', { name: 'Baseball Scorebook', exact: true })).toBeInTheDocument();
  });

  it('clears company, search and other filters together', () => {
    renderList('arrays-hashing');
    fireEvent.click(pill(filterRow(/^Companies$/), /TCS/));
    fireEvent.change(screen.getByLabelText('Search problems'), {
      target: { value: 'two sum' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Clear filters' }));

    expect(screen.getByLabelText('Search problems')).toHaveValue('');
    expect(pill(filterRow(/^Companies$/), /TCS/)).toHaveAttribute('aria-pressed', 'false');
    expect(screen.queryByRole('button', { name: 'Clear filters' })).not.toBeInTheDocument();
    expect(screen.getByText(new RegExp(`${PROBLEMS.length} / ${PROBLEMS.length}`))).toBeInTheDocument();
  });

  it('reflects solved progress from storage', () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ progress: { 'two-sum': 'Done' } }),
    );
    renderList('arrays-hashing');
    expect(screen.getByText(`${PROBLEMS.length} problems · 1 done · 0 starred`)).toBeInTheDocument();
    expect(screen.getByLabelText('Solved')).toBeInTheDocument();
  });
});
