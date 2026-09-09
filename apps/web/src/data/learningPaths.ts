export type StepType = 'visualizer' | 'problem' | 'quiz';

export interface PathStep {
  type: StepType;
  /** Visualizer id, problem slug, or quiz id (topic slug or 'mixed'). */
  id: string;
  /** `title` required only for mixed-quiz steps to be human-readable. */
  title?: string;
  /** One-line beginner summary shown on path detail pages. */
  summary?: string;
  /** Further-reading URLs (Foundation topics). */
  readingLinks?: string[];
}

export interface LearningPath {
  id: string;
  title: string;
  blurb: string;
  icon: 'LayoutGrid' | 'GitCommit' | 'Network' | 'Cpu';
  steps: PathStep[];
}

/**
 * Canonical 3-path structure (mirrors content/paths/*.json).
 * Summaries + reading links live in the JSON; the TS mirror keeps
 * routing/progress working offline. Regenerate by hand when JSON changes.
 */
export const LEARNING_PATHS: LearningPath[] = [
  {
    id: 'foundation',
    title: 'Foundation',
    blurb: 'Absolute-beginner track: basic data structures and algorithms with visualizers, short summaries, and further reading.',
    icon: 'LayoutGrid',
    steps: [
      { type: 'visualizer', id: 'array', title: 'Arrays: indexed storage', summary: 'Arrays store items side by side so any index reads in O(1). Inserting or deleting in the middle shifts everything after it, which costs O(n).', readingLinks: ['https://en.wikipedia.org/wiki/Array_data_structure', 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array'] },
      { type: 'problem', id: 'two-sum', title: 'Two Sum', summary: 'First hashing pattern: trade one pass plus a lookup table for the naive pair check.' },
      { type: 'problem', id: 'contains-duplicate', title: 'Contains Duplicate', summary: 'Same set-membership idea as Two Sum, reduced to a yes/no duplicate check.' },
      { type: 'visualizer', id: 'sorting', title: 'Sorting basics', summary: 'Sorting arranges data so binary search and two-pointer scans work.', readingLinks: ['https://en.wikipedia.org/wiki/Sorting_algorithm', 'https://visualgo.net/en/sorting'] },
      { type: 'visualizer', id: 'searching', title: 'Binary search step-through', summary: 'On sorted data, halving the search range each step finds any item in O(log n).', readingLinks: ['https://en.wikipedia.org/wiki/Binary_search'] },
      { type: 'problem', id: 'valid-palindrome', title: 'Valid Palindrome', summary: 'Converging two pointers: compare the ends and walk inward.' },
      { type: 'problem', id: 'longest-substring-without-repeating', title: 'Longest Substring Without Repeating Characters', summary: 'Variable sliding window: stretch the right edge, shrink from the left on duplicates.' },
      { type: 'visualizer', id: 'linked-list', title: 'Singly linked list', summary: 'Nodes linked by pointers: O(1) inserts at a known spot, O(n) access by index.', readingLinks: ['https://en.wikipedia.org/wiki/Linked_list'] },
      { type: 'problem', id: 'reverse-linked-list', title: 'Reverse Linked List', summary: "Rewire each node's pointer to its predecessor in one pass." },
      { type: 'visualizer', id: 'stack', title: 'LIFO stack', summary: 'Last-in first-out: pushes and pops cost O(1).', readingLinks: ['https://en.wikipedia.org/wiki/Stack_(abstract_data_type)'] },
      { type: 'problem', id: 'valid-parentheses', title: 'Valid Parentheses', summary: 'Push opening brackets, match closers off the top of the stack.' },
      { type: 'visualizer', id: 'hashmap', title: 'Hash map buckets', summary: 'Keys hash to buckets for average O(1) put and get.', readingLinks: ['https://en.wikipedia.org/wiki/Hash_table'] },
      { type: 'problem', id: 'valid-anagram', title: 'Valid Anagram', summary: 'Count characters with a frequency map, then compare the counts.' },
      { type: 'visualizer', id: 'binary-tree', title: 'Tree traversals', summary: 'Inorder, preorder, and postorder each visit every node once.', readingLinks: ['https://en.wikipedia.org/wiki/Tree_traversal'] },
      { type: 'problem', id: 'maximum-depth-of-binary-tree', title: 'Maximum Depth of Binary Tree', summary: 'Postorder depth: one plus the deeper of the two child depths.' },
      { type: 'quiz', id: 'arrays-hashing', title: 'Foundation check', summary: 'Mixed beginner questions across the structures above.' },
    ]
  },
  {
    id: 'targeted',
    title: 'Targeted',
    blurb: 'Lean placement track: highest-ROI problems sequenced so each question links to the previous and next.',
    icon: 'Cpu',
    steps: [
      { type: 'problem', id: 'two-sum' },
      { type: 'problem', id: 'contains-duplicate' },
      { type: 'problem', id: 'valid-anagram' },
      { type: 'problem', id: 'subarray-sum-equals-k' },
      { type: 'problem', id: 'product-of-array-except-self' },
      { type: 'problem', id: 'best-time-to-buy-and-sell-stock' },
      { type: 'problem', id: 'longest-consecutive-sequence' },
      { type: 'problem', id: 'container-with-most-water' },
      { type: 'problem', id: 'valid-palindrome' },
      { type: 'problem', id: 'longest-substring-without-repeating' },
      { type: 'problem', id: 'merge-intervals' },
      { type: 'problem', id: 'spiral-matrix' },
      { type: 'problem', id: 'decode-string' },
      { type: 'problem', id: 'valid-parentheses' },
      { type: 'problem', id: 'reverse-linked-list' },
      { type: 'problem', id: 'middle-of-the-linked-list' },
      { type: 'problem', id: 'linked-list-cycle' },
      { type: 'problem', id: 'merge-two-sorted-lists' },
      { type: 'problem', id: 'add-two-numbers' },
      { type: 'problem', id: 'maximum-depth-of-binary-tree' },
      { type: 'problem', id: 'diameter-of-binary-tree' },
      { type: 'problem', id: 'invert-binary-tree' },
      { type: 'problem', id: 'validate-binary-search-tree' },
      { type: 'problem', id: 'kth-smallest-element-in-a-bst' },
      { type: 'problem', id: 'lowest-common-ancestor-of-a-binary-tree' },
      { type: 'problem', id: 'longest-common-prefix' },
      { type: 'problem', id: 'find-if-path-exists-in-graph' },
      { type: 'problem', id: 'number-of-islands' },
      { type: 'problem', id: 'flood-fill' },
      { type: 'problem', id: 'course-schedule' },
      { type: 'problem', id: 'course-schedule-ii' },
      { type: 'problem', id: 'climbing-stairs' },
      { type: 'problem', id: 'house-robber' },
      { type: 'problem', id: 'maximum-subarray' },
      { type: 'problem', id: 'coin-change' },
      { type: 'problem', id: 'longest-increasing-subsequence' },
      { type: 'problem', id: 'unique-paths' },
      { type: 'problem', id: 'roman-to-integer' },
      { type: 'quiz', id: 'dynamic-programming', title: 'Targeted DP check' },
      { type: 'quiz', id: 'mixed', title: 'Targeted placement mock' },
    ]
  },
  {
    id: 'mastery',
    title: 'Mastery',
    blurb: 'Everything verified: all coding problems sequenced by category plus the full quiz bank.',
    icon: 'Network',
    steps: [
      { type: 'visualizer', id: 'array', title: 'Arrays' },
      { type: 'visualizer', id: 'sorting', title: 'Sorting' },
      { type: 'visualizer', id: 'searching', title: 'Searching' },
      { type: 'visualizer', id: 'linked-list', title: 'Linked lists' },
      { type: 'visualizer', id: 'stack', title: 'Stacks' },
      { type: 'visualizer', id: 'queue', title: 'Queues' },
      { type: 'visualizer', id: 'binary-tree', title: 'Binary trees' },
      { type: 'visualizer', id: 'bst', title: 'Binary search trees' },
      { type: 'visualizer', id: 'heap', title: 'Heaps' },
      { type: 'visualizer', id: 'hashmap', title: 'Hash maps' },
      { type: 'visualizer', id: 'graph', title: 'Graphs' },
      { type: 'visualizer', id: 'recursion-tree', title: 'Recursion' },
      { type: 'problem', id: 'two-sum' },
      { type: 'problem', id: 'contains-duplicate' },
      { type: 'problem', id: 'valid-anagram' },
      { type: 'problem', id: 'product-of-array-except-self' },
      { type: 'problem', id: 'subarray-sum-equals-k' },
      { type: 'problem', id: 'best-time-to-buy-and-sell-stock' },
      { type: 'problem', id: 'longest-consecutive-sequence' },
      { type: 'problem', id: 'container-with-most-water' },
      { type: 'problem', id: 'valid-palindrome' },
      { type: 'problem', id: 'merge-two-sorted-lists' },
      { type: 'problem', id: 'remove-nth-node-from-end' },
      { type: 'problem', id: 'longest-substring-without-repeating' },
      { type: 'problem', id: 'decode-string' },
      { type: 'problem', id: 'valid-parentheses' },
      { type: 'problem', id: 'reverse-linked-list' },
      { type: 'problem', id: 'middle-of-the-linked-list' },
      { type: 'problem', id: 'linked-list-cycle' },
      { type: 'problem', id: 'palindrome-linked-list' },
      { type: 'problem', id: 'add-two-numbers' },
      { type: 'problem', id: 'maximum-depth-of-binary-tree' },
      { type: 'problem', id: 'same-tree' },
      { type: 'problem', id: 'invert-binary-tree' },
      { type: 'problem', id: 'diameter-of-binary-tree' },
      { type: 'problem', id: 'validate-binary-search-tree' },
      { type: 'problem', id: 'kth-smallest-element-in-a-bst' },
      { type: 'problem', id: 'lowest-common-ancestor-of-a-binary-tree' },
      { type: 'problem', id: 'longest-common-prefix' },
      { type: 'problem', id: 'merge-intervals' },
      { type: 'problem', id: 'roman-to-integer' },
      { type: 'problem', id: 'spiral-matrix' },
      { type: 'problem', id: 'find-the-town-judge' },
      { type: 'problem', id: 'find-if-path-exists-in-graph' },
      { type: 'problem', id: 'number-of-islands' },
      { type: 'problem', id: 'flood-fill' },
      { type: 'problem', id: 'course-schedule' },
      { type: 'problem', id: 'course-schedule-ii' },
      { type: 'problem', id: 'climbing-stairs' },
      { type: 'problem', id: 'house-robber' },
      { type: 'problem', id: 'maximum-subarray' },
      { type: 'problem', id: 'coin-change' },
      { type: 'problem', id: 'longest-increasing-subsequence' },
      { type: 'problem', id: 'unique-paths' },
      { type: 'quiz', id: 'arrays-hashing', title: 'Arrays & hashing check' },
      { type: 'quiz', id: 'trees', title: 'Trees check' },
      { type: 'quiz', id: 'graphs', title: 'Graphs check' },
      { type: 'quiz', id: 'dynamic-programming', title: 'DP check' },
      { type: 'quiz', id: 'mixed', title: 'Mastery mock' },
    ]
  }
];
