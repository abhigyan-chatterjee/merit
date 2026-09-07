import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CodeRunner } from '../src/components/CodeRunner';
import { judgeApi } from '../src/utils/api';
import { AuthProvider } from '../src/store/AuthContext';

describe('CodeRunner Component (Phase 4)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const mockTestCases = [
    { label: 'Case 1', input: [[2, 7, 11, 15], 9], expected: [0, 1] },
    { label: 'Case 2', input: [[3, 2, 4], 6], expected: [1, 2] },
  ];

  it('renders language selector and switches to Python', () => {
    render(
      <AuthProvider>
        <CodeRunner
          problemSlug="two-sum"
          starterCode="function solve() {}"
          functionName="solve"
          testCases={mockTestCases}
        />
      </AuthProvider>
    );

    const select = screen.getByLabelText(/Execution Language/i);
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('javascript');

    fireEvent.change(select, { target: { value: 'python' } });
    expect(select).toHaveValue('python');

    const textarea = screen.getByLabelText(/Code Editor/i);
    expect(textarea).toHaveValue('def solve(*args):\n    # Write Python solution here\n    pass\n');
  });

  it('runs samples and displays Accepted badge on AC', async () => {
    vi.spyOn(judgeApi, 'runSamples').mockResolvedValueOnce({
      verdict: 'AC',
      runtime_ms: 12.4,
      test_results: [
        { label: 'Case 1', passed: true, input: [[2, 7], 9], expected: [0, 1], actual: [0, 1], runtime_ms: 5.2, error: null },
      ],
      compile_output: '',
    });

    render(
      <AuthProvider>
        <CodeRunner
          problemSlug="two-sum"
          starterCode="function solve() {}"
          functionName="solve"
          testCases={mockTestCases}
        />
      </AuthProvider>
    );

    const runBtn = screen.getByRole('button', { name: /Run Samples/i });
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(screen.getByText(/Accepted \(AC\)/i)).toBeVisible();
      expect(screen.getByRole('button', { name: /Case 1/i })).toBeVisible();
    });
  });

  it('submits solution and triggers onAllPassed when AC', async () => {
    const onAllPassed = vi.fn();
    vi.spyOn(judgeApi, 'submit').mockResolvedValueOnce({
      id: 'sub-1',
      problem_slug: 'two-sum',
      language: 'javascript',
      verdict: 'AC',
      runtime_ms: 8.5,
      test_results: [
        { label: 'Case 1', passed: true, input: [[2, 7], 9], expected: [0, 1], actual: [0, 1], runtime_ms: 4.1, error: null },
      ],
      created_at: '2026-09-07T00:00:00Z',
    });

    render(
      <AuthProvider>
        <CodeRunner
          problemSlug="two-sum"
          starterCode="function solve() {}"
          functionName="solve"
          testCases={mockTestCases}
          onAllPassed={onAllPassed}
        />
      </AuthProvider>
    );

    const submitBtn = screen.getByRole('button', { name: /Submit/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(onAllPassed).toHaveBeenCalled();
      expect(screen.getByText(/Accepted \(AC\)/i)).toBeVisible();
    });
  });
});
