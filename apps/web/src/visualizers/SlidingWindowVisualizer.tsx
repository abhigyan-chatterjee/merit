import React, { useState, useEffect } from 'react';
import { ControlBar } from '../components/ControlBar';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';

type SwPreset = 'longest' | 'fixed' | 'twoptr';

interface SwFrame {
  l: number;
  r: number;
  bestL: number;
  bestR: number;
  best: number;
  sum: number;
  entering: number | null;
  exiting: number | null;
  compare: string;
  freq: Record<string, number>;
  contracted: boolean;
  found: boolean;
  done: boolean;
  activeLine: number;
  log: string;
}

const LONGEST_PSEUDO = [
  'function longestUnique(s):',
  '  last = {}, L = 0, best = 0',
  '  for R, ch in s:',
  '    if ch in window: L = last[ch] + 1',
  '    last[ch] = R; best = max(best, R-L+1)',
  '  return best',
];

const FIXED_PSEUDO = [
  'function maxSumK(arr, k):',
  '  window = sum(arr[0:k]); best = window',
  '  for R in k..n-1:',
  '    window += arr[R] - arr[R-k]',
  '    best = max(best, window)',
  '  return best',
];

const TWOPTR_PSEUDO = [
  'function pairSum(arr, target):',
  '  L = 0, R = n - 1  // sorted input',
  '  while L < R:',
  '    sum = arr[L] + arr[R]',
  '    if sum == target: return (L, R)',
  '    else if sum < target: L++ else R--',
];

function computeLongest(s: string): SwFrame[] {
  const frames: SwFrame[] = [];
  const last: Record<string, number> = {};
  let l = 0;
  let best = 0;
  let bestL = 0;
  let bestR = -1;
  frames.push({
    l: 0, r: -1, bestL: 0, bestR: -1, best: 0, sum: 0, entering: null, exiting: null,
    compare: '', freq: {}, contracted: false, found: false, done: false, activeLine: 1,
    log: `Scanning "${s}" for longest substring without repeats.`,
  });
  for (let r = 0; r < s.length; r++) {
    const ch = s[r];
    let contracted = false;
    if (last[ch] !== undefined && last[ch] >= l) {
      l = last[ch] + 1;
      contracted = true;
    }
    last[ch] = r;
    const len = r - l + 1;
    if (len > best) {
      best = len;
      bestL = l;
      bestR = r;
    }
    frames.push({
      l, r, bestL, bestR, best, sum: len, entering: null, exiting: null,
      compare: `window "${s.slice(l, r + 1)}" len ${len}`,
      freq: { ...last }, contracted, found: false, done: false,
      activeLine: contracted ? 3 : 4,
      log: contracted
        ? `Duplicate '${ch}' entered at R=${r}: contract L to ${l}. Window [${l}..${r}] len ${len}, best ${best}.`
        : `R=${r} ('${ch}'): window [${l}..${r}] "${s.slice(l, r + 1)}" len ${len}, best [${bestL}..${bestR}] = ${best}.`,
    });
  }
  const tail = frames[frames.length - 1];
  frames.push({ ...tail, done: true, activeLine: 5, log: `Done. Longest substring without repeats has length ${best} at [${bestL}..${bestR}].` });
  return frames;
}

function computeFixed(arr: number[], k: number): SwFrame[] {
  const frames: SwFrame[] = [];
  let sum = 0;
  for (let j = 0; j < k && j < arr.length; j++) sum += arr[j];
  let best = sum;
  let bestL = 0;
  frames.push({
    l: 0, r: k - 1, bestL: 0, bestR: k - 1, best, sum, entering: null, exiting: null,
    compare: `sum = ${sum}`, freq: {}, contracted: false, found: false, done: false, activeLine: 1,
    log: `Initial window [0..${k - 1}] sum = ${sum}. Best = ${best}.`,
  });
  for (let r = k; r < arr.length; r++) {
    const l = r - k + 1;
    const exiting = arr[r - k];
    const entering = arr[r];
    sum = sum + entering - exiting;
    if (sum > best) {
      best = sum;
      bestL = l;
    }
    frames.push({
      l, r, bestL, bestR: bestL + k - 1, best, sum, entering, exiting,
      compare: `${sum - entering + exiting} + ${entering} - ${exiting} = ${sum}`,
      freq: {}, contracted: false, found: false, done: false, activeLine: 3,
      log: `Slide to [${l}..${r}]: +arr[${r}]=${entering}, -arr[${r - k}]=${exiting} -> sum ${sum}. Best ${best} at [${bestL}..${bestL + k - 1}].`,
    });
  }
  const tail = frames[frames.length - 1];
  frames.push({ ...tail, done: true, activeLine: 5, log: `Done. Maximum sum of size ${k} is ${best} at [${tail.bestL}..${tail.bestL + k - 1}].` });
  return frames;
}

