import React, { useState, useEffect } from 'react';
import { ControlBar } from '../components/ControlBar';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';

const N = 8;

interface Frame {
  parent: number[];
  rank: number[];
  highlight: number[];
  activeLine: number;
  log: string;
  cycle: boolean | null;
}

const freshSets = (): { parent: number[]; rank: number[] } => ({
  parent: Array.from({ length: N }, (_, i) => i),
  rank: Array.from({ length: N }, () => 0),
});

const freshFrame = (): Frame => ({
  parent: freshSets().parent,
  rank: freshSets().rank,
  highlight: [],
  activeLine: -1,
  log: `Disjoint sets initialized: ${N} singletons. Union by rank + path compression armed.`,
  cycle: null,
});

const findRoot = (parent: number[], x: number): number => {
  let r = x;
  while (parent[r] !== r) r = parent[r];
  return r;
};

const countComponents = (parent: number[]): number =>
  parent.filter((p, i) => p === i).length;

const findPath = (parent: number[], x: number): number[] => {
  const path = [x];
  let c = x;
  while (parent[c] !== c) {
    c = parent[c];
    path.push(c);
  }
  return path;
};

function buildUnionFrames(parentIn: number[], rankIn: number[], u: number, v: number): Frame[] {
  const parent = [...parentIn];
  const rank = [...rankIn];
  const frames: Frame[] = [];
  const snap = (highlight: number[], activeLine: number, log: string, cycle: boolean | null): Frame => ({
    parent: [...parent],
    rank: [...rank],
    highlight: [...highlight],
    activeLine,
    log,
    cycle,
  });

  const pathU = findPath(parent, u);
  pathU.forEach((_node, i) => {
    frames.push(
      snap(pathU.slice(0, i + 1), 1, `union(${u}, ${v}): find(${u}) climbs ${pathU.slice(0, i + 1).join(' -> ')}.`, null)
    );
  });
  const pathV = findPath(parent, v);
  pathV.forEach((_node, i) => {
    frames.push(
      snap(pathV.slice(0, i + 1), 1, `union(${u}, ${v}): find(${v}) climbs ${pathV.slice(0, i + 1).join(' -> ')}.`, null)
    );
  });
  const ru = pathU[pathU.length - 1];
  const rv = pathV[pathV.length - 1];

  for (const node of pathU) parent[node] = ru;
  for (const node of pathV) parent[node] = rv;
  frames.push(
    snap([...pathU, ...pathV], 2, `Path compression: re-linked visited nodes directly under roots ${ru} and ${rv}.`, null)
  );

  if (ru === rv) {
    frames.push(
      snap([u, v, ru], 6, `union(${u}, ${v}): find(${u}) === find(${v}) === ${ru} — redundant edge, cycle detected!`, true)
    );
    return frames;
  }

  if (rank[ru] < rank[rv]) {
    parent[ru] = rv;
    frames.push(
      snap([ru, rv], 7, `Union by rank: rank[${ru}]=${rank[ru]} < rank[${rv}]=${rank[rv]}, attach root ${ru} under ${rv}.`, false)
    );
  } else if (rank[ru] > rank[rv]) {
    parent[rv] = ru;
    frames.push(
      snap([ru, rv], 8, `Union by rank: rank[${ru}]=${rank[ru]} > rank[${rv}]=${rank[rv]}, attach root ${rv} under ${ru}.`, false)
    );
  } else {
    parent[rv] = ru;
    rank[ru] += 1;
    frames.push(
      snap([ru, rv], 9, `Tie: attach root ${rv} under ${ru} and increment rank[${ru}] to ${rank[ru]}.`, false)
    );
  }
  return frames;
}

function buildFindFrames(parentIn: number[], rankIn: number[], x: number): Frame[] {
  const parent = [...parentIn];
  const rank = [...rankIn];
  const frames: Frame[] = [];
  const path = findPath(parent, x);
  path.forEach((_node, i) => {
    frames.push({
      parent: [...parent],
      rank: [...rank],
      highlight: path.slice(0, i + 1),
      activeLine: 1,
      log: `find(${x}): climb ${path.slice(0, i + 1).join(' -> ')}.`,
      cycle: null,
    });
  });
  const root = path[path.length - 1];
  for (const node of path) parent[node] = root;
  frames.push({
    parent: [...parent],
    rank: [...rank],
    highlight: [...path],
    activeLine: 2,
    log: `find(${x}) = ${root}. Path compression flattened ${path.length - 1} link(s) to root ${root}.`,
    cycle: null,
  });
  return frames;
}

const rootColor = (root: number): string => `hsl(${(root * 47) % 360} 70% 55%)`;

