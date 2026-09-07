import React, { useState, useEffect } from 'react';
import { ControlBar } from '../components/ControlBar';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';
import { PSEUDOCODE_MAP } from '../data/pseudocode';

interface TreeVisualizerProps {
  variant?: 'binary-tree' | 'bst' | 'heap';
}

export const TreeVisualizer: React.FC<TreeVisualizerProps> = ({ variant = 'binary-tree' }) => {
  const [values, setValues] = useState<number[]>([40, 22, 65, 11, 30, 52, 85]);
  const [inputVal, setInputVal] = useState('');
  const [traversalOrder, setTraversalOrder] = useState<'inorder' | 'preorder' | 'postorder'>('inorder');
  const [visitedSequence, setVisitedSequence] = useState<number[]>([]);
  const [stepIdx, setStepIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  const computeTraversalOrder = (arr: number[], order: 'inorder' | 'preorder' | 'postorder') => {
    const seq: number[] = [];
    const dfs = (idx: number) => {
      if (idx >= arr.length) return;
      if (order === 'preorder') seq.push(idx);
      dfs(2 * idx + 1);
      if (order === 'inorder') seq.push(idx);
      dfs(2 * idx + 2);
      if (order === 'postorder') seq.push(idx);
    };
    dfs(0);
    return seq;
  };

  useEffect(() => {
    const seq = computeTraversalOrder(values, traversalOrder);
    setVisitedSequence(seq);
    setStepIdx(0);
  }, [values, traversalOrder]);

  useEffect(() => {
    if (!isPlaying) return;
    const timer = window.setInterval(() => {
      setStepIdx((prev) => {
        if (prev >= visitedSequence.length) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, Math.max(150, Math.round(700 / speed)));
    return () => clearInterval(timer);
  }, [isPlaying, speed, visitedSequence.length]);

  const handleInsertNode = (e: React.FormEvent) => {
    e.preventDefault();
    const num = parseInt(inputVal, 10);
    if (isNaN(num)) return;
    if (values.length >= 15) {
      alert('Tree max display depth reached (15 nodes)');
      return;
    }
    const next = [...values, num];
    if (variant === 'bst') {
      next.sort((a, b) => a - b);
    } else if (variant === 'heap') {
      next.sort((a, b) => a - b);
    }
    setValues(next);
    setInputVal('');
  };

  // Fixed coordinates for complete binary tree up to 15 nodes
  const getCoords = (index: number): { x: number; y: number } => {
    const level = Math.floor(Math.log2(index + 1));
    const offsetInLevel = index - ((1 << level) - 1);
    const nodesInLevel = 1 << level;
    const width = 440;
    const segment = width / (nodesInLevel + 1);
    return {
      x: segment * (offsetInLevel + 1),
      y: 50 + level * 75
    };
  };

  const activeVisitedIndices = visitedSequence.slice(0, stepIdx);
  const currentActiveIndex = visitedSequence[stepIdx - 1];

  const pseudo = PSEUDOCODE_MAP.tree;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl border border-line bg-surface">
        <div className="flex flex-wrap items-center gap-2">
          {(['inorder', 'preorder', 'postorder'] as const).map((ord) => (
            <button
              key={ord}
              onClick={() => setTraversalOrder(ord)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold capitalize cursor-pointer ${
                traversalOrder === ord
                  ? 'bg-mint text-canvas'
                  : 'bg-canvas text-muted border border-line'
              }`}
            >
              {ord} Traversal
            </button>
          ))}
        </div>

        <form onSubmit={handleInsertNode} className="flex items-center gap-2">
          <input
            type="number"
            placeholder="Insert key (e.g. 48)..."
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            className="w-40 px-3 py-1.5 rounded-lg bg-canvas border border-line text-xs font-mono text-ink focus:outline-none focus:border-mint"
          />
          <button
            type="submit"
            className="px-3.5 py-1.5 rounded-lg bg-mint text-canvas font-semibold text-xs hover:brightness-110 transition cursor-pointer"
          >
            + Insert Node
          </button>
        </form>
      </div>

      <ControlBar
        isPlaying={isPlaying}
        onPlayPause={() => setIsPlaying((p) => !p)}
        onStep={() => setStepIdx((i) => Math.min(visitedSequence.length, i + 1))}
        onReset={() => {
          setIsPlaying(false);
          setStepIdx(0);
        }}
        onRandomize={() =>
          setValues(
            Array.from({ length: 7 }, () => Math.floor(Math.random() * 89) + 10).sort((a, b) => a - b)
          )
        }
        speed={speed}
        onSpeedChange={setSpeed}
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8">
          <VisualizerCanvas
            metrics={[
              {
                label: 'Traversal Sequence',
                value: activeVisitedIndices.map((idx) => values[idx]).join(' → ') || 'Ready',
                color: 'var(--c-mint)'
              }
            ]}
          >
            <svg className="w-full h-72 select-none" viewBox="0 0 440 290">
              {/* Edges */}
              {values.map((_, idx) => {
                if (idx === 0) return null;
                const parentIdx = Math.floor((idx - 1) / 2);
                const p = getCoords(parentIdx);
                const c = getCoords(idx);
                return (
                  <line
                    key={`edge-${idx}`}
                    x1={p.x}
                    y1={p.y}
                    x2={c.x}
                    y2={c.y}
                    stroke="var(--c-steel)"
                    strokeWidth={2}
                  />
                );
              })}

              {/* Nodes */}
              {values.map((val, idx) => {
                const { x, y } = getCoords(idx);
                const isVisited = activeVisitedIndices.includes(idx);
                const isCurrent = currentActiveIndex === idx;

                let fill = 'var(--c-surface)';
                let stroke = 'var(--c-steel)';
                if (isCurrent) {
                  fill = 'var(--c-amber)';
                  stroke = 'var(--c-amber)';
                } else if (isVisited) {
                  fill = 'var(--c-mint)';
                  stroke = 'var(--c-mint)';
                }

                return (
                  <g key={idx}>
                    <circle
                      cx={x}
                      cy={y}
                      r={19}
                      fill={fill}
                      stroke={stroke}
                      strokeWidth={2.5}
                    />
                    <text
                      x={x}
                      y={y + 4}
                      textAnchor="middle"
                      className="font-mono text-xs font-bold"
                      fill={isCurrent || isVisited ? 'var(--c-canvas)' : 'var(--c-ink)'}
                    >
                      {val}
                    </text>
                  </g>
                );
              })}
            </svg>
          </VisualizerCanvas>
        </div>

        <div className="lg:col-span-4">
          <PseudoCodePanel
            title={`${traversalOrder.toUpperCase()} Tree Traversal`}
            lines={pseudo.lines}
            activeLine={stepIdx > 0 ? 3 : 0}
            timeComplexity="O(n)"
            spaceComplexity="O(h)"
            logs={activeVisitedIndices.map(
              (idx, step) => `Step #${step + 1}: Visited node key ${values[idx]}`
            )}
          />
        </div>
      </div>
    </div>
  );
};
