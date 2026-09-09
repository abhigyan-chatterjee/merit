import { z } from 'zod';

export const ProblemStatusSchema = z.enum(['Todo', 'Doing', 'Done']);

export const LastVisitedItemSchema = z.object({
  type: z.enum(['problem', 'visualizer']),
  title: z.string(),
  path: z.string(),
  subtitle: z.string().optional(),
});

export const DailyGoalSchema = z.object({
  kind: z.enum(['problems', 'quiz-score', 'custom']),
  label: z.string(),
  /** problems: N problems solved · quiz-score: min pct (0-100) · custom: freeform */
  target: z.number(),
  /** logged-in users can pin one goal that survives reloads and goal clears */
  permanent: z.boolean().optional().default(false).catch(false),
});

export type DailyGoal = {
  kind: 'problems' | 'quiz-score' | 'custom';
  label: string;
  target: number;
  permanent?: boolean;
};

export const DAILY_GOAL_PRESETS: DailyGoal[] = [
  { kind: 'problems', label: 'Solve 1 problem', target: 1 },
  { kind: 'problems', label: 'Solve 3 problems', target: 3 },
  { kind: 'problems', label: 'Solve 5 problems', target: 5 },
  { kind: 'quiz-score', label: 'Score at least 7/10 in a quiz', target: 70 },
  { kind: 'quiz-score', label: 'Score at least 9/10 in a quiz', target: 90 },
  { kind: 'custom', label: 'Custom goal (manual check-off)', target: 1 },
];

export const ProgressStateZodSchema = z.object({
  progress: z.record(z.string(), ProblemStatusSchema).default({}),
  quizzes: z.record(z.string(), z.number()).default({}),
  streak: z.array(z.string()).default([]),
  notes: z.record(z.string(), z.string()).default({}),
  bookmarks: z.array(z.string()).default([]),
  dailyGoalDone: z.record(z.string(), z.boolean()).default({}),
  dailyGoal: DailyGoalSchema.nullable().optional().default(null),
  dailyGoalProgress: z.record(z.string(), z.number()).default({}),
  visitedVisualizers: z.array(z.string()).default([]),
  lastVisited: LastVisitedItemSchema.nullable().optional().default(null),
});

export type ProgressStateSchema = z.infer<typeof ProgressStateZodSchema>;
export type ProblemStatus = z.infer<typeof ProblemStatusSchema>;
export type LastVisitedItem = z.infer<typeof LastVisitedItemSchema>;

export const EMPTY_INITIAL_STATE: ProgressStateSchema = {
  progress: {},
  quizzes: {},
  streak: [],
  notes: {},
  bookmarks: [],
  dailyGoalDone: {},
  dailyGoal: null,
  dailyGoalProgress: {},
  visitedVisualizers: [],
  lastVisited: null,
};
