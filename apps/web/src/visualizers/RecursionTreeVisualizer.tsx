import React, { useState, useEffect } from 'react';
import { ControlBar } from '../components/ControlBar';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';

interface RecNode {
  id: string;
  label: string;
  arg: number;
  returnValue: number | null;
  x: number;
  y: number;
  parentId?: string;
  isMemoHit?: boolean;
}

interface StackFrameItem {
  id: string;
  func: string;
  arg: number;
  ret: number | null;
}

interface Frame {
  activeNodeId: string | null;
  memoizedNodeIds: string[];
  callStack: StackFrameItem[];
  activeLine: number;
  log: string;
}

export const RecursionTreeVisualizer: React.FC = () => {
  const [mode, setMode] = useState<'fib' | 'fact'>('fib');
  const [inputN, setInputN] = useState<number>(4);
  const [useMemoization, setUseMemoization] = useState(false);

  const [nodes, setNodes] = useState<RecNode[]>([]);
  const [edges, setEdges] = useState<{ x1: number; y1: number; x2: number; y2: number }[]>([]);
  const [frames, setFrames] = useState<Frame[]>([]);
  const [frameIdx, setFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  // Generate fib tree layout and execution trace
  const computeFibTrace = (n: number, memoEnabled: boolean) => {
    const treeNodes: RecNode[] = [];
    const treeEdges: { x1: number; y1: number; x2: number; y2: number }[] = [];
    const animFrames: Frame[] = [];
    const memo = new Map<number, number>();
    const seenArgs = new Set<number>();
    let idCounter = 1;

    animFrames.push({
      activeNodeId: null,
      memoizedNodeIds: [],
      callStack: [],
      activeLine: 1,
      log: `Starting fib(${n}) execution ${memoEnabled ? 'with Memoization cache' : 'without memoization'}.`,
    });

    function recurse(
      val: number,
      depth: number,
      x: number,
      span: number,
      parentId?: string,
      parentCoords?: { x: number; y: number }
    ): { id: string; result: number } {
      const nodeId = `fib-${idCounter++}`;
      const isHit = memoEnabled && memo.has(val);

      const node: RecNode = {
        id: nodeId,
        label: `fib(${val})`,
        arg: val,
        returnValue: null,
        x,
        y: 45 + depth * 55,
        parentId,
        isMemoHit: isHit,
      };
      treeNodes.push(node);

      if (parentCoords) {
        treeEdges.push({
          x1: parentCoords.x,
          y1: parentCoords.y,
          x2: x,
          y2: node.y,
        });
      }

      animFrames.push({
        activeNodeId: nodeId,
        memoizedNodeIds: isHit ? [nodeId] : [],
        callStack: [{ id: nodeId, func: 'fib', arg: val, ret: null }],
        activeLine: isHit ? 4 : 2,
        log: isHit
          ? `MEMO HIT: fib(${val}) already cached = ${memo.get(val)}! Branch pruned.`
          : `Call fib(${val})`,
      });

      if (isHit) {
        node.returnValue = memo.get(val)!;
        return { id: nodeId, result: node.returnValue };
      }

      if (val <= 1) {
        node.returnValue = val;
        memo.set(val, val);
        animFrames.push({
          activeNodeId: nodeId,
          memoizedNodeIds: [],
          callStack: [],
          activeLine: 3,
          log: `Base case fib(${val}) = ${val}`,
        });
        return { id: nodeId, result: val };
      }

      // Left branch fib(val - 1)
      const leftChild = recurse(val - 1, depth + 1, x - span / 2, span / 2, nodeId, { x, y: node.y });
      // Right branch fib(val - 2)
      const rightChild = recurse(val - 2, depth + 1, x + span / 2, span / 2, nodeId, { x, y: node.y });

      const total = leftChild.result + rightChild.result;
      node.returnValue = total;
      memo.set(val, total);
      seenArgs.add(val);

      animFrames.push({
        activeNodeId: nodeId,
        memoizedNodeIds: [],
        callStack: [],
        activeLine: 5,
        log: `Returned fib(${val}) = ${leftChild.result} + ${rightChild.result} = ${total}`,
      });

      return { id: nodeId, result: total };
    }

    recurse(n, 0, 220, 180);
    return { treeNodes, treeEdges, animFrames };
  };

  // Generate factorial stack trace
  const computeFactTrace = (n: number) => {
    const animFrames: Frame[] = [];
    const stack: StackFrameItem[] = [];

    animFrames.push({
      activeNodeId: null,
      memoizedNodeIds: [],
      callStack: [],
      activeLine: 1,
      log: `Starting fact(${n}) call stack simulation.`,
    });

    // Push phase
    for (let k = n; k >= 1; k--) {
      stack.push({ id: `f-${k}`, func: 'fact', arg: k, ret: null });
      animFrames.push({
        activeNodeId: `f-${k}`,
        memoizedNodeIds: [],
        callStack: [...stack],
        activeLine: k === 1 ? 2 : 3,
        log: k === 1 ? `Base case fact(1) reached. Ret = 1.` : `Push frame: fact(${k}) waiting on fact(${k - 1})`,
      });
    }

    // Unwind phase
    let currentVal = 1;
    for (let k = 1; k <= n; k++) {
      currentVal = currentVal * (k === 1 ? 1 : k);
      const unwound = stack.map((item) => (item.arg === k ? { ...item, ret: currentVal } : item));
      animFrames.push({
        activeNodeId: `f-${k}`,
        memoizedNodeIds: [],
        callStack: [...unwound],
        activeLine: 4,
        log: `Unwinding: fact(${k}) returns ${currentVal}. Frame popped.`,
      });
      stack.pop();
    }

    return { treeNodes: [], treeEdges: [], animFrames };
  };

  useEffect(() => {
    if (mode === 'fib') {
      const { treeNodes, treeEdges, animFrames } = computeFibTrace(inputN, useMemoization);
      setNodes(treeNodes);
      setEdges(treeEdges);
      setFrames(animFrames);
    } else {
      const { animFrames } = computeFactTrace(inputN);
      setNodes([]);
      setEdges([]);
      setFrames(animFrames);
    }
    setFrameIdx(0);
  }, [mode, inputN, useMemoization]);

  useEffect(() => {
    if (!isPlaying) return;
    const timer = window.setInterval(() => {
      setFrameIdx((p) => {
        if (p >= frames.length - 1) {
          setIsPlaying(false);
          return p;
        }
        return p + 1;
      });
    }, Math.max(150, Math.round(750 / speed)));
    return () => clearInterval(timer);
  }, [isPlaying, speed, frames.length]);

  const curr = frames[frameIdx] || {
    activeNodeId: null,
    memoizedNodeIds: [],
    callStack: [],
    activeLine: 0,
    log: 'Ready',
  };

  return (
    <div className="space-y-4">
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
        onReset={() => {
          setIsPlaying(false);
          setFrameIdx(0);
        }}
        onRandomize={() => {
          setInputN(mode === 'fib' ? Math.floor(Math.random() * 2) + 3 : 4);
        }}
        speed={speed}
        onSpeedChange={setSpeed}
      />

      {/* Operation Toolbar */}
      <div className="flex flex-wrap items-center gap-3 p-3 bg-surface/50 border border-line rounded-xl text-xs">
        <div className="flex rounded border border-line overflow-hidden">
          <button
            onClick={() => setMode('fib')}
            className={`px-3 py-1 font-medium transition ${
              mode === 'fib' ? 'bg-mint text-canvas' : 'bg-surface text-muted'
            }`}
          >
            fib(n) Tree
          </button>
          <button
            onClick={() => setMode('fact')}
            className={`px-3 py-1 font-medium transition ${
              mode === 'fact' ? 'bg-mint text-canvas' : 'bg-surface text-muted'
            }`}
          >
            fact(n) Stack
          </button>
        </div>

        <div className="flex items-center gap-2 border-l border-line pl-3">
          <label className="text-muted">Parameter n:</label>
          <select
            value={inputN}
            onChange={(e) => setInputN(parseInt(e.target.value, 10))}
            className="px-2 py-1 bg-surface border border-line rounded text-ink"
          >
            {[2, 3, 4, 5].map((num) => (
              <option key={num} value={num}>
                n = {num}
              </option>
            ))}
          </select>
        </div>

        {mode === 'fib' && (
          <div className="flex items-center gap-2 border-l border-line pl-3">
            <button
              onClick={() => setUseMemoization(!useMemoization)}
              className={`px-3 py-1 rounded font-medium transition ${
                useMemoization
                  ? 'bg-violet text-canvas'
                  : 'border border-line text-muted hover:text-ink'
              }`}
            >
              {useMemoization ? 'Memoization: ON' : 'Memoization: OFF'}
            </button>
          </div>
        )}
      </div>

      {/* Visual Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8 space-y-3">
          <VisualizerCanvas
            metrics={[
              { label: 'Algorithm', value: mode === 'fib' ? `fib(${inputN})` : `fact(${inputN})`, color: 'var(--c-mint)' },
              { label: 'Memoized', value: useMemoization ? 'Enabled' : 'Disabled', color: 'var(--c-violet)' },
              { label: 'Call Depth', value: `${inputN} levels`, color: 'var(--c-amber)' },
            ]}
            legend={[
              { label: 'Pending Frame', color: 'var(--c-steel)' },
              { label: 'Active Call', color: 'var(--c-amber)' },
              { label: 'Memoized / Ret', color: 'var(--c-mint)' },
            ]}
          >
            <div data-testid="recursion-workbench" className="py-6 px-4 flex flex-col items-center justify-center min-h-[300px]">
              {mode === 'fib' ? (
                <svg className="w-full h-80 select-none" viewBox="0 0 440 300">
                  {/* Edges */}
                  {edges.map((e, idx) => (
                    <line
                      key={idx}
                      x1={e.x1}
                      y1={e.y1}
                      x2={e.x2}
                      y2={e.y2}
                      stroke="var(--c-line)"
                      strokeWidth="2"
                    />
                  ))}

                  {/* Call Tree Nodes */}
                  {nodes.map((node) => {
                    const isActive = curr.activeNodeId === node.id;
                    const isMemo = curr.memoizedNodeIds.includes(node.id) || node.isMemoHit;

                    let fill = 'var(--c-surface)';
                    let stroke = 'var(--c-line)';
                    let text = 'var(--c-ink)';

                    if (isActive) {
                      fill = 'var(--c-amber)';
                      stroke = 'var(--c-amber)';
                      text = '#0f141c';
                    } else if (isMemo) {
                      fill = 'var(--c-violet)';
                      stroke = 'var(--c-violet)';
                      text = '#ffffff';
                    } else if (node.returnValue !== null) {
                      fill = 'var(--c-mint)';
                      stroke = 'var(--c-mint)';
                      text = '#0f141c';
                    }

                    return (
                      <g key={node.id} className="transition-all duration-200">
                        <rect
                          x={node.x - 26}
                          y={node.y - 14}
                          width="52"
                          height="28"
                          rx="6"
                          fill={fill}
                          stroke={stroke}
                          strokeWidth="2"
                        />
                        <text
                          x={node.x}
                          y={node.y + 4}
                          textAnchor="middle"
                          fill={text}
                          fontSize="10"
                          fontWeight="bold"
                          className="font-mono pointer-events-none"
                        >
                          {node.returnValue !== null
                            ? `${node.label}=${node.returnValue}`
                            : node.label}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              ) : (
                /* Factorial Call Stack Visualizer */
                <div className="w-64 border-x-4 border-b-4 border-steel/40 rounded-b-2xl p-2 flex flex-col-reverse items-center gap-2 min-h-[220px]">
                  {curr.callStack.length === 0 ? (
                    <div className="text-muted font-mono text-xs my-auto">Stack empty</div>
                  ) : (
                    curr.callStack.map((item) => (
                      <div
                        key={item.id}
                        className="w-full py-2 px-3 rounded-lg border border-line bg-surface font-mono text-xs flex items-center justify-between"
                      >
                        <span className="font-bold text-mint">fact({item.arg})</span>
                        <span className="text-muted">
                          {item.ret !== null ? `ret = ${item.ret}` : 'waiting...'}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </VisualizerCanvas>

          {/* Activity Log */}
          <div className="p-3 bg-surface/40 border border-line rounded-xl font-mono text-xs text-muted flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-mint animate-ping" />
            <span>{curr.log}</span>
          </div>
        </div>

        {/* Pseudocode */}
        <div className="lg:col-span-4">
          <PseudoCodePanel
            title={mode === 'fib' ? 'Recursive Fibonacci' : 'Recursive Factorial'}
            lines={
              mode === 'fib'
                ? [
                    'function fib(n):',
                    '  if memo.has(n): return memo[n]',
                    '  if n <= 1: return n',
                    '  ans = fib(n-1) + fib(n-2)',
                    '  memo[n] = ans; return ans',
                  ]
                : [
                    'function fact(n):',
                    '  if n <= 1: return 1',
                    '  return n * fact(n - 1)',
                  ]
            }
            activeLine={curr.activeLine}
            timeComplexity={mode === 'fib' ? (useMemoization ? 'O(n)' : 'O(2ⁿ)') : 'O(n)'}
            spaceComplexity="O(n) Call Stack"
            logs={frames.slice(0, frameIdx + 1).map((f) => f.log)}
          />
        </div>
      </div>
    </div>
  );
};