function computeTwoPtr(arr: number[], target: number): SwFrame[] {
  const frames: SwFrame[] = [];
  let l = 0;
  let r = arr.length - 1;
  frames.push({
    l, r, bestL: -1, bestR: -1, best: 0, sum: 0, entering: null, exiting: null,
    compare: `L=0, R=${r}`, freq: {}, contracted: false, found: false, done: false, activeLine: 1,
    log: `Searching pair summing to ${target} in sorted array. L=0, R=${r}.`,
  });
  while (l < r) {
    const s = arr[l] + arr[r];
    if (s === target) {
      frames.push({
        l, r, bestL: l, bestR: r, best: s, sum: s, entering: null, exiting: null,
        compare: `${arr[l]} + ${arr[r]} = ${s} == ${target}`,
        freq: {}, contracted: false, found: true, done: true, activeLine: 4,
        log: `Found! arr[${l}] + arr[${r}] = ${arr[l]} + ${arr[r]} = ${target}.`,
      });
      return frames;
    }
    const dir = s < target ? 'L++' : 'R--';
    frames.push({
      l, r, bestL: -1, bestR: -1, best: 0, sum: s, entering: null, exiting: null,
      compare: `${arr[l]} + ${arr[r]} = ${s} ${s < target ? '<' : '>'} ${target} -> ${dir}`,
      freq: {}, contracted: false, found: false, done: false, activeLine: 5,
      log: `arr[${l}] + arr[${r}] = ${s} ${s < target ? '<' : '>'} ${target}: move ${dir}.`,
    });
    if (s < target) l++;
    else r--;
  }
  frames.push({
    l, r, bestL: -1, bestR: -1, best: 0, sum: 0, entering: null, exiting: null,
    compare: 'crossed, no pair', freq: {}, contracted: false, found: false, done: true, activeLine: 5,
    log: `Pointers crossed (L=${l}, R=${r}). No pair sums to ${target}.`,
  });
  return frames;
}

