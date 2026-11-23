import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
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

  it('renders language selector and defaults to Python', () => {
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
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

  it("opens each language on the problem's own starter, Python included", () => {
    // Regression: the Python tab used to show a bare `def solve(*args)` skeleton
    // no matter what the problem carried, while Java and C++ got their real
    // signatures — so the Python signature a learner edited was not the one the
    // judge ran.
    renderRunner({
      problemSlug: 'add-binary',
      starterCode: 'function solve(a, b) {}',
      starterCodePython: 'def solve(a, b):\n    # Write your solution here\n    raise NotImplementedError\n',
      starterCodeJava: 'class Solution {\n    public String solve(String a, String b) {}\n}',
      starterCodeCpp: 'class Solution {};',
      functionName: 'solve',
    });

    const textarea = screen.getByLabelText(/Code Editor/i);
    expect(textarea).toHaveValue(
      'def solve(a, b):\n    # Write your solution here\n    raise NotImplementedError\n'
    );

    const select = screen.getByLabelText(/Execution Language/i);
    fireEvent.change(select, { target: { value: 'java' } });
    expect(textarea).toHaveValue('class Solution {\n    public String solve(String a, String b) {}\n}');
  });

  it('places the tutor above the editor and actions in the results bar', () => {
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
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
    });

    const runBtn = screen.getByRole('button', { name: /Run Samples/i });
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(screen.getByText(/Accepted \(AC\)/i)).toBeVisible();
      expect(screen.getByRole('tab', { name: /Case 1/i })).toBeVisible();
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
    });

    fireEvent.click(screen.getByRole('button', { name: /Run Samples/i }));

    await waitFor(() => {
      expect(screen.getByText(/sign in to run or submit code/i)).toBeVisible();
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
    });

    const runBtn = screen.getByRole('button', { name: /Run Samples/i });
    fireEvent.click(runBtn);
    await waitFor(() => {
      expect(screen.getByText(/Accepted \(AC\)/i)).toBeVisible();
      expect(screen.getByRole('tab', { name: /Case 1/i })).toBeVisible();
    });

    fireEvent.click(runBtn);
    await waitFor(() => {
      expect(screen.getByText(/Runtime Error \(RE\)/i)).toBeVisible();
    });
    expect(screen.getByText('Judge exploded')).toBeVisible();
    expect(screen.queryByRole('tab', { name: /Case 1/i })).not.toBeInTheDocument();
    expect(screen.getByText(/Run samples or submit to see results\./i)).toBeVisible();
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
    });

    const runBtn = screen.getByRole('button', { name: /Run Samples/i });
    fireEvent.click(runBtn);
    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /Case 2/i })).toBeVisible();
    });

    fireEvent.click(screen.getByRole('tab', { name: /Case 2/i }));
    expect(screen.getByText('[[3,2,4],6]')).toBeVisible();

    fireEvent.click(runBtn);
    await waitFor(() => {
      expect(screen.queryByRole('tab', { name: /Case 2/i })).not.toBeInTheDocument();
    });
    // activeTab reset to 0: Case 1 details render instead of a blank panel.
    expect(screen.getByText('[[2,7],9]')).toBeVisible();
  });

  it('swaps boilerplate on language change even after typing (per-language buffers)', () => {
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
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

  it('skips confirm and resets directly when code equals starter', () => {
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
    });
    // Code defaults to the Python skeleton; the JS buffer opens on the
    // problem's own starter, so there is nothing to discard.
    const select = screen.getByLabelText(/Execution Language/i);
    fireEvent.change(select, { target: { value: 'javascript' } });
    const textarea = screen.getByLabelText(/Code Editor/i);
    expect(textarea).toHaveValue('function solve() {}');

    fireEvent.click(screen.getByRole('button', { name: /reset/i }));
    expect(screen.queryByText(/discard your edits/i)).not.toBeInTheDocument();
    expect(screen.getByLabelText(/Code Editor/i)).toHaveValue('function solve() {}');
  });

  it('Confirm Reset restores edited code back to the starter', () => {
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
    });
    const select = screen.getByLabelText(/Execution Language/i);
    fireEvent.change(select, { target: { value: 'javascript' } });
    const textarea = screen.getByLabelText(/Code Editor/i);
    fireEvent.change(textarea, { target: { value: 'function solve() { return 1; }' } });
    expect(textarea).toHaveValue('function solve() { return 1; }');

    fireEvent.click(screen.getByRole('button', { name: /reset/i }));
    fireEvent.click(screen.getByRole('button', { name: /discard/i }));
    expect(screen.getByLabelText(/Code Editor/i)).toHaveValue('function solve() {}');
  });

  it('does not steal focus on mount', () => {
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
    });
    expect(screen.getByRole('button', { name: /reset/i })).not.toHaveFocus();
    expect(screen.getByLabelText(/Code Editor/i)).not.toHaveFocus();
  });

  it('shows InlineConfirm when code differs from starter', () => {
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
    });
    const select = screen.getByLabelText(/Execution Language/i);
    fireEvent.change(select, { target: { value: 'javascript' } });
    const textarea = screen.getByLabelText(/Code Editor/i);
    fireEvent.change(textarea, { target: { value: 'function solve() { return 1; }' } });
    fireEvent.click(screen.getByRole('button', { name: /reset/i }));
    expect(screen.getByText(/discard your edits/i)).toBeInTheDocument();
  });

  it('restores focus to Reset button after confirm closes', async () => {
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
    });
    const select = screen.getByLabelText(/Execution Language/i);
    fireEvent.change(select, { target: { value: 'javascript' } });
    const textarea = screen.getByLabelText(/Code Editor/i);
    fireEvent.change(textarea, { target: { value: 'function solve() { return 1; }' } });
    fireEvent.click(screen.getByRole('button', { name: /reset/i }));
    // cancel
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
    await waitFor(() => expect(screen.getByRole('button', { name: /reset/i })).toHaveFocus());
  });

  it('hides the tutor when tutorEnabled is false', () => {
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
      tutorEnabled: false,
    });

    expect(screen.queryByRole('button', { name: /ask the tutor/i })).not.toBeInTheDocument();
  });

  it('inserts two spaces on Tab instead of moving focus', () => {
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
    });

    const textarea = screen.getByLabelText(/Code Editor/i) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'line1\nline2' } });
    textarea.setSelectionRange(6, 6); // start of second line
    fireEvent.keyDown(textarea, { key: 'Tab', code: 'Tab', charCode: 9 });
    expect((screen.getByLabelText(/Code Editor/i) as HTMLTextAreaElement).value).toBe(
      'line1\n  line2'
    );
  });

  it('shows upfront sign-in notice for guests without misleading test-code copy', () => {
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
    });

    expect(screen.getByText(/Sign in to run or submit code/i)).toBeVisible();
    expect(screen.getByText(/draft stays saved locally/i)).toBeVisible();
    expect(screen.queryByText(/you can test code/i)).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Sign in' })).toHaveAttribute(
      'href',
      '/login?next=%2Fproblems%2Farrays-hashing%2Ftwo-sum',
    );
    expect(screen.getByRole('button', { name: /Run Samples/i })).toHaveAttribute(
      'title',
      expect.stringContaining('Sign in required to run code'),
    );
    expect(screen.getByRole('button', { name: /^Submit$/i })).toHaveAttribute(
      'title',
      expect.stringContaining('Sign in required to submit'),
    );
  });

  it('submit CE shows compile_output without temporarily unavailable when not infra', async () => {
    vi.spyOn(judgeApi, 'submit').mockResolvedValueOnce({
      id: 'sub-ce',
      problem_slug: 'two-sum',
      language: 'javascript',
      verdict: 'CE',
      runtime_ms: 0,
      test_results: [],
      created_at: '2026-09-07T00:00:00Z',
      compile_output: 'SyntaxError: Unexpected token )',
      infrastructure_error: false,
    });
    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
    });
    fireEvent.click(screen.getByRole('button', { name: /^Submit$/i }));
    await waitFor(() => {
      expect(screen.getByText('SyntaxError: Unexpected token )')).toBeVisible();
    });
    expect(screen.queryByText(/temporarily unavailable/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Compile \/ Runtime Output/i)).toBeVisible();
  });

  it('late runSamples resolution after problem switch does not overwrite clean state', async () => {
    let resolveRun!: (v: unknown) => void;
    const pending = new Promise((resolve) => {
      resolveRun = resolve;
    });
    vi.spyOn(judgeApi, 'runSamples').mockReturnValueOnce(pending as never);
    const { rerender } = render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/problems/arrays-hashing/two-sum']}>
          <CodeRunner
            problemSlug="two-sum"
            starterCode="function solve() {}"
            functionName="solve"
          />
        </MemoryRouter>
      </AuthProvider>,
    );
    fireEvent.click(screen.getByRole('button', { name: /Run Samples/i }));
    rerender(
      <AuthProvider>
        <MemoryRouter initialEntries={['/problems/arrays-hashing/two-sum']}>
          <CodeRunner
            problemSlug="two-sum-ii-sorted"
            starterCode="function solve() {}"
            functionName="solve"
          />
        </MemoryRouter>
      </AuthProvider>,
    );
    await act(async () => {
      resolveRun({
        verdict: 'AC',
        runtime_ms: 1,
        test_results: [
          { label: 'Case 1', passed: true, input: [], expected: [], actual: [], runtime_ms: 1, error: null },
        ],
        compile_output: '',
      });
    });
    expect(screen.queryByText(/Accepted \(AC\)/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Run samples or submit to see results\./i)).toBeVisible();
  });

  it('persists guest editor drafts in localStorage across remounts', () => {
    const first = renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
    });

    const editor = screen.getByLabelText(/Code Editor/i) as HTMLTextAreaElement;
    fireEvent.change(editor, { target: { value: 'def solve(nums, target):\n    return [0, 1]' } });
    first.unmount();

    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
    });
    expect(screen.getByLabelText(/Code Editor/i)).toHaveValue(
      'def solve(nums, target):\n    return [0, 1]',
    );
  });

  it('rejects malformed scratchpad input and runs valid custom JSON without an Expected row', async () => {
    const runCustom = vi.spyOn(judgeApi, 'runCustom').mockResolvedValueOnce({
      verdict: 'CUSTOM',
      runtime_ms: 3.2,
      test_results: [
        { label: 'Custom', passed: true, input: [[1, 2], 3], expected: null, actual: 3, runtime_ms: 3.2, error: null },
      ],
      compile_output: '',
    });

    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
      sampleInput: [[2, 7], 9],
    });

    fireEvent.click(screen.getByRole('button', { name: /Custom Input/i }));
    const box = screen.getByLabelText(/Custom Input JSON/i);
    expect(box).toHaveValue(JSON.stringify([[2, 7], 9], null, 2));

    fireEvent.change(box, { target: { value: '{not json' } });
    fireEvent.click(screen.getByRole('button', { name: /Run Custom/i }));
    expect(screen.getByRole('alert')).toHaveTextContent(/valid JSON array/i);

    fireEvent.change(box, { target: { value: '{"a":1}' } });
    fireEvent.click(screen.getByRole('button', { name: /Run Custom/i }));
    expect(screen.getByRole('alert')).toHaveTextContent(/JSON array of arguments/i);
    expect(runCustom).not.toHaveBeenCalled();

    fireEvent.change(box, { target: { value: '[[1, 2], 3]' } });
    fireEvent.click(screen.getByRole('button', { name: /Run Custom/i }));

    await waitFor(() => {
      expect(screen.getByText(/Custom Run/i)).toBeVisible();
    });
    expect(runCustom).toHaveBeenCalledWith('two-sum', 'python', expect.any(String), [[1, 2], 3]);
    expect(screen.getByText('[[1,2],3]')).toBeVisible();
    expect(screen.getByText('Actual Output:')).toBeVisible();
    expect(screen.getByText('3')).toBeVisible();
    expect(screen.queryByText('Expected:')).not.toBeInTheDocument();
    expect(screen.queryByText(/Accepted \(AC\)/i)).not.toBeInTheDocument();
  });

  it('shows the OA passed/total summary and redacts hidden test cases', async () => {
    vi.spyOn(judgeApi, 'submit').mockResolvedValueOnce({
      id: 'sub-oa',
      problem_slug: 'two-sum',
      language: 'python',
      verdict: 'WA',
      runtime_ms: 9.4,
      test_results: [
        { label: 'Case 1', passed: true, input: [[2, 7], 9], expected: [0, 1], actual: [0, 1], runtime_ms: 1, error: null },
        { label: 'Case 2', passed: true, input: [[3, 2, 4], 6], expected: [1, 2], actual: [1, 2], runtime_ms: 1, error: null },
        { label: 'Hidden Case 1', passed: false, input: null, expected: null, actual: null, runtime_ms: 1, error: null, hidden: true },
      ],
      created_at: '2026-09-07T00:00:00Z',
      passed_count: 2,
      total_count: 3,
    });

    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
    });

    fireEvent.click(screen.getByRole('button', { name: /^Submit$/i }));

    await waitFor(() => {
      expect(screen.getByText(/Passed 2 \/ 3 test cases/i)).toBeVisible();
    });
    expect(screen.getByText(/\(2 sample · 1 hidden\)/i)).toBeVisible();
    expect(screen.getByText('[[2,7],9]')).toBeVisible();
    expect(screen.getByText('Expected:')).toBeVisible();

    fireEvent.click(screen.getByRole('tab', { name: /Hidden Case 1/i }));

    expect(
      screen.getByText(/Hidden test case — input and expected output are redacted in OA mode/i),
    ).toBeVisible();
    expect(screen.getByText('Failed')).toBeVisible();
    expect(screen.queryByText('[[2,7],9]')).not.toBeInTheDocument();
    expect(screen.queryByText('Expected:')).not.toBeInTheDocument();
    expect(screen.queryByText('Actual Output:')).not.toBeInTheDocument();
  });

  it('runs samples on Ctrl+Enter and submits on Ctrl+Shift+Enter', async () => {
    const runSamples = vi.spyOn(judgeApi, 'runSamples').mockResolvedValueOnce({
      verdict: 'AC',
      runtime_ms: 2,
      test_results: [
        { label: 'Case 1', passed: true, input: [[2, 7], 9], expected: [0, 1], actual: [0, 1], runtime_ms: 2, error: null },
      ],
      compile_output: '',
    });
    const submit = vi.spyOn(judgeApi, 'submit').mockResolvedValueOnce({
      id: 'sub-kb',
      problem_slug: 'two-sum',
      language: 'python',
      verdict: 'AC',
      runtime_ms: 2,
      test_results: [
        { label: 'Case 1', passed: true, input: [[2, 7], 9], expected: [0, 1], actual: [0, 1], runtime_ms: 2, error: null },
      ],
      created_at: '2026-09-07T00:00:00Z',
    });

    renderRunner({
      problemSlug: 'two-sum',
      starterCode: 'function solve() {}',
      functionName: 'solve',
    });

    expect(screen.getByRole('button', { name: /Run Samples/i })).toHaveAttribute('title', expect.stringContaining('Ctrl'));

    const editor = screen.getByLabelText(/Code Editor/i);
    fireEvent.keyDown(editor, { key: 'Enter', ctrlKey: true });
    await waitFor(() => expect(runSamples).toHaveBeenCalledTimes(1));
    expect(submit).not.toHaveBeenCalled();

    fireEvent.keyDown(editor, { key: 'Enter', ctrlKey: true, shiftKey: true });
    await waitFor(() => expect(submit).toHaveBeenCalledTimes(1));
  });
});
