export type StepType = 'visualizer' | 'problem' | 'quiz';

export interface PathStep {
  type: StepType;
  /** Visualizer id, problem slug, or quiz id (topic slug or 'mixed'). */
  id: string;
  /** `title` required only for mixed-quiz steps to be human-readable. */
  title?: string;
}

export interface LearningPath {
  id: string;
  title: string;
  blurb: string;
  icon: 'LayoutGrid' | 'GitCommit' | 'Network' | 'Cpu';
  steps: PathStep[];
}

export const LEARNING_PATHS: LearningPath[] = [
  {
    id: 'foundations',
    title: 'Foundations',
    blurb: 'Start here. Learn how to read arrays, search sorted data and measure your progress.',
    icon: 'LayoutGrid',
    steps: [
      { type: 'visualizer', id: 'array', title: 'Live array operations' },
      { type: 'visualizer', id: 'sorting', title: 'Five sorting algorithms' },
      { type: 'quiz', id: 'arrays', title: 'Arrays & two pointers quiz' },
      { type: 'problem', id: 'two-sum' },
      { type: 'problem', id: 'contains-duplicate' },
      { type: 'problem', id: 'valid-anagram' },
      { type: 'problem', id: 'valid-parentheses' },
      { type: 'problem', id: 'maximum-subarray' }
    ]
  },
  {
    id: 'pointers',
    title: 'Pointers & Strings',
    blurb: 'Work through arrays and strings by sliding a window across them.',
    icon: 'LayoutGrid',
    steps: [
      { type: 'visualizer', id: 'searching', title: 'Binary search step-through' },
      { type: 'problem', id: 'valid-palindrome' },
      { type: 'problem', id: 'two-sum' },
      { type: 'problem', id: 'container-with-most-water' },
      { type: 'problem', id: 'product-of-array-except-self' },
      { type: 'problem', id: 'longest-substring-without-repeating' },
      { type: 'quiz', id: 'arrays', title: 'Pointers mastery quiz' }
    ]
  },
  {
    id: 'structures',
    title: 'Data Structures',
    blurb: 'Lists, stacks, queues and trees — how they work and where they show up.',
    icon: 'GitCommit',
    steps: [
      { type: 'visualizer', id: 'linked-list', title: 'Singly linked list' },
      { type: 'visualizer', id: 'stack', title: 'LIFO stack' },
      { type: 'visualizer', id: 'queue', title: 'FIFO queue' },
      { type: 'visualizer', id: 'binary-tree', title: 'Tree traversals' },
      { type: 'visualizer', id: 'bst', title: 'Binary search tree' },
      { type: 'problem', id: 'reverse-linked-list' },
      { type: 'problem', id: 'middle-of-the-linked-list' },
      { type: 'problem', id: 'merge-two-sorted-lists' },
      { type: 'problem', id: 'maximum-depth-of-binary-tree' },
      { type: 'problem', id: 'invert-binary-tree' },
      { type: 'problem', id: 'kth-smallest-element-in-a-bst' },
      { type: 'quiz', id: 'trees', title: 'Trees & structures quiz' }
    ]
  },
  {
    id: 'advanced',
    title: 'Graphs & Dynamic Programming',
    blurb: 'Explore graphs and learn to break big problems into smaller ones.',
    icon: 'Cpu',
    steps: [
      { type: 'visualizer', id: 'graph', title: 'BFS / DFS explorer' },
      { type: 'visualizer', id: 'heap', title: 'Binary heap operations' },
      { type: 'problem', id: 'find-if-path-exists-in-graph' },
      { type: 'problem', id: 'number-of-islands' },
      { type: 'problem', id: 'climbing-stairs' },
      { type: 'problem', id: 'longest-increasing-subsequence' },
      { type: 'quiz', id: 'graphs', title: 'Graphs quiz' },
      { type: 'quiz', id: 'dp', title: 'Dynamic programming quiz' },
      { type: 'quiz', id: 'mixed', title: 'Mixed mastery quiz' }
    ]
  }
];
