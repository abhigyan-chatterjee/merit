import { beforeEach, describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ProblemListPage } from '../src/pages/ProblemListPage';
import { ProgressProvider } from '../src/store/ProgressContext';
import { PROBLEMS } from '../src/data/problems';
import { TOPICS } from '../src/data/curriculum';

const renderPage = () =>
  render(
    <ProgressProvider>
      <MemoryRouter initialEntries={['/problems/arrays-hashing']}>
        <ProblemListPage />
      </MemoryRouter>
    </ProgressProvider>
  );

const expandArrays = () => {
  const accordion = screen
    .getAllByRole('button', { name: /Arrays & Hashing/ })
    .find((button) => button.hasAttribute('aria-expanded'));
  expect(accordion).toBeDefined();
  fireEvent.click(accordion!);
};

describe('ProblemListPage', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('renders every canonical topic with its total count', () => {
    renderPage();

    TOPICS.forEach((topic) => {
      const count = PROBLEMS.filter((problem) => problem.topic === topic.slug).length;
      expect(screen.getAllByText(topic.title).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(new RegExp(`^0/${count}$`)).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('narrows an expanded topic when searching by title', () => {
    renderPage();
    expandArrays();

    fireEvent.change(screen.getByRole('searchbox', { name: 'Search problems' }), {
      target: { value: 'Two Sum' },
    });

    expect(screen.getByText('Two Sum')).toBeInTheDocument();
    expect(screen.queryByText('Contains Duplicate')).not.toBeInTheDocument();
  });

  it('updates the starred hero count when a problem is bookmarked', () => {
    renderPage();
    expandArrays();

    expect(screen.getByText('Starred')).toBeInTheDocument();
    expect(screen.getByText('0', { selector: 'div' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Add bookmark for Two Sum' }));

    expect(screen.getByText('1', { selector: 'div' })).toBeInTheDocument();
  });
});
