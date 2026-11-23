import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ReviewDeck } from '../src/components/ReviewDeck';
import { ProgressProvider, useProgress } from '../src/store/ProgressContext';
import * as apiModule from '../src/utils/api';

const item1 = {
  item_type: 'problem',
  item_id: 'two-sum',
  title: 'Two Sum',
  topic: 'arrays-hashing',
  due_date: '2026-11-23',
  interval_days: 3,
  reps: 2,
  lapses: 0,
  difficulty: 'Easy',
  prompt: 'Given nums and target, return indices.',
  answer_summary: 'Use a hash map for O(n).',
};

const item2 = {
  item_type: 'question',
  item_id: 'q-bst-1',
  title: 'BST Concept',
  topic: 'trees',
  due_date: '2026-11-23',
  interval_days: 1,
  reps: 1,
  lapses: 0,
  difficulty: 'Medium',
  prompt: 'What defines a BST?',
  answer_summary: 'Left smaller, right larger.',
};

const DueProbe: React.FC = () => {
  const { dueTodayCount } = useProgress();
  return <span data-testid="due-count">{dueTodayCount}</span>;
};

function renderDeck() {
  return render(
    <ProgressProvider>
      <MemoryRouter>
        <DueProbe />
        <ReviewDeck />
      </MemoryRouter>
    </ProgressProvider>
  );
}

describe('ReviewDeck', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  it('loads due items and syncs dueTodayCount', async () => {
    vi.spyOn(apiModule.revisionApi, 'getDue').mockResolvedValue({
      today: '2026-11-23',
      count: 2,
      items: [item1, item2] as never,
    });
    renderDeck();

    expect(await screen.findByText('Two Sum')).toBeInTheDocument();
    expect(screen.getByText(/Card 1 of 2/)).toBeInTheDocument();
    expect(screen.getByText('PROBLEM')).toBeInTheDocument();
    expect(screen.getByText('arrays-hashing')).toBeInTheDocument();
    expect(screen.getByText('Easy')).toBeInTheDocument();
    expect(screen.getByText(/reps 2/)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId('due-count')).toHaveTextContent('2'));
    const openLink = screen.getByText(/Open full item/);
    expect(openLink.closest('a')).toHaveAttribute('href', '/problems/arrays-hashing/two-sum');
  });

  it('reveals answer and rates Good to advance the deck', async () => {
    const reviewSpy = vi.spyOn(apiModule.revisionApi, 'review').mockResolvedValue({
      item_type: 'problem',
      item_id: 'two-sum',
      due_date: '2026-11-24',
      interval_days: 6,
      ease: 2.5,
      reps: 3,
      lapses: 0,
    });
    vi.spyOn(apiModule.revisionApi, 'getDue').mockResolvedValue({
      today: '2026-11-23',
      count: 2,
      items: [item1, item2] as never,
    });
    renderDeck();
    await screen.findByText('Two Sum');

    fireEvent.click(screen.getByText('Reveal Answer'));
    expect(screen.getByText(/Use a hash map/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Again/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Hard' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Good' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Easy' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Good' }));
    await waitFor(() => expect(reviewSpy).toHaveBeenCalledWith('problem', 'two-sum', 4));
    expect(await screen.findByText('BST Concept')).toBeInTheDocument();
    expect(screen.getByText(/Card 2 of 2/)).toBeInTheDocument();
    expect(screen.getByText('CONCEPT')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId('due-count')).toHaveTextContent('1'));
  });

  it('rates Again and shows caught-up empty state', async () => {
    const reviewSpy = vi.spyOn(apiModule.revisionApi, 'review').mockResolvedValue({
      item_type: 'question',
      item_id: 'q-bst-1',
      due_date: '2026-11-24',
      interval_days: 1,
      ease: 2.5,
      reps: 1,
      lapses: 1,
    });
    vi.spyOn(apiModule.revisionApi, 'getDue').mockResolvedValue({
      today: '2026-11-23',
      count: 1,
      items: [item2] as never,
    });
    renderDeck();
    await screen.findByText('BST Concept');

    fireEvent.click(screen.getByText('Reveal Answer'));
    fireEvent.click(screen.getByRole('button', { name: /Again/ }));
    await waitFor(() => expect(reviewSpy).toHaveBeenCalledWith('question', 'q-bst-1', 1));
    expect(await screen.findByText('All caught up for today!')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveAttribute('href', '/dashboard');
    expect(screen.getByRole('link', { name: 'Problems' })).toHaveAttribute('href', '/problems');
    await waitFor(() => expect(screen.getByTestId('due-count')).toHaveTextContent('0'));
  });

  it('shows Retry on load error instead of fake-empty', async () => {
    const getDueSpy = vi
      .spyOn(apiModule.revisionApi, 'getDue')
      .mockRejectedValueOnce(new Error('boom'))
      .mockResolvedValueOnce({ today: '2026-11-23', count: 1, items: [item1] as never });
    renderDeck();

    expect(await screen.findByRole('alert')).toHaveTextContent(/Could not load due reviews/);
    expect(screen.queryByText('All caught up for today!')).not.toBeInTheDocument();
    fireEvent.click(screen.getByText('Retry'));
    expect(await screen.findByText('Two Sum')).toBeInTheDocument();
    expect(getDueSpy).toHaveBeenCalledTimes(2);
  });
});
