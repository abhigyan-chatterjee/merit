import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Play,
  Send,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Clock,
  AlertCircle,
  Terminal,
  History,
  Code2,
} from "lucide-react";
import { TestCase } from "../data/problems";
import {
  judgeApi,
  JudgeResponse,
  SubmissionItem,
  TestCaseResult,
  progressApi,
} from "../utils/api";
import { useAuth } from "../store/AuthContext";
import { AiTutor } from "./AiTutor";

type EditorLang = "javascript" | "python";

const pythonSkeleton = (fn: string): string =>
  `def ${fn}(*args):\n    # Write your solution here\n    raise NotImplementedError\n`;

interface CodeRunnerProps {
  problemSlug: string;
  starterCode: string;
  functionName: string;
  testCases: TestCase[];
  onAllPassed?: () => void;
}

export const CodeRunner: React.FC<CodeRunnerProps> = ({
  problemSlug,
  starterCode,
  functionName,
  testCases: _testCases,
  onAllPassed,
}) => {
  const { user } = useAuth();
  const [language, setLanguage] = useState<EditorLang>(() => {
    try {
      let saved = window.localStorage.getItem('merit_lang_v1');
      if (saved === null) {
        const legacy = window.localStorage.getItem('algovista_lang_v1');
        if (legacy !== null) {
          saved = legacy;
          try {
            window.localStorage.setItem('merit_lang_v1', legacy);
            window.localStorage.removeItem('algovista_lang_v1');
          } catch {
            // ignore
          }
        }
      }
      return saved === 'python' ? 'python' : 'javascript';
    } catch {
      return 'javascript';
    }
  });
  // Per-language buffers: switching languages swaps skeletons without
  // clobbering what the user typed in the other language. Previously a
  // single `code` state plus an `editedCode` guard meant the switch was a
  // no-op after any keystroke, so e.g. the JS boilerplate stuck around
  // after selecting Python.
  const [codeByLang, setCodeByLang] = useState<Record<EditorLang, string>>(() => ({
    javascript: starterCode,
    python: pythonSkeleton(functionName),
  }));
  const code = codeByLang[language];
  const editorRef = useRef<HTMLTextAreaElement | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [activeView, setActiveView] = useState<"results" | "submissions">("results");
  const [results, setResults] = useState<TestCaseResult[] | null>(null);
  const [verdict, setVerdict] = useState<string | null>(null);
  const [runtimeMs, setRuntimeMs] = useState<number | null>(null);
  const [compileError, setCompileError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissions, setSubmissions] = useState<SubmissionItem[]>([]);

  const setCode = (next: string) => {
    setCodeByLang((prev) => ({ ...prev, [language]: next }));
  };

  // Fresh skeletons when navigating between problems: without this the
  // previous problem's code (and function name) lingered in the editor.
  useEffect(() => {
    setCodeByLang({
      javascript: starterCode,
      python: pythonSkeleton(functionName),
    });
    setResults(null);
    setVerdict(null);
    setCompileError(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [problemSlug]);

  // Tab inserts indentation instead of moving focus — a must for any code
  // editor. Plain Tab indents (multiline-aware); Shift+Tab outdents.
  const handleEditorKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key !== 'Tab') return;
    e.preventDefault();
    const el = editorRef.current;
    if (!el) return;
    const { selectionStart: start, selectionEnd: end, value } = el;
    const INDENT = '  ';
    if (e.shiftKey) {
      // Outdent: drop one indent level from each selected line's start.
      const lineStart = value.lastIndexOf('\n', start - 1) + 1;
      const endLineEnd = value.indexOf('\n', end);
      const blockEnd = endLineEnd === -1 ? value.length : endLineEnd;
      const block = value.slice(lineStart, blockEnd);
      const outdented = block
        .split('\n')
        .map((line) =>
          line.startsWith(INDENT) ? line.slice(INDENT.length) : line.startsWith(' ') ? line.slice(1) : line
        )
        .join('\n');
      const next = value.slice(0, lineStart) + outdented + value.slice(blockEnd);
      setCode(next);
      requestAnimationFrame(() => {
        el.focus();
        el.setSelectionRange(lineStart, lineStart + outdented.length);
      });
      return;
    }
    if (start !== end && value.slice(start, end).includes('\n')) {
      // Multiline indent.
      const lineStart = value.lastIndexOf('\n', start - 1) + 1;
      const endLineEnd = value.indexOf('\n', end);
      const blockEnd = endLineEnd === -1 ? value.length : endLineEnd;
      const block = value.slice(lineStart, blockEnd);
      const indented = block
        .split('\n')
        .map((line) => INDENT + line)
        .join('\n');
      const next = value.slice(0, lineStart) + indented + value.slice(blockEnd);
      setCode(next);
      requestAnimationFrame(() => {
        el.focus();
        el.setSelectionRange(lineStart, lineStart + indented.length);
      });
      return;
    }
    const next = value.slice(0, start) + INDENT + value.slice(end);
    setCode(next);
    requestAnimationFrame(() => {
      el.focus();
      el.setSelectionRange(start + INDENT.length, start + INDENT.length);
    });
  };

  // Update default starter code when switching languages. Each language
  // keeps its own buffer, so the user's edits in one language are never
  // clobbered by switching to the other and back.
  const handleLanguageChange = (lang: EditorLang) => {
    setLanguage(lang);
    try {
      window.localStorage.setItem('merit_lang_v1', lang);
    } catch {
      // private mode: ignore
    }
    if (user) {
      progressApi.saveSettings({ preferred_language: lang }).catch(() => {});
    }
    setResults(null);
    setVerdict(null);
    setCompileError(null);
  };

  const handleReset = () => {
    setCodeByLang((prev) => ({
      ...prev,
      [language]: language === "python" ? pythonSkeleton(functionName) : starterCode,
    }));
    setResults(null);
    setVerdict(null);
    setCompileError(null);
  };

  const fetchSubmissions = useCallback(async () => {
    if (!user) return;
    try {
      const subs = await judgeApi.getSubmissions(problemSlug);
      setSubmissions(subs);
    } catch {
      // Offline / guest
    }
  }, [user, problemSlug]);

  useEffect(() => {
    fetchSubmissions();
  }, [fetchSubmissions]);

  // Server preferred language wins on login; local choice persists for guests.
  useEffect(() => {
    if (!user) return;
    progressApi
      .getSettings()
      .then((s) => {
        if (s.preferred_language === 'python' || s.preferred_language === 'javascript') {
          setLanguage(s.preferred_language);
        }
      })
      .catch(() => {});
  }, [user]);

  const handleRunSamples = async () => {
    setIsRunning(true);
    setCompileError(null);
    setActiveView("results");
    try {
      const res: JudgeResponse = await judgeApi.runSamples(problemSlug, language, code);
      setVerdict(res.verdict);
      setRuntimeMs(res.runtime_ms);
      setResults(res.test_results);
      if (res.compile_output && res.verdict !== "AC") {
        setCompileError(res.compile_output);
      }
    } catch (err: unknown) {
      setVerdict("RE");
      setCompileError(err instanceof Error ? err.message : "Execution failed");
    } finally {
      setIsRunning(false);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setCompileError(null);
    setActiveView("results");
    try {
      const sub: SubmissionItem = await judgeApi.submit(problemSlug, language, code);
      setVerdict(sub.verdict);
      setRuntimeMs(sub.runtime_ms);
      setResults(sub.test_results);
      if (sub.verdict === "AC" && onAllPassed) {
        onAllPassed();
      }
      fetchSubmissions();
    } catch (err: unknown) {
      setVerdict("RE");
      setCompileError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderVerdictBadge = () => {
    if (!verdict) return null;
    if (verdict === "AC") {
      return (
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full border border-mint/40 bg-mint/10 text-mint font-mono text-xs font-semibold">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Accepted (AC)</span>
          {runtimeMs !== null && <span className="text-[10px] text-muted">· {runtimeMs.toFixed(1)}ms</span>}
        </div>
      );
    }
    if (verdict === "WA") {
      return (
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full border border-rose/40 bg-rose/10 text-rose font-mono text-xs font-semibold">
          <XCircle className="w-3.5 h-3.5" />
          <span>Wrong Answer (WA)</span>
        </div>
      );
    }
    if (verdict === "TLE") {
      return (
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full border border-amber/40 bg-amber/10 text-amber font-mono text-xs font-semibold">
          <Clock className="w-3.5 h-3.5" />
          <span>Time Limit Exceeded (TLE)</span>
        </div>
      );
    }
    return (
      <div className="flex items-center gap-1.5 px-3 py-1 rounded-full border border-rose/40 bg-rose/10 text-rose font-mono text-xs font-semibold">
        <AlertCircle className="w-3.5 h-3.5" />
        <span>{verdict === "CE" ? "Compile Error" : "Runtime Error"} ({verdict})</span>
      </div>
    );
  };

  return (
    <div className="flex flex-col rounded-xl border border-line bg-surface overflow-y-auto shadow-sm max-h-[calc(100vh-8rem)]">
      {/* Code Editor Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 border-b border-line bg-canvas">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-mint" />
            <select
              value={language}
              aria-label="Execution Language"
              onChange={(e) => handleLanguageChange(e.target.value as "javascript" | "python")}
              className="bg-surface border border-line rounded px-2 py-0.5 text-xs font-mono text-ink focus:outline-none focus:border-mint cursor-pointer"
            >
              <option value="javascript">JavaScript (Node.js)</option>
              <option value="python">Python 3</option>
            </select>
          </div>
          <span className="hidden sm:inline text-[11px] font-mono text-muted">
            Sandboxed Judge
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            title="Reset to starter code"
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-surface border border-line text-xs font-mono text-muted hover:text-ink cursor-pointer transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Reset</span>
          </button>

        </div>
      </div>

      <div className="p-2 border-b border-line bg-surface">
        <AiTutor problemSlug={problemSlug} code={code} />
      </div>

      {/* Code Area */}
      <div className="p-0 bg-canvas">
        <textarea
          ref={editorRef}
          value={code}
          onChange={(e) => {
            setCode(e.target.value);
          }}
          onKeyDown={handleEditorKeyDown}
          rows={12}
          spellCheck={false}
          aria-label="Code Editor"
          className="w-full p-4 bg-canvas text-ink font-mono text-xs leading-relaxed focus:outline-none resize-y border-b border-line"
        />
      </div>

      {/* Results / Submissions Navigation Bar */}
      <nav
        aria-label="Results navigation"
        className="flex flex-wrap items-center justify-between gap-2 px-4 py-2 border-b border-line bg-canvas text-xs font-mono"
      >
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveView("results")}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded cursor-pointer transition ${
              activeView === "results"
                ? "bg-surface border border-line text-ink font-semibold"
                : "text-muted hover:text-ink"
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Test Results</span>
          </button>

          <button
            onClick={() => setActiveView("submissions")}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded cursor-pointer transition ${
              activeView === "submissions"
                ? "bg-surface border border-line text-ink font-semibold"
                : "text-muted hover:text-ink"
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Submissions ({submissions.length})</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          {activeView === "results" && renderVerdictBadge()}
          <button
            onClick={handleRunSamples}
            disabled={isRunning || isSubmitting}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded bg-surface border border-line text-ink font-mono font-medium text-xs transition ${
              isRunning ? "opacity-50 cursor-not-allowed" : "hover:border-mint hover:text-mint cursor-pointer"
            }`}
          >
            <Play className={`w-3.5 h-3.5 text-mint ${isRunning ? "animate-spin" : ""}`} />
            <span>{isRunning ? "Testing…" : "Run Samples"}</span>
          </button>
          <button
            onClick={handleSubmit}
            disabled={isRunning || isSubmitting}
            className={`inline-flex items-center gap-1.5 px-3.5 py-1 rounded bg-mint text-canvas font-mono font-semibold text-xs transition ${
              isSubmitting ? "opacity-50 cursor-not-allowed" : "hover:bg-mint/90 cursor-pointer"
            }`}
          >
            <Send className={`w-3.5 h-3.5 ${isSubmitting ? "animate-spin" : ""}`} />
            <span>{isSubmitting ? "Judging…" : "Submit"}</span>
          </button>
        </div>
      </nav>

      {/* View Content */}
      <div className="p-4 bg-surface min-h-[160px]">
        {activeView === "results" ? (
          <div>
            {compileError && (
              <div className="mb-4 p-3 rounded-lg border border-rose/30 bg-rose/10 text-rose font-mono text-xs whitespace-pre-wrap">
                <div className="flex items-center gap-1.5 font-bold mb-1">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>Error Output</span>
                </div>
                {compileError}
              </div>
            )}

            {results ? (
              <div className="space-y-3">
                {/* Tabs */}
                <div className="flex flex-wrap items-center gap-2">
                  {results.map((res, idx) => (
                    <button
                      key={idx}
                      onClick={() => setActiveTab(idx)}
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono border cursor-pointer transition ${
                        activeTab === idx
                          ? res.passed
                            ? "border-mint bg-mint/15 text-ink"
                            : "border-rose bg-rose/15 text-ink"
                          : "border-line bg-canvas text-muted hover:text-ink"
                      }`}
                    >
                      {res.passed ? (
                        <CheckCircle2 className="w-3 h-3 text-mint" />
                      ) : (
                        <XCircle className="w-3 h-3 text-rose" />
                      )}
                      <span>{res.label || `Case ${idx + 1}`}</span>
                    </button>
                  ))}
                </div>

                {/* Selected Case Details */}
                {results[activeTab] && (
                  <div className="p-3 rounded-lg border border-line bg-canvas space-y-2 font-mono text-xs">
                    <div className="flex items-center justify-between text-muted text-[11px] pb-1 border-b border-line">
                      <span>{results[activeTab].label}</span>
                      {results[activeTab].runtime_ms !== undefined && (
                        <span>Runtime: {results[activeTab].runtime_ms} ms</span>
                      )}
                    </div>

                    <div className="space-y-1">
                      <span className="text-muted text-[10px] uppercase">Input:</span>
                      <pre className="p-2 rounded bg-surface border border-line text-ink overflow-x-auto text-[11px]">
                        {JSON.stringify(results[activeTab].input)}
                      </pre>
                    </div>

                    <div className="space-y-1">
                      <span className="text-muted text-[10px] uppercase">Expected:</span>
                      <pre className="p-2 rounded bg-surface border border-line text-ink overflow-x-auto text-[11px]">
                        {JSON.stringify(results[activeTab].expected)}
                      </pre>
                    </div>

                    <div className="space-y-1">
                      <span className="text-muted text-[10px] uppercase">Actual Output:</span>
                      <pre
                        className={`p-2 rounded border overflow-x-auto text-[11px] ${
                          results[activeTab].passed
                            ? "bg-surface border-line text-mint"
                            : "bg-rose/10 border-rose/30 text-rose"
                        }`}
                      >
                        {results[activeTab].error
                          ? results[activeTab].error
                          : JSON.stringify(results[activeTab].actual)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-8 text-center text-muted font-mono text-xs space-y-1">
                <Terminal className="w-6 h-6 text-mint/60 mb-1" />
                <p>Ready to run.</p>
                <p className="text-[11px] text-muted/70">
                  Click &ldquo;Run Samples&rdquo; to test sample cases or &ldquo;Submit&rdquo; to evaluate all test cases.
                </p>
              </div>
            )}
          </div>
        ) : (
          /* Submissions History */
          <div className="space-y-2 font-mono text-xs">
            {submissions.length === 0 ? (
              <div className="py-8 text-center text-muted">
                <p>No submissions recorded for this problem yet.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {submissions.map((s) => (
                  <div
                    key={s.id}
                    className="flex items-center justify-between p-2.5 rounded-lg border border-line bg-canvas text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          s.verdict === "AC"
                            ? "bg-mint/20 text-mint"
                            : "bg-rose/20 text-rose"
                        }`}
                      >
                        {s.verdict}
                      </span>
                      <span className="text-ink uppercase text-[10px]">{s.language}</span>
                      <span className="text-muted text-[10px]">{s.runtime_ms.toFixed(1)} ms</span>
                    </div>
                    <span className="text-[10px] text-muted">
                      {new Date(s.created_at).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
