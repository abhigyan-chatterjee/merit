import type { TargetTier } from '../store/ProgressContext';
import { PROBLEM_MANIFEST } from '../data/problemManifest';
import { TARGETED_EXAMS } from '../data/exams';

export interface TierMeta {
  label: string;
  subtitle: string;
  solvedTarget: number;
  mediumHardTarget: number;
  quizTarget: number;
  examTarget: number;
  streakTarget: number;
  recommendedExamId: string;
}

export const TARGET_TIER_META: Record<TargetTier, TierMeta> = {
  service: {
    label: 'Service & Mass',
    subtitle: 'TCS / Infosys / Wipro',
    solvedTarget: 40,
    mediumHardTarget: 10,
    quizTarget: 70,
    examTarget: 1,
    streakTarget: 5,
    recommendedExamId: 'tcs-nqt',
  },
  product: {
    label: 'Product & Core',
    subtitle: 'Atlassian / Flipkart / Oracle',
    solvedTarget: 100,
    mediumHardTarget: 45,
    quizTarget: 80,
    examTarget: 3,
    streakTarget: 7,
    recommendedExamId: 'product-oa',
  },
  faang: {
    label: 'FAANG & Dream',
    subtitle: 'Google / Microsoft / Amazon',
    solvedTarget: 180,
    mediumHardTarget: 90,
    quizTarget: 85,
    examTarget: 5,
    streakTarget: 14,
    recommendedExamId: 'full-mock',
  },
};

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

const toUtcMidnight = (dateStr: string): number | null => {
  if (!DATE_RE.test(dateStr)) return null;
  const [y, m, d] = dateStr.split('-').map(Number);
  const t = Date.UTC(y, m - 1, d);
  const check = new Date(t);
  if (check.getUTCFullYear() !== y || check.getUTCMonth() !== m - 1 || check.getUTCDate() !== d) return null;
  return t;
};

