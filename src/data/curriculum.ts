export interface VisualizerItem {
  id: string;
  title: string;
  category: 'Linear' | 'Trees' | 'Graphs' | 'Algorithms' | 'Hashing';
  description: string;
  timeComplexity: {
    best: string;
    avg: string;
    worst: string;
  };
  spaceComplexity: string;
  keyOperations: string[];
}

export interface TopicItem {
  slug: string;
  title: string;
  description: string;
  problemCount: number;
  iconName: string;
}

export const TOPICS: TopicItem[] = [
  {
    slug: 'arrays',
    title: 'Arrays & Two Pointers',
    description: 'Contiguous memory indexing, prefix sums, two pointers, and sliding windows.',
    problemCount: 5,
    iconName: 'LayoutGrid'
  },
  {
    slug: 'strings',
    title: 'Strings & Sliding Window',
    description: 'Character hashing, substrings, palindrome checks, and anagram invariants.',
    problemCount: 5,
    iconName: 'Type'
  },
  {
    slug: 'linked-list',
    title: 'Linked Lists',
    description: 'Pointer rewiring, fast-slow cycle detection, and in-place reversal.',
    problemCount: 5,
    iconName: 'GitCommit'
  },
  {
    slug: 'trees',
    title: 'Binary Trees & BST',
    description: 'Recursive DFS traversals, level-order BFS, and binary search tree invariants.',
    problemCount: 5,
    iconName: 'Network'
  },
  {
    slug: 'graphs',
    title: 'Graphs & Traversals',
    description: 'Adjacency lists, BFS shortest path, DFS connected components, and topological sort.',
    problemCount: 5,
    iconName: 'Share2'
  },
  {
    slug: 'dp',
    title: 'Dynamic Programming',
    description: 'Overlapping subproblems, optimal substructure, 1D/2D memoization & tabulation.',
    problemCount: 5,
    iconName: 'Cpu'
  }
];

export const VISUALIZERS: VisualizerItem[] = [
  {
    id: 'sorting',
    title: 'Sorting Algorithms',
    category: 'Algorithms',
    description: 'Compare Bubble, Selection, Insertion, Merge, and Quick Sort with live swap & comparison counters.',
    timeComplexity: { best: 'O(n log n)', avg: 'O(n log n)', worst: 'O(n²)' },
    spaceComplexity: 'O(1) - O(n)',
    keyOperations: ['Bubble Sort', 'Selection Sort', 'Insertion Sort', 'Merge Sort', 'Quick Sort']
  },
  {
    id: 'array',
    title: 'Static & Dynamic Array',
    category: 'Linear',
    description: 'Index lookup O(1), insertion shifts, deletion shifts, and two-pointer scan visualization.',
    timeComplexity: { best: 'O(1)', avg: 'O(n)', worst: 'O(n)' },
    spaceComplexity: 'O(n)',
    keyOperations: ['Access [i]', 'Insert at Index', 'Delete at Index', 'Two-Pointer Scan']
  },
  {
    id: 'linked-list',
    title: 'Singly Linked List',
    category: 'Linear',
    description: 'Step-by-step pointer rewiring for head/tail insertion, deletion, and iterative reversal.',
    timeComplexity: { best: 'O(1)', avg: 'O(n)', worst: 'O(n)' },
    spaceComplexity: 'O(n)',
    keyOperations: ['Insert Head', 'Insert Tail', 'Delete Node', 'Reverse List']
  },
  {
    id: 'stack',
    title: 'LIFO Stack',
    category: 'Linear',
    description: 'Last-In First-Out call stack operations with Push, Pop, and Peek pointer animation.',
    timeComplexity: { best: 'O(1)', avg: 'O(1)', worst: 'O(1)' },
    spaceComplexity: 'O(n)',
    keyOperations: ['Push(val)', 'Pop()', 'Peek()', 'Clear()']
  },
  {
    id: 'queue',
    title: 'FIFO Queue',
    category: 'Linear',
    description: 'First-In First-Out circular buffer queue with Head and Tail pointers.',
    timeComplexity: { best: 'O(1)', avg: 'O(1)', worst: 'O(1)' },
    spaceComplexity: 'O(n)',
    keyOperations: ['Enqueue(val)', 'Dequeue()', 'Front()', 'Clear()']
  },
  {
    id: 'binary-tree',
    title: 'Binary Tree Traversals',
    category: 'Trees',
    description: 'Interactive tree node insertion with animated Inorder, Preorder, and Postorder traversals.',
    timeComplexity: { best: 'O(n)', avg: 'O(n)', worst: 'O(n)' },
    spaceComplexity: 'O(h)',
    keyOperations: ['Inorder (LNR)', 'Preorder (NLR)', 'Postorder (LRN)', 'Insert Node']
  },
  {
    id: 'bst',
    title: 'Binary Search Tree (BST)',
    category: 'Trees',
    description: 'Ordered binary tree preserving left < root < right invariant with path highlighting.',
    timeComplexity: { best: 'O(log n)', avg: 'O(log n)', worst: 'O(n)' },
    spaceComplexity: 'O(h)',
    keyOperations: ['Insert Key', 'Search Key', 'Delete Key', 'Find Min/Max']
  },
  {
    id: 'heap',
    title: 'Min / Max Binary Heap',
    category: 'Trees',
    description: 'Complete binary tree priority queue with Sift-Up and Sift-Down bubble animations.',
    timeComplexity: { best: 'O(1)', avg: 'O(log n)', worst: 'O(log n)' },
    spaceComplexity: 'O(n)',
    keyOperations: ['Insert & Sift-Up', 'Extract Root', 'Sift-Down', 'Toggle Min/Max']
  },
  {
    id: 'hashmap',
    title: 'Hash Map (Separate Chaining)',
    category: 'Hashing',
    description: 'Modulo hash bucket computation `key % bucketCount` and linked collision chains.',
    timeComplexity: { best: 'O(1)', avg: 'O(1)', worst: 'O(n)' },
    spaceComplexity: 'O(n + m)',
    keyOperations: ['Put(key, val)', 'Get(key)', 'Delete(key)', 'Trigger Collision']
  },
  {
    id: 'graph',
    title: 'Graph BFS / DFS Explorer',
    category: 'Graphs',
    description: 'Click canvas to add nodes/edges and step through Breadth-First Queue or Depth-First Stack.',
    timeComplexity: { best: 'O(V + E)', avg: 'O(V + E)', worst: 'O(V + E)' },
    spaceComplexity: 'O(V)',
    keyOperations: ['Run BFS', 'Run DFS', 'Add Vertex', 'Connect Edge']
  },
  {
    id: 'searching',
    title: 'Linear vs Binary Search',
    category: 'Algorithms',
    description: 'Side-by-side comparison of sequential O(n) scan against divide-and-conquer O(log n) mid-point halving.',
    timeComplexity: { best: 'O(1)', avg: 'O(log n)', worst: 'O(log n)' },
    spaceComplexity: 'O(1)',
    keyOperations: ['Binary Search', 'Linear Search', 'Set Target', 'Random Sorted Array']
  },
  {
    id: 'recursion-tree',
    title: 'Recursion Call Tree',
    category: 'Algorithms',
    description: 'Visualize call stack frames and overlapping subproblem branches for Fibonacci & Factorial.',
    timeComplexity: { best: 'O(n)', avg: 'O(2ⁿ)', worst: 'O(2ⁿ)' },
    spaceComplexity: 'O(n)',
    keyOperations: ['fib(n) Tree', 'fact(n) Stack', 'Highlight Memoized', 'Step Stack Frame']
  }
];
