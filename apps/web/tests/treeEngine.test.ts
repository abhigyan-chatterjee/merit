import { describe, it, expect, beforeEach } from 'vitest';
import {
  TreeNode,
  createTreeNode,
  resetNodeIdCounter,
  insertBST,
  searchBST,
  insertBinaryTree,
  inorderTraversal,
  preorderTraversal,
  postorderTraversal,
  levelOrderTraversal,
  BinaryHeap,
} from '../src/visualizers/treeEngine';

describe('Tree Engine & Invariant Property Tests (D2)', () => {
  beforeEach(() => {
    resetNodeIdCounter();
  });

  describe('BST Invariant', () => {
    it('in-order traversal of BST is strictly non-decreasing after random insertions', () => {
      // Run 50 property trials with random arrays
      for (let trial = 0; trial < 50; trial++) {
        const count = 10 + Math.floor(Math.random() * 20);
        const randomValues: number[] = [];
        for (let i = 0; i < count; i++) {
          randomValues.push(Math.floor(Math.random() * 200) - 100);
        }

        let root: TreeNode | null = null;
        for (const val of randomValues) {
          root = insertBST(root, val);
        }

        const { values: inorder } = inorderTraversal(root);
        // Verify in-order traversal is sorted
        for (let i = 0; i < inorder.length - 1; i++) {
          expect(inorder[i]).toBeLessThanOrEqual(inorder[i + 1]);
        }
      }
    });

    it('finds existing elements and misses absent elements via BST search', () => {
      const values = [50, 30, 70, 20, 40, 60, 80];
      let root: TreeNode | null = null;
      for (const v of values) {
        root = insertBST(root, v);
      }

      for (const v of values) {
        const res = searchBST(root, v);
        expect(res.found).toBe(true);
        expect(res.path.length).toBeGreaterThan(0);
      }

      const notFound = searchBST(root, 999);
      expect(notFound.found).toBe(false);
    });
  });

  describe('Heap Invariant', () => {
    it('maintains min-heap invariant after random inserts and root extractions', () => {
      for (let trial = 0; trial < 25; trial++) {
        const heap = new BinaryHeap('min');
        const count = 15;
        for (let i = 0; i < count; i++) {
          heap.insert(Math.floor(Math.random() * 100));
          expect(heap.verifyInvariant()).toBe(true);
        }

        let lastExtracted = -Infinity;
        while (heap.items.length > 0) {
          const { value } = heap.extractRoot();
          expect(value).not.toBeNull();
          expect(value!).toBeGreaterThanOrEqual(lastExtracted);
          lastExtracted = value!;
          expect(heap.verifyInvariant()).toBe(true);
        }
      }
    });

    it('maintains max-heap invariant after random inserts and root extractions', () => {
      for (let trial = 0; trial < 25; trial++) {
        const heap = new BinaryHeap('max');
        const count = 15;
        for (let i = 0; i < count; i++) {
          heap.insert(Math.floor(Math.random() * 100));
          expect(heap.verifyInvariant()).toBe(true);
        }

        let lastExtracted = Infinity;
        while (heap.items.length > 0) {
          const { value } = heap.extractRoot();
          expect(value).not.toBeNull();
          expect(value!).toBeLessThanOrEqual(lastExtracted);
          lastExtracted = value!;
          expect(heap.verifyInvariant()).toBe(true);
        }
      }
    });
  });

  describe('Traversals on Fixed Fixture Tree', () => {
    // Fixed fixture tree:
    //         1
    //       /   \
    //      2     3
    //     / \   / \
    //    4   5 6   7
    let fixtureTree: TreeNode;

    beforeEach(() => {
      fixtureTree = createTreeNode(1, 'n1');
      fixtureTree.left = createTreeNode(2, 'n2');
      fixtureTree.right = createTreeNode(3, 'n3');
      fixtureTree.left.left = createTreeNode(4, 'n4');
      fixtureTree.left.right = createTreeNode(5, 'n5');
      fixtureTree.right.left = createTreeNode(6, 'n6');
      fixtureTree.right.right = createTreeNode(7, 'n7');
    });

    it('computes exact in-order traversal: 4, 2, 5, 1, 6, 3, 7', () => {
      const { values } = inorderTraversal(fixtureTree);
      expect(values).toEqual([4, 2, 5, 1, 6, 3, 7]);
    });

    it('computes exact pre-order traversal: 1, 2, 4, 5, 3, 6, 7', () => {
      const { values } = preorderTraversal(fixtureTree);
      expect(values).toEqual([1, 2, 4, 5, 3, 6, 7]);
    });

    it('computes exact post-order traversal: 4, 5, 2, 6, 7, 3, 1', () => {
      const { values } = postorderTraversal(fixtureTree);
      expect(values).toEqual([4, 5, 2, 6, 7, 3, 1]);
    });

    it('computes exact level-order traversal: 1, 2, 3, 4, 5, 6, 7', () => {
      const { values } = levelOrderTraversal(fixtureTree);
      expect(values).toEqual([1, 2, 3, 4, 5, 6, 7]);
    });
  });

  describe('Binary Tree Level-Order Insertion', () => {
    it('fills open slots in level-order fashion', () => {
      let root: TreeNode | null = null;
      for (const v of [10, 20, 30, 40, 50]) {
        root = insertBinaryTree(root, v);
      }
      const { values } = levelOrderTraversal(root);
      expect(values).toEqual([10, 20, 30, 40, 50]);
    });
  });
});
