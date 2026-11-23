import React, { useState, useEffect } from 'react';
import { ControlBar } from '../components/ControlBar';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';
import { ArrowRight } from 'lucide-react';

interface Entry {
  key: string;
  value: string;
}

interface Frame {
  buckets: Entry[][];
  activeBucket: number | null;
  activeKey: string | null;
  activeLine: number;
  log: string;
}

const BUCKET_COUNT = 5;

const INITIAL_BUCKETS: Entry[][] = [
  [{ key: 'apple', value: '42' }],
  [{ key: 'banana', value: '18' }],
  [{ key: 'cherry', value: '99' }, { key: 'date', value: '73' }],
  [],
  [{ key: 'elderberry', value: '55' }],
];

const cloneBuckets = (buckets: Entry[][]): Entry[][] => buckets.map((b) => [...b]);

const readyFrame = (buckets: Entry[][]): Frame => ({
  buckets: cloneBuckets(buckets),
  activeBucket: null,
  activeKey: null,
  activeLine: -1,
  log: `Hash Map initialized with ${BUCKET_COUNT} buckets. Separate chaining active.`,
});

function hashKey(key: string, m: number = BUCKET_COUNT): number {
  let sum = 0;
  for (let i = 0; i < key.length; i++) {
    sum += key.charCodeAt(i);
  }
  return sum % m;
}

