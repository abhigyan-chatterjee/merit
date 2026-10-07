import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ProblemTable } from '../src/components/ProblemTable';
import { ProgressProvider } from '../src/store/ProgressContext';
import { PROBLEMS } from '../src/data/problems';

const SAMPLE = PROBLEMS.slice(0, 5);
const STORAGE_KEY = 'merit_store_v1';

function renderTable() {
  const utils = render(
    <ProgressProvider>
      <MemoryRouter>
        <ProblemTable problems={SAMPLE} />
      </MemoryRouter>
    </ProgressProvider>,
  );
  // The component renders a desktop table AND a mobile card list with the
  // same accessible labels; scope row queries to the table.
  const table = utils.container.querySelector('table');
  if (!table) throw new Error('desktop table not rendered');
  return { ...utils, table };
}

function stored(): Record<string, unknown> {
  return JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? '{}');
}

describe('ProblemTable', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('lists the problems with a shown/total counter', () => {
    renderTable();
    expect(screen.getByText(`${SAMPLE.length}/${SAMPLE.length} shown`)).toBeInTheDocument();
    for (const p of SAMPLE) {
      expect(screen.getAllByText(p.title).length).toBeGreaterThan(0);
    }
  });

  it('filters by search query and can clear it', () => {
    renderTable();
    const search = screen.getByLabelText('Filter problems');
    fireEvent.change(search, { target: { value: SAMPLE[0].title } });
    expect(screen.getByText(`1/${SAMPLE.length} shown`)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Clear search' }));
    expect(screen.getByText(`${SAMPLE.length}/${SAMPLE.length} shown`)).toBeInTheDocument();
  });

  it('filters by difficulty', () => {
    renderTable();
    const target = SAMPLE[0].difficulty;
    const expected = SAMPLE.filter((p) => p.difficulty === target).length;

    fireEvent.change(screen.getByLabelText('Filter by difficulty'), { target: { value: target } });
    expect(screen.getByText(`${expected}/${SAMPLE.length} shown`)).toBeInTheDocument();
  });

  it('filters by status from stored progress', () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ progress: { [SAMPLE[0].slug]: 'Done' } }),
    );
    renderTable();
    fireEvent.change(screen.getByLabelText('Filter by status'), { target: { value: 'Done' } });
    expect(screen.getByText(`1/${SAMPLE.length} shown`)).toBeInTheDocument();
  });

  it('cycles the sort control', () => {
    renderTable();
    const sort = screen.getByRole('button', { name: /Sort/i });
    expect(sort).toHaveTextContent('Sort');
    fireEvent.click(sort);
    expect(screen.getByRole('button', { name: /difficulty/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /difficulty/i }));
    expect(screen.getByRole('button', { name: /title/i })).toBeInTheDocument();
  });

  it('shows an empty state that can reset every filter', () => {
    renderTable();
    fireEvent.change(screen.getByLabelText('Filter problems'), {
      target: { value: 'no-such-problem-xyz' },
    });
    expect(screen.getByText(/No problems match those filters/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Clear all filters/i }));
    expect(screen.getByText(`${SAMPLE.length}/${SAMPLE.length} shown`)).toBeInTheDocument();
  });

  it('persists a status change from a row', () => {
    const { table } = renderTable();
    fireEvent.change(within(table).getByLabelText(`Status for ${SAMPLE[0].title}`), {
      target: { value: 'Done' },
    });
    expect((stored().progress as Record<string, string>)[SAMPLE[0].slug]).toBe('Done');
  });
});
