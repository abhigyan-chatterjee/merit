import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { PROBLEMS } from '../data/problems';
import { contentApi } from '../utils/api';
import { CodeRunner } from '../components/CodeRunner';
import { ProblemExample, TestCase } from '../data/problems';

interface ExamCodingState {
  slug: string;
  title: string;
  statement: string;
  examples: ProblemExample[];
  constraints: string[];
  starterCode: string;
  functionName: string;
  testCases: TestCase[];
  topic?: string;
  passed: boolean | null;
}

export const ExamCodingSection: React.FC<{
  coding: { slug: string; title: string }[];
  selectedSlug?: string;
  onVerdict: (slug: string, passed: boolean) => void;
}> = ({
  coding,
  selectedSlug,
  onVerdict,
}) => {
  const [items, setItems] = useState<ExamCodingState[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      const next: ExamCodingState[] = [];
      for (const c of coding) {
        // Prefer the static bundle (guest-safe), fall back to the API.
        const local = PROBLEMS.find((p) => p.slug === c.slug);
        if (local) {
          next.push({
            slug: local.slug,
            title: local.title,
            statement: local.statement,
            examples: local.examples,
            constraints: local.constraints,
            starterCode: local.starterCode,
            functionName: local.functionName,
            testCases: local.testCases,
            topic: local.topic,
            passed: null,
          });
          continue;
        }
        try {
          const remote = await contentApi.getProblem(c.slug);
          const sc = typeof remote.starter_code === 'string' ? remote.starter_code : remote.starter_code?.javascript ?? '';
          next.push({
            slug: remote.slug,
            title: remote.title,
            statement: remote.statement ?? '',
            examples: remote.examples ?? [],
            constraints: remote.constraints ?? [],
            starterCode: sc,
            functionName: remote.function_name ?? 'solve',
            testCases: (remote.test_cases ?? []).map((t: { input: unknown[]; expected: unknown; label: string }) => ({
              input: t.input,
              expected: t.expected,
              label: t.label,
            })),
            topic: typeof remote.topic === 'string' ? remote.topic : undefined,
            passed: null,
          });
        } catch {
          next.push({ slug: c.slug, title: c.title, statement: '', examples: [], constraints: [], starterCode: '', functionName: 'solve', testCases: [], passed: null });
        }
      }
      if (active) {
        setItems(next);
        setLoaded(true);
      }
    })();
    return () => {
      active = false;
    };
  }, [coding]);

  if (!loaded) {
    return <p className="text-xs font-mono text-muted">Loading coding questions…</p>;
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1.5">
        <h2 className="text-base font-bold text-ink">Coding questions ({items.length})</h2>
        <p className="text-xs text-muted">
          Judge-graded against hidden tests. Submit each one — an Accepted verdict counts toward the exam score.
        </p>
      </div>
      {items.filter((item) => !selectedSlug || item.slug === selectedSlug).map((item) => (
        <div key={item.slug} className="space-y-3 rounded-xl border border-line bg-canvas p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-ink">{item.title}</h3>
              {item.passed === true && (
                <span className="px-2 py-0.5 rounded bg-mint/15 border border-mint/40 text-mint text-[10px] font-mono font-bold">
                  Accepted
                </span>
              )}
              {item.passed === false && (
                <span className="px-2 py-0.5 rounded bg-amber/15 border border-amber/40 text-amber text-[10px] font-mono font-bold">
                  Attempted
                </span>
              )}
            </div>
            <Link
              to={`/problems/${item.topic ?? PROBLEMS.find((p) => p.slug === item.slug)?.topic ?? 'arrays-hashing'}/${item.slug}`}
              target="_blank"
              rel="noreferrer"
              className="text-[11px] font-mono text-muted hover:text-mint transition-colors"
            >
              Open full statement →
            </Link>
          </div>
          <div className="p-3 rounded-lg border border-line bg-surface space-y-3">
            {item.statement && <p className="text-xs text-ink leading-relaxed">{item.statement}</p>}
            {item.examples.length > 0 && (
              <div className="space-y-2">
                {item.examples.map((ex, idx) => (
                  <div key={idx} className="p-2.5 rounded-lg bg-canvas border border-line font-mono text-[11px] space-y-1">
                    <div className="text-muted font-semibold">Example {idx + 1}:</div>
                    <div>
                      <span className="text-muted">Input: </span>
                      <span className="text-ink">{ex.input}</span>
                    </div>
                    <div>
                      <span className="text-muted">Output: </span>
                      <span className="text-mint">{ex.output}</span>
                    </div>
                    {ex.explanation && <div className="text-muted text-[10px] pt-1">Explanation: {ex.explanation}</div>}
                  </div>
                ))}
              </div>
            )}
            {item.constraints.length > 0 && (
              <div>
                <h4 className="text-[10px] font-mono uppercase tracking-wider text-muted mb-1">Constraints:</h4>
                <ul className="list-disc list-inside text-[11px] font-mono text-ink space-y-0.5">
                  {item.constraints.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          {item.testCases.length > 0 ? (
            <CodeRunner
              problemSlug={item.slug}
              starterCode={item.starterCode}
              functionName={item.functionName}
              testCases={item.testCases}
              onVerdict={(passed) => {
                setItems((prev) =>
                  prev.map((p) => (p.slug === item.slug ? { ...p, passed: passed ? true : false } : p)),
                );
                onVerdict(item.slug, passed);
              }}
              tutorEnabled={false}
            />
          ) : (
            <p className="text-xs text-muted">Could not load this question. Open the full statement instead.</p>
          )}
        </div>
      ))}
    </div>
  );
};
