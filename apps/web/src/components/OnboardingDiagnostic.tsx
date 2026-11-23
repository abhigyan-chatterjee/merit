import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useProgress } from '../store/ProgressContext';
import type { TargetTier } from '../store/ProgressContext';

export type DiagnosticTopic = 'arrays-hashing' | 'trees' | 'cs-fundamentals' | 'aptitude';

export interface DiagnosticQuestion {
  id: string;
  topic: DiagnosticTopic;
  pillarLabel: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  prompt: string;
  options: [string, string, string, string];
  correctIndex: number;
  explanation: string;
}

export const DIAGNOSTIC_QUESTIONS: DiagnosticQuestion[] = [
  {
    id: 'diag-arrays-1',
    topic: 'arrays-hashing',
    pillarLabel: 'Core Linear DSA',
    difficulty: 'Easy',
    prompt: 'In Two Sum, what is the average time complexity of the hash-map complement lookup approach?',
    options: ['O(n log n)', 'O(n) average', 'O(n^2)', 'O(1) always'],
    correctIndex: 1,
    explanation: 'Each element does one hash lookup, so the scan is O(n) on average.',
  },
  {
    id: 'diag-arrays-2',
    topic: 'arrays-hashing',
    pillarLabel: 'Core Linear DSA',
    difficulty: 'Medium',
    prompt: 'What invariant does a sliding window maintain while scanning an array?',
    options: [
      'A valid window [left, right] that expands right and shrinks left to satisfy the condition',
      'The whole array is sorted at every step',
      'Left always equals right',
      'Elements are never repeated in the window',
    ],
    correctIndex: 0,
    explanation: 'The window [left, right] is the minimal valid range; right expands and left shrinks past invalid states.',
  },
  {
    id: 'diag-arrays-3',
    topic: 'arrays-hashing',
    pillarLabel: 'Core Linear DSA',
    difficulty: 'Medium',
    prompt: 'After O(n) preprocessing, what is the time for a prefix-sum range query sum(l..r)?',
    options: ['O(n)', 'O(log n)', 'O(1)', 'O(n log n)'],
    correctIndex: 2,
    explanation: 'sum(l..r) = prefix[r] - prefix[l-1], a constant-time lookup.',
  },
  {
    id: 'diag-trees-1',
    topic: 'trees',
    pillarLabel: 'Trees, Graphs & DP',
    difficulty: 'Easy',
    prompt: 'What does an inorder traversal of a Binary Search Tree yield?',
    options: ['Level order', 'Sorted order', 'Reverse level order', 'Preorder only'],
    correctIndex: 1,
    explanation: 'Inorder (left, root, right) visits BST keys in ascending order.',
  },
  {
    id: 'diag-trees-2',
    topic: 'trees',
    pillarLabel: 'Trees, Graphs & DP',
    difficulty: 'Medium',
    prompt: 'Why does BFS give the shortest path on an unweighted graph?',
    options: [
      'It uses a stack (DFS)',
      'It explores nodes in increasing distance from the source',
      'It always picks the smallest edge weight',
      'It sorts the adjacency list',
    ],
    correctIndex: 1,
    explanation: 'The queue processes nodes layer by layer, so the first time a node is reached is via fewest edges.',
  },
  {
    id: 'diag-trees-3',
    topic: 'trees',
    pillarLabel: 'Trees, Graphs & DP',
    difficulty: 'Hard',
    prompt: 'How does dynamic programming differ from a greedy choice in overlapping-subproblem problems?',
    options: [
      'DP re-solves subproblems from scratch each time',
      'DP caches optimal subproblem results and combines them; greedy commits to a local choice without backtracking',
      'Greedy always uses more memory',
      'DP only works on trees',
    ],
    correctIndex: 1,
    explanation: 'DP memoizes overlapping subproblems to build an optimal solution; greedy never revisits its local pick.',
  },
  {
    id: 'diag-cs-1',
    topic: 'cs-fundamentals',
    pillarLabel: 'CS Fundamentals & SQL',
    difficulty: 'Medium',
    prompt: 'Which set of conditions is necessary for deadlock in an OS?',
    options: [
      'Mutual exclusion, hold-and-wait, no preemption, and circular wait',
      'Only mutual exclusion',
      'Only circular wait',
      'Large memory requests',
    ],
    correctIndex: 0,
    explanation: 'All four Coffman conditions must hold together for a deadlock to occur.',
  },
  {
    id: 'diag-cs-2',
    topic: 'cs-fundamentals',
    pillarLabel: 'CS Fundamentals & SQL',
    difficulty: 'Medium',
    prompt: 'What does a B+ Tree index primarily provide in a DBMS?',
    options: [
      'Full-text search over blobs',
      'Efficient range and point lookups with ordered leaf links',
      'Automatic schema migration',
      'In-memory caching only',
    ],
    correctIndex: 1,
    explanation: 'B+ Tree leaves are linked in key order, so range scans and point lookups are logarithmic.',
  },
  {
    id: 'diag-cs-3',
    topic: 'cs-fundamentals',
    pillarLabel: 'CS Fundamentals & SQL',
    difficulty: 'Hard',
    prompt: 'In SQL, what does a LEFT JOIN return for rows with no match in the right table?',
    options: [
      'The row is dropped entirely',
      'Right-table columns are NULL for that row',
      'An error is raised',
      'The left row is duplicated',
    ],
    correctIndex: 1,
    explanation: 'LEFT JOIN keeps every left row and pads unmatched right columns with NULL.',
  },
  {
    id: 'diag-apt-1',
    topic: 'aptitude',
    pillarLabel: 'Quantitative Aptitude & Logical Reasoning',
    difficulty: 'Easy',
    prompt: 'Train A at 60 km/h and Train B at 40 km/h move towards each other from 200 km apart. When do they meet?',
    options: ['1 hour', '2 hours', '3 hours', '4 hours'],
    correctIndex: 1,
    explanation: 'Relative speed is 100 km/h, so 200 km takes 2 hours.',
  },
  {
    id: 'diag-apt-2',
    topic: 'aptitude',
    pillarLabel: 'Quantitative Aptitude & Logical Reasoning',
    difficulty: 'Medium',
    prompt: 'A bag has 5 red and 3 blue balls. What is the probability of drawing 2 red balls without replacement?',
    options: ['10/28', '5/8', '20/56', '25/64'],
    correctIndex: 0,
    explanation: '(5/8)*(4/7) = 20/56 = 10/28.',
  },
  {
    id: 'diag-apt-3',
    topic: 'aptitude',
    pillarLabel: 'Quantitative Aptitude & Logical Reasoning',
    difficulty: 'Hard',
    prompt: 'All cats are animals. Some animals are black. Which conclusion definitely follows?',
    options: [
      'All cats are black',
      'Some black animals are cats',
      'No definite conclusion about cats being black',
      'All black animals are cats',
    ],
    correctIndex: 2,
    explanation: 'The black animals may or may not overlap with cats, so no definite link follows.',
  },
];

