import React, { useState, useEffect } from 'react';
import { ControlBar } from '../components/ControlBar';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';

interface Frame {
  array: number[];
  highlightIndices: number[];
  activeIndices: number[];
  pointers?: { label: string; index: number; color: string }[];
  activeLine: number;
  log: string;
}

export const ArrayVisualizer: React.FC = () => {
  const [array, setArray] = useState<number[]>([14, 32, 67, 89, 45, 23, 78]);
  const [targetIndex, setTargetIndex] = useState<number>(2);
  const [insertVal, setInsertVal] = useState<number>(99);

  const [frames, setFrames] = useState<Frame[]>([]);
  const [frameIdx, setFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  // Initialize with initial frame
  useEffect(() => {
    setFrames([
      {
        array: [...array],
        highlightIndices: [],
        activeIndices: [],
        activeLine: 0,
        log: 'Array initialized. Contiguous memory allocated.',
      },
    ]);
    setFrameIdx(0);
  }, [array]);

  // Timer playback
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
    }, Math.max(150, Math.round(700 / speed)));
    return () => clearInterval(timer);
  }, [isPlaying, speed, frames.length]);

  // 1. O(1) Index Access
  const handleAccess = () => {
    const idx = Math.max(0, Math.min(array.length - 1, targetIndex));
    const generated: Frame[] = [
      {
        array: [...array],
        highlightIndices: [],
        activeIndices: [],
        activeLine: 1,
        log: `Computing memory address: BaseAddr (0x1000) + ${idx} * 4 bytes = 0x${(0x1000 + idx * 4).toString(16).toUpperCase()}`,
      },
      {
        array: [...array],
        highlightIndices: [idx],
        activeIndices: [idx],
        pointers: [{ label: 'access', index: idx, color: 'var(--c-amber)' }],
        activeLine: 2,
        log: `O(1) Direct Lookup: arr[${idx}] = ${array[idx]}`,
      },
    ];
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // 2. Insert at index with shift
  const handleInsert = () => {
    const idx = Math.max(0, Math.min(array.length, targetIndex));
    const val = insertVal;
    const generated: Frame[] = [
      {
        array: [...array],
        highlightIndices: [],
        activeIndices: [],
        activeLine: 1,
        log: `Request to insert ${val} at index ${idx}. Must shift elements right.`,
      },
    ];

    const temp = [...array, 0];
    for (let i = temp.length - 1; i > idx; i--) {
      temp[i] = temp[i - 1];
      generated.push({
        array: [...temp],
        highlightIndices: [i, i - 1],
        activeIndices: [i],
        pointers: [{ label: 'shift', index: i, color: 'var(--c-amber)' }],
        activeLine: 3,
        log: `Shifted element from index ${i - 1} (${temp[i]}) to index ${i}`,
      });
    }

    temp[idx] = val;
    generated.push({
      array: [...temp],
      highlightIndices: [idx],
      activeIndices: [idx],
      pointers: [{ label: 'new', index: idx, color: 'var(--c-mint)' }],
      activeLine: 4,
      log: `Placed value ${val} into empty slot at index ${idx}. Insertion complete.`,
    });

    setArray(temp);
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // 3. Delete at index with shift
  const handleDelete = () => {
    if (array.length <= 1) return;
    const idx = Math.max(0, Math.min(array.length - 1, targetIndex));
    const val = array[idx];
    const generated: Frame[] = [
      {
        array: [...array],
        highlightIndices: [idx],
        activeIndices: [idx],
        pointers: [{ label: 'del', index: idx, color: 'var(--c-rose, #f43f5e)' }],
        activeLine: 1,
        log: `Deleting element arr[${idx}] = ${val}. Shifting subsequent elements left.`,
      },
    ];

    const temp = [...array];
    for (let i = idx; i < temp.length - 1; i++) {
      temp[i] = temp[i + 1];
      generated.push({
        array: [...temp],
        highlightIndices: [i, i + 1],
        activeIndices: [i],
        pointers: [{ label: 'shift', index: i, color: 'var(--c-amber)' }],
        activeLine: 3,
        log: `Shifted element from index ${i + 1} (${temp[i]}) to index ${i}`,
      });
    }
    temp.pop();

    generated.push({
      array: [...temp],
      highlightIndices: [],
      activeIndices: [],
      activeLine: 4,
      log: `Deletion complete. New array size: ${temp.length}.`,
    });

    setArray(temp);
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // 4. Two-Pointer Scan
  const handleTwoPointer = () => {
    const sorted = [...array].sort((a, b) => a - b);
    const generated: Frame[] = [
      {
        array: sorted,
        highlightIndices: [],
        activeIndices: [],
        activeLine: 1,
        log: 'Sorted array for two-pointer demonstration.',
      },
    ];

    let left = 0;
    let right = sorted.length - 1;

    while (left < right) {
      generated.push({
        array: sorted,
        highlightIndices: [left, right],
        activeIndices: [left, right],
        pointers: [
          { label: 'Left', index: left, color: 'var(--c-mint)' },
          { label: 'Right', index: right, color: 'var(--c-violet)' },
        ],
        activeLine: 3,
        log: `Scanning: Left [${left}] = ${sorted[left]}, Right [${right}] = ${sorted[right]}. Sum = ${sorted[left] + sorted[right]}`,
      });
      left++;
      right--;
    }

    generated.push({
      array: sorted,
      highlightIndices: [left],
      activeIndices: [],
      pointers: [{ label: 'Mid', index: left, color: 'var(--c-amber)' }],
      activeLine: 5,
      log: 'Pointers met at middle. Scan finished.',
    });

    setArray(sorted);
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  const curr = frames[frameIdx] || {
    array,
    highlightIndices: [],
    activeIndices: [],
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
          setArray([14, 32, 67, 89, 45, 23, 78]);
        }}
        onRandomize={() => {
          const rand = Array.from({ length: 7 }, () => Math.floor(Math.random() * 90) + 10);
          setArray(rand);
        }}
        speed={speed}
        onSpeedChange={setSpeed}
      />

      {/* Operation Toolbar */}
      <div className="flex flex-wrap items-center gap-3 p-3 bg-surface/50 border border-line rounded-xl text-xs">
        <div className="flex items-center gap-2">
          <label className="text-muted">Target Index:</label>
          <input
            type="number"
            value={targetIndex}
            min={0}
            max={array.length}
            onChange={(e) => setTargetIndex(parseInt(e.target.value, 10) || 0)}
            className="w-14 px-2 py-1 bg-surface border border-line rounded text-ink text-center"
          />
          <button
            onClick={handleAccess}
            className="px-3 py-1 bg-mint text-canvas font-medium rounded hover:bg-mint/90 transition"
          >
            Access [i]
          </button>
        </div>

        <div className="flex items-center gap-2 border-l border-line pl-3">
          <label className="text-muted">Value:</label>
          <input
            type="number"
            value={insertVal}
            onChange={(e) => setInsertVal(parseInt(e.target.value, 10) || 0)}
            className="w-16 px-2 py-1 bg-surface border border-line rounded text-ink text-center"
          />
          <button
            onClick={handleInsert}
            className="px-3 py-1 bg-violet text-canvas font-medium rounded hover:bg-violet/90 transition"
          >
            Insert at [i]
          </button>
          <button
            onClick={handleDelete}
            className="px-3 py-1 bg-rose-600 text-white font-medium rounded hover:bg-rose-500 transition"
          >
            Delete at [i]
          </button>
        </div>

        <div className="flex items-center gap-2 border-l border-line pl-3">
          <button
            onClick={handleTwoPointer}
            className="px-3 py-1 bg-amber text-canvas font-medium rounded hover:bg-amber/90 transition"
          >
            Two-Pointer Scan
          </button>
        </div>
      </div>

      {/* Visual Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8 space-y-3">
          <VisualizerCanvas
            metrics={[
              { label: 'Array Length', value: `${curr.array.length} items`, color: 'var(--c-mint)' },
              { label: 'Capacity', value: `${Math.max(8, curr.array.length)} slots`, color: 'var(--c-violet)' },
              { label: 'Element Size', value: '4 Bytes (Int32)', color: 'var(--c-amber)' },
            ]}
            legend={[
              { label: 'Unselected', color: 'var(--c-steel)' },
              { label: 'Active Pointer', color: 'var(--c-amber)' },
              { label: 'Modified Slot', color: 'var(--c-mint)' },
            ]}
          >
            <div data-testid="array-workbench" className="py-12 px-4 flex flex-col items-center justify-center gap-6">
              {/* Contiguous Memory Visualizer */}
              <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3">
                {curr.array.map((val, idx) => {
                  const isActive = curr.activeIndices.includes(idx);
                  const isHighlighted = curr.highlightIndices.includes(idx);
                  const ptr = curr.pointers?.find((p) => p.index === idx);

                  return (
                    <div key={idx} className="flex flex-col items-center gap-1.5">
                      {/* Pointer Tag */}
                      <div className="h-5 flex items-center justify-center font-mono text-[10px] font-bold">
                        {ptr && (
                          <span
                            className="px-1.5 py-0.5 rounded shadow text-canvas"
                            style={{ backgroundColor: ptr.color }}
                          >
                            {ptr.label}
                          </span>
                        )}
                      </div>

                      {/* Memory Cell */}
                      <div
                        className={`w-14 h-14 sm:w-16 sm:h-16 rounded-xl border flex flex-col items-center justify-center font-mono font-bold transition-colors duration-150 ${
                          isActive
                            ? 'bg-amber text-canvas border-amber scale-105 shadow-lg'
                            : isHighlighted
                            ? 'bg-mint/20 text-mint border-mint'
                            : 'bg-surface border-line text-ink'
                        }`}
                      >
                        <span className="text-base sm:text-lg">{val}</span>
                      </div>

                      {/* Index and Address */}
                      <span className="font-mono text-[10px] text-muted">[{idx}]</span>
                      <span className="font-mono text-[9px] text-muted/60">
                        0x{(0x1000 + idx * 4).toString(16).toUpperCase()}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </VisualizerCanvas>

          {/* Activity Log */}
          <div className="p-3 bg-surface/40 border border-line rounded-xl font-mono text-xs text-muted flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-mint" />
            <span>{curr.log}</span>
          </div>
        </div>

        {/* Pseudocode Panel */}
        <div className="lg:col-span-4">
          <PseudoCodePanel
            title="Array Contiguous Addressing"
            lines={[
              'address = base_address + index * element_size',
              'value = memory[address]  // O(1) Access',
              'for i from length down to index:',
              '    memory[i] = memory[i - 1]  // Shift right for insert',
              'memory[index] = new_value',
            ]}
            activeLine={curr.activeLine}
            timeComplexity="Access O(1) · Insert/Delete O(n)"
            spaceComplexity="O(n)"
            logs={frames.slice(0, frameIdx + 1).map((f) => f.log)}
          />
        </div>
      </div>
    </div>
  );
};
