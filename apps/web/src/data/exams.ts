export interface ExamCoding {
  slug: string;
  title: string;
}

export interface TargetedExam {
  id: string;
  title: string;
  description: string;
  /** backend quiz topics to sample from */
  topics: string[];
  questionCount: number;
  /** judge-graded coding questions bundled with the MCQ set */
  coding: ExamCoding[];
  durationSec: number;
  difficulty?: string;
  level: 'Beginner' | 'Intermediate' | 'Advanced';
}

export const TARGETED_EXAMS: TargetedExam[] = [
  {
    id: 'foundational-dsa',
    title: 'Foundational DSA',
    description: 'Arrays, hashing, pointers, stacks and basic trees. 20 MCQs plus 2 guided coding questions.',
    topics: ['arrays-hashing', 'two-pointers', 'stack', 'trees'],
    questionCount: 20,
    coding: [
      { slug: 'two-sum', title: 'Two Sum' },
      { slug: 'valid-parentheses', title: 'Valid Parentheses' },
    ],
    durationSec: 2700,
    level: 'Beginner',
  },
  {
    id: 'intermediate-dsa',
    title: 'Intermediate DSA',
    description: 'Balanced cross-topic placement set across arrays, trees, graphs and DP. 20 MCQs plus 2 coding questions.',
    topics: ['arrays-hashing', 'trees', 'graphs', 'dynamic-programming'],
    questionCount: 20,
    coding: [
      { slug: 'merge-intervals', title: 'Merge Intervals' },
      { slug: 'number-of-islands', title: 'Number of Islands' },
    ],
    durationSec: 3600,
    level: 'Intermediate',
  },
  {
    id: 'sorting-searching',
    title: 'Sorting & Searching',
    description: 'Binary search invariants, in-place sorts and comparison bounds. 20 MCQs plus 2 coding questions.',
    topics: ['sorting', 'binary-search'],
    questionCount: 20,
    coding: [
      { slug: 'best-time-to-buy-and-sell-stock', title: 'Best Time to Buy and Sell Stock' },
      { slug: 'subarray-sum-equals-k', title: 'Subarray Sum Equals K' },
    ],
    durationSec: 3600,
    level: 'Intermediate',
  },
  {
    id: 'dp-greedy',
    title: 'DP & Greedy',
    description: 'Optimal substructure, memoization, tabulation and greedy choices. 20 MCQs plus 2 coding questions.',
    topics: ['dynamic-programming'],
    questionCount: 20,
    coding: [
      { slug: 'climbing-stairs', title: 'Climbing Stairs' },
      { slug: 'coin-change', title: 'Coin Change' },
    ],
    durationSec: 3600,
    level: 'Advanced',
  },
  {
    id: 'trees-graphs',
    title: 'Trees & Graphs',
    description: 'Traversals, BST invariants, BFS/DFS and connectivity. 20 MCQs plus 2 coding questions.',
    topics: ['trees', 'graphs'],
    questionCount: 20,
    coding: [
      { slug: 'validate-binary-search-tree', title: 'Validate Binary Search Tree' },
      { slug: 'course-schedule', title: 'Course Schedule' },
    ],
    durationSec: 3600,
    level: 'Intermediate',
  },
  {
    id: 'aptitude',
    title: 'Aptitude',
    description: 'Quant, logical reasoning and verbal for screening rounds. 20 MCQs plus 2 coding questions.',
    topics: ['aptitude'],
    questionCount: 20,
    coding: [
      { slug: 'subarray-sum-equals-k', title: 'Subarray Sum Equals K' },
      { slug: 'roman-to-integer', title: 'Roman to Integer' },
    ],
    durationSec: 2700,
    level: 'Beginner',
  },
  {
    id: 'full-mock',
    title: 'Full Placement Mock',
    description: '3-hour simulation: aptitude, core CS (OS, DBMS, networks, design) and coding. 20 MCQs plus 2 coding questions.',
    topics: ['aptitude', 'core-cs', 'arrays-hashing', 'dynamic-programming'],
    questionCount: 20,
    coding: [
      { slug: 'merge-intervals', title: 'Merge Intervals' },
      { slug: 'course-schedule-ii', title: 'Course Schedule II' },
    ],
    durationSec: 10800,
    level: 'Advanced',
  },
];
