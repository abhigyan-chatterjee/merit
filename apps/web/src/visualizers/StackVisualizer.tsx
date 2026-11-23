import React, { useState, useEffect } from 'react';
import { ControlBar } from '../components/ControlBar';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';

interface Frame {
  stack: number[];
  activeIndices: number[];
  topIndex: number;
  activeLine: number;
  log: string;
}

const INITIAL_STACK = [15, 28, 42, 63];

const readyFrame = (values: number[]): Frame => ({
  stack: [...values],
  activeIndices: [],
  topIndex: values.length - 1,
  activeLine: -1,
  log: `Stack ready. Size: ${values.length}, Top index: ${values.length - 1}.`,
});

export const StackVisualizer: React.FC = () => {
  const [stack, setStack] = useState<number[]>(INITIAL_STACK);
  const [inputVal, setInputVal] = useState('89');
  const [status, setStatus] = useState('');

  const [frames, setFrames] = useState<Frame[]>(() => [readyFrame(INITIAL_STACK)]);
  const [frameIdx, setFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

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

  // Push
  const handlePush = () => {
    const parsed = parseInt(inputVal, 10);
    const val = Number.isNaN(parsed) ? 50 : parsed;
    if (stack.length >= 8) {
      setStatus('Stack overflow: visual limit is 8 items.');
      return;
    }
    setStatus('');

    const nextStack = [...stack, val];
    const generated: Frame[] = [
      {
        stack: [...stack],
        activeIndices: [],
        topIndex: stack.length - 1,
        activeLine: 0,
        log: `Push request for ${val}. Increment TOP to ${stack.length}.`,
      },
      {
        stack: nextStack,
        activeIndices: [nextStack.length - 1],
        topIndex: nextStack.length - 1,
        activeLine: 1,
        log: `Pushed ${val} onto top of stack. TOP is ${nextStack.length - 1}.`,
      },
    ];

    setStack(nextStack);
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // Pop
  const handlePop = () => {
    if (stack.length === 0) return;
    setStatus('');
    const poppedVal = stack[stack.length - 1];
    const nextStack = stack.slice(0, -1);

    const generated: Frame[] = [
      {
        stack: [...stack],
        activeIndices: [stack.length - 1],
        topIndex: stack.length - 1,
        activeLine: 2,
        log: `Popping top element: ${poppedVal}`,
      },
      {
        stack: nextStack,
        activeIndices: [],
        topIndex: nextStack.length - 1,
        activeLine: 3,
        log: `Popped ${poppedVal} (LIFO order). New TOP: ${nextStack.length > 0 ? nextStack[nextStack.length - 1] : 'empty'}.`,
      },
    ];

    setStack(nextStack);
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // Peek
  const handlePeek = () => {
    if (stack.length === 0) return;
    setStatus('');
    const topVal = stack[stack.length - 1];

    const generated: Frame[] = [
      {
        stack: [...stack],
        activeIndices: [stack.length - 1],
        topIndex: stack.length - 1,
        activeLine: 4,
        log: `O(1) Peek(): Top element is ${topVal} at index ${stack.length - 1}. Stack unchanged.`,
      },
    ];

    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // Clear
  const handleClear = () => {
    setStatus('');
    setStack([]);
    setFrames([
      {
        stack: [],
        activeIndices: [],
        topIndex: -1,
        activeLine: -1,
        log: 'Stack cleared. TOP reset to -1.',
      },
    ]);
    setFrameIdx(0);
  };

  const curr = frames[frameIdx] || readyFrame(stack);

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
          setStatus('');
          setStack(INITIAL_STACK);
          setFrames([readyFrame(INITIAL_STACK)]);
          setFrameIdx(0);
        }}
        onRandomize={() => {
          const rand = Array.from({ length: 4 }, () => Math.floor(Math.random() * 90) + 10);
          setIsPlaying(false);
          setStatus('');
          setStack(rand);
          setFrames([readyFrame(rand)]);
          setFrameIdx(0);
        }}
        speed={speed}
        onSpeedChange={setSpeed}
      />

      {/* Operations Toolbar */}
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
            onClick={handlePush}
            className="px-3 py-1 bg-mint text-canvas font-medium rounded hover:bg-mint/90 transition"
          >
            Push(val)
          </button>
          <button
            onClick={handlePop}
            className="px-3 py-1 bg-rose-600 text-white font-medium rounded hover:bg-rose-500 transition"
          >
            Pop()
          </button>
          <button
            onClick={handlePeek}
            className="px-3 py-1 bg-violet text-canvas font-medium rounded hover:bg-violet/90 transition"
          >
            Peek()
          </button>
          <button
            onClick={handleClear}
            className="px-3 py-1 border border-line text-muted rounded hover:text-ink transition"
          >
            Clear()
          </button>
        </div>
      </div>

      {status && (
        <p role="status" className="font-mono text-xs text-rose">
          {status}
        </p>
      )}

      {/* Visual Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8 space-y-3">
          <VisualizerCanvas
            metrics={[
              { label: 'Stack Size', value: `${curr.stack.length} / 8 max`, color: 'var(--c-mint)' },
              { label: 'TOP Pointer', value: curr.topIndex >= 0 ? `index ${curr.topIndex}` : 'NULL (-1)', color: 'var(--c-amber)' },
              { label: 'Access Policy', value: 'LIFO (Last-In First-Out)', color: 'var(--c-violet)' },
            ]}
            legend={[
              { label: 'Stack Frame', color: 'var(--c-steel)' },
              { label: 'Active / Peek', color: 'var(--c-amber)' },
              { label: 'TOP Element', color: 'var(--c-mint)' },
            ]}
          >
            <div data-testid="stack-workbench" className="py-6 px-4 flex flex-col items-center justify-center min-h-[300px]">
              {/* Vertical Stack U-shape Container */}
              <div className="relative w-48 border-x-4 border-b-4 border-steel/40 rounded-b-2xl p-2 flex flex-col-reverse items-center gap-1.5 min-h-[220px]">
                {curr.stack.length === 0 ? (
                  <div className="absolute inset-0 flex items-center justify-center text-muted font-mono text-xs">
                    Stack is Empty
                  </div>
                ) : (
                  curr.stack.map((val, idx) => {
                    const isTop = idx === curr.stack.length - 1;
                    const isActive = curr.activeIndices.includes(idx);

                    return (
                      <div
                        key={idx}
                        className={`w-full py-2.5 px-3 rounded-lg border font-mono font-bold flex items-center justify-between text-xs transition-colors duration-150 ${
                          isActive
                            ? 'bg-amber text-canvas border-amber shadow-lg scale-102'
                            : isTop
                            ? 'bg-mint/20 text-mint border-mint'
                            : 'bg-surface border-line text-ink'
                        }`}
                      >
                        <span>val: {val}</span>
                        <div className="flex items-center gap-1">
                          {isTop && (
                            <span className="px-1.5 py-0.5 rounded bg-amber text-[9px] font-black text-canvas uppercase">
                              TOP
                            </span>
                          )}
                          <span className="text-[10px] text-muted">[{idx}]</span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
              <span className="mt-2 font-mono text-[10px] text-muted uppercase tracking-wider">
                Base of Stack
              </span>
            </div>
          </VisualizerCanvas>

          {/* Activity Log */}
          <div className="p-3 bg-surface/40 border border-line rounded-xl font-mono text-xs text-muted flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-mint" />
            <span>{curr.log}</span>
          </div>
        </div>

        {/* Pseudocode */}
        <div className="lg:col-span-4">
          <PseudoCodePanel
            title="LIFO Stack Operations"
            lines={[
              'top = top + 1',
              'stack[top] = value  // Push O(1)',
              'value = stack[top]',
              'top = top - 1       // Pop O(1)',
              'return stack[top]   // Peek O(1)',
            ]}
            activeLine={curr.activeLine}
            timeComplexity="Push/Pop/Peek O(1)"
            spaceComplexity="O(n)"
            logs={frames.slice(0, frameIdx + 1).map((f) => f.log)}
          />
        </div>
      </div>
    </div>
  );
};
