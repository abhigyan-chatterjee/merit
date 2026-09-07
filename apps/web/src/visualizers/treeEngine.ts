/**
 * Pure Tree & Heap algorithms for TreeVisualizer
 * Invariant-preserving, tested and verified.
 */

export interface TreeNode {
  id: string;
  value: number;
  left: TreeNode | null;
  right: TreeNode | null;
}

export interface TreeLayoutNode {
  id: string;
  value: number;
  x: number;
  y: number;
  leftId: string | null;
  rightId: string | null;
}

export interface TreeLayoutEdge {
  fromId: string;
  toId: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

let nextNodeId = 1;
export function resetNodeIdCounter() {
  nextNodeId = 1;
}

export function createTreeNode(value: number, id?: string): TreeNode {
  return {
    id: id ?? `node-${nextNodeId++}`,
    value,
    left: null,
    right: null,
  };
}

// --------------------------------------------------------
// Binary Tree (Level-Order Insertion into first open slot)
// --------------------------------------------------------
export function insertBinaryTree(root: TreeNode | null, value: number): TreeNode {
  const newNode = createTreeNode(value);
  if (!root) return newNode;

  const queue: TreeNode[] = [root];
  while (queue.length > 0) {
    const curr = queue.shift()!;
    if (!curr.left) {
      curr.left = newNode;
      break;
    } else {
      queue.push(curr.left);
    }

    if (!curr.right) {
      curr.right = newNode;
      break;
    } else {
      queue.push(curr.right);
    }
  }
  return root;
}

// --------------------------------------------------------
// Binary Search Tree (BST)
// --------------------------------------------------------
export function insertBST(root: TreeNode | null, value: number): TreeNode {
  const newNode = createTreeNode(value);
  if (!root) return newNode;

  let curr = root;
  while (true) {
    if (value < curr.value) {
      if (!curr.left) {
        curr.left = newNode;
        break;
      }
      curr = curr.left;
    } else {
      if (!curr.right) {
        curr.right = newNode;
        break;
      }
      curr = curr.right;
    }
  }
  return root;
}

export function searchBST(root: TreeNode | null, target: number): { path: string[]; found: boolean } {
  const path: string[] = [];
  let curr = root;
  while (curr) {
    path.push(curr.id);
    if (curr.value === target) {
      return { path, found: true };
    }
    if (target < curr.value) {
      curr = curr.left;
    } else {
      curr = curr.right;
    }
  }
  return { path, found: false };
}

// --------------------------------------------------------
// Traversals
// --------------------------------------------------------
export function inorderTraversal(root: TreeNode | null): { values: number[]; ids: string[] } {
  const values: number[] = [];
  const ids: string[] = [];
  function traverse(node: TreeNode | null) {
    if (!node) return;
    traverse(node.left);
    values.push(node.value);
    ids.push(node.id);
    traverse(node.right);
  }
  traverse(root);
  return { values, ids };
}

export function preorderTraversal(root: TreeNode | null): { values: number[]; ids: string[] } {
  const values: number[] = [];
  const ids: string[] = [];
  function traverse(node: TreeNode | null) {
    if (!node) return;
    values.push(node.value);
    ids.push(node.id);
    traverse(node.left);
    traverse(node.right);
  }
  traverse(root);
  return { values, ids };
}

export function postorderTraversal(root: TreeNode | null): { values: number[]; ids: string[] } {
  const values: number[] = [];
  const ids: string[] = [];
  function traverse(node: TreeNode | null) {
    if (!node) return;
    traverse(node.left);
    traverse(node.right);
    values.push(node.value);
    ids.push(node.id);
  }
  traverse(root);
  return { values, ids };
}

export function levelOrderTraversal(root: TreeNode | null): { values: number[]; ids: string[] } {
  const values: number[] = [];
  const ids: string[] = [];
  if (!root) return { values, ids };

  const queue: TreeNode[] = [root];
  while (queue.length > 0) {
    const curr = queue.shift()!;
    values.push(curr.value);
    ids.push(curr.id);
    if (curr.left) queue.push(curr.left);
    if (curr.right) queue.push(curr.right);
  }
  return { values, ids };
}

// --------------------------------------------------------
// Tree Layout Calculation (Inorder x-coord, depth y-coord)
// --------------------------------------------------------
export function computeTreeLayout(
  root: TreeNode | null,
  width: number = 440,
  height: number = 320
): { nodes: TreeLayoutNode[]; edges: TreeLayoutEdge[] } {
  if (!root) return { nodes: [], edges: [] };

  const nodes: TreeLayoutNode[] = [];
  const edges: TreeLayoutEdge[] = [];
  const nodeMap = new Map<string, TreeLayoutNode>();

  let inorderIndex = 0;
  // First count total nodes for horizontal spacing
  const { ids } = inorderTraversal(root);
  const total = ids.length;
  const colWidth = width / (total + 1);

  function assignPositions(node: TreeNode | null, depth: number) {
    if (!node) return;
    assignPositions(node.left, depth + 1);

    const x = Math.round((inorderIndex + 1) * colWidth);
    const y = Math.min(height - 35, 45 + depth * 55);
    inorderIndex++;

    const layoutNode: TreeLayoutNode = {
      id: node.id,
      value: node.value,
      x,
      y,
      leftId: node.left ? node.left.id : null,
      rightId: node.right ? node.right.id : null,
    };
    nodes.push(layoutNode);
    nodeMap.set(node.id, layoutNode);

    assignPositions(node.right, depth + 1);
  }

  assignPositions(root, 0);

  // Build edges
  for (const n of nodes) {
    if (n.leftId && nodeMap.has(n.leftId)) {
      const target = nodeMap.get(n.leftId)!;
      edges.push({
        fromId: n.id,
        toId: target.id,
        x1: n.x,
        y1: n.y,
        x2: target.x,
        y2: target.y,
      });
    }
    if (n.rightId && nodeMap.has(n.rightId)) {
      const target = nodeMap.get(n.rightId)!;
      edges.push({
        fromId: n.id,
        toId: target.id,
        x1: n.x,
        y1: n.y,
        x2: target.x,
        y2: target.y,
      });
    }
  }

  return { nodes, edges };
}

// --------------------------------------------------------
// Binary Heap (Array-backed, Min or Max)
// --------------------------------------------------------
export type HeapType = 'min' | 'max';

export interface HeapOpFrame {
  heap: number[];
  activeIndices: number[];
  swappedIndices: [number, number] | null;
  log: string;
}

export class BinaryHeap {
  items: number[];
  type: HeapType;

