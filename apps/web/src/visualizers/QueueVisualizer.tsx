import React, { useState, useEffect } from 'react';
import { ControlBar } from '../components/ControlBar';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';

interface QueueSlot {
  index: number;
  value: number | null;
}

interface Frame {
  slots: QueueSlot[];
  head: number;
  tail: number;
  size: number;
  activeSlot: number | null;
  activeLine: number;
  log: string;
}

const CAPACITY = 8;

export const QueueVisualizer: React.FC = () => {
  const [slots, setSlots] = useState<QueueSlot[]>(() => [
    { index: 0, value: 10 },
    { index: 1, value: 20 },
    { index: 2, value: 30 },
    { index: 3, value: 40 },
    { index: 4, value: null },
    { index: 5, value: null },
    { index: 6, value: null },
    { index: 7, value: null },
  ]);
  const [head, setHead] = useState(0);
  const [tail, setTail] = useState(4);
  const [size, setSize] = useState(4);
  const [inputVal, setInputVal] = useState('50');

  const [frames, setFrames] = useState<Frame[]>([]);
  const [frameIdx, setFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  useEffect(() => {
    setFrames([
      {
        slots: [...slots],
        head,
        tail,
        size,
        activeSlot: null,
        activeLine: 0,
        log: `Circular Queue ready. Head: ${head}, Tail: ${tail}, Count: ${size}/${CAPACITY}.`,
      },
    ]);
    setFrameIdx(0);
  }, [slots, head, tail, size]);

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

  // Enqueue
  const handleEnqueue = () => {
    const val = parseInt(inputVal, 10) || 77;
    if (size >= CAPACITY) {
      alert('Queue is full (circular capacity reached)');
      return;
    }

    const nextSlots = slots.map((s) => (s.index === tail ? { ...s, value: val } : s));
    const nextTail = (tail + 1) % CAPACITY;
    const nextSize = size + 1;

    const generated: Frame[] = [
      {
        slots: [...slots],
        head,
        tail,
        size,
        activeSlot: tail,
        activeLine: 1,
        log: `Enqueue(${val}): placing into slot [${tail}] at TAIL pointer.`,
      },
      {
        slots: nextSlots,
        head,
        tail: nextTail,
        size: nextSize,
        activeSlot: tail,
        activeLine: 2,
        log: `Advanced TAIL to (${tail} + 1) % ${CAPACITY} = ${nextTail}. Count is now ${nextSize}.`,
      },
    ];

    setSlots(nextSlots);
    setTail(nextTail);
    setSize(nextSize);
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // Dequeue
  const handleDequeue = () => {
    if (size === 0) return;
    const dequeuedVal = slots[head].value;
    const nextSlots = slots.map((s) => (s.index === head ? { ...s, value: null } : s));
    const nextHead = (head + 1) % CAPACITY;
    const nextSize = size - 1;

    const generated: Frame[] = [
      {
        slots: [...slots],
        head,
        tail,
        size,
        activeSlot: head,
        activeLine: 3,
        log: `Dequeue(): removing element ${dequeuedVal} from HEAD slot [${head}].`,
      },
      {
        slots: nextSlots,
        head: nextHead,
        tail,
        size: nextSize,
        activeSlot: null,
        activeLine: 4,
        log: `Advanced HEAD to (${head} + 1) % ${CAPACITY} = ${nextHead}. Count is now ${nextSize}.`,
      },
    ];

    setSlots(nextSlots);
    setHead(nextHead);
    setSize(nextSize);
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // Front
  const handleFront = () => {
    if (size === 0) return;
    const frontVal = slots[head].value;
    const generated: Frame[] = [
      {
        slots: [...slots],
        head,
        tail,
        size,
        activeSlot: head,
        activeLine: 5,
        log: `Front() inspection: element at HEAD [${head}] is ${frontVal}. Queue unmodified.`,
      },
    ];
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // Clear
  const handleClear = () => {
    const emptySlots = Array.from({ length: CAPACITY }, (_, i) => ({ index: i, value: null }));
    setSlots(emptySlots);
    setHead(0);
    setTail(0);
    setSize(0);
    setFrames([
      {
        slots: emptySlots,
        head: 0,
        tail: 0,
        size: 0,
        activeSlot: null,
        activeLine: 0,
        log: 'Queue cleared.',
      },
    ]);
  };

  const curr = frames[frameIdx] || {
    slots,
    head,
    tail,
    size,
    activeSlot: null,
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
          setSlots([
            { index: 0, value: 10 },
            { index: 1, value: 20 },
            { index: 2, value: 30 },
            { index: 3, value: 40 },
            { index: 4, value: null },
            { index: 5, value: null },
            { index: 6, value: null },
            { index: 7, value: null },
          ]);
          setHead(0);
          setTail(4);
          setSize(4);
        }}
        onRandomize={() => {
          const count = 4;
          const newSlots = Array.from({ length: CAPACITY }, (_, i) => ({
            index: i,
            value: i < count ? Math.floor(Math.random() * 90) + 10 : null,
          }));
          setSlots(newSlots);
          setHead(0);
          setTail(count);
          setSize(count);
        }}
        speed={speed}
        onSpeedChange={setSpeed}
      />

      {/* Operation Toolbar */}
      <div className="flex flex-wrap items-center gap-3 p-3 bg-surface/50 border border-line rounded-xl text-xs">
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            className="w-16 px-2 py-1 bg-surface border border-line rounded text-ink text-center"
            placeholder="Val"
          />
          <button
            onClick={handleEnqueue}
            className="px-3 py-1 bg-mint text-canvas font-medium rounded hover:bg-mint/90 transition"
          >
            Enqueue(val)
          </button>
          <button
            onClick={handleDequeue}
            className="px-3 py-1 bg-rose-600 text-white font-medium rounded hover:bg-rose-500 transition"
          >
            Dequeue()
          </button>
          <button
            onClick={handleFront}
            className="px-3 py-1 bg-violet text-canvas font-medium rounded hover:bg-violet/90 transition"
          >
            Front()
          </button>
          <button
            onClick={handleClear}
            className="px-3 py-1 border border-line text-muted rounded hover:text-ink transition"
          >
            Clear()
          </button>
        </div>
      </div>

      {/* Visual Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8 space-y-3">
          <VisualizerCanvas
            metrics={[
              { label: 'Capacity', value: `${curr.size} / ${CAPACITY} slots`, color: 'var(--c-mint)' },
              { label: 'HEAD (Front)', value: `index [${curr.head}]`, color: 'var(--c-mint)' },
              { label: 'TAIL (Rear)', value: `index [${curr.tail}]`, color: 'var(--c-violet)' },
            ]}
            legend={[
              { label: 'Occupied Slot', color: 'var(--c-mint)' },
              { label: 'Empty Slot', color: 'var(--c-steel)' },
              { label: 'Active Pointer', color: 'var(--c-amber)' },
            ]}
          >
            <div data-testid="queue-workbench" className="py-12 px-4 flex flex-col items-center justify-center gap-6">
              {/* Circular Buffer Visualizer */}
              <div className="flex flex-wrap items-center justify-center gap-3">
                {curr.slots.map((slot) => {
                  const isHead = slot.index === curr.head && curr.size > 0;
                  const isTail = slot.index === curr.tail;
                  const isActive = slot.index === curr.activeSlot;
                  const hasValue = slot.value !== null;

                  return (
                    <div key={slot.index} className="flex flex-col items-center gap-1.5">
                      {/* Pointer Badges */}
                      <div className="h-5 flex items-center gap-1 font-mono text-[9px] font-black">
                        {isHead && (
                          <span className="px-1.5 py-0.5 rounded bg-mint text-canvas">HEAD</span>
                        )}
                        {isTail && (
                          <span className="px-1.5 py-0.5 rounded bg-violet text-canvas">TAIL</span>
                        )}
                      </div>

                      {/* Slot Box */}
                      <div
                        className={`w-14 h-14 sm:w-16 sm:h-16 rounded-xl border flex flex-col items-center justify-center font-mono font-bold transition-all duration-200 ${
                          isActive
                            ? 'bg-amber text-canvas border-amber scale-105 shadow-lg'
                            : hasValue
                            ? 'bg-mint/15 text-mint border-mint'
                            : 'bg-surface/50 border-dashed border-line text-muted/50'
                        }`}
                      >
                        <span className="text-base sm:text-lg">
                          {hasValue ? slot.value : '—'}
                        </span>
                      </div>

                      {/* Index */}
                      <span className="font-mono text-[10px] text-muted">[{slot.index}]</span>
                    </div>
                  );
                })}
              </div>

              <div className="text-xs text-muted font-mono flex items-center gap-2">
                <span>Buffer wrap formula:</span>
                <span className="px-2 py-0.5 rounded bg-surface border border-line text-ink">
                  next = (current + 1) % {CAPACITY}
                </span>
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
            title="FIFO Circular Queue"
            lines={[
              'buffer[tail] = value',
              'tail = (tail + 1) % CAPACITY  // Enqueue O(1)',
              'value = buffer[head]',
              'head = (head + 1) % CAPACITY  // Dequeue O(1)',
              'return buffer[head]           // Front O(1)',
            ]}
            activeLine={curr.activeLine}
            timeComplexity="Enqueue/Dequeue O(1)"
            spaceComplexity="O(n)"
            logs={frames.slice(0, frameIdx + 1).map((f) => f.log)}
          />
        </div>
      </div>
    </div>
  );
};
