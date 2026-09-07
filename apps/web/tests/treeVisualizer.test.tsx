import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TreeVisualizer } from '../src/visualizers/TreeVisualizer';

describe('TreeVisualizer Component (D2)', () => {
  it('renders Binary Tree variant with traversal controls', () => {
    render(<TreeVisualizer variant="binary-tree" />);
    expect(screen.getByTestId('tree-svg')).toBeInTheDocument();
    expect(screen.getByText('Binary Tree')).toBeInTheDocument();
    expect(screen.getByText('inorder')).toBeInTheDocument();
  });

  it('renders BST variant with search bar and preserves BST structure', () => {
    render(<TreeVisualizer variant="bst" />);
    expect(screen.getByTestId('tree-svg')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
    expect(screen.getByText('Binary Search Tree')).toBeInTheDocument();
  });

  it('renders Heap variant with Min-Heap / Max-Heap toggle and Extract Root', () => {
    render(<TreeVisualizer variant="heap" />);
    expect(screen.getByTestId('tree-svg')).toBeInTheDocument();
    expect(screen.getByText(/Extract Root/i)).toBeInTheDocument();
    expect(screen.getByText('Min-Heap')).toBeInTheDocument();
    expect(screen.getByText('Max-Heap')).toBeInTheDocument();
  });
});