  constructor(type: HeapType = 'min', initial: number[] = []) {
    this.type = type;
    this.items = [];
    for (const val of initial) {
      this.insert(val);
    }
  }

  private compare(a: number, b: number): boolean {
    return this.type === 'min' ? a < b : a > b;
  }

  insert(value: number): HeapOpFrame[] {
    const frames: HeapOpFrame[] = [];
    this.items.push(value);
    let idx = this.items.length - 1;

    frames.push({
      heap: [...this.items],
      activeIndices: [idx],
      swappedIndices: null,
      log: `Pushed ${value} at end (index ${idx})`,
    });

    // Sift-up
    while (idx > 0) {
      const parentIdx = Math.floor((idx - 1) / 2);
      if (this.compare(this.items[idx], this.items[parentIdx])) {
        // Swap
        const parentVal = this.items[parentIdx];
        const currVal = this.items[idx];
        this.items[parentIdx] = currVal;
        this.items[idx] = parentVal;

        frames.push({
          heap: [...this.items],
          activeIndices: [parentIdx, idx],
          swappedIndices: [parentIdx, idx],
          log: `Sift up: swapped ${currVal} with parent ${parentVal}`,
        });

        idx = parentIdx;
      } else {
        break;
      }
    }

    frames.push({
      heap: [...this.items],
      activeIndices: [idx],
      swappedIndices: null,
      log: `Value ${value} settled at index ${idx}. Heap invariant satisfied.`,
    });

    return frames;
  }

