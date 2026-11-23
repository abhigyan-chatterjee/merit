import React, { useState, useEffect } from 'react';
import { ControlBar } from '../components/ControlBar';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';

type DpPreset = 'lcs' | 'knapsack' | 'edit';

interface DpFrame {
  values: number[][];
  rowLabels: string[];
  colLabels: string[];
  active: [number, number] | null;
  deps: [number, number][];
  isMatch: boolean;
  activeLine: number;
  log: string;
  formula: string;
  path: [number, number][];
  result: string;
}

interface KnapsackItem {
  w: number;
  v: number;
}

const LCS_PSEUDO = [
  'function lcs(a, b):',
  '  dp = zero matrix (m+1) x (n+1)',
  '  if a[i-1] == b[j-1]: dp[i][j] = dp[i-1][j-1] + 1',
  '  else: dp[i][j] = max(dp[i-1][j], dp[i][j-1])',
  '  traceback from (m, n) to recover LCS',
  '  return dp[m][n]',
];

const KNAPSACK_PSEUDO = [
  'function knapsack(items, W):',
  '  dp = zero matrix (n+1) x (W+1)',
  '  skip = dp[i-1][w]',
  '  take = dp[i-1][w-wt] + val  (if wt <= w)',
  '  dp[i][w] = max(skip, take); traceback picks',
  '  return dp[n][W]',
];

const EDIT_PSEUDO = [
  'function editDistance(w1, w2):',
  '  dp[i][0] = i, dp[0][j] = j',
  '  cost = (w1[i-1] == w2[j-1]) ? 0 : 1',
  '  dp[i][j] = min(replace, delete, insert)',
  '  traceback ops from (m, n)',
  '  return dp[m][n]',
];

const KNAPSACK_DEFAULT: KnapsackItem[] = [
  { w: 2, v: 3 },
  { w: 3, v: 4 },
  { w: 4, v: 5 },
  { w: 5, v: 8 },
];

function snapshot(grid: number[][]): number[][] {
  return grid.map((row) => [...row]);
}

function computeLcs(a: string, b: string): DpFrame[] {
  const m = a.length;
  const n = b.length;
  const grid: number[][] = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
  const rowLabels = ['∅', ...a.split('')];
  const colLabels = ['∅', ...b.split('')];
  const frames: DpFrame[] = [
    {
      values: snapshot(grid),
      rowLabels,
      colLabels,
      active: null,
      deps: [],
      isMatch: false,
      activeLine: 1,
      log: `Init ${(m + 1)}x${n + 1} table for "${a}" vs "${b}". First row/col = 0.`,
      formula: 'dp[i][0] = dp[0][j] = 0',
      path: [],
      result: '',
    },
  ];
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      const match = a[i - 1] === b[j - 1];
      if (match) {
        grid[i][j] = grid[i - 1][j - 1] + 1;
        frames.push({
          values: snapshot(grid),
          rowLabels,
          colLabels,
          active: [i, j],
          deps: [[i - 1, j - 1]],
          isMatch: true,
          activeLine: 2,
          log: `Match '${a[i - 1]}' == '${b[j - 1]}': dp[${i}][${j}] = dp[${i - 1}][${j - 1}] + 1 = ${grid[i][j]}.`,
          formula: `dp[${i}][${j}] = dp[${i - 1}][${j - 1}] + 1 = ${grid[i][j]}`,
          path: [],
          result: '',
        });
      } else {
        grid[i][j] = Math.max(grid[i - 1][j], grid[i][j - 1]);
        frames.push({
          values: snapshot(grid),
          rowLabels,
          colLabels,
          active: [i, j],
          deps: [
            [i - 1, j],
            [i, j - 1],
          ],
          isMatch: false,
          activeLine: 3,
          log: `Mismatch '${a[i - 1]}' != '${b[j - 1]}': dp[${i}][${j}] = max(${grid[i - 1][j]}, ${grid[i][j - 1]}) = ${grid[i][j]}.`,
          formula: `dp[${i}][${j}] = max(dp[${i - 1}][${j}], dp[${i}][${j - 1}]) = ${grid[i][j]}`,
          path: [],
          result: '',
        });
      }
    }
  }
  const path: [number, number][] = [];
  let i = m;
  let j = n;
  let seq = '';
  while (i > 0 && j > 0) {
    if (a[i - 1] === b[j - 1]) {
      path.push([i, j]);
      seq = a[i - 1] + seq;
      i--;
      j--;
    } else if (grid[i - 1][j] >= grid[i][j - 1]) {
      i--;
    } else {
      j--;
    }
  }
  frames.push({
    values: snapshot(grid),
    rowLabels,
    colLabels,
    active: null,
    deps: [],
    isMatch: false,
    activeLine: 4,
    log: `Traceback complete. LCS = "${seq}" (length ${grid[m][n]}).`,
    formula: `LCS("${a}", "${b}") = "${seq}" (length ${grid[m][n]})`,
    path,
    result: `LCS = "${seq}" (length ${grid[m][n]})`,
  });
  return frames;
}

