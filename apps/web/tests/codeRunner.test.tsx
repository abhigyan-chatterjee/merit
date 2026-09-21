import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { CodeRunner } from '../src/components/CodeRunner';
import { ApiError, judgeApi } from '../src/utils/api';
import { AuthProvider } from '../src/store/AuthContext';

const renderRunner = (props: React.ComponentProps<typeof CodeRunner>) =>
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/problems/arrays-hashing/two-sum']}>
        <CodeRunner {...props} />
      </MemoryRouter>
    </AuthProvider>
  );

describe('CodeRunner Component (Phase 4)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
  });

  const mockTestCases = [
    { label: 'Case 1', input: [[2, 7, 11, 15], 9], expected: [0, 1] },
    { label: 'Case 2', input: [[3, 2, 4], 6], expected: [1, 2] },
  ];

  it('renders language selector and defaults to Python', () => {
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
      testCases: mockTestCases,
    });

    const select = screen.getByLabelText(/Execution Language/i);
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('python');

    const textarea = screen.getByLabelText(/Code Editor/i);
    expect(textarea).toHaveValue('def solve(*args):\n    # Write your solution here\n    raise NotImplementedError\n');

    fireEvent.change(select, { target: { value: 'javascript' } });
    expect(select).toHaveValue('javascript');
    expect(textarea).toHaveValue('function solve() {}');
  });

  it('places the tutor above the editor and actions in the results bar', () => {
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
      testCases: mockTestCases,
    });

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

    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
      testCases: mockTestCases,
    });

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

    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
      testCases: mockTestCases,
      onAllPassed,
    });

    const submitBtn = screen.getByRole('button', { name: /Submit/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(onAllPassed).toHaveBeenCalled();
      expect(screen.getByText(/Accepted \(AC\)/i)).toBeVisible();
    });
  });

  it('prompts sign-in instead of a runtime error when the judge returns 401', async () => {
    vi.spyOn(judgeApi, 'runSamples').mockRejectedValueOnce(
      new ApiError(401, { code: 'HTTP_401', message: 'Not authenticated' })
    );

    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
      testCases: mockTestCases,
    });

    fireEvent.click(screen.getByRole('button', { name: /Run Samples/i }));

    await waitFor(() => {
      expect(screen.getByText(/sign in to run code/i)).toBeVisible();
    });
    expect(screen.queryByText(/runtime error/i)).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Sign in' })).toHaveAttribute(
      'href',
      '/login?next=%2Fproblems%2Farrays-hashing%2Ftwo-sum'
    );
  });

  it('keeps the runtime-error verdict for non-401 judge failures', async () => {
    vi.spyOn(judgeApi, 'runSamples').mockRejectedValueOnce(
      new ApiError(500, { code: 'HTTP_500', message: 'Judge unavailable' })
    );

    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
      testCases: mockTestCases,
    });

    fireEvent.click(screen.getByRole('button', { name: /Run Samples/i }));

    await waitFor(() => {
      expect(screen.getByText(/Runtime Error \(RE\)/i)).toBeVisible();
    });
    expect(screen.queryByText(/sign in to run code/i)).not.toBeInTheDocument();
    expect(screen.getByText('Judge unavailable')).toBeVisible();
  });

  it('clears stale results when a later run fails', async () => {
    const spy = vi.spyOn(judgeApi, 'runSamples');
    spy.mockResolvedValueOnce({
      verdict: 'AC',
      runtime_ms: 5,
      test_results: [
        { label: 'Case 1', passed: true, input: [[2, 7], 9], expected: [0, 1], actual: [0, 1], runtime_ms: 2, error: null },
      ],
      compile_output: '',
    });
    spy.mockRejectedValueOnce(new ApiError(500, { code: 'HTTP_500', message: 'Judge exploded' }));

    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
      testCases: mockTestCases,
    });

    const runBtn = screen.getByRole('button', { name: /Run Samples/i });
    fireEvent.click(runBtn);
    await waitFor(() => {
      expect(screen.getByText(/Accepted \(AC\)/i)).toBeVisible();
      expect(screen.getByRole('button', { name: /Case 1/i })).toBeVisible();
    });

    fireEvent.click(runBtn);
    await waitFor(() => {
      expect(screen.getByText(/Runtime Error \(RE\)/i)).toBeVisible();
    });
    expect(screen.getByText('Judge exploded')).toBeVisible();
    expect(screen.queryByRole('button', { name: /Case 1/i })).not.toBeInTheDocument();
    expect(screen.getByText(/Ready to run\./i)).toBeVisible();
  });

  it('resets the selected case tab when new results arrive', async () => {
    const spy = vi.spyOn(judgeApi, 'runSamples');
    spy.mockResolvedValueOnce({
      verdict: 'AC',
      runtime_ms: 5,
      test_results: [
        { label: 'Case 1', passed: true, input: [[2, 7], 9], expected: [0, 1], actual: [0, 1], runtime_ms: 2, error: null },
        { label: 'Case 2', passed: true, input: [[3, 2, 4], 6], expected: [1, 2], actual: [1, 2], runtime_ms: 2, error: null },
      ],
      compile_output: '',
    });
    spy.mockResolvedValueOnce({
      verdict: 'AC',
      runtime_ms: 5,
      test_results: [
        { label: 'Case 1', passed: true, input: [[2, 7], 9], expected: [0, 1], actual: [0, 1], runtime_ms: 2, error: null },
      ],
      compile_output: '',
    });

    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
      testCases: mockTestCases,
    });

    const runBtn = screen.getByRole('button', { name: /Run Samples/i });
    fireEvent.click(runBtn);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Case 2/i })).toBeVisible();
    });

    fireEvent.click(screen.getByRole('button', { name: /Case 2/i }));
    expect(screen.getByText('[[3,2,4],6]')).toBeVisible();

    fireEvent.click(runBtn);
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /Case 2/i })).not.toBeInTheDocument();
    });
    // activeTab reset to 0: Case 1 details render instead of a blank panel.
    expect(screen.getByText('[[2,7],9]')).toBeVisible();
  });

  it('swaps boilerplate on language change even after typing (per-language buffers)', () => {
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
      testCases: mockTestCases,
    });

    const select = screen.getByLabelText(/Execution Language/i);
    const textarea = screen.getByLabelText(/Code Editor/i) as HTMLTextAreaElement;

    // User types in Python (default)...
    fireEvent.change(textarea, { target: { value: 'def solve(*args):\n    return 42' } });
    // ...switches to JS: must get the JS skeleton, not the Python text.
    fireEvent.change(select, { target: { value: 'javascript' } });
    expect(textarea).toHaveValue('function solve() {}');
    // ...types in JS, switches back to Python: Python edits preserved, not reset.
    fireEvent.change(textarea, { target: { value: 'function solve() { return 42; }' } });
    fireEvent.change(select, { target: { value: 'python' } });
    expect(textarea).toHaveValue('def solve(*args):\n    return 42');
  });

  it('hides the tutor when tutorEnabled is false', () => {
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
      testCases: mockTestCases,
      tutorEnabled: false,
    });

    expect(screen.queryByRole('button', { name: /ask the tutor/i })).not.toBeInTheDocument();
  });

  it('inserts two spaces on Tab instead of moving focus', () => {
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
      testCases: mockTestCases,
    });

    const textarea = screen.getByLabelText(/Code Editor/i) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'line1\nline2' } });
    textarea.setSelectionRange(6, 6); // start of second line
    fireEvent.keyDown(textarea, { key: 'Tab', code: 'Tab', charCode: 9 });
    expect((screen.getByLabelText(/Code Editor/i) as HTMLTextAreaElement).value).toBe(
      'line1\n  line2'
    );
  });
});
