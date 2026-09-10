import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { ControlBar } from '../components/ControlBar';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';
import { PSEUDOCODE_MAP } from '../data/pseudocode';
import {
  TreeNode,
  insertBST,
  searchBST,
  insertBinaryTree,
  inorderTraversal,
  preorderTraversal,
  postorderTraversal,
  computeTreeLayout,
  BinaryHeap,
  computeHeapLayout,
  HeapType,
} from './treeEngine';

interface TreeVisualizerProps {
  variant?: 'binary-tree' | 'bst' | 'heap';
}

interface Frame {
  highlightNodeIds: string[];
  activeNodeId: string | null;
  activeLine: number;
  log: string;
}

export const TreeVisualizer: React.FC<TreeVisualizerProps> = ({ variant = 'binary-tree' }) => {
  // Tree state
  const [treeRoot, setTreeRoot] = useState<TreeNode | null>(() => {
    let root: TreeNode | null = null;
    const initial = variant === 'bst' ? [40, 20, 60, 10, 30, 50, 70] : [1, 2, 3, 4, 5, 6, 7];
    for (const v of initial) {
      root = variant === 'bst' ? insertBST(root, v) : insertBinaryTree(root, v);
    }
    return root;
  });

  // Heap state
  const [heapType, setHeapType] = useState<HeapType>('min');
  const [heapInstance, setHeapInstance] = useState<BinaryHeap>(() => new BinaryHeap('min', [12, 18, 25, 30, 42, 55, 68]));

  // Controls & Inputs
  const [inputVal, setInputVal] = useState('');
  const [searchVal, setSearchVal] = useState('');
  const [traversalOrder, setTraversalOrder] = useState<'inorder' | 'preorder' | 'postorder'>('inorder');

  // Playback
  const [frames, setFrames] = useState<Frame[]>([]);
  const [frameIdx, setFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  // Compute Layout
  const layout = useMemo(() => {
    if (variant === 'heap') {
      return computeHeapLayout(heapInstance.items, 440, 320);
    }
    return computeTreeLayout(treeRoot, 440, 320);
  }, [variant, treeRoot, heapInstance]);

  // Generate Traversal Frames
  const generateTraversalFrames = useCallback(() => {
    if (variant === 'heap') return;
    let res: { values: number[]; ids: string[] };
    if (traversalOrder === 'preorder') {
      res = preorderTraversal(treeRoot);
    } else if (traversalOrder === 'postorder') {
      res = postorderTraversal(treeRoot);
    } else {
      res = inorderTraversal(treeRoot);
    }

    const generated: Frame[] = [
      {
        highlightNodeIds: [],
        activeNodeId: null,
        activeLine: 1,
        log: `Starting ${traversalOrder} traversal on tree...`,
      },
    ];

    const visitedIds: string[] = [];
    for (let i = 0; i < res.ids.length; i++) {
      visitedIds.push(res.ids[i]);
      generated.push({
        highlightNodeIds: [...visitedIds],
        activeNodeId: res.ids[i],
        activeLine: 3,
        log: `Visited node with value ${res.values[i]} (${i + 1}/${res.ids.length})`,
      });
    }

    generated.push({
      highlightNodeIds: [...visitedIds],
      activeNodeId: null,
      activeLine: 5,
      log: `Traversal completed: [${res.values.join(', ')}]`,
    });

    setFrames(generated);
    setFrameIdx(0);
  }, [variant, treeRoot, traversalOrder]);

  // Sync frames on tree or traversal change
  useEffect(() => {
    generateTraversalFrames();
  }, [generateTraversalFrames]);

  // Timer loop for animation
  useEffect(() => {
    if (!isPlaying) return;
    const timer = window.setInterval(() => {
      setFrameIdx((prev) => {
        if (prev >= frames.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, Math.max(120, Math.round(750 / speed)));
    return () => clearInterval(timer);
  }, [isPlaying, speed, frames.length]);

  // Insert handler
  const handleInsert = (e: React.FormEvent) => {
    e.preventDefault();
    const num = parseInt(inputVal, 10);
    if (isNaN(num)) return;

    if (variant === 'heap') {
      const newHeap = new BinaryHeap(heapType, heapInstance.items);
      const opFrames = newHeap.insert(num);
      setHeapInstance(newHeap);

      const animFrames: Frame[] = opFrames.map((f, i) => ({
        highlightNodeIds: f.activeIndices.map((idx) => `heap-${idx}`),
        activeNodeId: f.activeIndices[0] !== undefined ? `heap-${f.activeIndices[0]}` : null,
        activeLine: i + 1,
        log: f.log,
      }));
      setFrames(animFrames);
      setFrameIdx(0);
      setIsPlaying(true);
    } else if (variant === 'bst') {
      const newRoot = insertBST(treeRoot ? { ...treeRoot } : null, num);
      setTreeRoot(newRoot);
    } else {
      const newRoot = insertBinaryTree(treeRoot ? { ...treeRoot } : null, num);
      setTreeRoot(newRoot);
    }

    setInputVal('');
  };

  // Search handler (BST only)
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const num = parseInt(searchVal, 10);
    if (isNaN(num)) return;

    const { path, found } = searchBST(treeRoot, num);
    const animFrames: Frame[] = [
      {
        highlightNodeIds: [],
        activeNodeId: null,
        activeLine: 1,
        log: `Searching for ${num} in BST...`,
      },
    ];

    const currentPath: string[] = [];
    for (let i = 0; i < path.length; i++) {
      currentPath.push(path[i]);
      animFrames.push({
        highlightNodeIds: [...currentPath],
        activeNodeId: path[i],
        activeLine: 2,
        log: `Checking node ${path[i]} against target ${num}`,
      });
    }

    animFrames.push({
      highlightNodeIds: [...currentPath],
      activeNodeId: found ? path[path.length - 1] : null,
      activeLine: found ? 4 : 5,
      log: found ? `Found ${num} in BST!` : `Target ${num} not found in BST.`,
    });

    setFrames(animFrames);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // Extract root for Heap
  const handleExtractRoot = () => {
    if (variant !== 'heap') return;
    const newHeap = new BinaryHeap(heapType, heapInstance.items);
    const { value, frames: opFrames } = newHeap.extractRoot();
    if (value === null) return;
    setHeapInstance(newHeap);

    const animFrames: Frame[] = opFrames.map((f, i) => ({
      highlightNodeIds: f.activeIndices.map((idx) => `heap-${idx}`),
      activeNodeId: f.activeIndices[0] !== undefined ? `heap-${f.activeIndices[0]}` : null,
      activeLine: i + 1,
      log: f.log,
    }));
    setFrames(animFrames);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // Toggle Heap type
  const handleToggleHeapType = (type: HeapType) => {
    setHeapType(type);
    const rebuilt = new BinaryHeap(type, heapInstance.items);
    setHeapInstance(rebuilt);
  };

  // Reset to default
  const handleReset = () => {
    setIsPlaying(false);
    if (variant === 'heap') {
      setHeapInstance(new BinaryHeap(heapType, [12, 18, 25, 30, 42, 55, 68]));
    } else if (variant === 'bst') {
      let root: TreeNode | null = null;
      for (const v of [40, 20, 60, 10, 30, 50, 70]) {
        root = insertBST(root, v);
      }
      setTreeRoot(root);
    } else {
      let root: TreeNode | null = null;
      for (const v of [1, 2, 3, 4, 5, 6, 7]) {
        root = insertBinaryTree(root, v);
      }
      setTreeRoot(root);
    }
  };

  const currentFrame = frames[frameIdx] || {
    highlightNodeIds: [],
    activeNodeId: null,
    activeLine: 0,
    log: 'Ready',
  };

  return (
    <div className="space-y-4">
      {/* Control Bar */}
      <ControlBar
        isPlaying={isPlaying}
        onPlayPause={() => setIsPlaying(!isPlaying)}
        onStepForward={() => {
          setIsPlaying(false);
          setFrameIdx((p) => Math.min(frames.length - 1, p + 1));
        }}
        onStepBack={() => {
          setIsPlaying(false);
          setFrameIdx((p) => Math.max(0, p - 1));
        }}
        onReset={handleReset}
        onRandomize={() => {
          if (variant === 'heap') {
            const randoms = Array.from({ length: 7 }, () => Math.floor(Math.random() * 90) + 10);
            setHeapInstance(new BinaryHeap(heapType, randoms));
          } else {
            const randoms = Array.from({ length: 7 }, () => Math.floor(Math.random() * 90) + 10);
            let root: TreeNode | null = null;
            for (const r of randoms) {
              root = variant === 'bst' ? insertBST(root, r) : insertBinaryTree(root, r);
            }
            setTreeRoot(root);
          }
        }}
        speed={speed}
        onSpeedChange={setSpeed}
      />

      {/* Operation Toolbar */}
      <div className="flex flex-wrap items-center gap-3 p-3 bg-surface/50 border border-line rounded-xl text-xs">
        {/* Insert form */}
        <form onSubmit={handleInsert} className="flex items-center gap-2">
          <input
            type="number"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            placeholder="Value..."
            className="w-20 px-2 py-1 bg-surface border border-line rounded text-ink focus:outline-none focus:border-mint"
          />
          <button
            type="submit"
            className="px-3 py-1 bg-mint text-canvas font-medium rounded hover:bg-mint/90 transition"
          >
            Insert
          </button>
        </form>

        {/* BST Search */}
        {variant === 'bst' && (
          <form onSubmit={handleSearch} className="flex items-center gap-2 border-l border-line pl-3">
            <input
              type="number"
              value={searchVal}
              onChange={(e) => setSearchVal(e.target.value)}
              placeholder="Search..."
              className="w-20 px-2 py-1 bg-surface border border-line rounded text-ink focus:outline-none focus:border-violet"
            />
            <button
              type="submit"
              className="px-3 py-1 bg-violet text-canvas font-medium rounded hover:bg-violet/90 transition"
            >
              Search
            </button>
          </form>
        )}

        {/* Heap Operations */}
        {variant === 'heap' && (
          <div className="flex items-center gap-2 border-l border-line pl-3">
            <button
              onClick={handleExtractRoot}
              className="px-3 py-1 bg-amber text-canvas font-medium rounded hover:bg-amber/90 transition"
            >
              Extract Root ({heapType === 'min' ? 'Min' : 'Max'})
            </button>
            <div className="flex rounded border border-line overflow-hidden">
              <button
                onClick={() => handleToggleHeapType('min')}
                className={`px-2 py-1 ${heapType === 'min' ? 'bg-mint text-canvas' : 'bg-surface text-muted'}`}
              >
                Min-Heap
              </button>
              <button
                onClick={() => handleToggleHeapType('max')}
                className={`px-2 py-1 ${heapType === 'max' ? 'bg-mint text-canvas' : 'bg-surface text-muted'}`}
              >
                Max-Heap
              </button>
            </div>
          </div>
        )}

        {/* Traversal selector (Tree/BST only) */}
        {variant !== 'heap' && (
          <div className="flex items-center gap-2 ml-auto border-l border-line pl-3">
            <span className="text-muted">Traversal:</span>
            {(['inorder', 'preorder', 'postorder'] as const).map((order) => (
              <button
                key={order}
                onClick={() => setTraversalOrder(order)}
                className={`px-2 py-1 rounded capitalize transition ${
                  traversalOrder === order ? 'bg-white/10 text-ink font-semibold' : 'text-muted hover:text-ink'
                }`}
              >
                {order}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Main Visualizer Area */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8 space-y-3">
          <VisualizerCanvas
            metrics={[
              {
                label: 'Total Nodes',
                value: layout.nodes.length.toString(),
                color: 'var(--c-mint)',
              },
              {
                label: variant === 'heap' ? 'Heap Array' : 'Mode',
                value:
                  variant === 'heap'
                    ? `[${heapInstance.items.join(', ')}]`
                    : variant === 'bst'
                    ? 'Binary Search Tree'
                    : 'Binary Tree',
                color: 'var(--c-violet)',
              },
            ]}
            legend={[
              { label: 'Normal Node', color: 'var(--c-steel)' },
              { label: 'Active / Searched', color: 'var(--c-amber)' },
              { label: 'Traversed / Settled', color: 'var(--c-mint)' },
            ]}
          >
            <svg
              data-testid="tree-svg"
              className="w-full h-80 select-none"
              viewBox="0 0 440 320"
            >
              {/* Edges */}
              {layout.edges.map((e, idx) => (
                <line
                  key={`edge-${idx}`}
                  x1={e.x1}
                  y1={e.y1}
                  x2={e.x2}
                  y2={e.y2}
                  stroke="var(--c-line)"
                  strokeWidth="2"
                />
              ))}

              {/* Nodes */}
              {layout.nodes.map((node) => {
                const isHighlighted = currentFrame.highlightNodeIds.includes(node.id);
                const isActive = currentFrame.activeNodeId === node.id;

                let fill = 'var(--c-surface)';
                let stroke = 'var(--c-line)';
                let textColor = 'var(--c-ink)';

                if (isActive) {
                  fill = 'var(--c-amber)';
                  stroke = 'var(--c-amber)';
                  textColor = '#0f141c';
                } else if (isHighlighted) {
                  fill = 'var(--c-mint)';
                  stroke = 'var(--c-mint)';
                  textColor = '#0f141c';
                }

                return (
                  <g key={node.id} className="transition-colors duration-150">
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r="16"
                      fill={fill}
                      stroke={stroke}
                      strokeWidth="2"
                    />
                    <text
                      x={node.x}
                      y={node.y + 4}
                      textAnchor="middle"
                      fill={textColor}
                      fontSize="11"
                      fontWeight="bold"
                      className="font-mono pointer-events-none"
                    >
                      {node.value}
                    </text>
                  </g>
                );
              })}
            </svg>
          </VisualizerCanvas>

          {/* Activity Log */}
          <div className="p-3 bg-surface/40 border border-line rounded-xl font-mono text-xs text-muted flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-mint" />
            <span>{currentFrame.log}</span>
          </div>
        </div>

        {/* Pseudo-code panel */}
        <div className="lg:col-span-4">
          <PseudoCodePanel
            title={
              variant === 'heap'
                ? PSEUDOCODE_MAP.heap.title
                : variant === 'bst'
                ? PSEUDOCODE_MAP.bst.title
                : PSEUDOCODE_MAP['binary-tree'].title
            }
            lines={
              variant === 'heap'
                ? PSEUDOCODE_MAP.heap.lines
                : variant === 'bst'
                ? PSEUDOCODE_MAP.bst.lines
                : PSEUDOCODE_MAP['binary-tree'].lines
            }
            activeLine={currentFrame.activeLine}
            timeComplexity={
              variant === 'heap'
                ? PSEUDOCODE_MAP.heap.timeComplexity
                : variant === 'bst'
                ? PSEUDOCODE_MAP.bst.timeComplexity
                : PSEUDOCODE_MAP['binary-tree'].timeComplexity
            }
            spaceComplexity={
              variant === 'heap'
                ? PSEUDOCODE_MAP.heap.spaceComplexity
                : variant === 'bst'
                ? PSEUDOCODE_MAP.bst.spaceComplexity
                : PSEUDOCODE_MAP['binary-tree'].spaceComplexity
            }
          />
        </div>
      </div>
    </div>
  );
};