function computeKnapsack(items: KnapsackItem[], cap: number): DpFrame[] {
  const n = items.length;
  const grid: number[][] = Array.from({ length: n + 1 }, () => Array(cap + 1).fill(0));
  const rowLabels = ['∅', ...items.map((it, idx) => `#${idx + 1}(w${it.w},v${it.v})`)];
  const colLabels = Array.from({ length: cap + 1 }, (_, w) => `${w}`);
  const frames: DpFrame[] = [
    {
      values: snapshot(grid),
      rowLabels,
      colLabels,
      active: null,
      deps: [],
      isMatch: false,
      activeLine: 1,
      log: `Init ${n + 1}x${cap + 1} table. Capacity W = ${cap}, ${n} items.`,
      formula: 'dp[0][w] = 0 for all w',
      path: [],
      result: '',
    },
  ];
  for (let p = 1; p <= n; p++) {
    const { w: wt, v: val } = items[p - 1];
    for (let w = 0; w <= cap; w++) {
      const skip = grid[p - 1][w];
      if (wt <= w) {
        const take = grid[p - 1][w - wt] + val;
        grid[p][w] = Math.max(skip, take);
        frames.push({
          values: snapshot(grid),
          rowLabels,
          colLabels,
          active: [p, w],
          deps: [
            [p - 1, w],
            [p - 1, w - wt],
          ],
          isMatch: take > skip,
          activeLine: 4,
          log: `Item #${p} (w=${wt}, v=${val}), cap ${w}: skip=${skip} vs take=${take} -> dp=${grid[p][w]}.`,
          formula: `dp[${p}][${w}] = max(skip ${skip}, take ${take}) = ${grid[p][w]}`,
          path: [],
          result: '',
        });
      } else {
        grid[p][w] = skip;
        frames.push({
          values: snapshot(grid),
          rowLabels,
          colLabels,
          active: [p, w],
          deps: [[p - 1, w]],
          isMatch: false,
          activeLine: 2,
          log: `Item #${p} too heavy (w=${wt} > ${w}): dp[${p}][${w}] = skip = ${skip}.`,
          formula: `dp[${p}][${w}] = dp[${p - 1}][${w}] = ${skip} (too heavy)`,
          path: [],
          result: '',
        });
      }
    }
  }
  const path: [number, number][] = [];
  const picked: number[] = [];
  let w = cap;
  for (let p = n; p >= 1; p--) {
    if (grid[p][w] !== grid[p - 1][w]) {
      path.push([p, w]);
      picked.unshift(p);
      w -= items[p - 1].w;
    }
  }
  frames.push({
    values: snapshot(grid),
    rowLabels,
    colLabels,
    active: null,
    deps: [],
    isMatch: false,
    activeLine: 4,
    log: `Traceback complete. Max value ${grid[n][cap]} using items [${picked.join(', ') || 'none'}].`,
    formula: `max value = dp[${n}][${cap}] = ${grid[n][cap]}`,
    path,
    result: `Max value ${grid[n][cap]} with items [${picked.join(', ') || 'none'}]`,
  });
  return frames;
}

