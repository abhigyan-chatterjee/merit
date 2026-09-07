import { z } from 'zod';

export const ProblemStatusSchema = z.enum(['Todo', 'Doing', 'Done']);

export const LastVisitedItemSchema = z.object({
  type: z.enum(['problem', 'visualizer']),
  title: z.string(),
  path: z.string(),
  subtitle: z.string().optional(),
});

export const ProgressStateZodSchema = z.object({
  progress: z.record(z.string(), ProblemStatusSchema).default({}),
  quizzes: z.record(z.string(), z.number()).default({}),
  streak: z.array(z.string()).default([]),
  notes: z.record(z.string(), z.string()).default({}),
  bookmarks: z.array(z.string()).default([]),
  dailyGoalDone: z.record(z.string(), z.boolean()).default({}),
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
  visitedVisualizers: [],
  lastVisited: null,
};