export const HashMapVisualizer: React.FC = () => {
  const [buckets, setBuckets] = useState<Entry[][]>(INITIAL_BUCKETS.map((b) => [...b]));

  const [inputKey, setInputKey] = useState('fig');
  const [inputVal, setInputVal] = useState('64');

  const [frames, setFrames] = useState<Frame[]>(() => [readyFrame(INITIAL_BUCKETS)]);
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

  // Put
  const handlePut = () => {
    const k = inputKey.trim();
    const v = inputVal.trim();
    if (!k) return;

    const bIdx = hashKey(k);
    const generated: Frame[] = [
      {
        buckets: cloneBuckets(buckets),
        activeBucket: bIdx,
        activeKey: null,
        activeLine: 0,
        log: `hash("${k}") = sum(ascii) % ${BUCKET_COUNT} = Bucket [${bIdx}]`,
      },
    ];

    const nextBuckets = cloneBuckets(buckets);
    const existingIndex = nextBuckets[bIdx].findIndex((e) => e.key === k);

    if (existingIndex !== -1) {
      nextBuckets[bIdx][existingIndex] = { key: k, value: v };
      generated.push({
        buckets: nextBuckets,
        activeBucket: bIdx,
        activeKey: k,
        activeLine: 3,
        log: `Key "${k}" found in Bucket [${bIdx}]. Updated value to "${v}".`,
      });
    } else {
      nextBuckets[bIdx].push({ key: k, value: v });
      generated.push({
        buckets: nextBuckets,
        activeBucket: bIdx,
        activeKey: k,
        activeLine: 4,
        log: `Appended pair {"${k}": "${v}"} to collision chain of Bucket [${bIdx}].`,
      });
    }

    setBuckets(nextBuckets);
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // Get
  const handleGet = () => {
    const k = inputKey.trim();
    if (!k) return;

    const bIdx = hashKey(k);
    const generated: Frame[] = [
      {
        buckets: cloneBuckets(buckets),
        activeBucket: bIdx,
        activeKey: null,
        activeLine: 0,
        log: `Get("${k}"): Computing hash index -> Bucket [${bIdx}].`,
      },
    ];

    const chain = buckets[bIdx];
    let found = false;
    for (let i = 0; i < chain.length; i++) {
      const entry = chain[i];
      if (entry.key === k) {
        generated.push({
          buckets: cloneBuckets(buckets),
          activeBucket: bIdx,
          activeKey: k,
          activeLine: 2,
          log: `MATCH: Found key "${k}" with value "${entry.value}" in Bucket [${bIdx}] at position ${i}!`,
        });
        found = true;
        break;
      } else {
        generated.push({
          buckets: cloneBuckets(buckets),
          activeBucket: bIdx,
          activeKey: entry.key,
          activeLine: 1,
          log: `Checking "${entry.key}" != "${k}". Advancing collision chain...`,
        });
      }
    }

    if (!found) {
      generated.push({
        buckets: cloneBuckets(buckets),
        activeBucket: bIdx,
        activeKey: null,
        activeLine: 7,
        log: `Key "${k}" not found in Bucket [${bIdx}]. Returned null.`,
      });
    }

    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // Delete
  const handleDelete = () => {
    const k = inputKey.trim();
    if (!k) return;

    const bIdx = hashKey(k);
    const chain = buckets[bIdx];
    const index = chain.findIndex((e) => e.key === k);

    const generated: Frame[] = [
      {
        buckets: cloneBuckets(buckets),
        activeBucket: bIdx,
        activeKey: k,
        activeLine: 0,
        log: `Delete("${k}"): Searching Bucket [${bIdx}]...`,
      },
    ];

    if (index === -1) {
      generated.push({
        buckets: cloneBuckets(buckets),
        activeBucket: bIdx,
        activeKey: null,
        activeLine: 7,
        log: `Key not found: "${k}" is not present in Bucket [${bIdx}]. Nothing deleted.`,
      });
      setFrames(generated);
      setFrameIdx(0);
      setIsPlaying(true);
      return;
    }

    generated.push({
      buckets: cloneBuckets(buckets),
      activeBucket: bIdx,
      activeKey: k,
      activeLine: 5,
      log: `Found key "${k}" in Bucket [${bIdx}]. Unlinking its entry.`,
    });

    const nextBuckets = cloneBuckets(buckets);
    nextBuckets[bIdx] = nextBuckets[bIdx].filter((e) => e.key !== k);
    generated.push({
      buckets: nextBuckets,
      activeBucket: bIdx,
      activeKey: null,
      activeLine: 6,
      log: `Key "${k}" unlinked from Bucket [${bIdx}]. Deletion complete.`,
    });

    setBuckets(nextBuckets);
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // Demo Collision
  const handleTriggerCollision = () => {
    const working = cloneBuckets(buckets);
    const bIdx = hashKey('cat');
    const generated: Frame[] = [];
    const snapshot = (activeKey: string | null, activeLine: number, log: string) => {
      generated.push({
        buckets: cloneBuckets(working),
        activeBucket: bIdx,
        activeKey,
        activeLine,
        log,
      });
    };

    snapshot('cat', 0, `hash("cat") = ${bIdx}. Appending without clearing existing chain entries.`);
    if (!working[bIdx].some((e) => e.key === 'cat')) {
      working[bIdx].push({ key: 'cat', value: '100' });
      snapshot('cat', 4, `Appended "cat" to Bucket [${bIdx}]. Existing entries preserved.`);
    } else {
      snapshot('cat', 1, `Key "cat" is already chained in Bucket [${bIdx}].`);
    }

    snapshot('act', 0, `hash("act") = ${bIdx} -> collision with "cat".`);
    if (!working[bIdx].some((e) => e.key === 'act')) {
      working[bIdx].push({ key: 'act', value: '200' });
      snapshot('act', 4, `Chained colliding key "act" alongside the other entries in Bucket [${bIdx}].`);
    } else {
      snapshot('act', 1, `Key "act" is already chained in Bucket [${bIdx}].`);
    }

    setBuckets(working);
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  const curr = frames[frameIdx] || readyFrame(buckets);
  const totalEntries = curr.buckets.reduce((acc, b) => acc + b.length, 0);
  const loadFactor = (totalEntries / BUCKET_COUNT).toFixed(2);

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
          setBuckets(INITIAL_BUCKETS.map((b) => [...b]));
          setFrames([readyFrame(INITIAL_BUCKETS)]);
          setFrameIdx(0);
        }}
        onRandomize={() => {
          const words = ['alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'theta', 'omega'];
          const newBuckets: Entry[][] = Array.from({ length: BUCKET_COUNT }, () => []);
          for (const w of words) {
            newBuckets[hashKey(w)].push({ key: w, value: `${Math.floor(Math.random() * 90) + 10}` });
          }
          setIsPlaying(false);
          setBuckets(newBuckets);
          setFrames([readyFrame(newBuckets)]);
          setFrameIdx(0);
        }}
        speed={speed}
        onSpeedChange={setSpeed}
      />

      {/* Operation Toolbar */}
      <div className="flex flex-wrap items-center gap-3 p-3 bg-surface/50 border border-line rounded-xl text-xs">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={inputKey}
            onChange={(e) => setInputKey(e.target.value)}
            className="w-20 px-2 py-1 bg-surface border border-line rounded text-ink text-center"
            placeholder="Key"
          />
          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            className="w-16 px-2 py-1 bg-surface border border-line rounded text-ink text-center"
            placeholder="Val"
          />
          <button
            onClick={handlePut}
            className="px-3 py-1 bg-mint text-canvas font-medium rounded hover:bg-mint/90 transition"
          >
            Put(k, v)
          </button>
          <button
            onClick={handleGet}
            className="px-3 py-1 bg-violet text-canvas font-medium rounded hover:bg-violet/90 transition"
          >
            Get(k)
          </button>
          <button
            onClick={handleDelete}
            className="px-3 py-1 bg-rose-600 text-white font-medium rounded hover:bg-rose-500 transition"
          >
            Delete(k)
          </button>
        </div>

        <div className="flex items-center gap-2 border-l border-line pl-3">
          <button
            onClick={handleTriggerCollision}
            className="px-3 py-1 bg-amber text-canvas font-medium rounded hover:bg-amber/90 transition"
          >
            Trigger Collision
          </button>
        </div>
      </div>

      {/* Visual Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8 space-y-3">
          <VisualizerCanvas
            metrics={[
              { label: 'Bucket Count (M)', value: `${BUCKET_COUNT}`, color: 'var(--c-mint)' },
              { label: 'Total Entries (N)', value: `${totalEntries}`, color: 'var(--c-violet)' },
              { label: 'Load Factor (N/M)', value: `${loadFactor}`, color: 'var(--c-amber)' },
            ]}
            legend={[
              { label: 'Bucket Index', color: 'var(--c-steel)' },
              { label: 'Active Bucket', color: 'var(--c-amber)' },
              { label: 'Chained Pair [K:V]', color: 'var(--c-mint)' },
            ]}
          >
            <div data-testid="hashmap-workbench" className="py-8 px-4 flex flex-col gap-3 min-h-[300px]">
              {curr.buckets.map((chain, bIdx) => {
                const isBucketActive = curr.activeBucket === bIdx;

                return (
                  <div key={bIdx} className="flex items-center gap-3">
                    {/* Bucket Slot */}
                    <div
                      className={`w-24 px-2 py-2 rounded-xl border font-mono flex items-center justify-between text-xs transition-colors duration-150 ${
                        isBucketActive
                          ? 'bg-amber text-canvas border-amber shadow-lg font-bold'
                          : 'bg-surface border-line text-muted'
                      }`}
                    >
                      <span>Bucket</span>
                      <span className="font-bold">[{bIdx}]</span>
                    </div>

                    <ArrowRight className="w-4 h-4 text-muted shrink-0" />

                    {/* Linked Chain of Entries */}
                    <div className="flex items-center gap-2 overflow-x-auto py-1">
                      {chain.length === 0 ? (
                        <span className="text-muted/50 font-mono text-[11px] italic">null (empty)</span>
                      ) : (
                        chain.map((entry, eIdx) => {
                          const isEntryActive = curr.activeKey === entry.key;

                          return (
                            <React.Fragment key={eIdx}>
                              <div
                                className={`px-3 py-1.5 rounded-lg border font-mono text-xs flex items-center gap-1.5 transition-colors duration-150 ${
                                  isEntryActive
                                    ? 'bg-amber text-canvas border-amber scale-105 shadow'
                                    : 'bg-mint/15 border-mint text-ink'
                                }`}
                              >
                                <span className="font-bold text-mint">{entry.key}</span>
                                <span className="text-muted">:</span>
                                <span className="text-ink font-semibold">{entry.value}</span>
                              </div>
                              {eIdx < chain.length - 1 && (
                                <ArrowRight className="w-3.5 h-3.5 text-muted shrink-0" />
                              )}
                            </React.Fragment>
                          );
                        })
                      )}
                    </div>
                  </div>
                );
              })}
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
            title="Separate Chaining Hash Map"
            lines={[
              'bucket_index = hash(key) % BUCKET_COUNT',
              'for entry in buckets[bucket_index]:',
              '    if entry.key == key: return entry.value  // get',
              '    if entry.key == key: entry.value = value  // put update',
              'buckets[bucket_index].append(new Entry(key, value))  // put insert',
              'for entry in buckets[bucket_index]:',
              '    if entry.key == key: unlink entry  // delete',
              'return null  // key not found',
            ]}
            activeLine={curr.activeLine}
            timeComplexity="Average O(1) · Worst O(n)"
            spaceComplexity="O(n + m)"
            logs={frames.slice(0, frameIdx + 1).map((f) => f.log)}
          />
        </div>
      </div>
    </div>
  );
};
