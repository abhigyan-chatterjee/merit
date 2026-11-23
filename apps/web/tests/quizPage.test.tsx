import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
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

  it('selects the current DSA topic in the DSA dropdown and navigates on change', () => {
    renderQuiz('arrays-hashing');
    const select = screen.getByLabelText(/^DSA topic$/i);
    expect(select).toHaveValue('arrays-hashing');

    fireEvent.change(select, { target: { value: 'trees' } });
    // The route param changes, so the page re-renders for the new topic.
    expect(screen.getByRole('heading', { name: /Trees & BST/i })).toBeInTheDocument();
  });

  it('has no assessment breadcrumb and keeps a quiet diagnostic action', () => {
    renderQuiz('graphs');
    expect(screen.queryByRole('navigation', { name: /Breadcrumb/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '12-Q Diagnostic' })).toBeInTheDocument();
  });

  it('quick-switches to screening and mixed topics via pills', () => {
    renderQuiz('aptitude');
    expect(screen.getByRole('heading', { name: /Aptitude/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Verbal Ability/i }));
    expect(screen.getByRole('heading', { name: /Verbal Ability/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /SQL & Databases/i }));
    expect(screen.getByRole('heading', { name: /SQL & Databases/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /CS Fundamentals/i }));
    expect(screen.getByRole('heading', { name: /CS Fundamentals/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Mixed Mastery/i }));
    expect(screen.getByRole('heading', { name: /Mixed Mastery/i })).toBeInTheDocument();
  });

  it('keeps screening/mixed pills and DSA dropdown mutually exclusive without duplication', () => {
    renderQuiz('aptitude');
    expect(screen.getByRole('button', { name: 'Aptitude' })).toHaveAttribute('aria-pressed', 'true');

    const select = screen.getByLabelText(/^DSA topic$/i);
    expect(select).toHaveValue('');

    const dropdown = within(select);
    expect(dropdown.getByRole('option', { name: 'Arrays & Hashing' })).toBeInTheDocument();
    expect(dropdown.getByRole('option', { name: 'Trees & BST' })).toBeInTheDocument();
    expect(dropdown.queryByRole('option', { name: 'Aptitude' })).not.toBeInTheDocument();
    expect(dropdown.queryByRole('option', { name: 'Verbal Ability' })).not.toBeInTheDocument();
    expect(dropdown.queryByRole('option', { name: 'SQL & Databases' })).not.toBeInTheDocument();
    expect(dropdown.queryByRole('option', { name: 'CS Fundamentals' })).not.toBeInTheDocument();
    expect(dropdown.queryByRole('option', { name: 'Mixed Mastery' })).not.toBeInTheDocument();
  });
});
