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
 * routing/progress working offline. Regenerate with sync_paths_ts.py
 * when JSON changes -- do not hand-edit steps below.
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
      { type: 'visualizer', id: 'sorting', title: 'Sorting basics', summary: 'Sorting arranges data so binary search and two-pointer scans work. Watch how many comparisons each method needs.', readingLinks: ['https://en.wikipedia.org/wiki/Sorting_algorithm', 'https://visualgo.net/en/sorting'] },
      { type: 'visualizer', id: 'searching', title: 'Binary search step-through', summary: 'On sorted data, halving the search range each step finds any item in O(log n).', readingLinks: ['https://en.wikipedia.org/wiki/Binary_search'] },
      { type: 'problem', id: 'valid-palindrome', title: 'Valid Palindrome', summary: 'Converging two pointers: compare the ends and walk inward.' },
      { type: 'problem', id: 'longest-substring-without-repeating', title: 'Longest Substring Without Repeating Characters', summary: 'Variable sliding window: stretch the right edge, shrink from the left on duplicates.' },
      { type: 'visualizer', id: 'linked-list', title: 'Singly linked list', summary: 'Nodes linked by pointers: O(1) inserts at a known spot, O(n) access by index.', readingLinks: ['https://en.wikipedia.org/wiki/Linked_list'] },
      { type: 'problem', id: 'reverse-linked-list', title: 'Reverse Linked List', summary: 'Rewire each node\'s pointer to its predecessor in one pass.' },
      { type: 'visualizer', id: 'stack', title: 'LIFO stack', summary: 'Last-in first-out: pushes and pops cost O(1) and power bracket matching and undo histories.', readingLinks: ['https://en.wikipedia.org/wiki/Stack_(abstract_data_type)'] },
      { type: 'problem', id: 'valid-parentheses', title: 'Valid Parentheses', summary: 'Push opening brackets, match closers off the top of the stack.' },
      { type: 'visualizer', id: 'hashmap', title: 'Hash map buckets', summary: 'Keys hash to buckets for average O(1) put and get; collisions chain inside a bucket.', readingLinks: ['https://en.wikipedia.org/wiki/Hash_table'] },
      { type: 'problem', id: 'valid-anagram', title: 'Valid Anagram', summary: 'Count characters with a frequency map, then compare the counts.' },
      { type: 'visualizer', id: 'binary-tree', title: 'Tree traversals', summary: 'Inorder, preorder, and postorder each visit every node once; order decides what problems they fit.', readingLinks: ['https://en.wikipedia.org/wiki/Tree_traversal'] },
      { type: 'problem', id: 'maximum-depth-of-binary-tree', title: 'Maximum Depth of Binary Tree', summary: 'Postorder depth: one plus the deeper of the two child depths.' },
      { type: 'quiz', id: 'arrays-hashing', title: 'Foundation check', summary: 'Mixed beginner questions across the structures above.' },
    ]
  },
  {
    id: 'targeted',
    title: 'Targeted',
    blurb: 'Lean placement track: highest-ROI problems sequenced so each question links to the previous and next. Original ordering and statements throughout.',
    icon: 'Cpu',
    steps: [
      { type: 'problem', id: 'two-sum', title: 'Two Sum', summary: 'Start of the hashing chain: complement lookup in one pass.' },
      { type: 'problem', id: 'contains-duplicate', title: 'Contains Duplicate', summary: 'Same set idea, simplified to duplicate detection.' },
      { type: 'problem', id: 'valid-anagram', title: 'Valid Anagram', summary: 'Frequency maps instead of membership sets.' },
      { type: 'problem', id: 'subarray-sum-equals-k', title: 'Subarray Sum Equals K', summary: 'Prefix sums plus a hash map: count earlier prefixes equal to sum minus k.' },
      { type: 'problem', id: 'product-of-array-except-self', title: 'Product of Array Except Self', summary: 'Prefix and suffix passes without division.' },
      { type: 'problem', id: 'best-time-to-buy-and-sell-stock', title: 'Best Time to Buy and Sell Stock', summary: 'One-pass minimum tracking: the greedy cousin of the prefix idea.' },
      { type: 'problem', id: 'longest-consecutive-sequence', title: 'Longest Consecutive Sequence', summary: 'Set streaks in O(n): only count from streak starts.' },
      { type: 'problem', id: 'container-with-most-water', title: 'Container With Most Water', summary: 'Converging pointers: move the shorter wall inward.' },
      { type: 'problem', id: 'valid-palindrome', title: 'Valid Palindrome', summary: 'Same converging pattern on characters with cleanup first.' },
      { type: 'problem', id: 'longest-substring-without-repeating', title: 'Longest Substring Without Repeating Characters', summary: 'From fixed ends to a sliding window with a membership set.' },
      { type: 'problem', id: 'merge-intervals', title: 'Merge Intervals', summary: 'Sort by start, then sweep and merge overlaps in one pass.' },
      { type: 'problem', id: 'spiral-matrix', title: 'Spiral Matrix', summary: 'Boundary shrinking: peel the matrix layer by layer.' },
      { type: 'problem', id: 'decode-string', title: 'Decode String', summary: 'Stack unwinding for nested repeats.' },
      { type: 'problem', id: 'valid-parentheses', title: 'Valid Parentheses', summary: 'Same stack discipline applied to bracket matching.' },
      { type: 'problem', id: 'reverse-linked-list', title: 'Reverse Linked List', summary: 'Pointer rewiring fundamentals.' },
      { type: 'problem', id: 'middle-of-the-linked-list', title: 'Middle of the Linked List', summary: 'Fast and slow pointers locate the middle in one pass.' },
      { type: 'problem', id: 'linked-list-cycle', title: 'Linked List Cycle', summary: 'Same two-speed walk proves a cycle exists.' },
      { type: 'problem', id: 'merge-two-sorted-lists', title: 'Merge Two Sorted Lists', summary: 'Two-pointer merge across two sorted inputs.' },
      { type: 'problem', id: 'add-two-numbers', title: 'Add Two Numbers', summary: 'Digit-by-digit addition with carry, reusing the merge walk.' },
      { type: 'problem', id: 'maximum-depth-of-binary-tree', title: 'Maximum Depth of Binary Tree', summary: 'Postorder depth recursion on level-order arrays.' },
      { type: 'problem', id: 'diameter-of-binary-tree', title: 'Diameter of Binary Tree', summary: 'Track the best through-path while returning heights.' },
      { type: 'problem', id: 'invert-binary-tree', title: 'Invert Binary Tree', summary: 'Swap children level by level.' },
      { type: 'problem', id: 'validate-binary-search-tree', title: 'Validate Binary Search Tree', summary: 'Range bounds passed down instead of local checks.' },
      { type: 'problem', id: 'kth-smallest-element-in-a-bst', title: 'Kth Smallest Element in a BST', summary: 'Inorder traversal yields sorted order; pick index k minus one.' },
      { type: 'problem', id: 'lowest-common-ancestor-of-a-binary-tree', title: 'Lowest Common Ancestor of a Binary Tree', summary: 'Compare root-to-node paths; last shared value wins.' },
      { type: 'problem', id: 'longest-common-prefix', title: 'Longest Common Prefix', summary: 'Character-column scan, the trie idea without the structure.' },
      { type: 'problem', id: 'find-if-path-exists-in-graph', title: 'Find if Path Exists in Graph', summary: 'BFS connectivity on an adjacency list.' },
      { type: 'problem', id: 'number-of-islands', title: 'Number of Islands', summary: 'Flood fill each landmass once via grid DFS.' },
      { type: 'problem', id: 'flood-fill', title: 'Flood Fill', summary: 'Same fill from a given start pixel and color.' },
      { type: 'problem', id: 'course-schedule', title: 'Course Schedule', summary: 'Cycle detection decides whether a topological order exists.' },
      { type: 'problem', id: 'course-schedule-ii', title: 'Course Schedule II', summary: 'Emit the actual Kahn order instead of just a yes/no.' },
      { type: 'problem', id: 'climbing-stairs', title: 'Climbing Stairs', summary: 'Fibonacci recurrence: ways(n) equals ways(n-1) plus ways(n-2).' },
      { type: 'problem', id: 'house-robber', title: 'House Robber', summary: 'Include-or-skip choice at each index extends the recurrence.' },
      { type: 'problem', id: 'maximum-subarray', title: 'Maximum Subarray', summary: 'Kadane: extend or restart the running sum at each index.' },
      { type: 'problem', id: 'coin-change', title: 'Coin Change', summary: 'Unbounded knapsack tabulation over amounts.' },
      { type: 'problem', id: 'longest-increasing-subsequence', title: 'Longest Increasing Subsequence', summary: 'Quadratic DP over earlier smaller elements; patience piles reach n log n.' },
      { type: 'problem', id: 'unique-paths', title: 'Unique Paths', summary: '2D grid DP: each cell sums its top and left neighbors.' },
      { type: 'problem', id: 'roman-to-integer', title: 'Roman to Integer', summary: 'Subtractive peek: subtract when a smaller value precedes a larger one.' },
      { type: 'quiz', id: 'dynamic-programming', title: 'Targeted DP check', summary: 'Mixed recurrence questions over the DP block above.' },
      { type: 'quiz', id: 'mixed', title: 'Targeted placement mock', summary: 'Timed mixed assessment across the whole targeted sequence.' },
    ]
  },
  {
    id: 'mastery',
    title: 'Mastery',
    blurb: 'Everything verified: all coding problems sequenced by category plus the full quiz bank.',
    icon: 'Network',
    steps: [
      { type: 'visualizer', id: 'array', title: 'Arrays', summary: 'Indexed storage and two-pointer scans.', readingLinks: ['https://en.wikipedia.org/wiki/Array_data_structure'] },
      { type: 'visualizer', id: 'sorting', title: 'Sorting', summary: 'Comparison sorts and partitioning.', readingLinks: ['https://en.wikipedia.org/wiki/Sorting_algorithm'] },
      { type: 'visualizer', id: 'searching', title: 'Searching', summary: 'Binary search invariants.', readingLinks: ['https://en.wikipedia.org/wiki/Binary_search'] },
      { type: 'visualizer', id: 'linked-list', title: 'Linked lists', summary: 'Pointer rewiring and reversal.', readingLinks: ['https://en.wikipedia.org/wiki/Linked_list'] },
      { type: 'visualizer', id: 'stack', title: 'Stacks', summary: 'LIFO matching and evaluation.', readingLinks: ['https://en.wikipedia.org/wiki/Stack_(abstract_data_type)'] },
      { type: 'visualizer', id: 'queue', title: 'Queues', summary: 'FIFO buffers and BFS frontiers.', readingLinks: ['https://en.wikipedia.org/wiki/Queue_(abstract_data_type)'] },
      { type: 'visualizer', id: 'binary-tree', title: 'Binary trees', summary: 'Traversals and structural recursion.', readingLinks: ['https://en.wikipedia.org/wiki/Tree_traversal'] },
      { type: 'visualizer', id: 'bst', title: 'Binary search trees', summary: 'Ordered inserts, search, and delete.', readingLinks: ['https://en.wikipedia.org/wiki/Binary_search_tree'] },
      { type: 'visualizer', id: 'heap', title: 'Heaps', summary: 'Priority queues with sift operations.', readingLinks: ['https://en.wikipedia.org/wiki/Heap_(data_structure)'] },
      { type: 'visualizer', id: 'hashmap', title: 'Hash maps', summary: 'Buckets, hashing, and collision chains.', readingLinks: ['https://en.wikipedia.org/wiki/Hash_table'] },
      { type: 'visualizer', id: 'graph', title: 'Graphs', summary: 'BFS and DFS exploration.', readingLinks: ['https://en.wikipedia.org/wiki/Graph_traversal'] },
      { type: 'visualizer', id: 'recursion-tree', title: 'Recursion', summary: 'Call trees and overlapping subproblems.', readingLinks: ['https://en.wikipedia.org/wiki/Recursion_(computer_science)'] },
      { type: 'problem', id: 'two-sum', title: 'Two Sum', summary: 'Full arrays-hashing chain in category order.' },
      { type: 'problem', id: 'contains-duplicate', title: 'Contains Duplicate', summary: 'Full arrays-hashing chain in category order.' },
      { type: 'problem', id: 'valid-anagram', title: 'Valid Anagram', summary: 'Full arrays-hashing chain in category order.' },
      { type: 'problem', id: 'product-of-array-except-self', title: 'Product of Array Except Self', summary: 'Full arrays-hashing chain in category order.' },
      { type: 'problem', id: 'subarray-sum-equals-k', title: 'Subarray Sum Equals K', summary: 'Full arrays-hashing chain in category order.' },
      { type: 'problem', id: 'best-time-to-buy-and-sell-stock', title: 'Best Time to Buy and Sell Stock', summary: 'Full arrays-hashing chain in category order.' },
      { type: 'problem', id: 'longest-consecutive-sequence', title: 'Longest Consecutive Sequence', summary: 'Full arrays-hashing chain in category order.' },
      { type: 'problem', id: 'container-with-most-water', title: 'Container With Most Water', summary: 'Full two-pointers chain in category order.' },
      { type: 'problem', id: 'valid-palindrome', title: 'Valid Palindrome', summary: 'Full two-pointers chain in category order.' },
      { type: 'problem', id: 'merge-two-sorted-lists', title: 'Merge Two Sorted Lists', summary: 'Full two-pointers chain in category order.' },
      { type: 'problem', id: 'remove-nth-node-from-end', title: 'Remove Nth Node From End', summary: 'Full two-pointers chain in category order.' },
      { type: 'problem', id: 'longest-substring-without-repeating', title: 'Longest Substring Without Repeating Characters', summary: 'Sliding-windows chain in category order.' },
      { type: 'problem', id: 'decode-string', title: 'Decode String', summary: 'Full stack chain in category order.' },
      { type: 'problem', id: 'valid-parentheses', title: 'Valid Parentheses', summary: 'Full stack chain in category order.' },
      { type: 'problem', id: 'reverse-linked-list', title: 'Reverse Linked List', summary: 'Full linked-lists chain in category order.' },
      { type: 'problem', id: 'middle-of-the-linked-list', title: 'Middle of the Linked List', summary: 'Full linked-lists chain in category order.' },
      { type: 'problem', id: 'linked-list-cycle', title: 'Linked List Cycle', summary: 'Full linked-lists chain in category order.' },
      { type: 'problem', id: 'palindrome-linked-list', title: 'Palindrome Linked List', summary: 'Full linked-lists chain in category order.' },
      { type: 'problem', id: 'add-two-numbers', title: 'Add Two Numbers', summary: 'Full linked-lists chain in category order.' },
      { type: 'problem', id: 'maximum-depth-of-binary-tree', title: 'Maximum Depth of Binary Tree', summary: 'Full trees chain in category order.' },
      { type: 'problem', id: 'same-tree', title: 'Same Tree', summary: 'Full trees chain in category order.' },
      { type: 'problem', id: 'invert-binary-tree', title: 'Invert Binary Tree', summary: 'Full trees chain in category order.' },
      { type: 'problem', id: 'diameter-of-binary-tree', title: 'Diameter of Binary Tree', summary: 'Full trees chain in category order.' },
      { type: 'problem', id: 'validate-binary-search-tree', title: 'Validate Binary Search Tree', summary: 'Full trees chain in category order.' },
      { type: 'problem', id: 'kth-smallest-element-in-a-bst', title: 'Kth Smallest Element in a BST', summary: 'Full trees chain in category order.' },
      { type: 'problem', id: 'lowest-common-ancestor-of-a-binary-tree', title: 'Lowest Common Ancestor of a Binary Tree', summary: 'Full trees chain in category order.' },
      { type: 'problem', id: 'longest-common-prefix', title: 'Longest Common Prefix', summary: 'Trie-adjacent prefix scan.' },
      { type: 'problem', id: 'merge-intervals', title: 'Merge Intervals', summary: 'Intervals chain in category order.' },
      { type: 'problem', id: 'roman-to-integer', title: 'Roman to Integer', summary: 'Math chain in category order.' },
      { type: 'problem', id: 'spiral-matrix', title: 'Spiral Matrix', summary: 'Math chain in category order.' },
      { type: 'problem', id: 'find-the-town-judge', title: 'Find the Town Judge', summary: 'Full graphs chain in category order.' },
      { type: 'problem', id: 'find-if-path-exists-in-graph', title: 'Find if Path Exists in Graph', summary: 'Full graphs chain in category order.' },
      { type: 'problem', id: 'number-of-islands', title: 'Number of Islands', summary: 'Full graphs chain in category order.' },
      { type: 'problem', id: 'flood-fill', title: 'Flood Fill', summary: 'Full graphs chain in category order.' },
      { type: 'problem', id: 'course-schedule', title: 'Course Schedule', summary: 'Full graphs chain in category order.' },
      { type: 'problem', id: 'course-schedule-ii', title: 'Course Schedule II', summary: 'Full graphs chain in category order.' },
      { type: 'problem', id: 'climbing-stairs', title: 'Climbing Stairs', summary: 'Full dynamic-programming chain in category order.' },
      { type: 'problem', id: 'house-robber', title: 'House Robber', summary: 'Full dynamic-programming chain in category order.' },
      { type: 'problem', id: 'maximum-subarray', title: 'Maximum Subarray', summary: 'Full dynamic-programming chain in category order.' },
      { type: 'problem', id: 'coin-change', title: 'Coin Change', summary: 'Full dynamic-programming chain in category order.' },
      { type: 'problem', id: 'longest-increasing-subsequence', title: 'Longest Increasing Subsequence', summary: 'Full dynamic-programming chain in category order.' },
      { type: 'problem', id: 'unique-paths', title: 'Unique Paths', summary: 'Full dynamic-programming chain in category order.' },
      { type: 'quiz', id: 'arrays-hashing', title: 'Arrays & hashing check', summary: 'Quiz checkpoint after the arrays block.' },
      { type: 'quiz', id: 'trees', title: 'Trees check', summary: 'Quiz checkpoint after the trees block.' },
      { type: 'quiz', id: 'graphs', title: 'Graphs check', summary: 'Quiz checkpoint after the graphs block.' },
      { type: 'quiz', id: 'dynamic-programming', title: 'DP check', summary: 'Quiz checkpoint after the DP block.' },
      { type: 'quiz', id: 'mixed', title: 'Mastery mock', summary: 'Timed mixed assessment across everything above.' },
    ]
  },
];