  extractRoot(): { value: number | null; frames: HeapOpFrame[] } {
    const frames: HeapOpFrame[] = [];
    if (this.items.length === 0) {
      return { value: null, frames };
    }

    const rootVal = this.items[0];
    const lastVal = this.items.pop()!;

    if (this.items.length === 0) {
      frames.push({
        heap: [],
        activeIndices: [],
        swappedIndices: null,
        log: `Extracted only element ${rootVal}`,
      });
      return { value: rootVal, frames };
    }

    this.items[0] = lastVal;
    frames.push({
      heap: [...this.items],
      activeIndices: [0],
      swappedIndices: null,
      log: `Moved last element ${lastVal} to root. Sifting down...`,
    });

    // Sift-down
    let idx = 0;
    const len = this.items.length;

    while (true) {
      const leftIdx = 2 * idx + 1;
      const rightIdx = 2 * idx + 2;
      let targetIdx = idx;

      if (leftIdx < len && this.compare(this.items[leftIdx], this.items[targetIdx])) {
        targetIdx = leftIdx;
      }
      if (rightIdx < len && this.compare(this.items[rightIdx], this.items[targetIdx])) {
        targetIdx = rightIdx;
      }

      if (targetIdx !== idx) {
        const temp = this.items[idx];
        this.items[idx] = this.items[targetIdx];
        this.items[targetIdx] = temp;

        frames.push({
          heap: [...this.items],
          activeIndices: [idx, targetIdx],
          swappedIndices: [idx, targetIdx],
          log: `Sift down: swapped ${temp} with child ${this.items[idx]}`,
        });

        idx = targetIdx;
      } else {
        break;
      }
    }

    frames.push({
      heap: [...this.items],
      activeIndices: [idx],
      swappedIndices: null,
      log: `Heap invariant restored. New root is ${this.items[0]}.`,
    });

    return { value: rootVal, frames };
  }

  verifyInvariant(): boolean {
    for (let i = 0; i < this.items.length; i++) {
      const left = 2 * i + 1;
      const right = 2 * i + 2;
      if (left < this.items.length) {
        if (this.compare(this.items[left], this.items[i])) return false;
      }
      if (right < this.items.length) {
        if (this.compare(this.items[right], this.items[i])) return false;
      }
    }
    return true;
  }
}

export function computeHeapLayout(
  heap: number[],
  width: number = 440,
  height: number = 320
): { nodes: TreeLayoutNode[]; edges: TreeLayoutEdge[] } {
  const nodes: TreeLayoutNode[] = [];
  const edges: TreeLayoutEdge[] = [];

  for (let i = 0; i < heap.length; i++) {
    const level = Math.floor(Math.log2(i + 1));
    const offset = i - ((1 << level) - 1);
    const countInLevel = 1 << level;
    const x = Math.round(((offset + 1) / (countInLevel + 1)) * width);
    const y = Math.min(height - 35, 45 + level * 65);

    const leftIdx = 2 * i + 1;
    const rightIdx = 2 * i + 2;

    nodes.push({
      id: `heap-${i}`,
      value: heap[i],
      x,
      y,
      leftId: leftIdx < heap.length ? `heap-${leftIdx}` : null,
      rightId: rightIdx < heap.length ? `heap-${rightIdx}` : null,
    });
  }

  for (const n of nodes) {
    if (n.leftId) {
      const child = nodes.find((x) => x.id === n.leftId);
      if (child) {
        edges.push({
          fromId: n.id,
          toId: child.id,
          x1: n.x,
          y1: n.y,
          x2: child.x,
          y2: child.y,
        });
      }
    }
    if (n.rightId) {
      const child = nodes.find((x) => x.id === n.rightId);
      if (child) {
        edges.push({
          fromId: n.id,
          toId: child.id,
          x1: n.x,
          y1: n.y,
          x2: child.x,
          y2: child.y,
        });
      }
    }
  }

  return { nodes, edges };
}
