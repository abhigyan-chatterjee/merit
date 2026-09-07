import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ControlBar } from '../components/ControlBar';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';
import { PSEUDOCODE_MAP } from '../data/pseudocode';

export type SortAlgorithm = 'bubble' | 'selection' | 'insertion' | 'merge' | 'quick';

interface SortStepFrame {
  array: number[];
  comparing: number[];
  swapping: number[];
  sorted: number[];
  comparisons: number;
  swaps: number;
  activeLine: number;
  log: string;
}

export const SortingVisualizer: React.FC = () => {
  const [algorithm, setAlgorithm] = useState<SortAlgorithm>('quick');
  const [arraySize, setArraySize] = useState<number>(20);
  const [speed, setSpeed] = useState<number>(1);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [frames, setFrames] = useState<SortStepFrame[]>([]);
  const [currentFrameIndex, setCurrentFrameIndex] = useState<number>(0);
  const timerRef = useRef<number | null>(null);

  const generateRandomArray = useCallback((size: number) => {
    const arr: number[] = [];
    for (let i = 0; i < size; i++) {
      arr.push(Math.floor(Math.random() * 88) + 10);
    }
    return arr;
  }, []);

  const computeSortFrames = useCallback((initialArr: number[], algo: SortAlgorithm) => {
    const steps: SortStepFrame[] = [];
    const arr = [...initialArr];
    let comps = 0;
    let swps = 0;
    const sortedSet = new Set<number>();

    const record = (
      comparing: number[],
      swapping: number[],
      activeLine: number,
      log: string
    ) => {
      steps.push({
        array: [...arr],
        comparing,
        swapping,
        sorted: Array.from(sortedSet),
        comparisons: comps,
        swaps: swps,
        activeLine,
        log
      });
    };

    record([], [], 0, `Initialized array with ${arr.length} elements`);

    if (algo === 'bubble') {
      const n = arr.length;
      for (let i = 0; i < n; i++) {
        for (let j = 0; j < n - i - 1; j++) {
          comps++;
          record([j, j + 1], [], 3, `Compare arr[${j}]=${arr[j]} and arr[${j + 1}]=${arr[j + 1]}`);
          if (arr[j] > arr[j + 1]) {
            swps++;
            [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]];
            record([], [j, j + 1], 4, `Swap ${arr[j + 1]} and ${arr[j]}`);
          }
        }
        sortedSet.add(n - i - 1);
      }
    } else if (algo === 'selection') {
      const n = arr.length;
      for (let i = 0; i < n; i++) {
        let minIdx = i;
        record([i], [], 2, `Set minIdx = ${i} (val=${arr[i]})`);
        for (let j = i + 1; j < n; j++) {
          comps++;
          record([minIdx, j], [], 4, `Compare arr[${j}]=${arr[j]} with min arr[${minIdx}]=${arr[minIdx]}`);
          if (arr[j] < arr[minIdx]) {
            minIdx = j;
          }
        }
        if (minIdx !== i) {
          swps++;
          [arr[i], arr[minIdx]] = [arr[minIdx], arr[i]];
          record([], [i, minIdx], 5, `Swap minimum ${arr[i]} into position ${i}`);
        }
        sortedSet.add(i);
      }
    } else if (algo === 'insertion') {
      const n = arr.length;
      sortedSet.add(0);
      for (let i = 1; i < n; i++) {
        const key = arr[i];
        let j = i - 1;
        record([i], [], 2, `Insert key=${key} into sorted prefix`);
        while (j >= 0) {
          comps++;
          record([j, j + 1], [], 3, `Compare arr[${j}]=${arr[j]} > key=${key}`);
          if (arr[j] > key) {
            swps++;
            arr[j + 1] = arr[j];
            record([], [j, j + 1], 4, `Shift ${arr[j]} right to index ${j + 1}`);
            j--;
          } else {
            break;
          }
        }
        arr[j + 1] = key;
        sortedSet.add(i);
        record([], [j + 1], 5, `Placed key=${key} at index ${j + 1}`);
      }
    } else if (algo === 'quick') {
      const quickSort = (low: number, high: number) => {
        if (low < high) {
          const pivot = arr[high];
          record([high], [], 2, `Partition range [${low}..${high}] with pivot=${pivot}`);
          let i = low - 1;
          for (let j = low; j < high; j++) {
            comps++;
            record([j, high], [], 2, `Compare arr[${j}]=${arr[j]} with pivot=${pivot}`);
            if (arr[j] < pivot) {
              i++;
              swps++;
              [arr[i], arr[j]] = [arr[j], arr[i]];
              record([], [i, j], 2, `Swap ${arr[i]} and ${arr[j]}`);
            }
          }
          swps++;
          [arr[i + 1], arr[high]] = [arr[high], arr[i + 1]];
          const pIdx = i + 1;
          sortedSet.add(pIdx);
          record([], [pIdx, high], 2, `Pivot ${pivot} locked at index ${pIdx}`);
          quickSort(low, pIdx - 1);
          quickSort(pIdx + 1, high);
        } else if (low === high) {
          sortedSet.add(low);
        }
      };
      quickSort(0, arr.length - 1);
    } else if (algo === 'merge') {
      const merge = (l: number, m: number, r: number) => {
        const left = arr.slice(l, m + 1);
        const right = arr.slice(m + 1, r + 1);
        let i = 0,
          j = 0,
          k = l;
        while (i < left.length && j < right.length) {
          comps++;
          record([l + i, m + 1 + j], [], 5, `Compare ${left[i]} and ${right[j]}`);
          if (left[i] <= right[j]) {
            arr[k] = left[i++];
          } else {
            arr[k] = right[j++];
            swps++;
          }
          record([], [k], 5, `Merged ${arr[k]} into position ${k}`);
          k++;
        }
        while (i < left.length) {
          arr[k] = left[i++];
          record([], [k], 5, `Copy remaining left ${arr[k]} to index ${k}`);
          k++;
        }
        while (j < right.length) {
          arr[k] = right[j++];
          record([], [k], 5, `Copy remaining right ${arr[k]} to index ${k}`);
          k++;
        }
      };

      const mergeSort = (l: number, r: number) => {
        if (l >= r) return;
        const m = Math.floor((l + r) / 2);
        record([m], [], 2, `Divide range [${l}..${r}] at midpoint ${m}`);
        mergeSort(l, m);
        mergeSort(m + 1, r);
        merge(l, m, r);
      };
      mergeSort(0, arr.length - 1);
    }

    for (let i = 0; i < arr.length; i++) sortedSet.add(i);
    record([], [], 5, `Sorting complete! Total comparisons: ${comps}, swaps: ${swps}`);
    return steps;
  }, []);

  const initWithRandom = useCallback(() => {
    setIsPlaying(false);
    const randomArr = generateRandomArray(arraySize);
    const computed = computeSortFrames(randomArr, algorithm);
    setFrames(computed);
    setCurrentFrameIndex(0);
  }, [arraySize, algorithm, generateRandomArray, computeSortFrames]);

  useEffect(() => {
    initWithRandom();
  }, [initWithRandom]);

  useEffect(() => {
    if (!isPlaying) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    const intervalMs = Math.max(25, Math.round(180 / speed));
    timerRef.current = window.setInterval(() => {
      setCurrentFrameIndex((prev) => {
        if (prev >= frames.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, intervalMs);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, speed, frames.length]);

  const currentFrame = frames[currentFrameIndex] || {
    array: [],
    comparing: [],
    swapping: [],
    sorted: [],
    comparisons: 0,
    swaps: 0,
    activeLine: 0,
    log: ''
  };

  const pseudo = PSEUDOCODE_MAP[algorithm];

  return (
    <div className="space-y-4">
      {/* Top Algorithm Selector & Array Size Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl border border-line bg-surface">
        <div className="flex flex-wrap items-center gap-1.5">
          {(['quick', 'merge', 'bubble', 'selection', 'insertion'] as SortAlgorithm[]).map((alg) => (
            <button
              key={alg}
              onClick={() => {
                setAlgorithm(alg);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold capitalize transition cursor-pointer ${
                algorithm === alg
                  ? 'bg-mint text-canvas'
                  : 'bg-canvas text-muted hover:text-ink border border-line'
              }`}
            >
              {alg} Sort
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3 bg-canvas px-3 py-1.5 rounded-lg border border-line">
          <span className="text-xs font-mono text-muted">Array Size (N):</span>
          <input
            type="range"
            min={5}
            max={50}
            value={arraySize}
            onChange={(e) => setArraySize(parseInt(e.target.value, 10))}
            className="w-28 accent-mint cursor-pointer"
          />
          <span className="text-xs font-mono font-bold text-mint w-6">{arraySize}</span>
        </div>
      </div>

      {/* Transport Control Bar */}
      <ControlBar
        isPlaying={isPlaying}
        onPlayPause={() => setIsPlaying((p) => !p)}
        onStep={() => setCurrentFrameIndex((idx) => Math.min(frames.length - 1, idx + 1))}
        onReset={() => {
          setIsPlaying(false);
          setCurrentFrameIndex(0);
        }}
        onRandomize={initWithRandom}
        speed={speed}
        onSpeedChange={setSpeed}
        disabledStep={currentFrameIndex >= frames.length - 1}
      />

      {/* Execution timeline scrubber */}
      <div className="flex items-center gap-3 px-4 py-2.5 rounded-xl border border-line bg-surface">
        <span className="text-[9px] font-mono uppercase tracking-[0.16em] text-muted shrink-0">
          Trace
        </span>
        <input
          type="range"
          min={0}
          max={Math.max(0, frames.length - 1)}
          value={currentFrameIndex}
          aria-label="Scrub execution timeline"
          onChange={(e) => {
            setIsPlaying(false);
            setCurrentFrameIndex(parseInt(e.target.value, 10));
          }}
          className="flex-1 accent-mint cursor-pointer"
        />
        <span className="text-[11px] font-mono text-ink tnum shrink-0">
          {currentFrameIndex + 1}
          <span className="text-muted"> / {frames.length}</span>
        </span>
      </div>

      {/* Split Screen Workbench */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Center Bar Stage */}
        <div className="lg:col-span-8">
          <VisualizerCanvas
            metrics={[
              { label: 'Comparisons', value: currentFrame.comparisons, color: 'var(--c-amber)' },
              { label: 'Swaps / Shifts', value: currentFrame.swaps, color: 'var(--c-rose)' },
              { label: 'Frame', value: `${currentFrameIndex + 1}/${frames.length}` }
            ]}
          >
            <div className="w-full">
              <div className="w-full h-64 flex items-end justify-center gap-[3px] px-1">
                {currentFrame.array.map((val, idx) => {
                  const isComparing = currentFrame.comparing.includes(idx);
                  const isSwapping = currentFrame.swapping.includes(idx);
                  const isSorted = currentFrame.sorted.includes(idx);

                  let barColor = 'var(--c-steel)';
                  if (isSwapping) barColor = 'var(--c-rose)';
                  else if (isComparing) barColor = 'var(--c-amber)';
                  else if (isSorted) barColor = 'var(--c-mint)';

                  const flagged = isComparing || isSwapping;

                  return (
                    <div
                      key={idx}
                      className="flex-1 flex flex-col items-center justify-end h-full min-w-0"
                    >
                      {arraySize <= 26 && (
                        <span
                          className={`text-[9px] font-mono mb-1 tnum transition-colors duration-150 ${
                            flagged ? 'text-ink font-bold' : 'text-muted'
                          }`}
                        >
                          {val}
                        </span>
                      )}
                      <div
                        style={{
                          height: `${val}%`,
                          backgroundColor: barColor,
                          transform: flagged ? 'scaleX(1.06)' : 'scaleX(1)'
                        }}
                        className="w-full rounded-t-[3px] origin-bottom transition-all duration-150 ease-out"
                      />
                    </div>
                  );
                })}
              </div>

              {/* baseline + index ruler */}
              <div className="w-full h-px bg-line mt-0.5" />
              <div className="w-full h-1.5 tick-rule opacity-60" aria-hidden="true" />
              {arraySize <= 26 && (
                <div className="w-full flex justify-center gap-[3px] px-1 mt-1">
                  {currentFrame.array.map((_, idx) => (
                    <span
                      key={idx}
                      className={`flex-1 text-center text-[9px] font-mono tnum min-w-0 ${
                        currentFrame.comparing.includes(idx) || currentFrame.swapping.includes(idx)
                          ? 'text-amber'
                          : 'text-muted'
                      }`}
                    >
                      {idx}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </VisualizerCanvas>
        </div>

        {/* Right Pseudocode & Execution Log */}
        <div className="lg:col-span-4">
          <PseudoCodePanel
            title={pseudo.title}
            lines={pseudo.lines}
            activeLine={currentFrame.activeLine}
            timeComplexity={pseudo.timeComplexity}
            spaceComplexity={pseudo.spaceComplexity}
            logs={frames.slice(0, currentFrameIndex + 1).map((f) => f.log)}
          />
        </div>
      </div>
    </div>
  );
};