const localTodayStr = (): string => {
  const n = new Date();
  const y = n.getFullYear();
  const m = String(n.getMonth() + 1).padStart(2, '0');
  const d = String(n.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
};

export const computeDaysToDrive = (targetDriveDate: string | null, todayStr?: string): number | null => {
  if (!targetDriveDate) return null;
  const drive = toUtcMidnight(targetDriveDate);
  if (drive === null) return null;
  const today = toUtcMidnight(todayStr ?? localTodayStr());
  if (today === null) return null;
  return Math.round((drive - today) / 86400000);
};

export interface FocusItem {
  id: string;
  tag: string;
  title: string;
  detail: string;
  link: string;
  cta: string;
}

export interface ReadinessPillars {
  dsa: number;
  quizzes: number;
  exams: number;
  consistency: number;
}

export type ReadinessBand = 'Getting Started' | 'Building Momentum' | 'Interview Ready' | 'Placement Ready';

export interface ReadinessInput {
  progress: Record<string, string>;
  quizzes: Record<string, number>;
  streakDays: number;
  dueTodayCount: number;
  targetTier: TargetTier;
  targetDriveDate: string | null;
  todayStr?: string;
}

export interface ReadinessResult {
  score: number;
  band: ReadinessBand;
  pillars: ReadinessPillars;
  focusItems: FocusItem[];
  daysToDrive: number | null;
}

const difficultyBySlug = new Map(PROBLEM_MANIFEST.map((p) => [p.slug, p.difficulty]));

export const computePlacementReadiness = (input: ReadinessInput): ReadinessResult => {
  const tier = TARGET_TIER_META[input.targetTier] ?? TARGET_TIER_META.product;
  const entries = Object.entries(input.progress ?? {});
  const solvedSlugs = entries.filter(([, v]) => v === 'Done').map(([k]) => k);
  const solvedCount = solvedSlugs.length;
  const solvedSet = new Set(solvedSlugs);
  const mediumHardSolved = solvedSlugs.filter((s) => difficultyBySlug.get(s) !== 'Easy').length;

  const dsa = Math.max(
    0,
    Math.min(
      45,
      Math.round(
        25 * Math.min(1, solvedCount / tier.solvedTarget) +
          20 * Math.min(1, mediumHardSolved / tier.mediumHardTarget),
      ),
    ),
  );

  const quizEntries = Object.entries(input.quizzes ?? {}).filter(([k]) => !k.startsWith('exam:'));
  const topicCount = quizEntries.length;
  const avgQuiz = topicCount === 0 ? 0 : quizEntries.reduce((a, [, v]) => a + v, 0) / topicCount;
  const quizzes = Math.max(
    0,
    Math.min(
      25,
      Math.round(25 * Math.min(1, avgQuiz / tier.quizTarget) * (0.5 + 0.5 * Math.min(1, topicCount / 3))),
    ),
  );

  const examEntries = Object.entries(input.quizzes ?? {}).filter(([k]) => k.startsWith('exam:'));
  const examCount = examEntries.length;
  const avgExam = examCount === 0 ? 0 : examEntries.reduce((a, [, v]) => a + v, 0) / examCount;
  const exams =
    examCount === 0
      ? 0
      : Math.max(0, Math.min(20, Math.round(20 * Math.min(1, examCount / tier.examTarget) * Math.min(1, avgExam / 100))));

  const quizTotal = Object.keys(input.quizzes ?? {}).length;
  const activity = solvedCount + quizTotal;
  let revisionPts = 0;
  if (activity > 0) {
    revisionPts = input.dueTodayCount === 0 ? 3 : (3 * activity) / (activity + input.dueTodayCount);
  }
  const consistency = Math.max(
    0,
    Math.min(10, Math.round(7 * Math.min(1, input.streakDays / tier.streakTarget) + revisionPts)),
  );

  const score = Math.max(0, Math.min(100, dsa + quizzes + exams + consistency));
  const band: ReadinessBand =
    score < 25 ? 'Getting Started' : score < 55 ? 'Building Momentum' : score < 80 ? 'Interview Ready' : 'Placement Ready';

  return {
    score,
    band,
    pillars: { dsa, quizzes, exams, consistency },
    focusItems: buildFocusItems(input, tier, solvedSet, solvedCount),
    daysToDrive: computeDaysToDrive(input.targetDriveDate, input.todayStr),
  };
};

const buildFocusItems = (
  input: ReadinessInput,
  tier: TierMeta,
  solvedSet: Set<string>,
  solvedCount: number,
): FocusItem[] => {
  const items: FocusItem[] = [];
  const used = new Set<string>();
  const push = (item: FocusItem) => {
    if (used.has(item.link)) return;
    used.add(item.link);
    items.push(item);
  };

  if (input.dueTodayCount > 0) {
    push({
      id: 'review-due',
      tag: 'Revision',
      title: `Clear ${input.dueTodayCount} due review card${input.dueTodayCount === 1 ? '' : 's'}`,
      detail: 'Spaced repetition due today — rate Got it to grow the interval.',
      link: '/review',
      cta: 'Open deck',
    });
  }

  const quizEntries = Object.entries(input.quizzes ?? {}).filter(([k]) => !k.startsWith('exam:'));
  if (quizEntries.length === 0) {
    push({
      id: 'quiz-aptitude',
      tag: 'Quiz',
      title: 'Take Aptitude screening quiz',
      detail: 'Baseline quant, logical reasoning and verbal for screening rounds.',
      link: '/quiz/aptitude',
      cta: 'Start quiz',
    });
  } else {
    const weakest = [...quizEntries].sort((a, b) => a[1] - b[1])[0];
    if (weakest && weakest[1] < 75) {
      const [slug, score] = weakest;
      const quizSlug = slug === 'core-cs' ? 'cs-fundamentals' : slug;
      push({
        id: `quiz-${slug}`,
        tag: 'Quiz',
        title: `Strengthen ${slug} quiz`,
        detail: `Scored ${score}% — retake to push past 75%.`,
        link: `/quiz/${quizSlug}`,
        cta: 'Retake',
      });
    }
  }

  const rankOf = (diff: string): number => {
    if (input.targetTier === 'service') return diff === 'Easy' ? 0 : diff === 'Medium' ? 1 : 2;
    if (input.targetTier === 'faang') return diff === 'Medium' ? 0 : diff === 'Hard' ? 1 : 2;
    if (solvedCount < 10) return diff === 'Easy' ? 0 : diff === 'Medium' ? 1 : 2;
    return diff === 'Medium' ? 0 : diff === 'Easy' ? 1 : 2;
  };
  const next = PROBLEM_MANIFEST.filter((p) => !solvedSet.has(p.slug)).sort(
    (a, b) => rankOf(a.difficulty) - rankOf(b.difficulty),
  )[0];
  if (next) {
    push({
      id: `problem-${next.slug}`,
      tag: 'DSA',
      title: next.title,
      detail: `${next.difficulty} · ${next.topic} · high-yield for ${tier.label}.`,
      link: `/problems/${next.topic}/${next.slug}`,
      cta: 'Solve',
    });
  }

  const recommended = TARGETED_EXAMS.find((e) => e.id === tier.recommendedExamId);
  if (recommended) {
    push({
      id: `exam-${recommended.id}`,
      tag: 'Mock',
      title: recommended.title,
      detail: `Recommended ${tier.label} mock — ${recommended.questionCount} MCQs.`,
      link: `/exams/${recommended.id}`,
      cta: 'Start mock',
    });
  }
  if (items.length < 3) {
    const untaken = TARGETED_EXAMS.find((e) => !(input.quizzes ?? {})[`exam:${e.id}`] && !used.has(`/exams/${e.id}`));
    if (untaken) {
      push({
        id: `exam-${untaken.id}`,
        tag: 'Mock',
        title: untaken.title,
        detail: `${untaken.questionCount} MCQs · ${untaken.level}.`,
        link: `/exams/${untaken.id}`,
        cta: 'Start mock',
      });
    }
  }
  if (items.length < 3 && !used.has('/learn/foundation')) {
    push({
      id: 'path-foundation',
      tag: 'Path',
      title: 'Follow Foundation path',
      detail: 'Guided beginner sequence of visualizers, problems and checks.',
      link: '/learn/foundation',
      cta: 'Open path',
    });
  }
  if (items.length < 3 && !used.has('/learn')) {
    push({
      id: 'path-learn',
      tag: 'Path',
      title: 'Browse guided paths',
      detail: 'Pick the track that matches your target tier.',
      link: '/learn',
      cta: 'View paths',
    });
  }

  return items.slice(0, 3);
};
