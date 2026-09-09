import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useReducedMotion } from 'framer-motion';
import {
  ArrowRight,
  Code2,
  Layers,
  Terminal,
  CircleDot,
  ArrowUpRight,
  Route,
  BrainCircuit,
  LayoutDashboard
} from 'lucide-react';
import { Panel } from '../components/ui/Panel';
import { SectionLabel } from '../components/ui/SectionLabel';
import { Reveal } from '../components/ui/Reveal';
import { useAuth } from '../store/AuthContext';
import { PROBLEMS } from '../data/problems';
import { VISUALIZERS } from '../data/curriculum';
import { LEARNING_PATHS } from '../data/learningPaths';

const PATTERN_TAGS = [
  'Two Pointers', 'Sliding Window', "Kadane's Algorithm", 'Prefix Sums', 'Fast & Slow Pointers',
  'Binary Search', 'Lomuto Partition', 'Merge Intervals', 'Monotonic Stack', 'Topological Sort',
  'Union-Find', 'Flood Fill', 'Memoization', 'Tabulation', 'Sift-Down Heapify', 'Backtracking'
];

/* --- Live bubble-sort demo that actually runs the algorithm --- */
const useLiveSortDemo = (enabled: boolean) => {
  const [arr, setArr] = useState<number[]>([52, 31, 88, 24, 95, 46, 71, 18, 63, 39, 80, 57]);
  const cursor = useRef({ i: 0, j: 0 });
  const [pair, setPair] = useState<[number, number]>([0, 1]);
  const [passes, setPasses] = useState(0);
  const [comparisons, setComparisons] = useState(0);

  useEffect(() => {
    if (!enabled) return;
    const id = setInterval(() => {
      setArr((prev) => {
        const next = [...prev];
        const n = next.length;
        const { i, j } = cursor.current;

        if (i >= n - 1) {
          cursor.current = { i: 0, j: 0 };
          setPasses(0);
          return next
            .map((v) => ({ v, k: Math.random() }))
            .sort((a, b) => a.k - b.k)
            .map((o) => o.v);
        }

        if (j >= n - 1 - i) {
          cursor.current = { i: i + 1, j: 0 };
          setPasses(i + 1);
          return next;
        }

        setPair([j, j + 1]);
        setComparisons((c) => c + 1);
        if (next[j] > next[j + 1]) {
          [next[j], next[j + 1]] = [next[j + 1], next[j]];
        }
        cursor.current = { i, j: j + 1 };
        return next;
      });
    }, 150);
    return () => clearInterval(id);
  }, [enabled]);

  return { arr, pair, sortedFrom: arr.length - passes, comparisons };
};

