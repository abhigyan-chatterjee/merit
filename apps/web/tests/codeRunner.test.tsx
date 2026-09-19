import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CodeRunner } from '../src/components/CodeRunner';
import { judgeApi } from '../src/utils/api';
import { AuthProvider } from '../src/store/AuthContext';

describe('CodeRunner Component (Phase 4)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
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
    expect(textarea).toHaveValue('def solve(*args):\n    # Write your solution here\n    raise NotImplementedError\n');
  });

  it('places the tutor above the editor and actions in the results bar', () => {
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

    const tutor = screen.getByRole('button', { name: /ask the tutor/i });
    const editor = screen.getByLabelText(/Code Editor/i);
    const resultsBar = screen.getByRole('navigation', { name: /results navigation/i });

    expect(tutor.compareDocumentPosition(editor) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(resultsBar).toContainElement(screen.getByRole('button', { name: /Run Samples/i }));
    expect(resultsBar).toContainElement(screen.getByRole('button', { name: /^Submit$/i }));
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

  it('swaps boilerplate on language change even after typing (per-language buffers)', () => {
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
    const textarea = screen.getByLabelText(/Code Editor/i) as HTMLTextAreaElement;

    // User types in JS...
    fireEvent.change(textarea, { target: { value: 'function solve() { return 42; }' } });
    // ...switches to Python: must get the Python skeleton, not the JS text.
    fireEvent.change(select, { target: { value: 'python' } });
    expect(textarea).toHaveValue('def solve(*args):\n    # Write your solution here\n    raise NotImplementedError\n');
    // ...types in Python, switches back: JS edits preserved, not reset.
    fireEvent.change(textarea, { target: { value: 'def solve(*args):\n    return 42' } });
    fireEvent.change(select, { target: { value: 'javascript' } });
    expect(textarea).toHaveValue('function solve() { return 42; }');
  });

  it('inserts two spaces on Tab instead of moving focus', () => {
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

    const textarea = screen.getByLabelText(/Code Editor/i) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'line1\nline2' } });
    textarea.setSelectionRange(6, 6); // start of second line
    fireEvent.keyDown(textarea, { key: 'Tab', code: 'Tab', charCode: 9 });
    expect((screen.getByLabelText(/Code Editor/i) as HTMLTextAreaElement).value).toBe(
      'line1\n  line2'
    );
  });
});
