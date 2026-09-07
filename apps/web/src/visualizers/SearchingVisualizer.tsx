import React, { useState, useEffect } from 'react';
import { ControlBar } from '../components/ControlBar';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';

interface Frame {
  // Linear state
  linearIdx: number;
  linearDone: boolean;
  linearSteps: number;

  // Binary state
  binaryLow: number;
  binaryMid: number;
  binaryHigh: number;
  binaryDone: boolean;
  binarySteps: number;

  activeLine: number;
  log: string;
}

export const SearchingVisualizer: React.FC = () => {
  const [array, setArray] = useState<number[]>([12, 24, 35, 47, 53, 68, 72, 85, 91, 99]);
  const [target, setTarget] = useState<number>(72);

  const [frames, setFrames] = useState<Frame[]>([]);
  const [frameIdx, setFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  // Compute combined steps for both Linear and Binary search side-by-side
  const computeSearchFrames = (arr: number[], tgt: number) => {
    const generated: Frame[] = [];

    let linIdx = 0;
    let linDone = false;
    let linSteps = 0;

    let bLow = 0;
    let bHigh = arr.length - 1;
    let bMid = Math.floor((bLow + bHigh) / 2);
    let bDone = false;
    let bSteps = 0;

    generated.push({
      linearIdx: -1,
      linearDone: false,
      linearSteps: 0,
      binaryLow: bLow,
      binaryMid: bMid,
      binaryHigh: bHigh,
      binaryDone: false,
      binarySteps: 0,
      activeLine: 1,
      log: `Starting comparison search for target ${tgt} in sorted array of size ${arr.length}.`,
    });

    while (!linDone || !bDone) {
      // Step Linear
      if (!linDone) {
        linSteps++;
        if (linIdx < arr.length) {
          if (arr[linIdx] === tgt) {
            linDone = true;
          } else {
            linIdx++;
          }
        } else {
          linDone = true;
        }
      }

      // Step Binary
      if (!bDone) {
        bSteps++;
        bMid = Math.floor((bLow + bHigh) / 2);
        if (arr[bMid] === tgt) {
          bDone = true;
        } else if (tgt < arr[bMid]) {
          bHigh = bMid - 1;
          if (bLow > bHigh) bDone = true;
        } else {
          bLow = bMid + 1;
          if (bLow > bHigh) bDone = true;
        }
      }

      generated.push({
        linearIdx: linIdx,
        linearDone: linDone,
        linearSteps: linSteps,
        binaryLow: bLow,
        binaryMid: bMid,
        binaryHigh: bHigh,
        binaryDone: bDone,
        binarySteps: bSteps,
        activeLine: 3,
        log: `Step: Linear at [${linIdx < arr.length ? linIdx : 'end'}] (${linSteps} ops) vs Binary mid [${bMid}] range [${bLow}..${bHigh}] (${bSteps} ops)`,
      });
    }

    generated.push({
      linearIdx: linIdx,
      linearDone: true,
      linearSteps: linSteps,
      binaryLow: bLow,
      binaryMid: bMid,
      binaryHigh: bHigh,
      binaryDone: true,
      activeLine: 5,
      log: `Completed! Binary search finished in ${bSteps} steps (O(log n)). Linear search took ${linSteps} steps (O(n)).`,
    });

    return generated;
  };

  useEffect(() => {
    const f = computeSearchFrames(array, target);
    setFrames(f);
    setFrameIdx(0);
  }, [array, target]);

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
    linearIdx: 0,
    linearDone: false,
    linearSteps: 0,
    binaryLow: 0,
    binaryMid: 0,
    binaryHigh: array.length - 1,
    binaryDone: false,
    binarySteps: 0,
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
          const sorted = Array.from({ length: 10 }, () => Math.floor(Math.random() * 95) + 5).sort((a, b) => a - b);
          setArray(sorted);
          const randomTarget = sorted[Math.floor(Math.random() * sorted.length)];
          setTarget(randomTarget);
        }}
        speed={speed}
        onSpeedChange={setSpeed}
      />

      {/* Operations Toolbar */}
      <div className="flex flex-wrap items-center gap-3 p-3 bg-surface/50 border border-line rounded-xl text-xs">
        <div className="flex items-center gap-2">
          <label className="text-muted">Target Value:</label>
          <input
            type="number"
            value={target}
            onChange={(e) => setTarget(parseInt(e.target.value, 10) || 0)}
            className="w-16 px-2 py-1 bg-surface border border-line rounded text-ink text-center"
          />
        </div>

        <div className="flex items-center gap-2 border-l border-line pl-3">
          <span className="text-muted">Quick Pick:</span>
          {array.slice(0, 5).map((v) => (
            <button
              key={v}
              onClick={() => setTarget(v)}
              className="px-2 py-0.5 rounded bg-surface border border-line hover:border-mint text-ink font-mono text-[11px]"
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* Visual Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8 space-y-3">
          <VisualizerCanvas
            metrics={[
              { label: 'Target Value', value: `${target}`, color: 'var(--c-amber)' },
              { label: 'Linear Ops', value: `${curr.linearSteps} steps`, color: 'var(--c-rose, #f43f5e)' },
              { label: 'Binary Ops', value: `${curr.binarySteps} steps`, color: 'var(--c-mint)' },
            ]}
            legend={[
              { label: 'Linear Pointer', color: 'var(--c-rose, #f43f5e)' },
              { label: 'Binary Mid', color: 'var(--c-mint)' },
              { label: 'Binary Range [L..H]', color: 'var(--c-violet)' },
            ]}
          >
            <div data-testid="searching-workbench" className="py-8 px-4 flex flex-col gap-8">
              {/* Row 1: Linear Search */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-bold text-ink">Linear Search (Sequential O(n))</span>
                  <span className="text-muted">Step count: {curr.linearSteps}</span>
                </div>
                <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
                  {array.map((val, idx) => {
                    const isCurrent = idx === curr.linearIdx;
                    const isPast = idx < curr.linearIdx;
                    const isFound = isCurrent && val === target;

                    return (
                      <div key={idx} className="flex flex-col items-center gap-1">
                        <div className="h-4 text-[9px] font-mono font-bold">
                          {isCurrent && <span className="text-rose-400">SCAN</span>}
                        </div>
                        <div
                          className={`w-11 h-11 sm:w-12 sm:h-12 rounded-lg border font-mono font-bold flex items-center justify-center text-xs transition-all ${
                            isFound
                              ? 'bg-mint text-canvas border-mint scale-105'
                              : isCurrent
                              ? 'bg-rose-500/20 text-rose-400 border-rose-500 scale-105'
                              : isPast
                              ? 'bg-surface/30 border-line/40 text-muted/40'
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
              </div>

              {/* Row 2: Binary Search */}
              <div className="space-y-2 pt-4 border-t border-line">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-bold text-ink">Binary Search (Divide & Conquer O(log n))</span>
                  <span className="text-muted">Step count: {curr.binarySteps}</span>
                </div>
                <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
                  {array.map((val, idx) => {
                    const inRange = idx >= curr.binaryLow && idx <= curr.binaryHigh;
                    const isMid = idx === curr.binaryMid;
                    const isFound = isMid && val === target;

                    return (
                      <div key={idx} className="flex flex-col items-center gap-1">
                        <div className="h-4 text-[9px] font-mono font-bold">
                          {isMid ? (
                            <span className="text-mint">MID</span>
                          ) : idx === curr.binaryLow ? (
                            <span className="text-violet">LOW</span>
                          ) : idx === curr.binaryHigh ? (
                            <span className="text-violet">HIGH</span>
                          ) : null}
                        </div>
                        <div
                          className={`w-11 h-11 sm:w-12 sm:h-12 rounded-lg border font-mono font-bold flex items-center justify-center text-xs transition-all ${
                            isFound
                              ? 'bg-mint text-canvas border-mint scale-105 shadow'
                              : isMid
                              ? 'bg-amber text-canvas border-amber scale-105 shadow'
                              : inRange
                              ? 'bg-violet/15 border-violet text-ink'
                              : 'bg-surface/20 border-line/20 text-muted/30 opacity-40'
                          }`}
                        >
                          {val}
                        </div>
                        <span className="font-mono text-[9px] text-muted">[{idx}]</span>
                      </div>
                    );
                  })}
                </div>
              </div>
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
            title="Search Complexity Comparison"
            lines={[
              '// Binary Search O(log n)',
              'low = 0, high = n - 1',
              'while low <= high:',
              '    mid = (low + high) / 2',
              '    if arr[mid] == target: return mid',
              '    else if target < arr[mid]: high = mid - 1',
              '    else: low = mid + 1',
            ]}
            activeLine={curr.activeLine}
            timeComplexity="Binary O(log n) vs Linear O(n)"
            spaceComplexity="O(1)"
            logs={frames.slice(0, frameIdx + 1).map((f) => f.log)}
          />
        </div>
      </div>
    </div>
  );
};