export const UnionFindVisualizer: React.FC = () => {
  const [committed, setCommitted] = useState(freshSets);
  const [frames, setFrames] = useState<Frame[]>([freshFrame()]);
  const [frameIdx, setFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [u, setU] = useState(0);
  const [v, setV] = useState(1);
  const [x, setX] = useState(0);
  const [result, setResult] = useState('8 singleton sets. Pick an operation to begin.');

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

  const play = (generated: Frame[], next: { parent: number[]; rank: number[] }, message: string) => {
    setCommitted(next);
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
    setResult(message);
  };

  const handleUnion = (a: number, b: number, base = committed) => {
    const generated = buildUnionFrames(base.parent, base.rank, a, b);
    const tail = generated[generated.length - 1];
    play(
      generated,
      { parent: tail.parent, rank: tail.rank },
      tail.cycle
        ? `Cycle detected: edge (${a}, ${b}) is redundant (find(${a}) === find(${b})).`
        : `union(${a}, ${b}): merged — ${countComponents(tail.parent)} component(s) remain.`
    );
  };

  const handleFind = () => {
    const generated = buildFindFrames(committed.parent, committed.rank, x);
    const tail = generated[generated.length - 1];
    play(
      generated,
      { parent: tail.parent, rank: tail.rank },
      `find(${x}) = ${findRoot(tail.parent, x)} — path compressed.`
    );
  };

  const runSequence = (ops: Array<[number, number]>, label: string) => {
    let base = freshSets();
    let all: Frame[] = [];
    let lastTail: Frame | null = null;
    for (const [a, b] of ops) {
      const generated = buildUnionFrames(base.parent, base.rank, a, b);
      all = all.concat(generated);
      lastTail = generated[generated.length - 1];
      base = { parent: lastTail.parent, rank: lastTail.rank };
    }
    const tail = lastTail!;
    setCommitted(base);
    setFrames(all);
    setFrameIdx(0);
    setIsPlaying(true);
    setResult(
      tail.cycle
        ? `Cycle detected: edge (${ops[ops.length - 1][0]}, ${ops[ops.length - 1][1]}) is redundant — ${label}.`
        : `${label}: ${countComponents(tail.parent)} component(s) remain.`
    );
  };

  const handleReset = () => {
    const fresh = freshSets();
    setCommitted(fresh);
    setFrames([freshFrame()]);
    setFrameIdx(0);
    setIsPlaying(false);
    setResult('8 singleton sets. Pick an operation to begin.');
  };

  const curr = frames[frameIdx] ?? freshFrame();
  const depths = curr.parent.map((_, i) => findPath(curr.parent, i).length - 1);
  const maxDepth = Math.max(0, ...depths);
  const W = N * 62 + 20;
  const H = Math.max(200, (maxDepth + 1) * 72 + 40);
  const pos = (i: number): [number, number] => [10 + i * 62 + 31, 30 + depths[i] * 72];
  const rootOf = (i: number): number => findRoot(curr.parent, i);

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
        onReset={handleReset}
        onRandomize={() => {
          const a = Math.floor(Math.random() * N);
          let b = Math.floor(Math.random() * N);
          if (b === a) b = (b + 1) % N;
          handleUnion(a, b);
        }}
        speed={speed}
        onSpeedChange={setSpeed}
      />

      <div className="flex flex-wrap items-center gap-3 p-3 bg-surface/50 border border-line rounded-xl text-xs">
        <div className="flex items-center gap-2">
          <select
            aria-label="Union u"
            value={u}
            onChange={(e) => setU(Number(e.target.value))}
            className="px-2 py-1 bg-surface border border-line rounded text-ink text-center"
          >
            {Array.from({ length: N }, (_, i) => (
              <option key={i} value={i}>{i}</option>
            ))}
          </select>
          <select
            aria-label="Union v"
            value={v}
            onChange={(e) => setV(Number(e.target.value))}
            className="px-2 py-1 bg-surface border border-line rounded text-ink text-center"
          >
            {Array.from({ length: N }, (_, i) => (
              <option key={i} value={i}>{i}</option>
            ))}
          </select>
          <button
            onClick={() => handleUnion(u, v)}
            className="px-3 py-1 bg-mint text-canvas font-medium rounded hover:bg-mint/90 transition"
          >
            Union(u, v)
          </button>
        </div>

        <div className="flex items-center gap-2 border-l border-line pl-3">
          <select
            aria-label="Find x"
            value={x}
            onChange={(e) => setX(Number(e.target.value))}
            className="px-2 py-1 bg-surface border border-line rounded text-ink text-center"
          >
            {Array.from({ length: N }, (_, i) => (
              <option key={i} value={i}>{i}</option>
            ))}
          </select>
          <button
            onClick={handleFind}
            className="px-3 py-1 bg-violet text-canvas font-medium rounded hover:bg-violet/90 transition"
          >
            Find(x) &amp; Compress
          </button>
        </div>

        <div className="flex items-center gap-2 border-l border-line pl-3">
          <button
            onClick={() => runSequence([[0, 1], [2, 3], [4, 5], [1, 2]], 'Connected components demo')}
            className="px-3 py-1 bg-amber text-canvas font-medium rounded hover:bg-amber/90 transition"
          >
            Connected Components Demo
          </button>
          <button
            onClick={() => runSequence([[0, 1], [1, 2], [2, 3], [0, 3]], 'cycle demo')}
            className="px-3 py-1 bg-rose-600 text-white font-medium rounded hover:bg-rose-500 transition"
          >
            Cycle Detection Demo
          </button>
          <button
            onClick={handleReset}
            className="px-3 py-1 bg-canvas text-muted border border-line font-medium rounded hover:text-ink hover:border-steel transition"
          >
            Reset Sets
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8 space-y-3">
          <VisualizerCanvas
            metrics={[
              { label: 'Components', value: `${countComponents(curr.parent)}`, color: 'var(--c-mint)' },
              { label: 'Cycle', value: curr.cycle === null ? '—' : curr.cycle ? 'YES' : 'NO', color: 'var(--c-amber)' },
              { label: 'Frame', value: `${frameIdx + 1}/${frames.length}`, color: 'var(--c-violet)' },
            ]}
            legend={[
              { label: 'Component Root', color: 'var(--c-mint)' },
              { label: 'Active Path', color: 'var(--c-amber)' },
              { label: 'Child Link', color: 'var(--c-steel)' },
            ]}
          >
            <div data-testid="union-find-workbench" className="py-4 px-2 space-y-3">
              <svg viewBox={`0 0 ${W} ${H}`} className="w-full select-none" style={{ minHeight: 200 }}>
                <defs>
                  <marker id="uf-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
                    <path d="M0,0 L8,4 L0,8 Z" fill="var(--c-steel)" />
                  </marker>
                </defs>
                {Array.from({ length: N }, (_, i) => {
                  const p = curr.parent[i];
                  if (p === i) return null;
                  const [x1, y1] = pos(i);
                  const [x2, y2] = pos(p);
                  return (
                    <line
                      key={`e-${i}`}
                      x1={x1}
                      y1={y1}
                      x2={x2}
                      y2={y2 + 20}
                      stroke="var(--c-steel)"
                      strokeWidth={2}
                      markerEnd="url(#uf-arrow)"
                    />
                  );
                })}
                {Array.from({ length: N }, (_, i) => {
                  const [cx, cy] = pos(i);
                  const isRoot = curr.parent[i] === i;
                  const isActive = curr.highlight.includes(i);
                  const color = rootColor(rootOf(i));
                  return (
                    <g key={i}>
                      <circle
                        cx={cx}
                        cy={cy}
                        r={isActive ? 21 : 18}
                        fill={isActive ? 'var(--c-amber)' : color}
                        stroke={isActive ? 'var(--c-amber)' : 'var(--c-canvas)'}
                        strokeWidth={isActive ? 3 : 2}
                        opacity={isRoot ? 1 : 0.85}
                      />
                      {isRoot && (
                        <circle cx={cx} cy={cy} r={23} fill="none" stroke={color} strokeWidth={1.5} strokeDasharray="4 3" />
                      )}
                      <text x={cx} y={cy + 5} textAnchor="middle" fontSize={13} fontWeight={700} fill="var(--c-canvas)">
                        {i}
                      </text>
                      <text x={cx} y={cy + 36} textAnchor="middle" fontSize={10} fill="var(--c-muted)">
                        r:{curr.rank[i]}
                      </text>
                    </g>
                  );
                })}
              </svg>

              <div className="overflow-x-auto">
                <table className="w-full font-mono text-[11px] border-collapse">
                  <tbody>
                    <tr>
                      <td className="pr-2 py-1 text-muted">parent[]</td>
                      {curr.parent.map((p, i) => (
                        <td
                          key={i}
                          className={`px-2 py-1 text-center border border-line ${curr.highlight.includes(i) ? 'bg-amber text-canvas font-bold' : 'bg-surface text-ink'}`}
                        >
                          {p}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="pr-2 py-1 text-muted">rank[]</td>
                      {curr.rank.map((r, i) => (
                        <td key={i} className="px-2 py-1 text-center border border-line bg-surface text-ink">
                          {r}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="pr-2 py-1 text-muted">index</td>
                      {Array.from({ length: N }, (_, i) => (
                        <td key={i} className="px-2 py-1 text-center text-muted">{i}</td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </VisualizerCanvas>

          <div className="p-3 bg-surface/40 border border-line rounded-xl font-mono text-xs text-muted flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-mint shrink-0" />
            <span>{curr.log}</span>
          </div>
          <div className="p-3 bg-surface/40 border border-line rounded-xl font-mono text-xs text-ink">
            {result}
          </div>
        </div>

        <div className="lg:col-span-4">
          <PseudoCodePanel
            title="Disjoint Set Union"
            lines={[
              'function find(x):',
              '  if parent[x] != x: climb to root',
              '    parent[x] = find(parent[x])  // compress',
              '  return parent[x]',
              'function union(u, v):',
              '  ru = find(u); rv = find(v)',
              '  if ru == rv: redundant edge (cycle!)',
              '  if rank[ru] < rank[rv]: parent[ru] = rv',
              '  elif rank[ru] > rank[rv]: parent[rv] = ru',
              '  else: parent[rv] = ru; rank[ru] += 1',
            ]}
            activeLine={curr.activeLine}
            timeComplexity="O(α(n)) amortized"
            spaceComplexity="O(n)"
            logs={frames.slice(0, frameIdx + 1).map((f) => f.log)}
          />
        </div>
      </div>
    </div>
  );
};
