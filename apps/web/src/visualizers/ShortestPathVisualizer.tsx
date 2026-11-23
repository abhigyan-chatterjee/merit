import React, { useState, useEffect } from 'react';
import { ControlBar } from '../components/ControlBar';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';

type Algo = 'dijkstra' | 'bellmanford';
type GraphPreset = 'standard' | 'negative';

interface Edge {
  from: string;
  to: string;
  w: number;
}

interface SpFrame {
  dist: Record<string, number | null>;
  prev: Record<string, string | null>;
  settled: string[];
  pq: [string, number][];
  u: string | null;
  edge: Edge | null;
  relaxed: boolean;
  pass: number;
  totalPasses: number;
  activeLine: number;
  log: string;
  treeEdges: string[];
  done: boolean;
  negativeCycle: boolean;
}

const NODES = ['A', 'B', 'C', 'D', 'E', 'F'];

const POS: Record<string, { x: number; y: number }> = {
  A: { x: 70, y: 60 },
  B: { x: 210, y: 50 },
  C: { x: 110, y: 160 },
  D: { x: 250, y: 160 },
  E: { x: 140, y: 260 },
  F: { x: 280, y: 260 },
};

const STANDARD_EDGES: Edge[] = [
  { from: 'A', to: 'B', w: 4 },
  { from: 'A', to: 'C', w: 2 },
  { from: 'B', to: 'C', w: 1 },
  { from: 'B', to: 'D', w: 5 },
  { from: 'C', to: 'D', w: 8 },
  { from: 'C', to: 'E', w: 10 },
  { from: 'D', to: 'E', w: 2 },
  { from: 'D', to: 'F', w: 6 },
  { from: 'E', to: 'F', w: 3 },
];

const NEGATIVE_EDGES: Edge[] = [
  { from: 'A', to: 'B', w: 4 },
  { from: 'A', to: 'C', w: 2 },
  { from: 'B', to: 'C', w: -3 },
  { from: 'B', to: 'D', w: 5 },
  { from: 'C', to: 'D', w: 1 },
  { from: 'C', to: 'E', w: 10 },
  { from: 'D', to: 'E', w: 2 },
  { from: 'D', to: 'F', w: 6 },
  { from: 'E', to: 'F', w: -1 },
];

const DIJKSTRA_PSEUDO = [
  'function dijkstra(graph, src):',
  '  dist[*] = inf; dist[src] = 0; pq = [(0, src)]',
  '  while pq not empty:',
  '    u = pq.extractMin(); settle u',
  '    for (u -> v, w): if dist[u]+w < dist[v]: relax',
  '  return dist, prev',
];

const BELLMANFORD_PSEUDO = [
  'function bellmanFord(edges, src):',
  '  dist[*] = inf; dist[src] = 0',
  '  repeat V-1 passes:',
  '    for (u -> v, w): if dist[u]+w < dist[v]: relax',
  '  check every edge once more for negative cycle',
  '  return dist, prev',
];

function initMaps(source: string): { dist: Record<string, number | null>; prev: Record<string, string | null> } {
  const dist: Record<string, number | null> = {};
  const prev: Record<string, string | null> = {};
  for (const n of NODES) {
    dist[n] = n === source ? 0 : null;
    prev[n] = null;
  }
  return { dist, prev };
}

