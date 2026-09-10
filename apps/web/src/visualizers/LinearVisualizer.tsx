import React, { useState } from 'react';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';
import { PSEUDOCODE_MAP } from '../data/pseudocode';
import { Plus, Trash2, ArrowRight, Search } from 'lucide-react';

interface LinearVisualizerProps {
  id: string;
}

export const LinearVisualizer: React.FC<LinearVisualizerProps> = ({ id }) => {
  const [items, setItems] = useState<number[]>([14, 28, 42, 56, 70, 84]);
  const [inputVal, setInputVal] = useState('');
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [logs, setLogs] = useState<string[]>([`Initialized ${id} structure with 6 items`]);
  const [searchTarget, setSearchTarget] = useState('56');

  const logOp = (msg: string) => {
    setLogs((prev) => [...prev, msg]);
  };

  const handlePushOrInsert = (e: React.FormEvent) => {
    e.preventDefault();
    const num = parseInt(inputVal, 10);
    if (isNaN(num)) return;
    setItems((prev) => [...prev, num]);
    setActiveIndex(items.length);
    logOp(`Inserted value ${num} at tail index ${items.length}`);
    setInputVal('');
  };

  const handlePopOrDequeue = () => {
    if (items.length === 0) return;
    if (id === 'queue') {
      const removed = items[0];
      setItems((prev) => prev.slice(1));
      setActiveIndex(0);
      logOp(`Dequeued head element ${removed}`);
    } else {
      const removed = items[items.length - 1];
      setItems((prev) => prev.slice(0, -1));
      setActiveIndex(items.length - 2);
      logOp(`Popped top element ${removed}`);
    }
  };

  const handleRunBinarySearch = () => {
    const target = parseInt(searchTarget, 10);
    if (isNaN(target)) return;
    const sorted = [...items].sort((a, b) => a - b);
    setItems(sorted);

    let l = 0,
      r = sorted.length - 1;
    const trace: string[] = [];
    let foundIdx = -1;
    while (l <= r) {
      const mid = Math.floor((l + r) / 2);
      trace.push(`Check mid=${mid} (val=${sorted[mid]}) vs target=${target}`);
      if (sorted[mid] === target) {
        foundIdx = mid;
        trace.push(`✓ Found target ${target} at index ${mid}!`);
        break;
      } else if (sorted[mid] < target) {
        l = mid + 1;
      } else {
        r = mid - 1;
      }
    }
    if (foundIdx === -1) trace.push(`✗ Target ${target} not found in array.`);
    setActiveIndex(foundIdx !== -1 ? foundIdx : null);
    setLogs((prev) => [...prev, ...trace]);
  };

  const pseudo = id === 'searching' ? PSEUDOCODE_MAP['binary-search'] : PSEUDOCODE_MAP.linear;

  return (
    <div className="space-y-4">
      {/* Interactive Operation Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl border border-line bg-surface">
        <form onSubmit={handlePushOrInsert} className="flex items-center gap-2">
          <input
            type="number"
            placeholder="Value (e.g. 99)..."
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            className="w-36 px-3 py-1.5 rounded-lg bg-canvas border border-line text-xs font-mono text-ink focus:outline-none focus:border-mint"
          />
          <button
            type="submit"
            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-mint text-canvas font-semibold text-xs hover:brightness-110 transition cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            {id === 'stack' ? 'Push' : id === 'queue' ? 'Enqueue' : 'Insert'}
          </button>

          <button
            type="button"
            onClick={handlePopOrDequeue}
            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-rose/15 border border-rose/40 text-rose font-mono text-xs hover:bg-rose hover:text-canvas transition cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
            {id === 'stack' ? 'Pop' : id === 'queue' ? 'Dequeue' : 'Delete Tail'}
          </button>
        </form>

        {id === 'searching' && (
          <div className="flex items-center gap-2">
            <input
              type="number"
              value={searchTarget}
              onChange={(e) => setSearchTarget(e.target.value)}
              placeholder="Target..."
              className="w-24 px-2.5 py-1.5 rounded-lg bg-canvas border border-line text-xs font-mono text-ink"
            />
            <button
              onClick={handleRunBinarySearch}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet text-canvas font-semibold text-xs hover:brightness-110 transition cursor-pointer"
            >
              <Search className="w-3.5 h-3.5" />
              Binary Search Target
            </button>
          </div>
        )}
      </div>

      {/* Main Canvas + Pseudocode */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8">
          <VisualizerCanvas
            metrics={[
              { label: 'Size / Count', value: items.length, color: 'var(--c-mint)' },
              {
                label: 'Active Pointer',
                value: activeIndex !== null ? `index [${activeIndex}]` : 'None',
                color: 'var(--c-amber)'
              }
            ]}
          >
            <div className="flex flex-wrap items-center justify-center gap-3 p-4">
              {items.map((val, idx) => {
                const isActive = activeIndex === idx;
                const bucketLabel = id === 'hashmap' ? `Hash(${val}) = ${val % 7}` : `[${idx}]`;
                return (
                  <React.Fragment key={idx}>
                    <div className="flex flex-col items-center">
                      <span className="text-[10px] font-mono text-muted mb-1">
                        {bucketLabel}
                      </span>
                      <div
                        className={`w-16 h-16 rounded-xl border-2 flex flex-col items-center justify-center font-mono transition-colors duration-150 ${
                          isActive
                            ? 'border-mint bg-mint/20 text-mint scale-110'
                            : 'border-line bg-surface text-ink'
                        }`}
                      >
                        <span className="text-sm font-bold">{val}</span>
                        {idx === 0 && (
                          <span className="text-[9px] text-violet uppercase">HEAD</span>
                        )}
                        {idx === items.length - 1 && items.length > 1 && (
                          <span className="text-[9px] text-amber uppercase">TAIL</span>
                        )}
                      </div>
                    </div>

                    {id === 'linked-list' && idx < items.length - 1 && (
                      <ArrowRight className="w-5 h-5 text-mint mt-4" />
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </VisualizerCanvas>
        </div>

        <div className="lg:col-span-4">
          <PseudoCodePanel
            title={pseudo.title}
            lines={pseudo.lines}
            activeLine={activeIndex !== null ? 2 : 0}
            timeComplexity={pseudo.timeComplexity}
            spaceComplexity={pseudo.spaceComplexity}
            logs={logs}
          />
        </div>
      </div>
    </div>
  );
};