const TOPIC_ORDER: DiagnosticTopic[] = ['arrays-hashing', 'trees', 'cs-fundamentals', 'aptitude'];

const TIER_LABEL: Record<TargetTier, string> = {
  faang: 'FAANG & Dream',
  product: 'Product & Core',
  service: 'Service & Mass',
};

export const OnboardingDiagnostic: React.FC<{ isOpen: boolean; onClose: () => void }> = ({
  isOpen,
  onClose,
}) => {
  const { saveQuizScore, savePlacementTarget } = useProgress();
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [results, setResults] = useState<{
    perPillar: Array<{ topic: DiagnosticTopic; correct: number; pillarPct: number; pillarLabel: string }>;
    totalCorrect: number;
    overallPct: number;
    recommendedTier: TargetTier;
    weakestTopic: DiagnosticTopic;
  } | null>(null);
  const [tierApplied, setTierApplied] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIndex(0);
      setAnswers({});
      setResults(null);
      setTierApplied(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const question = DIAGNOSTIC_QUESTIONS[index];
  const answeredCount = Object.keys(answers).length;

  const handleFinish = () => {
    const perPillar = TOPIC_ORDER.map((topic) => {
      const qs = DIAGNOSTIC_QUESTIONS.filter((q) => q.topic === topic);
      const correct = qs.filter((q) => answers[DIAGNOSTIC_QUESTIONS.indexOf(q)] === q.correctIndex).length;
      const pillarPct = Math.round((correct / qs.length) * 100);
      saveQuizScore(topic, pillarPct);
      return { topic, correct, pillarPct, pillarLabel: qs[0].pillarLabel };
    });
    const totalCorrect = perPillar.reduce((sum, p) => sum + p.correct, 0);
    const overallPct = Math.round((totalCorrect / DIAGNOSTIC_QUESTIONS.length) * 100);
    const recommendedTier: TargetTier = overallPct >= 75 ? 'faang' : overallPct >= 50 ? 'product' : 'service';
    const weakestTopic = [...perPillar].sort((a, b) => a.pillarPct - b.pillarPct)[0].topic;
    try {
      window.localStorage.setItem('merit_onboarding_diag_done_v1', new Date().toISOString());
    } catch {
      // Storage unavailable: scores are already saved via ProgressContext.
    }
    setResults({ perPillar, totalCorrect, overallPct, recommendedTier, weakestTopic });
  };

  if (results) {
    const { perPillar, totalCorrect, overallPct, recommendedTier, weakestTopic } = results;

    return (
      <div
        role="dialog"
        aria-modal="true"
        aria-label="12-Question Placement Diagnostic"
        className="fixed inset-0 z-50 flex items-center justify-center bg-canvas/80 p-4"
      >
        <div className="w-full max-w-lg rounded-2xl border border-line bg-surface p-6 space-y-5 max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-base font-bold text-ink">Diagnostic Results</h2>
            <button
              type="button"
              aria-label="Close diagnostic"
              onClick={onClose}
              className="px-2 py-1 rounded border border-line text-muted hover:text-ink cursor-pointer"
            >
              ✕
            </button>
          </div>

          <div className="space-y-1">
            <p className="text-2xl font-bold font-mono text-ink tnum">{totalCorrect}/12 · {overallPct}%</p>
          </div>

          <div className="space-y-2">
            {perPillar.map((p) => (
              <div key={p.topic} className="flex items-center justify-between text-xs border-b border-line pb-2">
                <span className="text-ink font-medium">{p.pillarLabel}</span>
                <span className="font-mono text-muted tnum">
                  {p.correct}/3 · {p.pillarPct}%
                </span>
              </div>
            ))}
          </div>

          <div className="space-y-2">
            <p className="text-xs text-muted">
              Recommended Target Tier: <span className="font-semibold text-ink">{TIER_LABEL[recommendedTier]}</span>
            </p>
            <button
              type="button"
              onClick={() => {
                savePlacementTarget({ targetTier: recommendedTier });
                setTierApplied(true);
              }}
              className="px-4 py-2 rounded-lg bg-mint text-canvas font-semibold text-xs hover:brightness-110 transition cursor-pointer"
            >
              Apply Recommended Tier
            </button>
            {tierApplied && <p className="text-xs text-mint">Tier applied!</p>}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Link to={`/quiz/${weakestTopic}`} className="text-xs font-mono text-mint hover:underline">
              Practice Weakest Pillar →
            </Link>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg border border-line text-xs text-ink hover:border-mint cursor-pointer"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="12-Question Placement Diagnostic"
      className="fixed inset-0 z-50 flex items-center justify-center bg-canvas/80 p-4"
    >
      <div className="w-full max-w-lg rounded-2xl border border-line bg-surface p-6 space-y-5 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between gap-3">
          <span className="text-xs font-mono text-muted">Q{index + 1} · {question.pillarLabel} · {question.difficulty}</span>
          <button
            type="button"
            aria-label="Close diagnostic"
            onClick={onClose}
            className="px-2 py-1 rounded border border-line text-muted hover:text-ink cursor-pointer"
          >
            ✕
          </button>
        </div>

        <p className="text-sm font-medium text-ink leading-relaxed">{question.prompt}</p>

        <div className="space-y-2">
          {question.options.map((opt, i) => {
            const selected = answers[index] === i;
            return (
              <button
                key={i}
                type="button"
                aria-pressed={selected}
                onClick={() => setAnswers((prev) => ({ ...prev, [index]: i }))}
                className={`w-full text-left px-3 py-2.5 rounded-lg border text-xs transition cursor-pointer ${
                  selected
                    ? 'border-mint bg-mint/10 text-mint font-semibold'
                    : 'border-line bg-canvas text-ink hover:border-mint/50'
                }`}
              >
                {String.fromCharCode(65 + i)}. {opt}
              </button>
            );
          })}
        </div>

        <div className="flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={() => setIndex((i) => Math.max(0, i - 1))}
            disabled={index === 0}
            className="px-3 py-2 rounded-lg text-xs text-muted hover:text-ink disabled:opacity-40 cursor-pointer"
          >
            ← Previous
          </button>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIndex((i) => Math.min(DIAGNOSTIC_QUESTIONS.length - 1, i + 1))}
              disabled={index === DIAGNOSTIC_QUESTIONS.length - 1}
              className="px-3 py-2 rounded-lg border border-line text-xs text-muted hover:text-ink disabled:opacity-40 cursor-pointer"
            >
              Next →
            </button>
            <button
              type="button"
              onClick={handleFinish}
              disabled={answeredCount === 0}
              className="px-3 py-2 rounded-lg bg-mint text-canvas font-semibold text-xs disabled:opacity-40 cursor-pointer"
            >
              Finish Diagnostic
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