function computeEdit(w1: string, w2: string): DpFrame[] {
  const m = w1.length;
  const n = w2.length;
  const grid: number[][] = Array.from({ length: m + 1 }, (_, r) =>
    Array.from({ length: n + 1 }, (_, c) => (r === 0 ? c : c === 0 ? r : 0)),
  );
  const rowLabels = ['∅', ...w1.split('')];
  const colLabels = ['∅', ...w2.split('')];
  const frames: DpFrame[] = [
    {
      values: snapshot(grid),
      rowLabels,
      colLabels,
      active: null,
      deps: [],
      isMatch: false,
      activeLine: 1,
      log: `Init base row/col for "${w1}" -> "${w2}". dp[i][0]=i, dp[0][j]=j.`,
      formula: 'dp[i][0] = i, dp[0][j] = j',
      path: [],
      result: '',
    },
  ];
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      const cost = w1[i - 1] === w2[j - 1] ? 0 : 1;
      const replace = grid[i - 1][j - 1] + cost;
      const del = grid[i - 1][j] + 1;
      const ins = grid[i][j - 1] + 1;
      grid[i][j] = Math.min(replace, del, ins);
      frames.push({
        values: snapshot(grid),
        rowLabels,
        colLabels,
        active: [i, j],
        deps: [
          [i - 1, j - 1],
          [i - 1, j],
          [i, j - 1],
        ],
        isMatch: cost === 0,
        activeLine: 3,
        log: `'${w1[i - 1]}' vs '${w2[j - 1]}' (cost ${cost}): min(replace ${replace}, delete ${del}, insert ${ins}) = ${grid[i][j]}.`,
        formula: `dp[${i}][${j}] = min(${replace}, ${del}, ${ins}) = ${grid[i][j]}`,
        path: [],
        result: '',
      });
    }
  }
  const path: [number, number][] = [];
  const ops: string[] = [];
  let i = m;
  let j = n;
  while (i > 0 || j > 0) {
    path.push([i, j]);
    if (i > 0 && j > 0 && w1[i - 1] === w2[j - 1]) {
      ops.unshift(`keep '${w1[i - 1]}'`);
      i--;
      j--;
    } else if (i > 0 && j > 0 && grid[i][j] === grid[i - 1][j - 1] + 1) {
      ops.unshift(`replace '${w1[i - 1]}' -> '${w2[j - 1]}'`);
      i--;
      j--;
    } else if (i > 0 && grid[i][j] === grid[i - 1][j] + 1) {
      ops.unshift(`delete '${w1[i - 1]}'`);
      i--;
    } else {
      ops.unshift(`insert '${w2[j - 1]}'`);
      j--;
    }
  }
  frames.push({
    values: snapshot(grid),
    rowLabels,
    colLabels,
    active: null,
    deps: [],
    isMatch: false,
    activeLine: 4,
    log: `Edit distance ${grid[m][n]}. Ops: ${ops.join('; ')}.`,
    formula: `edit("${w1}", "${w2}") = ${grid[m][n]}`,
    path,
    result: `Distance ${grid[m][n]}: ${ops.join('; ')}`,
  });
  return frames;
}

function randomLetters(len: number): string {
  const pool = 'ABCDEF';
  return Array.from({ length: len }, () => pool[Math.floor(Math.random() * pool.length)]).join('');
}

