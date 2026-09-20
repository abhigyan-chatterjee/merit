export type StepType = 'visualizer' | 'problem' | 'quiz' | 'mock';

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
      { type: 'visualizer', id: 'array', title: 'Arrays: indexed storage', summary: 'Arrays store items contiguously for O(1) indexed access. Inserting or deleting in the middle shifts all later items, costing O(n).', readingLinks: ['https://en.wikipedia.org/wiki/Array_data_structure', 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array'] },
      { type: 'problem', id: 'two-sum', title: 'Two Sum', summary: 'First hashing pattern: trade one pass plus a lookup table for the naive pair check.' },
      { type: 'problem', id: 'contains-duplicate', title: 'Contains Duplicate', summary: 'Same set-membership idea as Two Sum, reduced to a yes/no duplicate check.' },
      { type: 'visualizer', id: 'sorting', title: 'Sorting basics', summary: 'Sorting arranges data so binary search and two-pointer scans work. Watch how many comparisons each method needs.', readingLinks: ['https://en.wikipedia.org/wiki/Sorting_algorithm', 'https://visualgo.net/en/sorting'] },
      { type: 'visualizer', id: 'searching', title: 'Binary search step-through', summary: 'On sorted data, halving the search range each step finds any item in O(log n).', readingLinks: ['https://en.wikipedia.org/wiki/Binary_search'] },
      { type: 'problem', id: 'binary-search', title: 'Binary Search', summary: 'Classic halving invariant on a sorted array: test midpoint, discard half in O(log n).', readingLinks: ['https://en.wikipedia.org/wiki/Binary_search'] },
      { type: 'problem', id: 'sort-an-array', title: 'Sort an Array', summary: 'Reinforce sorting after binary search: order values in place with a predictable comparison strategy.', readingLinks: ['https://en.wikipedia.org/wiki/Sorting_algorithm'] },
      { type: 'problem', id: 'valid-palindrome', title: 'Valid Palindrome', summary: 'Converging two pointers: compare the ends and walk inward.' },
      { type: 'problem', id: 'move-zeroes', title: 'Move Zeroes', summary: 'Two pointers in-place: slow write pointer tracks zeros while fast pointer scans.', readingLinks: ['https://en.wikipedia.org/wiki/In-place_algorithm'] },
      { type: 'problem', id: 'longest-substring-without-repeating', title: 'Longest Substring Without Repeating Characters', summary: 'Variable sliding window: stretch the right edge, shrink from the left on duplicates.' },
      { type: 'visualizer', id: 'linked-list', title: 'Singly linked list', summary: 'Nodes linked by pointers: O(1) inserts at a known spot, O(n) access by index.', readingLinks: ['https://en.wikipedia.org/wiki/Linked_list'] },
      { type: 'problem', id: 'reverse-linked-list', title: 'Reverse Linked List', summary: 'Rewire each node\'s pointer to its predecessor in one pass.' },
      { type: 'problem', id: 'linked-list-cycle', title: 'Linked List Cycle', summary: 'Fast-slow pointer chase: detect cycles in O(n) time and O(1) space.', readingLinks: ['https://en.wikipedia.org/wiki/Cycle_detection'] },
      { type: 'visualizer', id: 'stack', title: 'LIFO stack', summary: 'Last-in first-out: pushes and pops cost O(1) and power bracket matching and undo histories.', readingLinks: ['https://en.wikipedia.org/wiki/Stack_(abstract_data_type)'] },
      { type: 'problem', id: 'valid-parentheses', title: 'Valid Parentheses', summary: 'Push opening brackets, match closers off the top of the stack.' },
      { type: 'visualizer', id: 'hashmap', title: 'Hash map buckets', summary: 'Keys hash to buckets for average O(1) put and get; collisions chain inside a bucket.', readingLinks: ['https://en.wikipedia.org/wiki/Hash_table'] },
      { type: 'problem', id: 'valid-anagram', title: 'Valid Anagram', summary: 'Count characters with a frequency map, then compare the counts.' },
      { type: 'visualizer', id: 'binary-tree', title: 'Tree traversals', summary: 'Inorder, preorder, and postorder each visit every node once; order decides what problems they fit.', readingLinks: ['https://en.wikipedia.org/wiki/Tree_traversal'] },
      { type: 'problem', id: 'maximum-depth-of-binary-tree', title: 'Maximum Depth of Binary Tree', summary: 'Postorder depth: one plus the deeper of the two child depths.' },
      { type: 'problem', id: 'same-tree', title: 'Same Tree', summary: 'Simultaneous recursive walk: structural and value equality across two trees.', readingLinks: ['https://en.wikipedia.org/wiki/Tree_traversal'] },
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
      { type: 'problem', id: 'gas-station', title: 'Gas Station', summary: 'Greedy surplus tracking finds the unique start that can complete the circuit.' },
      { type: 'problem', id: 'jump-game-ii', title: 'Jump Game II', summary: 'Greedy range expansion counts the minimum jumps needed to reach the end.' },
      { type: 'problem', id: 'valid-palindrome', title: 'Valid Palindrome', summary: 'Same converging pattern on characters with cleanup first.' },
      { type: 'problem', id: 'three-sum', title: 'Three Sum', summary: 'Sort and fix one element, then converge two pointers for the remaining sum.', readingLinks: ['https://en.wikipedia.org/wiki/3SUM'] },
      { type: 'problem', id: 'longest-substring-without-repeating', title: 'Longest Substring Without Repeating Characters', summary: 'From fixed ends to a sliding window with a membership set.' },
      { type: 'problem', id: 'merge-intervals', title: 'Merge Intervals', summary: 'Sort by start, then sweep and merge overlaps in one pass.' },
      { type: 'problem', id: 'insert-interval', title: 'Insert Interval', summary: 'Append non-overlapping left intervals, merge the overlapping zone, append rest.', readingLinks: ['https://en.wikipedia.org/wiki/Interval_tree'] },
      { type: 'problem', id: 'spiral-matrix', title: 'Spiral Matrix', summary: 'Four boundaries moving inward as each edge is traversed.' },
      { type: 'problem', id: 'decode-string', title: 'Decode String', summary: 'Nested repeats handled with a count stack and a string stack.' },
      { type: 'problem', id: 'valid-parentheses', title: 'Valid Parentheses', summary: 'Classic bracket matcher: the foundational stack problem.' },
      { type: 'problem', id: 'daily-temperatures', title: 'Daily Temperatures', summary: 'Monotonic decreasing stack of indices: pop when finding a warmer day.', readingLinks: ['https://en.wikipedia.org/wiki/Stack_(abstract_data_type)'] },
      { type: 'problem', id: 'reverse-linked-list', title: 'Reverse Linked List', summary: 'Start of the linked-list chain: pointer rewiring in place.' },
      { type: 'problem', id: 'middle-of-the-linked-list', title: 'Middle of the Linked List', summary: 'Fast-and-slow pointers: 2x step finds the midpoint in one pass.' },
      { type: 'problem', id: 'linked-list-cycle', title: 'Linked List Cycle', summary: 'Floyd\'s cycle detection: same fast-slow pattern, now looking for collision.' },
      { type: 'problem', id: 'merge-two-sorted-lists', title: 'Merge Two Sorted Lists', summary: 'Splice two ordered lists with a dummy head.' },
      { type: 'problem', id: 'add-two-numbers', title: 'Add Two Numbers', summary: 'Digit-by-digit addition with carry across two lists.' },
      { type: 'problem', id: 'maximum-depth-of-binary-tree', title: 'Maximum Depth of Binary Tree', summary: 'Start of the tree chain: simplest recursive depth.' },
      { type: 'problem', id: 'diameter-of-binary-tree', title: 'Diameter of Binary Tree', summary: 'Bottom-up tree height where longest path through each node is checked.' },
      { type: 'problem', id: 'invert-binary-tree', title: 'Invert Binary Tree', summary: 'Swap left and right subtrees recursively.' },
      { type: 'problem', id: 'validate-binary-search-tree', title: 'Validate Binary Search Tree', summary: 'Pass valid ranges down the recursion: left < node < right.' },
      { type: 'problem', id: 'kth-smallest-element-in-a-bst', title: 'Kth Smallest Element in a BST', summary: 'Inorder traversal visits nodes in ascending order; stop at k.' },
      { type: 'problem', id: 'lowest-common-ancestor-of-a-binary-tree', title: 'Lowest Common Ancestor of a Binary Tree', summary: 'Split point in the tree where targets fall in different subtrees.' },
      { type: 'problem', id: 'search-in-rotated-sorted-array', title: 'Search in Rotated Sorted Array', summary: 'Determine which half is sorted to preserve O(log n) elimination invariant.', readingLinks: ['https://en.wikipedia.org/wiki/Binary_search'] },
      { type: 'problem', id: 'kth-largest-element-in-an-array', title: 'Kth Largest Element in an Array', summary: 'Maintain a min-heap of size k to find the kth largest element in O(n log k).', readingLinks: ['https://en.wikipedia.org/wiki/Heap_(data_structure)'] },
      { type: 'problem', id: 'letter-combinations-of-a-phone-number', title: 'Letter Combinations of a Phone Number', summary: 'Backtrack through each digit\'s choices, undoing a choice before trying the next.' },
      { type: 'problem', id: 'find-if-path-exists-in-graph', title: 'Find if Path Exists in Graph', summary: 'Start of graph chain: simple BFS or DFS reachability check.' },
      { type: 'problem', id: 'number-of-islands', title: 'Number of Islands', summary: 'Grid DFS/BFS: flood-fill visited lands to count connected components.' },
      { type: 'problem', id: 'word-search', title: 'Word Search', summary: 'Backtrack through adjacent cells while marking and restoring the current path.' },
      { type: 'problem', id: 'course-schedule', title: 'Course Schedule', summary: 'Topological sort: detect cycles in prerequisites using Kahn\'s or DFS 3-color.' },
      { type: 'problem', id: 'course-schedule-ii', title: 'Course Schedule II', summary: 'Return the actual valid ordering, not just cycle detection.' },
      { type: 'problem', id: 'rotting-oranges', title: 'Rotting Oranges', summary: 'Multi-source BFS: enqueue all rotten oranges initially and track elapsed time.', readingLinks: ['https://en.wikipedia.org/wiki/Breadth-first_search'] },
      { type: 'problem', id: 'climbing-stairs', title: 'Climbing Stairs', summary: 'Start of DP chain: Fibonacci recurrence with two variables.' },
      { type: 'problem', id: 'house-robber', title: 'House Robber', summary: 'Adjacent choice: max(rob current + prev2, skip current).' },
      { type: 'problem', id: 'maximum-subarray', title: 'Maximum Subarray', summary: 'Kadane\'s algorithm: extend current subarray or start fresh at each index.' },
      { type: 'problem', id: 'coin-change', title: 'Coin Change', summary: 'Unbounded knapsack: min coins to make amount across all denominations.' },
      { type: 'problem', id: 'longest-increasing-subsequence', title: 'Longest Increasing Subsequence', summary: 'Quadratic DP over earlier smaller elements; patience piles reach n log n.' },
      { type: 'problem', id: 'unique-paths', title: 'Unique Paths', summary: '2D grid DP: paths to (r, c) = paths from top + paths from left.' },
      { type: 'problem', id: 'word-break', title: 'Word Break', summary: 'Boolean DP where dp[i] is true if a prefix s[0..i] can be segmented using words.', readingLinks: ['https://en.wikipedia.org/wiki/Dynamic_programming'] },
      { type: 'problem', id: 'majority-element', title: 'Majority Element', summary: 'Sorting or voting reveals the value that occurs more than half the time.' },
      { type: 'problem', id: 'subsets', title: 'Subsets', summary: 'Bit choices or backtracking enumerate every subset without repeating a combination.', readingLinks: ['https://en.wikipedia.org/wiki/Bitwise_operation'] },
      { type: 'quiz', id: 'dynamic-programming', title: 'Targeted DP check', summary: 'Recurrence relations, memoization bounds, and subproblem structure.' },
      { type: 'mock', id: 'mixed', title: 'Targeted placement mock', summary: 'Timed mixed assessment across the whole targeted sequence.' },
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
      { type: 'visualizer', id: 'recursion-tree', title: 'Recursion', summary: 'Call-tree unrolling and memo tables.', readingLinks: ['https://en.wikipedia.org/wiki/Recursion_(computer_science)'] },
      { type: 'problem', id: 'two-sum', title: 'Two Sum', summary: 'Full arrays-hashing chain in category order.' },
      { type: 'problem', id: 'contains-duplicate', title: 'Contains Duplicate', summary: 'Full arrays-hashing chain in category order.' },
      { type: 'problem', id: 'valid-anagram', title: 'Valid Anagram', summary: 'Full arrays-hashing chain in category order.' },
      { type: 'problem', id: 'product-of-array-except-self', title: 'Product of Array Except Self', summary: 'Full arrays-hashing chain in category order.' },
      { type: 'problem', id: 'subarray-sum-equals-k', title: 'Subarray Sum Equals K', summary: 'Full arrays-hashing chain in category order.' },
      { type: 'problem', id: 'best-time-to-buy-and-sell-stock', title: 'Best Time to Buy and Sell Stock', summary: 'Full arrays-hashing chain in category order.' },
      { type: 'problem', id: 'longest-consecutive-sequence', title: 'Longest Consecutive Sequence', summary: 'Full arrays-hashing chain in category order.' },
      { type: 'problem', id: 'first-missing-positive', title: 'First Missing Positive', summary: 'In-place cyclic sort: place each value x at index x-1 to solve in O(n) and O(1) space.', readingLinks: ['https://en.wikipedia.org/wiki/Cycle_sort'] },
      { type: 'problem', id: 'container-with-most-water', title: 'Container With Most Water', summary: 'Full two-pointers chain in category order.' },
      { type: 'problem', id: 'valid-palindrome', title: 'Valid Palindrome', summary: 'Full two-pointers chain in category order.' },
      { type: 'problem', id: 'merge-two-sorted-lists', title: 'Merge Two Sorted Lists', summary: 'Full two-pointers chain in category order.' },
      { type: 'problem', id: 'remove-nth-node-from-end', title: 'Remove Nth Node From End', summary: 'Full two-pointers chain in category order.' },
      { type: 'problem', id: 'trapping-rain-water', title: 'Trapping Rain Water', summary: 'Two pointers converge while tracking max left and right walls to accumulate trapped water.', readingLinks: ['https://en.wikipedia.org/wiki/In-place_algorithm'] },
      { type: 'problem', id: 'longest-substring-without-repeating', title: 'Longest Substring Without Repeating Characters', summary: 'Full sliding-windows chain in category order.' },
      { type: 'problem', id: 'sliding-window-maximum', title: 'Sliding Window Maximum', summary: 'Monotonic decreasing deque keeps candidate maxima at the front over each window shift.', readingLinks: ['https://en.wikipedia.org/wiki/Double-ended_queue'] },
      { type: 'problem', id: 'decode-string', title: 'Decode String', summary: 'Full stack chain in category order.' },
      { type: 'problem', id: 'valid-parentheses', title: 'Valid Parentheses', summary: 'Full stack chain in category order.' },
      { type: 'problem', id: 'largest-rectangle-in-histogram', title: 'Widest Bar Rectangle', summary: 'Monotonic stack finds nearest smaller bars left and right to compute maximal rectangle.', readingLinks: ['https://en.wikipedia.org/wiki/Stack_(abstract_data_type)'] },
      { type: 'problem', id: 'reverse-linked-list', title: 'Reverse Linked List', summary: 'Full linked-lists chain in category order.' },
      { type: 'problem', id: 'middle-of-the-linked-list', title: 'Middle of the Linked List', summary: 'Full linked-lists chain in category order.' },
      { type: 'problem', id: 'linked-list-cycle', title: 'Linked List Cycle', summary: 'Full linked-lists chain in category order.' },
      { type: 'problem', id: 'palindrome-linked-list', title: 'Palindrome Linked List', summary: 'Full linked-lists chain in category order.' },
      { type: 'problem', id: 'add-two-numbers', title: 'Add Two Numbers', summary: 'Full linked-lists chain in category order.' },
      { type: 'problem', id: 'merge-k-sorted-lists', title: 'Merge k Sorted Lists', summary: 'Min-heap of list heads extracts the minimum node in O(log k) per element across k lists.', readingLinks: ['https://en.wikipedia.org/wiki/K-way_merge_algorithm'] },
      { type: 'problem', id: 'reverse-nodes-in-k-group', title: 'Reverse Nodes in k-Group', summary: 'Count k nodes, reverse sub-chain in-place, and iteratively link remainder.', readingLinks: ['https://en.wikipedia.org/wiki/Linked_list'] },
      { type: 'problem', id: 'maximum-depth-of-binary-tree', title: 'Maximum Depth of Binary Tree', summary: 'Full trees chain in category order.' },
      { type: 'problem', id: 'combination-sum', title: 'Combination Sum', summary: 'Backtracking chooses, reuses, and undoes candidates while pruning sums over the target.', readingLinks: ['https://en.wikipedia.org/wiki/Backtracking'] },
      { type: 'problem', id: 'invert-binary-tree', title: 'Invert Binary Tree', summary: 'Full trees chain in category order.' },
      { type: 'problem', id: 'diameter-of-binary-tree', title: 'Diameter of Binary Tree', summary: 'Full trees chain in category order.' },
      { type: 'problem', id: 'validate-binary-search-tree', title: 'Validate Binary Search Tree', summary: 'Full trees chain in category order.' },
      { type: 'problem', id: 'kth-smallest-element-in-a-bst', title: 'Kth Smallest Element in a BST', summary: 'Full trees chain in category order.' },
      { type: 'problem', id: 'lowest-common-ancestor-of-a-binary-tree', title: 'Lowest Common Ancestor of a Binary Tree', summary: 'Full trees chain in category order.' },
      { type: 'problem', id: 'binary-tree-maximum-path-sum', title: 'Best Downward Chain', summary: 'Postorder traversal: combine left and right branch gains at each node to find maximum path.', readingLinks: ['https://en.wikipedia.org/wiki/Tree_traversal'] },
      { type: 'problem', id: 'letter-combinations-of-a-phone-number', title: 'Letter Combinations of a Phone Number', summary: 'Backtracking builds one valid digit-to-letter choice at a time.' },
      { type: 'problem', id: 'merge-intervals', title: 'Merge Intervals', summary: 'Full intervals chain in category order.' },
      { type: 'problem', id: 'insert-interval', title: 'Insert Interval', summary: 'Merge the overlapping zone into a sorted interval list after Merge Intervals.' },
      { type: 'problem', id: 'subsets', title: 'Subsets', summary: 'Bit choices or backtracking enumerate every subset without duplicate output.' },
      { type: 'problem', id: 'majority-element', title: 'Majority Element', summary: 'Sorting or voting identifies the element appearing more than half the time.' },
      { type: 'problem', id: 'gas-station', title: 'Gas Station', summary: 'Greedy surplus tracking finds the only viable circuit start.' },
      { type: 'problem', id: 'number-of-islands', title: 'Number of Islands', summary: 'Full graphs chain in category order.' },
      { type: 'problem', id: 'jump-game-ii', title: 'Jump Game II', summary: 'Greedy range expansion counts the minimum jumps to reach the end.' },
      { type: 'problem', id: 'course-schedule', title: 'Course Schedule', summary: 'Full graphs chain in category order.' },
      { type: 'problem', id: 'course-schedule-ii', title: 'Course Schedule II', summary: 'Full graphs chain in category order.' },
      { type: 'problem', id: 'word-ladder', title: 'Word Ladder', summary: 'Shortest transformation sequence via BFS over one-letter word substitutions.', readingLinks: ['https://en.wikipedia.org/wiki/Breadth-first_search'] },
      { type: 'problem', id: 'climbing-stairs', title: 'Climbing Stairs', summary: 'Full dynamic-programming chain in category order.' },
      { type: 'problem', id: 'house-robber', title: 'House Robber', summary: 'Full dynamic-programming chain in category order.' },
      { type: 'problem', id: 'maximum-subarray', title: 'Maximum Subarray', summary: 'Full dynamic-programming chain in category order.' },
      { type: 'problem', id: 'coin-change', title: 'Coin Change', summary: 'Full dynamic-programming chain in category order.' },
      { type: 'problem', id: 'longest-increasing-subsequence', title: 'Longest Increasing Subsequence', summary: 'Full dynamic-programming chain in category order.' },
      { type: 'problem', id: 'unique-paths', title: 'Unique Paths', summary: 'Full dynamic-programming chain in category order.' },
      { type: 'problem', id: 'edit-distance', title: 'Edit Distance', summary: '2D DP grid calculates minimum insertions, deletions, and replacements between two strings.', readingLinks: ['https://en.wikipedia.org/wiki/Levenshtein_distance'] },
      { type: 'problem', id: 'find-words-on-board', title: 'Word Search II', summary: 'Trie-guided backtracking finds every dictionary word on the board.', readingLinks: ['https://en.wikipedia.org/wiki/Backtracking'] },
      { type: 'quiz', id: 'arrays-hashing', title: 'Arrays & hashing check', summary: 'Full category quiz for arrays and hashing.' },
      { type: 'quiz', id: 'trees', title: 'Trees check', summary: 'Full category quiz for binary trees and BSTs.' },
      { type: 'quiz', id: 'graphs', title: 'Graphs check', summary: 'Full category quiz for graph algorithms.' },
      { type: 'quiz', id: 'dynamic-programming', title: 'DP check', summary: 'Full category quiz for dynamic programming.' },
      { type: 'mock', id: 'mixed', title: 'Mastery mock', summary: 'Full platform-level mock assessment across all topics.' },
    ]
  },
];
