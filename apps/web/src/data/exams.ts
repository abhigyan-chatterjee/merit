export interface TargetedExam {
  id: string;
  title: string;
  description: string;
  /** backend quiz topics to sample from */
  topics: string[];
  questionCount: number;
  durationSec: number;
  difficulty?: string;
  level: 'Beginner' | 'Intermediate' | 'Advanced';
}

export const TARGETED_EXAMS: TargetedExam[] = [
  {
    id: 'intermediate-dsa',
    title: 'Intermediate DSA',
    description: 'Balanced cross-topic placement set across arrays, trees, graphs and DP.',
    topics: ['arrays-hashing', 'trees', 'graphs', 'dynamic-programming'],
    questionCount: 20,
    durationSec: 1800,
    level: 'Intermediate',
  },
  {
    id: 'arrays-hashmaps',
    title: 'Arrays & HashMaps',
    description: 'Two pointers, sliding window, prefix sums and complement lookups.',
    topics: ['arrays-hashing'],
    questionCount: 10,
    durationSec: 900,
    level: 'Beginner',
  },
  {
    id: 'dynamic-programming',
    title: 'Dynamic Programming',
    description: 'Optimal substructure, memoization and tabulation recurrences.',
    topics: ['dynamic-programming'],
    questionCount: 10,
    durationSec: 1200,
    level: 'Advanced',
  },
  {
    id: 'trees-graphs',
    title: 'Trees & Graphs',
    description: 'Traversals, BST invariants, BFS/DFS and connectivity.',
    topics: ['trees', 'graphs'],
    questionCount: 12,
    durationSec: 1200,
    level: 'Intermediate',
  },
  {
    id: 'sorting-searching',
    title: 'Sorting & Searching',
    description: 'Binary search invariants, in-place sorts and comparison bounds.',
    topics: ['sorting'],
    questionCount: 10,
    durationSec: 900,
    level: 'Intermediate',
  },
  {
    id: 'full-mock',
    title: 'Full Placement Mock',
    description: 'Comprehensive 20-question timed simulation across all topics.',
    topics: ['arrays-hashing', 'trees', 'graphs', 'dynamic-programming'],
    questionCount: 20,
    durationSec: 1800,
    level: 'Advanced',
  },
];
