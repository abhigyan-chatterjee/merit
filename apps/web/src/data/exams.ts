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
  /** Per-section MCQ quotas; sizes hold per topic. Omit = one blended pool. */
  topicPlan?: [string, number][];
  /** judge-graded coding questions bundled with the MCQ set */
  coding: ExamCoding[];
  durationSec: number;
  difficulty?: string;
  level: 'Beginner' | 'Intermediate' | 'Advanced';
  /** exam family: recruiter mock, screening round, or DSA topic drill */
  category: 'company' | 'screening' | 'dsa';
  /** recruiter name for company-category exam cards */
  company?: string;
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
    category: 'dsa',
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
    category: 'dsa',
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
    category: 'dsa',
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
    category: 'dsa',
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
    category: 'dsa',
  },
  {
    id: 'aptitude',
    title: 'Aptitude',
    description: 'Quant, logical reasoning and verbal for screening rounds. 20 MCQs in one sitting.',
    topics: ['aptitude'],
    questionCount: 20,
    coding: [],
    durationSec: 1800,
    level: 'Beginner',
    category: 'screening',
  },
  {
    id: 'full-mock',
    title: 'Full Placement Mock',
    description: '3-hour simulation in 3 sections: aptitude screening (30), core CS — OS, DBMS, networks, design (20) — then DSA + coding (20 + 4).',
    topics: ['aptitude', 'core-cs', 'arrays-hashing', 'dynamic-programming'],
    questionCount: 80,
    topicPlan: [
      ['aptitude', 30],
      ['core-cs', 20],
      ['arrays-hashing', 15],
      ['dynamic-programming', 15],
    ],
    coding: [
      { slug: 'merge-intervals', title: 'Merge Intervals' },
      { slug: 'course-schedule-ii', title: 'Course Schedule II' },
      { slug: 'longest-consecutive-sequence', title: 'Longest Consecutive Sequence' },
      { slug: 'coin-change', title: 'Coin Change' },
    ],
    durationSec: 10800,
    level: 'Advanced',
    category: 'screening',
  },
  {
    id: 'tcs-nqt',
    title: 'TCS NQT & Digital Mock',
    description: 'TCS NQT and Digital pattern: aptitude, verbal, and core CS sections plus 2 coding questions.',
    topics: ['aptitude', 'verbal', 'core-cs'],
    questionCount: 50,
    topicPlan: [
      ['aptitude', 20],
      ['verbal', 15],
      ['core-cs', 15],
    ],
    coding: [
      { slug: 'two-sum', title: 'Two Sum' },
      { slug: 'subarray-sum-equals-k', title: 'Subarray Sum Equals K' },
    ],
    durationSec: 5400,
    level: 'Intermediate',
    category: 'company',
    company: 'TCS',
  },
  {
    id: 'infosys-sp-dse',
    title: 'Infosys SP & DSE Mock',
    description: 'Infosys SP and DSE pattern: aptitude, core CS, and SQL sections plus 2 coding questions.',
    topics: ['aptitude', 'core-cs', 'sql'],
    questionCount: 40,
    topicPlan: [
      ['aptitude', 15],
      ['core-cs', 15],
      ['sql', 10],
    ],
    coding: [
      { slug: 'longest-substring-without-repeating', title: 'Longest Substring Without Repeating Characters' },
      { slug: 'coin-change', title: 'Coin Change' },
    ],
    durationSec: 5400,
    level: 'Advanced',
    category: 'company',
    company: 'Infosys',
  },
  {
    id: 'service-screening',
    title: 'Service Screening Mock',
    description: 'Service-company first round: aptitude, verbal, SQL, and core CS MCQs with no coding section.',
    topics: ['aptitude', 'verbal', 'sql', 'core-cs'],
    questionCount: 40,
    topicPlan: [
      ['aptitude', 15],
      ['verbal', 10],
      ['sql', 10],
      ['core-cs', 5],
    ],
    coding: [],
    durationSec: 2700,
    level: 'Beginner',
    category: 'screening',
  },
  {
    id: 'product-oa',
    title: 'Product OA Simulation',
    description: 'Product-company online assessment: core CS plus DSA sections and 3 coding questions.',
    topics: ['core-cs', 'arrays-hashing', 'trees', 'dynamic-programming'],
    questionCount: 30,
    topicPlan: [
      ['core-cs', 10],
      ['arrays-hashing', 8],
      ['trees', 6],
      ['dynamic-programming', 6],
    ],
    coding: [
      { slug: 'trapping-rain-water', title: 'Trapping Rain Water' },
      { slug: 'merge-intervals', title: 'Merge Intervals' },
      { slug: 'course-schedule', title: 'Course Schedule' },
    ],
    durationSec: 5400,
    level: 'Advanced',
    category: 'company',
    company: 'Product',
  },
];