export const LandingPage: React.FC = () => {
  const reduce = useReducedMotion();
  const { user } = useAuth();
  const { arr, pair, sortedFrom, comparisons } = useLiveSortDemo(!reduce);

  return (
    <div className="pb-10">
      {/* ============ HERO ============ */}
      <section className="relative overflow-hidden border-b border-line">
        <div className="absolute inset-0 blueprint-grid mask-fade pointer-events-none" aria-hidden="true" />

        <div className="relative max-w-7xl mx-auto px-4 pt-12 pb-14 md:pt-20 md:pb-20 grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
          {/* Left column */}
          <div className="lg:col-span-7 space-y-7">
            <div className="inline-flex items-center gap-2 pl-2 pr-3 py-1 rounded-full border border-line bg-surface text-[11px] font-mono text-muted">
              <span className="relative flex items-center justify-center w-3.5 h-3.5">
                <span className="absolute w-1.5 h-1.5 rounded-full bg-mint animate-pulse-dot" />
              </span>
              <span className="text-ink">An interactive DSA lab</span>
            </div>

            <h1 className="text-[2.1rem] leading-[1.06] sm:text-6xl sm:leading-[1.03] font-bold tracking-[-0.03em] text-ink">
              Stop memorising
              <br />
              algorithms.
              <br />
              <span className="relative inline-block text-mint">
                Watch them run.
                <span className="absolute -bottom-1 left-0 w-full h-px bg-mint/40" />
              </span>
            </h1>

            <p className="text-sm sm:text-base text-muted max-w-xl leading-relaxed">
              One end-to-end place to watch algorithms run, solve problems with
              instant verification, and check yourself with quizzes and exams.
            </p>

            <div className="flex flex-wrap items-center gap-3">
              {user ? (
                <Link
                  to="/dashboard"
                  className="group inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-mint text-canvas font-semibold text-sm hover:brightness-110 transition"
                >
                  Go to your dashboard
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform duration-200" />
                </Link>
              ) : (
                <Link
                  to="/learn"
                  className="group inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-mint text-canvas font-semibold text-sm hover:brightness-110 transition"
                >
                  Start a guided path
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform duration-200" />
                </Link>
              )}

              <Link
                to="/visualizers/sorting"
                className="group inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-line bg-surface text-sm font-medium text-ink hover:border-mint transition"
              >
                <Layers className="w-4 h-4 text-mint" />
                Open a workbench
                <ArrowUpRight className="w-3.5 h-3.5 text-muted group-hover:text-mint transition-colors" />
              </Link>
            </div>

          </div>

          {/* Right column — live terminal demo */}
          <div className="lg:col-span-5 w-full">
            <div className="rounded-xl border border-line bg-surface overflow-hidden shadow-2xl">
              {/* Title bar */}
              <div className="flex items-center justify-between px-3 h-9 border-b border-line bg-canvas">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose/80" />
                  <span className="w-2.5 h-2.5 rounded-full bg-amber/80" />
                  <span className="w-2.5 h-2.5 rounded-full bg-mint/80" />
                  <span className="ml-1.5 text-[11px] font-mono text-muted">bubble_sort.trace</span>
                </div>
                <span className="inline-flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-widest text-mint">
                  <CircleDot className="w-3 h-3 animate-pulse-dot" />
                  live
                </span>
              </div>

              {/* Bars */}
              <div className="p-4 bg-canvas">
                <div className="relative h-44 flex items-end gap-1.5">
                  {arr.map((val, idx) => {
                    const comparing = pair[0] === idx || pair[1] === idx;
                    const sorted = idx >= sortedFrom;
                    const color = comparing
                      ? 'bg-amber'
                      : sorted
                      ? 'bg-mint'
                      : 'bg-steel';
                    return (
                      <div key={idx} className="flex-1 h-full flex items-end">
                        <div
                          style={{ height: `${val}%` }}
                          className={`w-full rounded-t-[3px] ${color} transition-all duration-150 ease-out`}
                        />
                      </div>
                    );
                  })}
                </div>
                {/* ruler */}
                <div className="h-2 mt-1 tick-rule opacity-70" aria-hidden="true" />
              </div>

              {/* Readout */}
              <div className="grid grid-cols-3 divide-x divide-line border-t border-line text-center">
                <div className="py-2.5">
                  <div className="text-sm font-mono font-bold text-ink tnum">{comparisons}</div>
                  <div className="text-[10px] font-mono uppercase tracking-widest text-muted">compares</div>
                </div>
                <div className="py-2.5">
                  <div className="text-sm font-mono font-bold text-amber tnum">
                    [{pair[0]},{pair[1]}]
                  </div>
                  <div className="text-[10px] font-mono uppercase tracking-widest text-muted">cursor</div>
                </div>
                <div className="py-2.5">
                  <div className="text-sm font-mono font-bold text-mint tnum">O(n²)</div>
                  <div className="text-[10px] font-mono uppercase tracking-widest text-muted">worst</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Pattern ticker */}
        <div className="relative border-t border-line bg-surface/60 overflow-hidden">
          <div className="flex w-max animate-marquee py-2.5" aria-hidden="true">
            {[...PATTERN_TAGS, ...PATTERN_TAGS].map((tag, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-2 px-5 text-[11px] font-mono uppercase tracking-[0.14em] text-muted whitespace-nowrap"
              >
                <span className="w-1 h-1 rounded-full bg-mint/60" />
                {tag}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ============ QUICK START (right under hero: one tap to begin) ============ */}
      <section className="max-w-7xl mx-auto px-4 pt-10 space-y-5">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
            Quick start
          </span>
          <span className="flex-1 h-px bg-line" />
          <span className="text-[11px] text-muted">One tap to begin</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {[
            {
              to: '/learn/foundations',
              title: 'Start the Foundations path',
              hint: '8 steps · recommended first',
              Icon: Route,
              tone: 'text-mint',
              accent: true
            },
            {
              to: '/visualizers/sorting',
              title: 'Watch an algorithm run',
              hint: 'Step through sorting',
              Icon: Layers,
              tone: 'text-violet'
            },
            {
              to: '/problems/arrays-hashing',
              title: 'Solve a problem',
              hint: 'Arrays & pointers',
              Icon: Code2,
              tone: 'text-amber'
            },
            {
              to: '/quiz/mixed',
              title: 'Test yourself',
              hint: '10-question mixed quiz',
              Icon: BrainCircuit,
              tone: 'text-violet'
            },
            {
              to: '/dashboard',
              title: 'Open dashboard',
              hint: 'Your progress at a glance',
              Icon: LayoutDashboard,
              tone: 'text-ink'
            }
          ].map((t) => (
            <Link
              key={t.to}
              to={t.to}
              className={`group relative flex items-start gap-3 p-4 rounded-xl border bg-surface transition-colors duration-200 min-h-[88px] ${
                t.accent ? 'border-mint/50 hover:border-mint' : 'border-line hover:border-steel'
              }`}
            >
              <div
                className={`w-9 h-9 rounded-lg border border-line bg-canvas grid place-items-center shrink-0 ${t.tone}`}
              >
                <t.Icon className="w-4 h-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-semibold text-ink group-hover:text-mint transition-colors leading-tight">
                  {t.title}
                </div>
                <div className="text-[11px] text-muted mt-0.5 leading-snug">{t.hint}</div>
              </div>
              <ArrowRight className="w-4 h-4 text-muted/0 group-hover:text-mint group-hover:opacity-100 opacity-0 -translate-x-1 group-hover:translate-x-0 transition-all shrink-0 mt-1" />
              {t.accent && (
                <span className="absolute -top-2 left-3 px-1.5 py-0.5 rounded bg-mint text-canvas text-[9px] font-mono uppercase tracking-widest">
                  Start here
                </span>
              )}
            </Link>
          ))}
        </div>
      </section>

      {/* ============ STATS (live counts from the actual content bundle) ============ */}
      <section className="max-w-7xl mx-auto px-4 py-14">
        <div className="grid grid-cols-1 sm:grid-cols-3 border-t border-l border-line">
          {[
            { n: String(VISUALIZERS.length), l: 'Interactive workbenches', c: 'text-mint' },
            { n: String(PROBLEMS.length), l: 'Practical problems', c: 'text-violet' },
            { n: String(LEARNING_PATHS.length), l: 'Guided learning paths', c: 'text-amber' }
          ].map((s, i) => (
            <Reveal key={s.l} delay={i * 0.05}>
              <div className="relative flex items-center gap-4 border-r border-b border-line p-6 group hover:bg-surface transition-colors duration-200">
                <div className="absolute top-0 left-0 w-6 h-px bg-mint opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className={`text-4xl font-bold font-mono tracking-tighter tnum leading-none ${s.c}`}>
                  {s.n}
                </div>
                <span className="text-sm font-medium text-ink leading-snug">{s.l}</span>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ============ FEATURES ============ */}
      <section className="max-w-7xl mx-auto px-4 space-y-8">
        <SectionLabel index="01" title="Capabilities" />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {[
            {
              i: Layers,
              t: 'Synchronised pseudocode',
              d: 'The exact executing line highlights as bars swap, queues drain and recursion unwinds — with a scrubbable operation log beside it.',
              tone: 'text-mint',
              tag: 'STEP DEBUGGER'
            },
            {
              i: Code2,
              t: 'Instant code verification',
              d: 'Write a solution and run it against three test cases. See pass or fail per case, with output diffs and runtime.',
              tone: 'text-violet',
              tag: 'RUN & VERIFY'
            },
            {
              i: Terminal,
              t: 'Guided learning paths',
              d: 'Follow a managed sequence that mixes problems, quizzes and visualizers into one coherent route to mastery.',
              tone: 'text-amber',
              tag: 'GUIDED'
            }
          ].map((f, idx) => {
            const Icon = f.i;
            return (
              <Reveal key={f.t} delay={idx * 0.06}>
                <Panel bracket className="h-full p-5 hover:border-steel transition-colors duration-200">
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <div className={`w-9 h-9 rounded-lg border border-line bg-canvas flex items-center justify-center ${f.tone}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <span className="font-mono text-[10px] tracking-[0.18em] text-muted">
                        0{idx + 1}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-ink">{f.t}</h3>
                    <p className="text-xs text-muted leading-relaxed">{f.d}</p>
                    <div className="pt-2 border-t border-line">
                      <span className={`text-[10px] font-mono uppercase tracking-[0.14em] ${f.tone}`}>
                        {f.tag}
                      </span>
                    </div>
                  </div>
                </Panel>
              </Reveal>
            );
          })}
        </div>
      </section>

      {/* ============ HOW IT WORKS ============ */}
      <section className="max-w-7xl mx-auto px-4 py-16 space-y-8">
        <SectionLabel index="02" title="Method" />

        <div className="relative grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="hidden md:block absolute top-4 left-0 right-0 h-px bg-line" aria-hidden="true" />
          {[
            {
              n: '01',
              t: 'Visualise the invariant',
              d: 'Scrub Quick Sort partitions, BST inserts or a BFS frontier at 0.25×–2× and see exactly which state changes.',
              c: 'text-mint'
            },
            {
              n: '02',
              t: 'Implement & verify',
              d: 'Solve curated problems across six patterns and get pass/fail per case with execution timings.',
              c: 'text-violet'
            },
            {
              n: '03',
              t: 'Check it stuck',
              d: 'Timed quizzes with instant explanations and a retry-wrong-only loop until the pattern holds.',
              c: 'text-amber'
            }
          ].map((s, i) => (
            <Reveal key={s.n} delay={i * 0.07}>
              <div className="relative space-y-3">
                <div className="flex items-center gap-3">
                  <span className={`relative z-10 w-8 h-8 rounded-lg border border-line bg-surface flex items-center justify-center font-mono text-[11px] font-bold ${s.c}`}>
                    {s.n}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-ink">{s.t}</h3>
                <p className="text-xs text-muted leading-relaxed max-w-xs">{s.d}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>
    </div>
  );
};
