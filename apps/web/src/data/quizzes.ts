export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
}

export const QUIZZES: Record<string, QuizQuestion[]> = {
  'arrays-hashing': [
    {
      id: 'arr-q1',
      question: 'What is the time complexity of accessing an element by index in a contiguous static array?',
      options: ['O(1)', 'O(log n)', 'O(n)', 'O(n log n)'],
      correctIndex: 0,
      explanation: 'Memory address is computed directly via base_address + index * element_size in O(1) constant time.'
    },
    {
      id: 'arr-q2',
      question: 'Which algorithmic technique finds a pair summing to a target in a sorted array using O(1) extra space?',
      options: ['Hash Map Complement', 'Converging Two Pointers', 'Breadth-First Search', 'Monotonic Stack'],
      correctIndex: 1,
      explanation: 'With a sorted array, left=0 and right=n-1 pointers adjust inward based on sum comparisons in O(n) time and O(1) space.'
    },
    {
      id: 'arr-q3',
      question: "What is the recurrence invariant maintained by Kadane's Maximum Subarray algorithm?",
      options: [
        'currMax = max(nums[i], currMax + nums[i])',
        'currMax = min(nums[i], currMax - nums[i])',
        'currMax = currMax * nums[i]',
        'currMax = nums[i] + nums[i - 1]'
      ],
      correctIndex: 0,
      explanation: 'At each index i, we either extend the previous subarray or start fresh at nums[i] if the prior sum became negative.'
    },
    {
      id: 'arr-q4',
      question: 'What is the worst-case time complexity of inserting an element at index 0 of an n-element array?',
      options: ['O(1)', 'O(log n)', 'O(n)', 'O(n²)'],
      correctIndex: 2,
      explanation: 'All n existing elements must shift one position to the right in memory, costing O(n) operations.'
    },
    {
      id: 'arr-q5',
      question: 'When computing prefix sums P[i] = nums[0] + ... + nums[i], how do you query the sum of subarray nums[L..R] in O(1)?',
      options: ['P[R] - P[L - 1] (or P[R] if L == 0)', 'P[R] + P[L]', 'P[R - L]', 'P[L] - P[R]'],
      correctIndex: 0,
      explanation: 'Prefix sum subtraction cancels all elements before index L, leaving the exact sum of range [L..R] in O(1).'
    },
    {
      id: 'arr-q6',
      question: 'Which sorting algorithm guarantees O(n log n) worst-case time complexity and is stable, but requires O(n) auxiliary space?',
      options: ['Quick Sort', 'Heap Sort', 'Merge Sort', 'Insertion Sort'],
      correctIndex: 2,
      explanation: 'Merge Sort splits arrays in half recursively and merges sorted halves stably using an O(n) temporary buffer.'
    },
    {
      id: 'arr-q7',
      question: 'In Quick Sort, what happens if the pivot chosen is repeatedly the smallest or largest element?',
      options: [
        'Time complexity degrades to O(n²)',
        'Time complexity remains O(n log n)',
        'Space complexity becomes O(1)',
        'The array cannot be sorted'
      ],
      correctIndex: 0,
      explanation: 'Unbalanced partitions of size 0 and n-1 create a recursion depth of n, resulting in O(n²) comparisons.'
    },
    {
      id: 'arr-q8',
      question: 'What is the amortized time complexity of appending (push) to a dynamically resizing array (e.g., C++ std::vector)?',
      options: ['O(1) amortized', 'O(log n) amortized', 'O(n) amortized', 'O(n²)'],
      correctIndex: 0,
      explanation: 'Doubling capacity when full spreads the O(n) copy cost over n insertions, giving O(1) amortized time per push.'
    },
    {
      id: 'arr-q9',
      question: 'To find the minimum length subarray with sum >= S in an array of positive integers, which pattern is optimal?',
      options: ['Variable-Size Sliding Window', 'Binary Search on Unsorted Array', 'Floyd Cycle Detection', 'Bellman-Ford'],
      correctIndex: 0,
      explanation: 'Because all numbers are positive, expanding right increases sum and shrinking left decreases sum monotonically in O(n).'
    },
    {
      id: 'arr-q10',
      question: 'What is the time complexity of Binary Search on a sorted array of size n?',
      options: ['O(1)', 'O(log₂ n)', 'O(√n)', 'O(n)'],
      correctIndex: 1,
      explanation: 'Each comparison eliminates half of the remaining search space, requiring at most floor(log₂ n) + 1 steps.'
    }
  ],
  trees: [
    {
      id: 'tree-q1',
      question: 'Which traversal of a Binary Search Tree (BST) visits all node keys in non-decreasing sorted order?',
      options: ['Preorder (NLR)', 'Inorder (LNR)', 'Postorder (LRN)', 'Level-Order BFS'],
      correctIndex: 1,
      explanation: 'Inorder traversal visits Left subtree (< root), then Root, then Right subtree (> root), producing sorted output.'
    },
    {
      id: 'tree-q2',
      question: 'What is the maximum number of nodes in a binary tree of height h (where a single root node has height 1)?',
      options: ['2^h - 1', '2^(h-1)', 'h²', '2h + 1'],
      correctIndex: 0,
      explanation: 'Summing nodes across levels 0 to h-1 gives 1 + 2 + 4 + ... + 2^(h-1) = 2^h - 1.'
    },
    {
      id: 'tree-q3',
      question: 'What is the worst-case height of a Binary Search Tree containing n nodes inserted in strictly increasing order?',
      options: ['O(log n)', 'O(n)', 'O(√n)', 'O(1)'],
      correctIndex: 1,
      explanation: 'Inserting sorted keys into an unbalanced BST creates a degenerate right-skewed chain of height n.'
    },
    {
      id: 'tree-q4',
      question: 'In an array-backed 0-indexed Binary Heap, what are the indices of the left and right children of node i?',
      options: ['left = 2i + 1, right = 2i + 2', 'left = 2i, right = 2i + 1', 'left = i + 1, right = i + 2', 'left = i/2, right = i/2 + 1'],
      correctIndex: 0,
      explanation: 'Level-order packing places children of index i at 2i + 1 and 2i + 2, with parent at floor((i - 1) / 2).'
    },
    {
      id: 'tree-q5',
      question: 'Which traversal order is most appropriate for deleting or freeing all nodes in a tree from bottom up?',
      options: ['Preorder', 'Inorder', 'Postorder', 'Level-order'],
      correctIndex: 2,
      explanation: 'Postorder processes both Left and Right children completely before processing the parent node.'
    },
    {
      id: 'tree-q6',
      question: 'What is the time complexity of extracting the minimum element from a Min-Heap of size n?',
      options: ['O(1)', 'O(log n)', 'O(n)', 'O(n log n)'],
      correctIndex: 1,
      explanation: 'Swapping root with the last leaf takes O(1), followed by Sift-Down along the tree height of O(log n).'
    },
    {
      id: 'tree-q7',
      question: 'A full binary tree is defined as a tree where every node has how many children?',
      options: ['Either 0 or 2 children', 'Exactly 2 children', 'At most 1 child', 'All leaves at same depth'],
      correctIndex: 0,
      explanation: 'In a full (proper) binary tree, every internal node has exactly 2 children and leaves have 0.'
    },
    {
      id: 'tree-q8',
      question: 'What data structure is used internally to implement Level-Order (Breadth-First) Tree Traversal?',
      options: ['FIFO Queue', 'LIFO Stack', 'Priority Queue', 'Hash Set'],
      correctIndex: 0,
      explanation: 'A FIFO queue processes nodes level by level, enqueuing left and right children as each node is visited.'
    },
    {
      id: 'tree-q9',
      question: 'To validate if a binary tree is a valid BST, what state must be passed down recursive calls?',
      options: [
        'Valid range (minAllowed, maxAllowed) for each subtree',
        'Only the immediate parent value',
        'Current depth counter',
        'Total number of nodes'
      ],
      correctIndex: 0,
      explanation: 'Checking only parent < child is insufficient; every node in the left subtree must be smaller than all ancestors above it.'
    },
    {
      id: 'tree-q10',
      question: 'What is the space complexity of recursive DFS traversal on a balanced binary tree with n nodes?',
      options: ['O(log n) call stack frames', 'O(n) call stack frames', 'O(1)', 'O(n²)'],
      correctIndex: 0,
      explanation: 'The recursion stack only holds nodes along the active root-to-leaf path, which is O(height) = O(log n) for balanced trees.'
    }
  ],
  graphs: [
    {
      id: 'graph-q1',
      question: 'What is the time complexity of Breadth-First Search (BFS) on a graph represented as an Adjacency List with V vertices and E edges?',
      options: ['O(V + E)', 'O(V²)', 'O(V * E)', 'O(E log V)'],
      correctIndex: 0,
      explanation: 'BFS visits every vertex at most once O(V) and inspects every directed/undirected edge at most twice O(E).'
    },
    {
      id: 'graph-q2',
      question: 'Which algorithm finds the shortest path in an unweighted graph from a source vertex to all other vertices?',
      options: ['Breadth-First Search (BFS)', 'Depth-First Search (DFS)', 'Kruskal MST', 'Topological Sort'],
      correctIndex: 0,
      explanation: 'BFS explores vertices in concentric layers of distance d, d+1, d+2, guaranteeing shortest hop count upon first visit.'
    },
    {
      id: 'graph-q3',
      question: 'For which class of graphs does a valid Topological Ordering exist?',
      options: ['Directed Acyclic Graphs (DAGs)', 'Undirected Connected Graphs', 'Graphs with Negative Cycles', 'Complete Graphs K_n'],
      correctIndex: 0,
      explanation: 'Any directed cycle creates a circular dependency where no node in the cycle can come first.'
    },
    {
      id: 'graph-q4',
      question: 'How much memory does an Adjacency Matrix require for a graph with V vertices?',
      options: ['O(V²)', 'O(V + E)', 'O(E)', 'O(V log V)'],
      correctIndex: 0,
      explanation: 'An adjacency matrix allocates a V × V grid regardless of how sparse or dense the edge set E is.'
    },
    {
      id: 'graph-q5',
      question: 'In Kahn’s BFS algorithm for Topological Sort, which vertices are pushed into the initial queue?',
      options: [
        'All vertices with in-degree equal to 0',
        'All vertices with out-degree equal to 0',
        'The vertex with highest degree',
        'A randomly chosen vertex'
      ],
      correctIndex: 0,
      explanation: 'Vertices with 0 prerequisites (in-degree 0) can be scheduled immediately without dependencies.'
    },
    {
      id: 'graph-q6',
      question: 'What data structure achieves nearly O(1) time per operation for Dynamic Connectivity & Cycle Detection in undirected graphs?',
      options: ['Disjoint Set Union (Union-Find) with Path Compression', 'Adjacency Matrix', 'Binary Search Tree', 'Min-Heap'],
      correctIndex: 0,
      explanation: 'Union by rank + path compression yields O(α(V)) inverse Ackermann time per find/union operation.'
    },
    {
      id: 'graph-q7',
      question: 'In a connected undirected graph with V vertices and no cycles (a tree), how many edges E are present?',
      options: ['E = V - 1', 'E = V', 'E = V + 1', 'E = V(V - 1)/2'],
      correctIndex: 0,
      explanation: 'Every tree with V vertices has exactly V - 1 edges; adding any edge creates a cycle.'
    },
    {
      id: 'graph-q8',
      question: 'When running DFS on a directed graph, which edge type indicates the presence of a directed cycle?',
      options: ['Back Edge (to an ancestor currently on the recursion stack)', 'Cross Edge', 'Forward Edge', 'Tree Edge'],
      correctIndex: 0,
      explanation: 'A back edge points to an active ancestor node (colored gray / in recursion stack), completing a cycle.'
    },
    {
      id: 'graph-q9',
      question: 'Why does Dijkstra’s Shortest Path algorithm fail on graphs containing negative edge weights?',
      options: [
        'It greedily assumes adding future edges can never decrease a path weight',
        'It only works on trees',
        'It uses a FIFO queue instead of a heap',
        'It cannot handle disconnected components'
      ],
      correctIndex: 0,
      explanation: 'Dijkstra finalizes the shortest distance to a popped vertex; negative edges downstream could later yield a shorter path.'
    },
    {
      id: 'graph-q10',
      question: 'How many connected components exist in an undirected graph if a full DFS traversal requires 4 outer loop starts?',
      options: ['4 connected components', '1 connected component', '2 connected components', '0 connected components'],
      correctIndex: 0,
      explanation: 'Each outer loop invocation of DFS visits one entire connected component.'
    }
  ],
  'dynamic-programming': [
    {
      id: 'dp-q1',
      question: 'What two fundamental properties must a problem exhibit to be solved effectively via Dynamic Programming?',
      options: [
        'Overlapping Subproblems & Optimal Substructure',
        'Greedy Choice Property & Sorted Input',
        'Divide and Conquer & Disjoint Subproblems',
        'Bipartite Graph & Monotonicity'
      ],
      correctIndex: 0,
      explanation: 'Optimal solutions build from optimal sub-solutions (Optimal Substructure), and recursive branches repeat identical states (Overlapping Subproblems).'
    },
    {
      id: 'dp-q2',
      question: 'What is the difference between Top-Down Memoization and Bottom-Up Tabulation?',
      options: [
        'Top-Down caches recursive calls on demand; Bottom-Up iteratively fills a table from base cases',
        'Top-Down is always O(1) space; Bottom-Up is always O(n²)',
        'Bottom-Up uses recursion; Top-Down uses loops',
        'They produce different time complexities on dense state spaces'
      ],
      correctIndex: 0,
      explanation: 'Memoization wraps recursive functions with a lookup cache, whereas Tabulation orders states topologically in loops.'
    },
    {
      id: 'dp-q3',
      question: 'What is the naive recursive time complexity of fib(n) = fib(n-1) + fib(n-2) WITHOUT memoization?',
      options: ['O(2ⁿ)', 'O(n)', 'O(n²)', 'O(n log n)'],
      correctIndex: 0,
      explanation: 'The recursion tree branches into 2 calls at every depth up to n, yielding ~1.618^n = O(2ⁿ) calls.'
    },
    {
      id: 'dp-q4',
      question: 'In the 0/1 Knapsack problem with N items and capacity W, what is the state space dimension of the DP table?',
      options: ['O(N * W)', 'O(2^N)', 'O(N + W)', 'O(N²)'],
      correctIndex: 0,
      explanation: 'Each state depends on item index i ∈ [0..N] and remaining knapsack capacity w ∈ [0..W].'
    },
    {
      id: 'dp-q5',
      question: 'How can the space complexity of 2D Grid Unique Paths dp[r][c] = dp[r-1][c] + dp[r][c-1] be reduced?',
      options: [
        'To O(columns) using a single 1D rolling array',
        'To O(1) without math formulas',
        'It cannot be reduced below O(rows * columns)',
        'By sorting the grid first'
      ],
      correctIndex: 0,
      explanation: 'Because row r only depends on row r-1 and the current row, a 1D array updated left-to-right suffices.'
    },
    {
      id: 'dp-q6',
      question: 'In Coin Change (minimum coins to make amount A), what value should dp[0] be initialized to?',
      options: ['0 (zero coins needed to make amount 0)', 'Infinity', '1', '-1'],
      correctIndex: 0,
      explanation: 'Base case: making an amount of 0 requires 0 coins. All positive amounts start at Infinity.'
    },
    {
      id: 'dp-q7',
      question: 'What is the optimal time complexity for finding the Longest Increasing Subsequence (LIS) of an array of length n?',
      options: ['O(n log n) via binary search patience piles', 'O(n²)', 'O(n)', 'O(2ⁿ)'],
      correctIndex: 0,
      explanation: 'Maintaining the smallest tail of all increasing subsequences of length k allows binary search updates in O(n log n).'
    },
    {
      id: 'dp-q8',
      question: 'In House Robber (cannot rob adjacent houses), what is the recurrence for dp[i]?',
      options: [
        'dp[i] = max(dp[i - 1], nums[i] + dp[i - 2])',
        'dp[i] = dp[i - 1] + dp[i - 2]',
        'dp[i] = nums[i] + dp[i - 1]',
        'dp[i] = min(dp[i - 1], dp[i - 2])'
      ],
      correctIndex: 0,
      explanation: 'Either skip house i (retaining dp[i-1]) or rob house i (adding nums[i] to best result from i-2).'
    },
    {
      id: 'dp-q9',
      question: 'Which DP problem computes the minimum number of insertions, deletions, and substitutions to transform string A into string B?',
      options: ['Edit Distance (Levenshtein Distance)', 'Longest Common Substring', 'KMP String Matching', 'Rabin-Karp Rolling Hash'],
      correctIndex: 0,
      explanation: 'Edit distance builds an (m+1)×(n+1) table comparing prefixes of A and B.'
    },
    {
      id: 'dp-q10',
      question: 'When converting a 2D DP table into a 1D array for 0/1 Knapsack, in which direction must the inner capacity loop iterate?',
      options: [
        'Backwards from W down to item.weight',
        'Forwards from item.weight up to W',
        'In random order',
        'Only even capacities'
      ],
      correctIndex: 0,
      explanation: 'Iterating backwards ensures each item is used at most once (reading from the previous row state rather than reusing the same item twice).'
    }
  ],
  mixed: [
    {
      id: 'mix-q1',
      question: 'What is the time complexity of Binary Search on a sorted array of n elements?',
      options: ['O(1)', 'O(log₂ n)', 'O(√n)', 'O(n)'],
      correctIndex: 1,
      explanation: 'Each comparison halves the remaining search space, so at most floor(log₂ n) + 1 steps are needed.'
    },
    {
      id: 'mix-q2',
      question: 'Which traversal of a Binary Search Tree visits keys in sorted order?',
      options: ['Preorder (NLR)', 'Inorder (LNR)', 'Postorder (LRN)', 'Level-order (BFS)'],
      correctIndex: 1,
      explanation: 'Inorder visits Left subtree, then Root, then Right subtree — yielding ascending key order for a BST.'
    },
    {
      id: 'mix-q3',
      question: 'What is the time complexity of BFS on a graph represented as an adjacency list with V vertices and E edges?',
      options: ['O(V + E)', 'O(V²)', 'O(V · E)', 'O(E log V)'],
      correctIndex: 0,
      explanation: 'Each vertex is visited once and each edge inspected (at most twice for undirected), giving O(V + E).'
    },
    {
      id: 'mix-q4',
      question: 'Which two properties must hold for a problem to be solved by Dynamic Programming?',
      options: [
        'Overlapping subproblems & optimal substructure',
        'Sorted input & greedy choice',
        'Disjoint subproblems & divide-and-conquer',
        'Bipartite graph & monotonicity'
      ],
      correctIndex: 0,
      explanation: 'DP works when optimal solutions are built from optimal sub-solutions and subproblems repeat.'
    },
    {
      id: 'mix-q5',
      question: "In Kadane's algorithm, how is the running maximum updated at each index?",
      options: [
        'curr = max(nums[i], curr + nums[i])',
        'curr = min(nums[i], curr - nums[i])',
        'curr = curr * nums[i]',
        'curr = nums[i] + nums[i-1]'
      ],
      correctIndex: 0,
      explanation: 'Either extend the existing subarray (curr + nums[i]) or start fresh at nums[i] when the prior sum is negative.'
    },
    {
      id: 'mix-q6',
      question: 'Which data structure is used to implement Level-Order tree traversal?',
      options: ['FIFO Queue', 'LIFO Stack', 'Min-Heap', 'Hash Set'],
      correctIndex: 0,
      explanation: 'A FIFO queue processes nodes layer by layer, enqueuing children as each node is visited.'
    },
    {
      id: 'mix-q7',
      question: 'What is the worst-case time complexity of Quick Sort using Lomuto partition?',
      options: ['O(n log n)', 'O(n²)', 'O(n)', 'O(log n)'],
      correctIndex: 1,
      explanation: 'Choosing the smallest or largest element as pivot at every step produces unbalanced partitions of size 0 and n-1.'
    },
    {
      id: 'mix-q8',
      question: 'In a Min-Heap, what is the time complexity of extracting the minimum element?',
      options: ['O(1)', 'O(log n)', 'O(n)', 'O(n log n)'],
      correctIndex: 1,
      explanation: 'Swapping root with the last leaf is O(1), then Sift-Down runs along tree height O(log n).'
    },
    {
      id: 'mix-q9',
      question: 'Which technique finds the longest substring without repeating characters in O(n)?',
      options: ['Sliding window', 'Binary search', 'Prefix product', 'Union-Find'],
      correctIndex: 0,
      explanation: 'A sliding window with a hash set expands the right edge and contracts the left when a duplicate appears.'
    },
    {
      id: 'mix-q10',
      question: 'How is the space complexity of 2D grid DP (dp[r][c] = dp[r-1][c] + dp[r][c-1]) reduced?',
      options: [
        'To O(columns) with a 1D rolling array',
        'To O(1) with no changes',
        'It cannot be reduced below O(rows·columns)',
        'By sorting the grid first'
      ],
      correctIndex: 0,
      explanation: 'Each row only depends on the previous row and itself, so a single 1D array updated left-to-right suffices.'
    }
  ],
  sorting: [
    {
      id: 'sort-q1',
      question: 'Which sorting algorithm is guaranteed O(n log n) in the worst-case and sorts in-place with O(1) auxiliary memory?',
      options: ['Heap Sort', 'Merge Sort', 'Quick Sort', 'Counting Sort'],
      correctIndex: 0,
      explanation: 'Heap Sort builds a binary heap in-place in O(n) time and performs n extractions in O(n log n) with O(1) extra space.'
    },
    {
      id: 'sort-q2',
      question: 'In standard binary search on an array of length n, what is the maximum number of comparisons performed?',
      options: ['⌊log₂ n⌋ + 1', 'n / 2', 'n', 'log₁₀ n'],
      correctIndex: 0,
      explanation: 'Binary search halves the search space at each iteration, giving logarithmic depth ⌊log₂ n⌋ + 1.'
    },
    {
      id: 'sort-q3',
      question: 'Which sorting algorithm has linear O(n + k) time complexity when keys are integers in range [0, k]?',
      options: ['Counting Sort', 'Merge Sort', 'Quick Sort', 'Bubble Sort'],
      correctIndex: 0,
      explanation: 'Counting Sort tallies frequencies of keys in range [0, k] in O(n + k) without comparison-based sorting bounds.'
    }
  ],
  'data-structures': [
    {
      id: 'ds-q1',
      question: 'What is the amortized time complexity of inserting into a dynamic array (like std::vector or ArrayList)?',
      options: ['O(1)', 'O(n)', 'O(log n)', 'O(n²)'],
      correctIndex: 0,
      explanation: 'Doubling array capacity when full ensures the cost of reallocations averages out to O(1) per insertion amortized.'
    },
    {
      id: 'ds-q2',
      question: 'In a circular queue implemented using an array of size capacity, how is the next rear position calculated?',
      options: ['(rear + 1) % capacity', 'rear + 1', 'rear % capacity', '(rear - 1) % capacity'],
      correctIndex: 0,
      explanation: 'Modulo arithmetic wraps the index around from capacity-1 back to 0.'
    },
    {
      id: 'ds-q3',
      question: 'Which data structure allows O(1) amortized insertion, deletion, and minimum element lookup?',
      options: ['Min-Heap', 'Hash Table with min pointer', 'Self-balancing BST', 'Monotonic Queue / Stack'],
      correctIndex: 3,
      explanation: 'A monotonic deque maintains elements in monotonic order, yielding amortized O(1) operations.'
    }
  ],
  'cs-fundamentals': [
    {
      id: 'cs-q1',
      question: 'In database systems, what does the ACID property "Isolation" guarantee?',
      options: [
        'Concurrent transactions execute without interfering with one another as if sequential',
        'Transactions survive hardware crashes permanently',
        'All or nothing execution of transaction statements',
        'Database integrity constraints are never violated'
      ],
      correctIndex: 0,
      explanation: 'Isolation ensures concurrent transaction execution produces the same outcome as some serial schedule.'
    },
    {
      id: 'cs-q2',
      question: 'In OS memory management, what is Belady\'s Anomaly?',
      options: [
        'Increasing page frames results in more page faults under FIFO replacement',
        'CPU thrashing due to lack of page table entries',
        'LRU performance degrading below optimal replacement',
        'Deadlock caused by circular page references'
      ],
      correctIndex: 0,
      explanation: 'Belady\'s Anomaly is the phenomenon where allocating more physical frames increases the number of page faults under FIFO.'
    },
    {
      id: 'cs-q3',
      question: 'How many usable host IP addresses are available in an IPv4 subnet with a /27 CIDR mask?',
      options: ['30', '32', '62', '14'],
      correctIndex: 0,
      explanation: 'A /27 subnet leaves 32 - 27 = 5 host bits. 2^5 = 32 total addresses minus 2 (network and broadcast) = 30 usable hosts.'
    }
  ],
  'bit-manipulation': [
    {
      id: 'bit-q1',
      question: 'What operation does the expression n & (n - 1) perform on a non-zero integer n?',
      options: [
        'Clears the lowest (rightmost) set bit',
        'Isolates the lowest set bit',
        'Inverts all bits',
        'Checks if n is odd'
      ],
      correctIndex: 0,
      explanation: 'n & (n - 1) clears the rightmost 1-bit, forming the basis of Brian Kernighan\'s popcount algorithm.'
    },
    {
      id: 'bit-q2',
      question: 'How can you isolate the lowest set bit of an integer n in two\'s complement representation?',
      options: ['n & (-n)', 'n | (-n)', 'n ^ (n - 1)', '~n & 1'],
      correctIndex: 0,
      explanation: 'In two\'s complement, -n is ~n + 1. Performing n & (-n) masks out all bits except the lowest set bit.'
    },
    {
      id: 'bit-q3',
      question: 'What is the result of evaluating x ^ x for any integer x?',
      options: ['0', 'x', '1', '-1'],
      correctIndex: 0,
      explanation: 'XORing any number with itself produces 0 since every matching bit pair yields 0.'
    }
  ]
};

