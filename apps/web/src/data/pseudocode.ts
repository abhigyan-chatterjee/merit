export interface PseudoCodeBlock {
  title: string;
  lines: string[];
  timeComplexity: string;
  spaceComplexity: string;
}

export const PSEUDOCODE_MAP: Record<string, PseudoCodeBlock> = {
  bubble: {
    title: 'Bubble Sort',
    lines: [
      'function bubbleSort(arr):',
      '  for i = 0 to n - 1:',
      '    for j = 0 to n - i - 2:',
      '      if arr[j] > arr[j + 1]:',
      '        swap(arr[j], arr[j + 1])',
      '  return arr'
    ],
    timeComplexity: 'O(n²)',
    spaceComplexity: 'O(1)'
  },
  selection: {
    title: 'Selection Sort',
    lines: [
      'function selectionSort(arr):',
      '  for i = 0 to n - 1:',
      '    minIdx = i',
      '    for j = i + 1 to n - 1:',
      '      if arr[j] < arr[minIdx]: minIdx = j',
      '    swap(arr[i], arr[minIdx])',
      '  return arr'
    ],
    timeComplexity: 'O(n²)',
    spaceComplexity: 'O(1)'
  },
  insertion: {
    title: 'Insertion Sort',
    lines: [
      'function insertionSort(arr):',
      '  for i = 1 to n - 1:',
      '    key = arr[i], j = i - 1',
      '    while j >= 0 and arr[j] > key:',
      '      arr[j + 1] = arr[j]; j = j - 1',
      '    arr[j + 1] = key',
      '  return arr'
    ],
    timeComplexity: 'O(n²)',
    spaceComplexity: 'O(1)'
  },
  merge: {
    title: 'Merge Sort',
    lines: [
      'function mergeSort(arr, l, r):',
      '  if l >= r: return',
      '  mid = floor((l + r) / 2)',
      '  mergeSort(arr, l, mid)',
      '  mergeSort(arr, mid + 1, r)',
      '  merge(arr, l, mid, r)'
    ],
    timeComplexity: 'O(n log n)',
    spaceComplexity: 'O(n)'
  },
  quick: {
    title: 'Quick Sort (Lomuto Partition)',
    lines: [
      'function quickSort(arr, low, high):',
      '  if low < high:',
      '    pivotIdx = partition(arr, low, high)',
      '    quickSort(arr, low, pivotIdx - 1)',
      '    quickSort(arr, pivotIdx + 1, high)',
      '  return arr'
    ],
    timeComplexity: 'O(n log n)',
    spaceComplexity: 'O(log n)'
  },
  'binary-search': {
    title: 'Binary Search',
    lines: [
      'function binarySearch(arr, target):',
      '  left = 0, right = n - 1',
      '  while left <= right:',
      '    mid = floor((left + right) / 2)',
      '    if arr[mid] == target: return mid',
      '    else if arr[mid] < target: left = mid + 1',
      '    else: right = mid - 1',
      '  return -1'
    ],
    timeComplexity: 'O(log n)',
    spaceComplexity: 'O(1)'
  },
  bfs: {
    title: 'Breadth-First Search (BFS)',
    lines: [
      'function bfs(graph, start):',
      '  queue = [start], visited = {start}',
      '  while queue is not empty:',
      '    curr = queue.dequeue()',
      '    for neighbor of graph[curr]:',
      '      if neighbor not in visited:',
      '        visited.add(neighbor)',
      '        queue.enqueue(neighbor)'
    ],
    timeComplexity: 'O(V + E)',
    spaceComplexity: 'O(V)'
  },
  dfs: {
    title: 'Depth-First Search (DFS)',
    lines: [
      'function dfs(graph, curr, visited):',
      '  visited.add(curr)',
      '  for neighbor of graph[curr]:',
      '    if neighbor not in visited:',
      '      dfs(graph, neighbor, visited)'
    ],
    timeComplexity: 'O(V + E)',
    spaceComplexity: 'O(V)'
  },
  tree: {
    title: 'Binary Tree Traversal (Recursive)',
    lines: [
      'function traverse(node):',
      '  if node == null: return',
      '  traverse(node.left)    // Left Subtree',
      '  visit(node.val)        // Process Node',
      '  traverse(node.right)   // Right Subtree'
    ],
    timeComplexity: 'O(n)',
    spaceComplexity: 'O(h)'
  },
  'binary-tree': {
    title: 'Binary Tree Traversal (Recursive)',
    lines: [
      'function traverse(node):',
      '  if node == null: return',
      '  traverse(node.left)    // Left Subtree',
      '  visit(node.val)        // Process Node',
      '  traverse(node.right)   // Right Subtree'
    ],
    timeComplexity: 'O(n)',
    spaceComplexity: 'O(h)'
  },
  bst: {
    title: 'Binary Search Tree (BST)',
    lines: [
      'function insert(root, val):',
      '  if root == null: return new Node(val)',
      '  if val < root.val: root.left = insert(root.left, val)',
      '  else: root.right = insert(root.right, val)  // BST: Left < Root <= Right',
      '  return root'
    ],
    timeComplexity: 'O(log n) avg, O(n) worst',
    spaceComplexity: 'O(h)'
  },
  heap: {
    title: 'Binary Heap (sift-up / sift-down)',
    lines: [
      'function insert(heap, val):',
      '  heap.append(val); siftUp(heap, last)      // Restore heap invariant',
      'function extractRoot(heap):',
      '  swap(heap[0], heap[last]); pop()',
      '  siftDown(heap, 0)                          // Restore heap invariant'
    ],
    timeComplexity: 'O(log n)',
    spaceComplexity: 'O(1)'
  },
  linear: {
    title: 'Data Structure Operation',
    lines: [
      'function performOperation(ds, val):',
      '  validateBounds(ds)',
      '  allocateNodeOrSlot(val)',
      '  updatePointers(ds.head, ds.tail)',
      '  return ds.size'
    ],
    timeComplexity: 'O(1)',
    spaceComplexity: 'O(1)'
  }
};