function computeDijkstra(edges: Edge[], source: string): SpFrame[] {
  const { dist, prev } = initMaps(source);
  const settled: string[] = [];
  const treeEdges: string[] = [];
  const frames: SpFrame[] = [
    {
      dist: { ...dist }, prev: { ...prev }, settled: [], pq: [[source, 0]],
      u: null, edge: null, relaxed: false, pass: 0, totalPasses: 0,
      activeLine: 1, log: `Dijkstra from ${source}. dist[${source}] = 0, rest = inf.`, treeEdges: [], done: false, negativeCycle: false,
    },
  ];
  const pq: [string, number][] = [[source, 0]];
  while (pq.length > 0) {
    pq.sort((a, b) => a[1] - b[1]);
    const [u, du] = pq.shift()!;
    if (settled.includes(u)) continue;
    if (dist[u] !== null && du > (dist[u] as number)) continue;
    settled.push(u);
    frames.push({
      dist: { ...dist }, prev: { ...prev }, settled: [...settled], pq: [...pq],
      u, edge: null, relaxed: false, pass: 0, totalPasses: 0,
      activeLine: 3, log: `Settle vertex ${u} with dist ${du}. PQ = [${pq.map(([n, d]) => `(${n},${d})`).join(', ') || 'empty'}].`,
      treeEdges: [...treeEdges], done: false, negativeCycle: false,
    });
    for (const e of edges.filter((x) => x.from === u)) {
      const alt = (dist[u] as number) + e.w;
      const relaxed = dist[e.to] === null || alt < (dist[e.to] as number);
      if (relaxed) {
        dist[e.to] = alt;
        prev[e.to] = u;
        pq.push([e.to, alt]);
        const key = `${u}->${e.to}`;
        if (!treeEdges.includes(key)) treeEdges.push(key);
      }
      frames.push({
        dist: { ...dist }, prev: { ...prev }, settled: [...settled], pq: [...pq],
        u, edge: e, relaxed, pass: 0, totalPasses: 0,
        activeLine: 4,
        log: relaxed
          ? `Relax ${u} -> ${e.to} (w=${e.w}): ${alt - e.w} + ${e.w} = ${alt} < old. Update dist[${e.to}] = ${alt}, prev = ${u}.`
          : `Relax ${u} -> ${e.to} (w=${e.w}): ${alt - e.w} + ${e.w} = ${alt} >= dist[${e.to}]. No change.`,
        treeEdges: [...treeEdges], done: false, negativeCycle: false,
      });
    }
  }
  frames.push({
    dist: { ...dist }, prev: { ...prev }, settled: [...settled], pq: [],
    u: null, edge: null, relaxed: false, pass: 0, totalPasses: 0,
    activeLine: 5, log: `Dijkstra complete from ${source}. All reachable vertices settled.`,
    treeEdges: [...treeEdges], done: true, negativeCycle: false,
  });
  return frames;
}

function computeBellmanFord(edges: Edge[], source: string): SpFrame[] {
  const { dist, prev } = initMaps(source);
  const treeEdges: string[] = [];
  const total = NODES.length - 1;
  const frames: SpFrame[] = [
    {
      dist: { ...dist }, prev: { ...prev }, settled: [], pq: [],
      u: null, edge: null, relaxed: false, pass: 0, totalPasses: total,
      activeLine: 1, log: `Bellman-Ford from ${source}: ${total} passes over ${edges.length} edges.`, treeEdges: [], done: false, negativeCycle: false,
    },
  ];
  for (let p = 1; p <= total; p++) {
    let changed = false;
    for (const e of edges) {
      if (dist[e.from] === null) {
        frames.push({
          dist: { ...dist }, prev: { ...prev }, settled: [], pq: [],
          u: e.from, edge: e, relaxed: false, pass: p, totalPasses: total,
          activeLine: 3, log: `Pass ${p}/${total}: skip ${e.from} -> ${e.to} (dist[${e.from}] = inf).`,
          treeEdges: [...treeEdges], done: false, negativeCycle: false,
        });
        continue;
      }
      const alt = (dist[e.from] as number) + e.w;
      const relaxed = dist[e.to] === null || alt < (dist[e.to] as number);
      if (relaxed) {
        dist[e.to] = alt;
        prev[e.to] = e.from;
        changed = true;
        const key = `${e.from}->${e.to}`;
        if (!treeEdges.includes(key)) treeEdges.push(key);
      }
      frames.push({
        dist: { ...dist }, prev: { ...prev }, settled: [], pq: [],
        u: e.from, edge: e, relaxed, pass: p, totalPasses: total,
        activeLine: 3,
        log: relaxed
          ? `Pass ${p}/${total}: relax ${e.from} -> ${e.to} (w=${e.w}): dist = ${alt}, prev[${e.to}] = ${e.from}.`
          : `Pass ${p}/${total}: check ${e.from} -> ${e.to} (w=${e.w}): ${alt} >= dist[${e.to}]. No change.`,
        treeEdges: [...treeEdges], done: false, negativeCycle: false,
      });
    }
    if (!changed) break;
  }
  let cycle = false;
  for (const e of edges) {
    if (dist[e.from] !== null && (dist[e.to] === null || (dist[e.from] as number) + e.w < (dist[e.to] as number))) {
      cycle = true;
      break;
    }
  }
  frames.push({
    dist: { ...dist }, prev: { ...prev }, settled: [...NODES.filter((n) => dist[n] !== null)], pq: [],
    u: null, edge: null, relaxed: false, pass: total, totalPasses: total,
    activeLine: 4, log: cycle ? 'Negative-cycle check: a further relaxation is possible -> negative cycle!' : 'Negative-cycle check passed: no edge relaxes further. Distances final.',
    treeEdges: [...treeEdges], done: true, negativeCycle: cycle,
  });
  return frames;
}

