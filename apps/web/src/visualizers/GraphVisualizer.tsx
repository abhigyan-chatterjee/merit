import React, { useState, useEffect } from 'react';
import { ControlBar } from '../components/ControlBar';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';
import { PSEUDOCODE_MAP } from '../data/pseudocode';
import { PlusCircle, Share2 } from 'lucide-react';

interface GraphNode {
  id: number;
  x: number;
  y: number;
}

interface GraphEdge {
  from: number;
  to: number;
}

interface TraversalStep {
  currentNode: number | null;
  visited: number[];
  frontier: number[]; // Queue for BFS, Stack for DFS
  activeLine: number;
  log: string;
}

const DEFAULT_NODES: GraphNode[] = [
  { id: 0, x: 180, y: 80 },
  { id: 1, x: 100, y: 180 },
  { id: 2, x: 260, y: 180 },
  { id: 3, x: 60, y: 290 },
  { id: 4, x: 170, y: 290 },
  { id: 5, x: 290, y: 290 }
];

const DEFAULT_EDGES: GraphEdge[] = [
  { from: 0, to: 1 },
  { from: 0, to: 2 },
  { from: 1, to: 3 },
  { from: 1, to: 4 },
  { from: 2, to: 5 },
  { from: 4, to: 5 }
];

export const GraphVisualizer: React.FC = () => {
  const [mode, setMode] = useState<'bfs' | 'dfs'>('bfs');
  const [nodes, setNodes] = useState<GraphNode[]>(DEFAULT_NODES);
  const [edges, setEdges] = useState<GraphEdge[]>(DEFAULT_EDGES);
  const [selectedNodeForEdge, setSelectedNodeForEdge] = useState<number | null>(null);
  const [steps, setSteps] = useState<TraversalStep[]>([]);
  const [stepIdx, setStepIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  const computeTraversal = () => {
    const adj: Record<number, number[]> = {};
    nodes.forEach((n) => (adj[n.id] = []));
    edges.forEach((e) => {
      if (!adj[e.from].includes(e.to)) adj[e.from].push(e.to);
      if (!adj[e.to].includes(e.from)) adj[e.to].push(e.from);
    });

    const frames: TraversalStep[] = [];
    const visited = new Set<number>();

    if (nodes.length === 0) return;
    const startId = nodes[0].id;

    if (mode === 'bfs') {
      const queue: number[] = [startId];
      visited.add(startId);
      frames.push({
        currentNode: null,
        visited: Array.from(visited),
        frontier: [...queue],
        activeLine: 1,
        log: `Enqueue start vertex ${startId}`
      });

      while (queue.length > 0) {
        const curr = queue.shift()!;
        frames.push({
          currentNode: curr,
          visited: Array.from(visited),
          frontier: [...queue],
          activeLine: 3,
          log: `Dequeued vertex ${curr} and visiting neighbors`
        });

        for (const neighbor of adj[curr] || []) {
          if (!visited.has(neighbor)) {
            visited.add(neighbor);
            queue.push(neighbor);
            frames.push({
              currentNode: curr,
              visited: Array.from(visited),
              frontier: [...queue],
              activeLine: 6,
              log: `Discovered unvisited neighbor ${neighbor} -> Enqueue`
            });
          }
        }
      }
    } else {
      // DFS
      const stack: number[] = [];
      const dfsVisit = (curr: number) => {
        visited.add(curr);
        stack.push(curr);
        frames.push({
          currentNode: curr,
          visited: Array.from(visited),
          frontier: [...stack],
          activeLine: 1,
          log: `DFS visit vertex ${curr}`
        });

        for (const neighbor of adj[curr] || []) {
          if (!visited.has(neighbor)) {
            frames.push({
              currentNode: curr,
              visited: Array.from(visited),
              frontier: [...stack],
              activeLine: 4,
              log: `Recurse DFS on unvisited neighbor ${neighbor}`
            });
            dfsVisit(neighbor);
          }
        }
        stack.pop();
      };
      dfsVisit(startId);
    }

    frames.push({
      currentNode: null,
      visited: Array.from(visited),
      frontier: [],
      activeLine: 0,
      log: `Traversal complete. Visited ${visited.size} vertices.`
    });

    setSteps(frames);
    setStepIdx(0);
  };

  useEffect(() => {
    computeTraversal();
  }, [nodes, edges, mode]);

  useEffect(() => {
    if (!isPlaying) return;
    const timer = window.setInterval(() => {
      setStepIdx((prev) => {
        if (prev >= steps.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, Math.max(120, Math.round(650 / speed)));
    return () => clearInterval(timer);
  }, [isPlaying, speed, steps.length]);

  const handleSvgClick = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.round(e.clientX - rect.left);
    const y = Math.round(e.clientY - rect.top);
    // Avoid adding on top of existing node
    if (nodes.some((n) => Math.hypot(n.x - x, n.y - y) < 35)) return;
    const newId = nodes.length > 0 ? Math.max(...nodes.map((n) => n.id)) + 1 : 0;
    setNodes([...nodes, { id: newId, x, y }]);
  };

  const handleNodeClick = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (selectedNodeForEdge === null) {
      setSelectedNodeForEdge(id);
    } else if (selectedNodeForEdge === id) {
      setSelectedNodeForEdge(null);
    } else {
      setEdges((prev) => [...prev, { from: selectedNodeForEdge, to: id }]);
      setSelectedNodeForEdge(null);
    }
  };

  const currentStep = steps[stepIdx] || {
    currentNode: null,
    visited: [],
    frontier: [],
    activeLine: 0,
    log: ''
  };

  const pseudo = PSEUDOCODE_MAP[mode];

  return (
    <div className="space-y-4">
      {/* Mode Selector Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl border border-line bg-surface">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setMode('bfs')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-semibold cursor-pointer ${
              mode === 'bfs'
                ? 'bg-mint text-canvas'
                : 'bg-canvas text-muted border border-line'
            }`}
          >
            Breadth-First Search (Queue)
          </button>
          <button
            onClick={() => setMode('dfs')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-semibold cursor-pointer ${
              mode === 'dfs'
                ? 'bg-mint text-canvas'
                : 'bg-canvas text-muted border border-line'
            }`}
          >
            Depth-First Search (Stack)
          </button>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono text-muted">
          <span className="flex items-center gap-1">
            <PlusCircle className="w-3.5 h-3.5 text-mint" />
            Click empty canvas to add node
          </span>
          <span className="flex items-center gap-1">
            <Share2 className="w-3.5 h-3.5 text-violet" />
            Click 2 nodes to connect edge
          </span>
        </div>
      </div>

      <ControlBar
        isPlaying={isPlaying}
        onPlayPause={() => setIsPlaying((p) => !p)}
        onStep={() => setStepIdx((i) => Math.min(steps.length - 1, i + 1))}
        onReset={() => {
          setIsPlaying(false);
          setStepIdx(0);
        }}
        onRandomize={() => {
          setNodes(DEFAULT_NODES);
          setEdges(DEFAULT_EDGES);
        }}
        speed={speed}
        onSpeedChange={setSpeed}
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8">
          <VisualizerCanvas
            metrics={[
              { label: 'Visited Count', value: `${currentStep.visited.length}/${nodes.length}`, color: 'var(--c-mint)' },
              {
                label: mode === 'bfs' ? 'Queue Frontier' : 'Call Stack',
                value: `[${currentStep.frontier.join(', ')}]`,
                color: 'var(--c-violet)'
              }
            ]}
            legend={[
              { label: 'Unvisited', color: 'var(--c-steel)' },
              { label: 'Active Vertex', color: 'var(--c-amber)' },
              { label: 'Visited', color: 'var(--c-mint)' }
            ]}
          >
            <svg
              onClick={handleSvgClick}
              className="w-full h-80 cursor-crosshair select-none"
              viewBox="0 0 420 350"
            >
              {/* Edges */}
              {edges.map((e, i) => {
                const u = nodes.find((n) => n.id === e.from);
                const v = nodes.find((n) => n.id === e.to);
                if (!u || !v) return null;
                return (
                  <line
                    key={i}
                    x1={u.x}
                    y1={u.y}
                    x2={v.x}
                    y2={v.y}
                    stroke="var(--c-steel)"
                    strokeWidth={2.5}
                  />
                );
              })}

              {/* Nodes */}
              {nodes.map((node) => {
                const isVisited = currentStep.visited.includes(node.id);
                const isCurrent = currentStep.currentNode === node.id;
                const isSelected = selectedNodeForEdge === node.id;

                let fill = 'var(--c-surface)';
                let stroke = 'var(--c-steel)';
                if (isCurrent) {
                  fill = 'var(--c-amber)';
                  stroke = 'var(--c-amber)';
                } else if (isVisited) {
                  fill = 'var(--c-mint)';
                  stroke = 'var(--c-mint)';
                } else if (isSelected) {
                  stroke = 'var(--c-violet)';
                }

                return (
                  <g
                    key={node.id}
                    onClick={(ev) => handleNodeClick(ev, node.id)}
                    className="cursor-pointer transition-transform hover:scale-110"
                  >
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={20}
                      fill={fill}
                      stroke={stroke}
                      strokeWidth={3}
                    />
                    <text
                      x={node.x}
                      y={node.y + 4}
                      textAnchor="middle"
                      className="font-mono text-xs font-bold"
                      fill={isCurrent || isVisited ? 'var(--c-canvas)' : 'var(--c-ink)'}
                    >
                      {node.id}
                    </text>
                  </g>
                );
              })}
            </svg>
          </VisualizerCanvas>
        </div>

        <div className="lg:col-span-4">
          <PseudoCodePanel
            title={pseudo.title}
            lines={pseudo.lines}
            activeLine={currentStep.activeLine}
            timeComplexity={pseudo.timeComplexity}
            spaceComplexity={pseudo.spaceComplexity}
            logs={steps.slice(0, stepIdx + 1).map((s) => s.log)}
          />
        </div>
      </div>
    </div>
  );
};
