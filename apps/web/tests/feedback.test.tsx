import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FeedbackModal } from '../src/components/FeedbackModal';

describe('FeedbackModal', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders correctly when open', () => {
    const handleClose = vi.fn();
    render(<FeedbackModal isOpen={true} onClose={handleClose} defaultProblemSlug="two-sum" />);

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Feedback & Bug Report')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/e\.g\. two-sum/i)).toHaveValue('two-sum');
  });

  it('does not render when closed', () => {
    render(<FeedbackModal isOpen={false} onClose={vi.fn()} />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('submits feedback successfully to api', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        status: 'ok',
        message: 'Issue created successfully on GitHub!',
        issue_url: 'https://github.com/abhigyan-chatterjee/merit/issues/42',
      }),
    });
    global.fetch = mockFetch;

    render(<FeedbackModal isOpen={true} onClose={vi.fn()} defaultProblemSlug="two-sum" />);

    fireEvent.change(screen.getByPlaceholderText(/empty input test case/i), {
      target: { value: 'Bug in Two Sum test runner' },
    });
    fireEvent.change(screen.getByPlaceholderText(/provide steps to reproduce/i), {
      target: { value: 'When passing empty array, test crashes unexpectedly.' },
    });

    fireEvent.click(screen.getByRole('button', { name: /submit report/i }));

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/feedback',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );
      expect(screen.getByText(/thank you for your report/i)).toBeInTheDocument();
    });
  });
});