export interface QuizTopicMeta {
  id: string;
  title: string;
  description: string;
}

export const QUIZ_TOPICS: QuizTopicMeta[] = [
  { id: 'arrays-hashing', title: 'Arrays & Hashing', description: 'Indexing, frequency maps, and subarray bounds.' },
  { id: 'trees', title: 'Trees & BST', description: 'Traversals, binary search trees, and heap invariants.' },
  { id: 'graphs', title: 'Graphs & Traversals', description: 'BFS, DFS, Dijkstra, topological sort, and connectivity.' },
  { id: 'dynamic-programming', title: 'Dynamic Programming', description: 'Optimal substructure, memoization, and tabulation recurrence.' },
  { id: 'sorting', title: 'Sorting & Searching', description: 'Binary search invariants, in-place sorts, and comparison bounds.' },
  { id: 'data-structures', title: 'Stacks, Queues & Heaps', description: 'Amortized structures, circular queues, and priority queues.' },
  { id: 'bit-manipulation', title: 'Bit Manipulation', description: 'Bitwise masks, popcounts, and bit tricks.' },
  { id: 'cs-fundamentals', title: 'CS Fundamentals', description: 'Operating systems, memory management, networks, and DBMS.' },
  { id: 'mixed', title: 'Mixed Mastery', description: 'Adaptive placement assessment drawn across all 830+ verified items.' }
];