export const DpTableVisualizer: React.FC = () => {
  const [preset, setPreset] = useState<DpPreset>('lcs');
  const [strA, setStrA] = useState('ABCBDA');
  const [strB, setStrB] = useState('BDCABA');
  const [word1, setWord1] = useState('HORSE');
  const [word2, setWord2] = useState('ROS');
  const [items, setItems] = useState<KnapsackItem[]>(KNAPSACK_DEFAULT);
  const [frames, setFrames] = useState<DpFrame[]>([]);
  const [frameIdx, setFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  useEffect(() => {
    if (preset === 'lcs') setFrames(computeLcs(strA, strB));
    else if (preset === 'knapsack') setFrames(computeKnapsack(items, 7));
    else setFrames(computeEdit(word1, word2));
    setFrameIdx(0);
  }, [preset, strA, strB, word1, word2, items]);

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

  const curr: DpFrame =
    frames[frameIdx] || {
      values: [[0]],
      rowLabels: ['∅'],
      colLabels: ['∅'],
      active: null,
      deps: [],
      isMatch: false,
      activeLine: 0,
      log: 'Ready',
      formula: '',
      path: [],
      result: '',
    };

  const pseudo = preset === 'lcs' ? LCS_PSEUDO : preset === 'knapsack' ? KNAPSACK_PSEUDO : EDIT_PSEUDO;
  const title = preset === 'lcs' ? 'Longest Common Subsequence' : preset === 'knapsack' ? '0/1 Knapsack' : 'Edit Distance';
  const inPath = (r: number, c: number) => curr.path.some(([pr, pc]) => pr === r && pc === c);
  const isDep = (r: number, c: number) => curr.deps.some(([dr, dc]) => dr === r && dc === c);

  const clean = (v: string) => v.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 8);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 p-3 rounded-xl border border-line bg-surface">
        {(
          [
            ['lcs', 'LCS'],
            ['knapsack', '0/1 Knapsack'],
            ['edit', 'Edit Distance'],
          ] as [DpPreset, string][]
        ).map(([key, label]) => (
          <button
            key={key}
            onClick={() => {
              setPreset(key);
              setIsPlaying(false);
            }}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-semibold cursor-pointer ${
              preset === key ? 'bg-mint text-canvas' : 'bg-canvas text-muted border border-line'
            }`}
          >
            {label}
          </button>
        ))}
        {preset === 'lcs' && (
          <div className="flex items-center gap-2 ml-2 text-xs font-mono">
            <label className="text-muted">A:</label>
            <input
              aria-label="String A"
              value={strA}
              onChange={(e) => setStrA(clean(e.target.value))}
              className="w-24 px-2 py-1 bg-canvas border border-line rounded text-ink text-center"
            />
            <label className="text-muted">B:</label>
            <input
              aria-label="String B"
              value={strB}
              onChange={(e) => setStrB(clean(e.target.value))}
              className="w-24 px-2 py-1 bg-canvas border border-line rounded text-ink text-center"
            />
          </div>
        )}
        {preset === 'edit' && (
          <div className="flex items-center gap-2 ml-2 text-xs font-mono">
            <label className="text-muted">W1:</label>
            <input
              aria-label="Word 1"
              value={word1}
              onChange={(e) => setWord1(clean(e.target.value))}
              className="w-24 px-2 py-1 bg-canvas border border-line rounded text-ink text-center"
            />
            <label className="text-muted">W2:</label>
            <input
              aria-label="Word 2"
              value={word2}
              onChange={(e) => setWord2(clean(e.target.value))}
              className="w-24 px-2 py-1 bg-canvas border border-line rounded text-ink text-center"
            />
          </div>
        )}
      </div>

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
          if (preset === 'lcs') {
            setStrA(randomLetters(6));
            setStrB(randomLetters(6));
          } else if (preset === 'edit') {
            const pairs = [['HORSE', 'ROS'], ['INTENTION', 'EXECUTION'].map((s) => s.slice(0, 8)) as string[], ['KITTEN', 'SITTING']];
            const pick = pairs[Math.floor(Math.random() * pairs.length)];
            setWord1(pick[0]);
            setWord2(pick[1]);
          } else {
            setItems(KNAPSACK_DEFAULT.map((it) => ({ w: it.w, v: Math.floor(Math.random() * 8) + 1 })));
          }
        }}
        speed={speed}
        onSpeedChange={setSpeed}
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8 space-y-3">
          <VisualizerCanvas
            metrics={[
              { label: 'Frame', value: `${frameIdx + 1}/${frames.length}`, color: 'var(--c-amber)' },
              { label: 'Result', value: curr.result || 'computing…', color: 'var(--c-mint)' },
            ]}
            legend={[
              { label: 'Active Cell', color: 'var(--c-amber)' },
              { label: 'Dependency', color: 'var(--c-violet)' },
              { label: 'Optimal Path', color: 'var(--c-mint)' },
            ]}
          >
            <div data-testid="dp-table-workbench" className="py-4 px-2 space-y-3">
              <div className="p-3 bg-surface border border-line rounded-xl font-mono text-xs text-center">
                <span className="text-muted">Recurrence: </span>
                <span className="text-amber font-semibold">{curr.formula}</span>
              </div>
              <div className="overflow-auto">
                <table className="mx-auto border-collapse font-mono text-xs">
                  <thead>
                    <tr>
                      <th className="w-16 p-1 text-muted text-[10px]">{title}</th>
                      {curr.colLabels.map((c, j) => (
                        <th key={j} className="min-w-9 p-1 text-center text-violet text-[11px]">
                          {j === 0 ? c : `${c}`}
                          <span className="block text-[9px] text-muted">{j}</span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {curr.values.map((row, r) => (
                      <tr key={r}>
                        <th className="p-1 text-amber text-[11px] text-right pr-2">
                          {curr.rowLabels[r]}
                          <span className="block text-[9px] text-muted">{r}</span>
                        </th>
                        {row.map((val, c) => {
                          const active = curr.active !== null && curr.active[0] === r && curr.active[1] === c;
                          const dep = isDep(r, c);
                          const onPath = inPath(r, c);
                          return (
                            <td key={c} className="p-0.5">
                              <div
                                className={`min-w-9 h-9 rounded-md border flex items-center justify-center font-bold transition-colors ${
                                  active
                                    ? 'bg-amber text-canvas border-amber scale-105'
                                    : onPath
                                    ? 'bg-mint/20 text-mint border-mint'
                                    : dep
                                    ? curr.isMatch || preset !== 'lcs'
                                      ? 'bg-mint/15 text-mint border-mint'
                                      : 'bg-violet/15 text-violet border-violet'
                                    : 'bg-surface border-line text-ink'
                                }`}
                              >
                                {val}
                              </div>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {curr.result && (
                <div className="p-2.5 bg-mint/10 border border-mint rounded-xl font-mono text-xs text-mint text-center">
                  {curr.result}
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
            title={title}
            lines={pseudo}
            activeLine={curr.activeLine}
            timeComplexity={preset === 'knapsack' ? 'O(n·W)' : 'O(m·n)'}
            spaceComplexity={preset === 'knapsack' ? 'O(n·W)' : 'O(m·n)'}
            logs={frames.slice(0, frameIdx + 1).map((f) => f.log)}
          />
        </div>
      </div>
    </div>
  );
};