export const SlidingWindowVisualizer: React.FC = () => {
  const [preset, setPreset] = useState<SwPreset>('longest');
  const [text, setText] = useState('abcabcbb');
  const [arr, setArr] = useState<number[]>([2, 1, 5, 1, 3, 2, 8, 1]);
  const [k, setK] = useState(3);
  const [sorted, setSorted] = useState<number[]>([2, 4, 7, 11, 15, 19, 24]);
  const [target, setTarget] = useState(26);
  const [frames, setFrames] = useState<SwFrame[]>([]);
  const [frameIdx, setFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  useEffect(() => {
    if (preset === 'longest') setFrames(computeLongest(text));
    else if (preset === 'fixed') setFrames(computeFixed(arr, Math.min(Math.max(k, 2), 5)));
    else setFrames(computeTwoPtr(sorted, target));
    setFrameIdx(0);
  }, [preset, text, arr, k, sorted, target]);

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

  const curr: SwFrame = frames[frameIdx] || {
    l: 0, r: -1, bestL: 0, bestR: -1, best: 0, sum: 0, entering: null, exiting: null,
    compare: '', freq: {}, contracted: false, found: false, done: false, activeLine: 0, log: 'Ready',
  };

  const pseudo = preset === 'longest' ? LONGEST_PSEUDO : preset === 'fixed' ? FIXED_PSEUDO : TWOPTR_PSEUDO;
  const title =
    preset === 'longest' ? 'Longest Substring Without Repeats' : preset === 'fixed' ? 'Fixed Window Maximum Sum' : 'Two Pointers Pair Sum';

  const tiles: (string | number)[] = preset === 'longest' ? text.split('') : preset === 'fixed' ? arr : sorted;
  const inWindow = (idx: number) => idx >= curr.l && idx <= curr.r;
  const inBest = (idx: number) => curr.bestR >= 0 && idx >= curr.bestL && idx <= curr.bestR;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 p-3 rounded-xl border border-line bg-surface">
        {(
          [
            ['longest', 'Longest Substring'],
            ['fixed', 'Fixed Window'],
            ['twoptr', 'Two Pointers'],
          ] as [SwPreset, string][]
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
        {preset === 'longest' && (
          <div className="flex items-center gap-2 ml-2 text-xs font-mono">
            <label className="text-muted">String:</label>
            <input
              aria-label="Input string"
              value={text}
              onChange={(e) => setText(e.target.value.toLowerCase().slice(0, 14))}
              className="w-36 px-2 py-1 bg-canvas border border-line rounded text-ink text-center"
            />
          </div>
        )}
        {preset === 'fixed' && (
          <div className="flex items-center gap-2 ml-2 text-xs font-mono">
            <label className="text-muted">k (2..5):</label>
            <input
              aria-label="Window size k"
              type="number"
              min={2}
              max={5}
              value={k}
              onChange={(e) => setK(Math.min(5, Math.max(2, parseInt(e.target.value, 10) || 2)))}
              className="w-14 px-2 py-1 bg-canvas border border-line rounded text-ink text-center"
            />
          </div>
        )}
        {preset === 'twoptr' && (
          <div className="flex items-center gap-2 ml-2 text-xs font-mono">
            <label className="text-muted">Target:</label>
            <input
              aria-label="Pair sum target"
              type="number"
              value={target}
              onChange={(e) => setTarget(parseInt(e.target.value, 10) || 0)}
              className="w-16 px-2 py-1 bg-canvas border border-line rounded text-ink text-center"
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
          if (preset === 'longest') {
            const pool = 'abcdef';
            setText(Array.from({ length: 8 }, () => pool[Math.floor(Math.random() * pool.length)]).join(''));
          } else if (preset === 'fixed') {
            setArr(Array.from({ length: 8 }, () => Math.floor(Math.random() * 9) + 1));
          } else {
            const base = Array.from({ length: 7 }, () => Math.floor(Math.random() * 20) + 1).sort((a, b) => a - b);
            setSorted(base);
            setTarget(base[0] + base[base.length - 1]);
          }
        }}
        speed={speed}
        onSpeedChange={setSpeed}
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8 space-y-3">
          <VisualizerCanvas
            metrics={[
              { label: 'Window [L..R]', value: `[${curr.l}..${curr.r}]`, color: 'var(--c-amber)' },
              {
                label: preset === 'fixed' ? 'Window Sum' : preset === 'twoptr' ? 'L + R' : 'Window Len',
                value: `${curr.sum}`,
                color: 'var(--c-violet)',
              },
              {
                label: preset === 'twoptr' ? 'Target' : 'Best',
                value: preset === 'twoptr' ? `${target}` : curr.bestR >= 0 ? `[${curr.bestL}..${curr.bestR}] = ${curr.best}` : `${curr.best}`,
                color: 'var(--c-mint)',
              },
            ]}
            legend={[
              { label: 'Window [L..R]', color: 'var(--c-amber)' },
              { label: 'Best Window', color: 'var(--c-mint)' },
              { label: 'Outside', color: 'var(--c-steel)' },
            ]}
          >
            <div data-testid="sliding-window-workbench" className="py-6 px-4 space-y-4">
              <div className="flex flex-wrap items-end justify-center gap-1.5">
                {tiles.map((val, idx) => {
                  const win = inWindow(idx);
                  const best = inBest(idx) && (curr.done || curr.found || preset !== 'twoptr');
                  const isL = idx === curr.l;
                  const isR = idx === curr.r;
                  return (
                    <div key={idx} className="flex flex-col items-center gap-1">
                      <div className="h-4 text-[9px] font-mono font-bold flex gap-1">
                        {isL && <span className="text-amber">L</span>}
                        {isR && <span className="text-violet">R</span>}
                      </div>
                      <div
                        className={`w-10 h-10 sm:w-11 sm:h-11 rounded-lg border font-mono font-bold flex items-center justify-center text-xs transition-colors ${
                          curr.found && (idx === curr.l || idx === curr.r)
                            ? 'bg-mint text-canvas border-mint scale-105'
                            : win
                            ? 'bg-amber/15 text-amber border-amber scale-105'
                            : best
                            ? 'bg-mint/15 text-mint border-mint'
                            : 'bg-surface border-line text-ink'
                        }`}
                      >
                        {val}
                      </div>
                      <span className="font-mono text-[9px] text-muted">[{idx}]</span>
                    </div>
                  );
                })}
              </div>
              <div className="p-3 bg-surface border border-line rounded-xl font-mono text-xs space-y-1.5">
                <div className="flex flex-wrap gap-x-4 gap-y-1">
                  <span className="text-muted">
                    Window <span className="text-amber font-bold">[L..R] = [{curr.l}..{curr.r}]</span>
                  </span>
                  {preset === 'longest' && (
                    <span className="text-muted">
                      Best <span className="text-mint font-bold">[bestL..bestR] = [{curr.bestL}..{curr.bestR}] len {curr.best}</span>
                    </span>
                  )}
                  {preset === 'fixed' && (
                    <span className="text-muted">
                      Sum <span className="text-violet font-bold">{curr.sum}</span>
                      {curr.entering !== null && (
                        <span>
                          {' '}(+{curr.entering} <span className="text-mint">enter</span>, -{curr.exiting}{' '}
                          <span className="text-rose">exit</span>)
                        </span>
                      )}
                      <span>
                        {' '}Best <span className="text-mint font-bold">{curr.best}</span>
                      </span>
                    </span>
                  )}
                  {preset === 'twoptr' && (
                    <span className="text-muted">
                      Compare <span className="text-violet font-bold">{curr.compare}</span>
                    </span>
                  )}
                </div>
                {preset === 'longest' && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {Object.entries(curr.freq).map(([ch, pos]) => (
                      <span key={ch} className="px-2 py-0.5 rounded bg-canvas border border-line text-ink">
                        {ch}:<span className="text-mint font-bold">{pos}</span>
                      </span>
                    ))}
                  </div>
                )}
                {curr.contracted && <div className="text-rose">Contraction: L moved right past duplicate.</div>}
                {curr.found && <div className="text-mint font-bold">Pair found at [{curr.bestL}, {curr.bestR}].</div>}
              </div>
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
            timeComplexity="O(n)"
            spaceComplexity={preset === 'longest' ? 'O(min(n, σ))' : 'O(1)'}
            logs={frames.slice(0, frameIdx + 1).map((f) => f.log)}
          />
        </div>
      </div>
    </div>
  );
};
