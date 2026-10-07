import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QuizPage } from '../src/pages/QuizPage';
import { ProgressProvider } from '../src/store/ProgressContext';

function renderQuiz(topic = 'arrays-hashing', search = '') {
  return render(
    <ProgressProvider>
      <MemoryRouter initialEntries={[`/quiz/${topic}${search}`]}>
        <Routes>
          <Route path="/quiz/:topic" element={<QuizPage />} />
        </Routes>
      </MemoryRouter>
    </ProgressProvider>,
  );
}

describe('QuizPage', () => {
  beforeEach(() => {
    window.localStorage.clear();
    // Guest: the embedded QuizEngine probes /auth/me; 401 keeps it on the
    // local-question fallback path.
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: async () => ({ error: { code: 'UNAUTHENTICATED', message: 'no session' } }),
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the catalog topic title', () => {
    renderQuiz('arrays-hashing');
    expect(screen.getByRole('heading', { name: /Arrays & Hashing/i })).toBeInTheDocument();
  });

  it('prettifies an unknown topic id', () => {
    renderQuiz('my-custom-topic');
    expect(screen.getByRole('heading', { name: /My Custom Topic/i })).toBeInTheDocument();
  });

  it('defaults the topic selector to the current topic and navigates on change', () => {
    renderQuiz('arrays-hashing');
    const select = screen.getByLabelText(/^Topic$/i);
    expect(select).toHaveValue('arrays-hashing');

    fireEvent.change(select, { target: { value: 'trees' } });
    // The route param changes, so the page re-renders for the new topic.
    expect(screen.getByRole('heading', { name: /Trees & BST/i })).toBeInTheDocument();
  });

  it('shows the assessment breadcrumb', () => {
    renderQuiz('graphs');
    expect(screen.getByRole('navigation', { name: /Breadcrumb/i })).toHaveTextContent(
      'assessment',
    );
  });
});