function pathFromSource(prev: Record<string, string | null>, source: string, node: string): string {
  if (node === source) return source;
  const chain: string[] = [node];
  let p = prev[node];
  const guard = new Set<string>();
  while (p !== null && p !== undefined && !guard.has(p)) {
    guard.add(p);
    chain.unshift(p);
    if (p === source) return chain.join(' → ');
    p = prev[p];
  }
  return 'unreachable';
}

export const ShortestPathVisualizer: React.FC = () => {
  const [algo, setAlgo] = useState<Algo>('dijkstra');
  const [graph, setGraph] = useState<GraphPreset>('standard');
  const [source, setSource] = useState('A');
  const [frames, setFrames] = useState<SpFrame[]>([]);
  const [frameIdx, setFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  const edges = graph === 'standard' ? STANDARD_EDGES : NEGATIVE_EDGES;
  const showWarning = algo === 'dijkstra' && graph === 'negative';

  useEffect(() => {
    setFrames(algo === 'dijkstra' ? computeDijkstra(edges, source) : computeBellmanFord(edges, source));
    setFrameIdx(0);
  }, [algo, edges, source]);

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

  const curr: SpFrame = frames[frameIdx] || {
    dist: {}, prev: {}, settled: [], pq: [], u: null, edge: null, relaxed: false,
    pass: 0, totalPasses: 0, activeLine: 0, log: 'Ready', treeEdges: [], done: false, negativeCycle: false,
  };

  const pseudo = algo === 'dijkstra' ? DIJKSTRA_PSEUDO : BELLMANFORD_PSEUDO;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 p-3 rounded-xl border border-line bg-surface">
        <button
          onClick={() => {
            setAlgo('dijkstra');
            setIsPlaying(false);
          }}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-semibold cursor-pointer ${
            algo === 'dijkstra' ? 'bg-mint text-canvas' : 'bg-canvas text-muted border border-line'
          }`}
        >
          Dijkstra
        </button>
        <button
          onClick={() => {
            setAlgo('bellmanford');
            setIsPlaying(false);
          }}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-semibold cursor-pointer ${
            algo === 'bellmanford' ? 'bg-mint text-canvas' : 'bg-canvas text-muted border border-line'
          }`}
        >
          Bellman-Ford
        </button>
        <div className="flex items-center gap-2 border-l border-line pl-3">
          <button
            onClick={() => {
              setGraph('standard');
              setIsPlaying(false);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono cursor-pointer ${
              graph === 'standard' ? 'bg-violet text-canvas' : 'bg-canvas text-muted border border-line'
            }`}
          >
            Standard Network
          </button>
          <button
            onClick={() => {
              setGraph('negative');
              setIsPlaying(false);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono cursor-pointer ${
              graph === 'negative' ? 'bg-violet text-canvas' : 'bg-canvas text-muted border border-line'
            }`}
          >
            Negative-Weight Network
          </button>
        </div>
        <div className="flex items-center gap-2 ml-2 text-xs font-mono">
          <label htmlFor="sp-source" className="text-muted">Source:</label>
          <select
            id="sp-source"
            aria-label="Source"
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="px-2 py-1 bg-canvas border border-line rounded text-ink text-center"
          >
            {NODES.map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
      </div>

      {showWarning && (
        <div className="p-3 bg-amber/10 border border-amber rounded-xl font-mono text-xs text-amber">
          Dijkstra requires non-negative edge weights — switch to Bellman-Ford for negative edges
        </div>
      )}

      <ControlBar
        isPlaying={isPlaying}
        onPlayPause={() => setIsPlaying((p) => !p)}
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
          setIsPlaying(false);
          setSource(NODES[Math.floor(Math.random() * NODES.length)]);
        }}
        speed={speed}
        onSpeedChange={setSpeed}
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8 space-y-3">
          <VisualizerCanvas
            metrics={[
              { label: 'Algorithm', value: algo === 'dijkstra' ? 'Dijkstra' : 'Bellman-Ford', color: 'var(--c-mint)' },
              algo === 'dijkstra'
                ? { label: 'Settled', value: `${curr.settled.length}/${NODES.length}`, color: 'var(--c-amber)' }
                : { label: 'Pass', value: `Pass ${curr.pass} of V-1`, color: 'var(--c-amber)' },
              { label: 'Source', value: source, color: 'var(--c-violet)' },
            ]}
            legend={[
              { label: 'Source', color: 'var(--c-violet)' },
              { label: 'Active u', color: 'var(--c-amber)' },
              { label: 'Relaxing v', color: 'var(--c-rose)' },
              { label: 'Settled', color: 'var(--c-mint)' },
            ]}
          >
            <div data-testid="shortest-path-workbench" className="py-4 px-2 space-y-3">
              <svg data-testid="shortest-path-svg" viewBox="0 0 360 320" className="w-full h-72 select-none">
                <defs>
                  <marker id="sp-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                    <path d="M 0 1 L 9 5 L 0 9 z" fill="var(--c-steel)" />
                  </marker>
                  <marker id="sp-arrow-hot" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                    <path d="M 0 1 L 9 5 L 0 9 z" fill="var(--c-amber)" />
                  </marker>
                </defs>
                {edges.map((e, idx) => {
                  const a = POS[e.from];
                  const b = POS[e.to];
                  const isActive = curr.edge !== null && curr.edge.from === e.from && curr.edge.to === e.to;
                  const inTree = curr.treeEdges.includes(`${e.from}->${e.to}`);
                  const dx = b.x - a.x;
                  const dy = b.y - a.y;
                  const len = Math.hypot(dx, dy) || 1;
                  const sx = a.x + (dx / len) * 20;
                  const sy = a.y + (dy / len) * 20;
                  const ex = b.x - (dx / len) * 24;
                  const ey = b.y - (dy / len) * 24;
                  const mx = (sx + ex) / 2;
                  const my = (sy + ey) / 2;
                  return (
                    <g key={idx}>
                      <line
                        x1={sx} y1={sy} x2={ex} y2={ey}
                        stroke={isActive ? 'var(--c-amber)' : inTree ? 'var(--c-mint)' : 'var(--c-steel)'}
                        strokeWidth={isActive || inTree ? 3 : 2}
                        markerEnd={isActive ? 'url(#sp-arrow-hot)' : 'url(#sp-arrow)'}
                      />
                      <text x={mx} y={my - 4} textAnchor="middle" className="font-mono" fontSize="11" fontWeight="bold"
                        fill={e.w < 0 ? 'var(--c-rose)' : 'var(--c-ink)'}>
                        {e.w}
                      </text>
                    </g>
                  );
                })}
                {NODES.map((n) => {
                  const p = POS[n];
                  const isSource = n === source;
                  const isSettled = curr.settled.includes(n);
                  const isU = curr.u === n;
                  const isV = curr.edge !== null && curr.edge.to === n;
                  let fill = 'var(--c-surface)';
                  let stroke = 'var(--c-steel)';
                  if (isU) {
                    fill = 'var(--c-amber)';
                    stroke = 'var(--c-amber)';
                  } else if (isV) {
                    fill = 'var(--c-rose)';
                    stroke = 'var(--c-rose)';
                  } else if (isSettled) {
                    fill = 'var(--c-mint)';
                    stroke = 'var(--c-mint)';
                  } else if (isSource) {
                    stroke = 'var(--c-violet)';
                  }
                  return (
                    <g key={n}>
                      <circle cx={p.x} cy={p.y} r={19} fill={fill} stroke={stroke} strokeWidth={3} />
                      {isSource && <circle cx={p.x} cy={p.y} r={24} fill="none" stroke="var(--c-violet)" strokeWidth={1.5} strokeDasharray="4 3" />}
                      <text x={p.x} y={p.y + 4} textAnchor="middle" fontSize="12" fontWeight="bold" className="font-mono"
                        fill={isU || isV || isSettled ? 'var(--c-canvas)' : 'var(--c-ink)'}>
                        {n}
                      </text>
                      <text x={p.x} y={p.y + 34} textAnchor="middle" fontSize="10" className="font-mono" fill="var(--c-muted)">
                        {curr.dist[n] === null || curr.dist[n] === undefined ? '∞' : curr.dist[n]}
                      </text>
                    </g>
                  );
                })}
              </svg>
              <div className="overflow-auto">
                <table className="w-full border-collapse font-mono text-xs">
                  <thead>
                    <tr className="text-muted text-[10px] uppercase tracking-wider">
                      <th className="p-1.5 text-left">Node</th>
                      <th className="p-1.5 text-left">Dist</th>
                      <th className="p-1.5 text-left">Prev</th>
                      <th className="p-1.5 text-left">Path from Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {NODES.map((n) => (
                      <tr key={n} className={`border-t border-line ${curr.u === n ? 'bg-amber/10' : ''}`}>
                        <td className="p-1.5 font-bold text-ink">{n}</td>
                        <td className="p-1.5 text-mint font-bold">{curr.dist[n] === null || curr.dist[n] === undefined ? '∞' : curr.dist[n]}</td>
                        <td className="p-1.5 text-violet">{curr.prev[n] ?? '—'}</td>
                        <td className="p-1.5 text-muted">{pathFromSource(curr.prev, source, n)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {algo === 'dijkstra' && curr.pq.length > 0 && (
                <div className="p-2.5 bg-surface border border-line rounded-xl font-mono text-xs text-muted">
                  PQ: <span className="text-amber">{curr.pq.map(([n, d]) => `(${n}, ${d})`).join(' ')}</span>
                </div>
              )}
              <div className="p-3 bg-surface/40 border border-line rounded-xl font-mono text-xs text-muted flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-mint shrink-0" />
                <span>{curr.log}</span>
              </div>
            </div>
          </VisualizerCanvas>
        </div>
        <div className="lg:col-span-4">
          <PseudoCodePanel
            title={algo === 'dijkstra' ? "Dijkstra's Algorithm" : 'Bellman-Ford Algorithm'}
            lines={pseudo}
            activeLine={curr.activeLine}
            timeComplexity={algo === 'dijkstra' ? 'O(E log V)' : 'O(V·E)'}
            spaceComplexity="O(V)"
            logs={frames.slice(0, frameIdx + 1).map((f) => f.log)}
          />
        </div>
      </div>
    </div>
  );
};
