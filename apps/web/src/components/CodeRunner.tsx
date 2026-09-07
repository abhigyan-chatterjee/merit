import React, { useState } from 'react';
import { Play, RotateCcw, CheckCircle2, XCircle, Terminal } from 'lucide-react';
import { TestCase } from '../data/problems';

interface CodeRunnerProps {
  starterCode: string;
  functionName: string;
  testCases: TestCase[];
  onAllPassed?: () => void;
}

interface TestResult {
  passed: boolean;
  actual: any;
  expected: any;
  timeMs: number;
  error?: string;
}

export const CodeRunner: React.FC<CodeRunnerProps> = ({
  starterCode,
  functionName,
  testCases,
  onAllPassed
}) => {
  const [code, setCode] = useState(starterCode);
  const [activeTab, setActiveTab] = useState(0);
  const [results, setResults] = useState<TestResult[] | null>(null);

  const deepEqual = (a: any, b: any): boolean => {
    return JSON.stringify(a) === JSON.stringify(b);
  };

  const handleRunTests = () => {
    const output: TestResult[] = [];
    let allPass = true;

    for (const tc of testCases) {
      const start = performance.now();
      try {
        // Sandboxed new Function evaluation
        const runner = new Function(
          `${code};\nreturn typeof ${functionName} !== 'undefined' ? ${functionName} : solve;`
        )();
        // Clone input arguments so in-place mutations don't corrupt test cases
        const clonedArgs = JSON.parse(JSON.stringify(tc.input));
        const actual = runner(...clonedArgs);
        const end = performance.now();
        const passed = deepEqual(actual, tc.expected);
        if (!passed) allPass = false;

        output.push({
          passed,
          actual,
          expected: tc.expected,
          timeMs: Math.max(0.1, Number((end - start).toFixed(2)))
        });
      } catch (err: any) {
        allPass = false;
        output.push({
          passed: false,
          actual: null,
          expected: tc.expected,
          timeMs: 0,
          error: err?.message || 'Runtime Error'
        });
      }
    }

    setResults(output);
    if (allPass && onAllPassed) {
      onAllPassed();
    }
  };

  return (
    <div className="flex flex-col rounded-xl border border-line bg-surface overflow-hidden">
      {/* Code Editor Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-line bg-canvas">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-mint" />
          <span className="text-xs font-mono font-semibold text-ink">
            solution.js (JavaScript ES2023 Sandbox)
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setCode(starterCode);
              setResults(null);
            }}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-surface border border-line text-xs font-mono text-muted hover:text-ink cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Code
          </button>

          <button
            onClick={handleRunTests}
            className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded bg-mint text-canvas font-semibold text-xs hover:brightness-110 transition cursor-pointer"
          >
            <Play className="w-3.5 h-3.5" />
            Run 3 Test Cases
          </button>
        </div>
      </div>

      {/* Textarea Code Editor */}
      <div className="p-0 bg-canvas">
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          rows={11}
          spellCheck={false}
          aria-label="Interactive JavaScript Code Editor"
          className="w-full p-4 bg-canvas text-ink font-mono text-xs leading-relaxed focus:outline-none resize-y border-b border-line"
        />
      </div>

      {/* Test Cases Result Tabs */}
      <div className="p-4 bg-surface">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            {testCases.map((_, idx) => {
              const res = results?.[idx];
              return (
                <button
                  key={idx}
                  onClick={() => setActiveTab(idx)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono border transition cursor-pointer ${
                    activeTab === idx
                      ? 'border-mint bg-canvas text-ink'
                      : 'border-line bg-canvas/50 text-muted'
                  }`}
                >
                  {res &&
                    (res.passed ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-mint" />
                    ) : (
                      <XCircle className="w-3.5 h-3.5 text-rose" />
                    ))}
                  Case #{idx + 1}
                </button>
              );
            })}
          </div>

          {results && (
            <span className="text-xs font-mono">
              {results.every((r) => r.passed) ? (
                <span className="text-mint font-bold">✓ All 3 Test Cases Passed!</span>
              ) : (
                <span className="text-rose font-bold">
                  ✗ {results.filter((r) => !r.passed).length} Test Case(s) Failed
                </span>
              )}
            </span>
          )}
        </div>

        {/* Active Case Detail Box */}
        <div className="p-3 rounded-lg border border-line bg-canvas font-mono text-xs space-y-2">
          <div>
            <span className="text-muted">Input: </span>
            <span className="text-ink">{testCases[activeTab]?.label}</span>
          </div>
          <div>
            <span className="text-muted">Expected Output: </span>
            <span className="text-mint">{JSON.stringify(testCases[activeTab]?.expected)}</span>
          </div>

          {results && results[activeTab] && (
            <>
              <div>
                <span className="text-muted">Actual Output: </span>
                {results[activeTab].error ? (
                  <span className="text-rose">{results[activeTab].error}</span>
                ) : (
                  <span
                    className={results[activeTab].passed ? 'text-mint' : 'text-rose'}
                  >
                    {JSON.stringify(results[activeTab].actual)}
                  </span>
                )}
              </div>
              <div className="text-[11px] text-muted">
                Execution Time: <span className="text-ink">{results[activeTab].timeMs} ms</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
