import React, { useState, useEffect } from 'react';
import { ControlBar } from '../components/ControlBar';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';
import { ArrowRight } from 'lucide-react';

interface LLNode {
  id: string;
  value: number;
}

interface Frame {
  nodes: LLNode[];
  activeNodeIds: string[];
  pointers?: { label: string; nodeId: string; color: string }[];
  activeLine: number;
  log: string;
}

export const LinkedListVisualizer: React.FC = () => {
  const [nodes, setNodes] = useState<LLNode[]>([
    { id: 'n1', value: 12 },
    { id: 'n2', value: 34 },
    { id: 'n3', value: 56 },
    { id: 'n4', value: 78 },
  ]);
  const [inputVal, setInputVal] = useState('99');

  const [frames, setFrames] = useState<Frame[]>([]);
  const [frameIdx, setFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  useEffect(() => {
    setFrames([
      {
        nodes: [...nodes],
        activeNodeIds: [],
        pointers: [
          { label: 'HEAD', nodeId: nodes[0]?.id || '', color: 'var(--c-mint)' },
          { label: 'TAIL', nodeId: nodes[nodes.length - 1]?.id || '', color: 'var(--c-violet)' },
        ],
        activeLine: 0,
        log: 'Linked list initialized with head and tail pointers.',
      },
    ]);
    setFrameIdx(0);
  }, [nodes]);

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

  // Insert Head
  const handleInsertHead = () => {
    const val = parseInt(inputVal, 10) || 10;
    const newNode: LLNode = { id: `n-${Date.now()}`, value: val };

    const generated: Frame[] = [
      {
        nodes: [...nodes],
        activeNodeIds: [],
        activeLine: 1,
        log: `Allocated new node with value ${val}`,
      },
      {
        nodes: [newNode, ...nodes],
        activeNodeIds: [newNode.id],
        pointers: [
          { label: 'NEW', nodeId: newNode.id, color: 'var(--c-amber)' },
          { label: 'HEAD', nodeId: nodes[0]?.id || '', color: 'var(--c-mint)' },
        ],
        activeLine: 2,
        log: `Pointed newNode.next -> current HEAD (${nodes[0]?.value ?? 'null'})`,
      },
      {
        nodes: [newNode, ...nodes],
        activeNodeIds: [newNode.id],
        pointers: [
          { label: 'HEAD', nodeId: newNode.id, color: 'var(--c-mint)' },
          { label: 'TAIL', nodeId: nodes[nodes.length - 1]?.id || newNode.id, color: 'var(--c-violet)' },
        ],
        activeLine: 3,
        log: `Updated HEAD pointer to new node ${val}. O(1) prepend complete.`,
      },
    ];

    setNodes([newNode, ...nodes]);
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // Insert Tail
  const handleInsertTail = () => {
    const val = parseInt(inputVal, 10) || 99;
    const newNode: LLNode = { id: `n-${Date.now()}`, value: val };

    const generated: Frame[] = [
      {
        nodes: [...nodes],
        activeNodeIds: [],
        activeLine: 1,
        log: `Allocated new node with value ${val}`,
      },
      {
        nodes: [...nodes, newNode],
        activeNodeIds: [newNode.id],
        pointers: [
          { label: 'TAIL', nodeId: nodes[nodes.length - 1]?.id || '', color: 'var(--c-violet)' },
          { label: 'NEW', nodeId: newNode.id, color: 'var(--c-amber)' },
        ],
        activeLine: 2,
        log: `Rewired tail.next -> newNode (${val})`,
      },
      {
        nodes: [...nodes, newNode],
        activeNodeIds: [newNode.id],
        pointers: [
          { label: 'HEAD', nodeId: nodes[0]?.id || newNode.id, color: 'var(--c-mint)' },
          { label: 'TAIL', nodeId: newNode.id, color: 'var(--c-violet)' },
        ],
        activeLine: 3,
        log: `Updated TAIL pointer to new node ${val}. Append complete.`,
      },
    ];

    setNodes([...nodes, newNode]);
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // Delete Head
  const handleDeleteHead = () => {
    if (nodes.length <= 1) return;
    const oldHead = nodes[0];
    const newHead = nodes[1];

    const generated: Frame[] = [
      {
        nodes: [...nodes],
        activeNodeIds: [oldHead.id],
        pointers: [{ label: 'DEL', nodeId: oldHead.id, color: 'var(--c-rose, #f43f5e)' }],
        activeLine: 1,
        log: `Targeting HEAD node (${oldHead.value}) for removal`,
      },
      {
        nodes: nodes.slice(1),
        activeNodeIds: [newHead.id],
        pointers: [
          { label: 'HEAD', nodeId: newHead.id, color: 'var(--c-mint)' },
          { label: 'TAIL', nodeId: nodes[nodes.length - 1].id, color: 'var(--c-violet)' },
        ],
        activeLine: 2,
        log: `Advanced HEAD to next node (${newHead.value}). Free old head memory.`,
      },
    ];

    setNodes(nodes.slice(1));
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  // Reverse List (Three-pointer technique: prev, curr, next)
  const handleReverse = () => {
    if (nodes.length <= 1) return;
    const generated: Frame[] = [
      {
        nodes: [...nodes],
        activeNodeIds: [],
        pointers: [{ label: 'CURR', nodeId: nodes[0].id, color: 'var(--c-amber)' }],
        activeLine: 1,
        log: 'Initializing 3-pointer in-place reversal: prev = null, curr = head',
      },
    ];

    const reversed: LLNode[] = [];
    for (let i = 0; i < nodes.length; i++) {
      const currNode = nodes[i];
      reversed.unshift(currNode);

      generated.push({
        nodes: [...nodes],
        activeNodeIds: [currNode.id],
        pointers: [
          { label: 'CURR', nodeId: currNode.id, color: 'var(--c-amber)' },
          ...(i > 0 ? [{ label: 'PREV', nodeId: nodes[i - 1].id, color: 'var(--c-mint)' }] : []),
          ...(i < nodes.length - 1 ? [{ label: 'NEXT', nodeId: nodes[i + 1].id, color: 'var(--c-violet)' }] : []),
        ],
        activeLine: 3,
        log: `Reversing link of node ${currNode.value}: curr.next = prev`,
      });
    }

    generated.push({
      nodes: [...reversed],
      activeNodeIds: [reversed[0].id],
      pointers: [
        { label: 'HEAD', nodeId: reversed[0].id, color: 'var(--c-mint)' },
        { label: 'TAIL', nodeId: reversed[reversed.length - 1].id, color: 'var(--c-violet)' },
      ],
      activeLine: 5,
      log: 'Reversal complete! New HEAD established.',
    });

    setNodes(reversed);
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
  };

  const curr = frames[frameIdx] || {
    nodes,
    activeNodeIds: [],
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
          setNodes([
            { id: 'n1', value: 12 },
            { id: 'n2', value: 34 },
            { id: 'n3', value: 56 },
            { id: 'n4', value: 78 },
          ]);
        }}
        onRandomize={() => {
          const rand = Array.from({ length: 5 }, (_, i) => ({
            id: `r-${i}-${Date.now()}`,
            value: Math.floor(Math.random() * 90) + 10,
          }));
          setNodes(rand);
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
            onClick={handleInsertHead}
            className="px-3 py-1 bg-mint text-canvas font-medium rounded hover:bg-mint/90 transition"
          >
            Insert Head
          </button>
          <button
            onClick={handleInsertTail}
            className="px-3 py-1 bg-violet text-canvas font-medium rounded hover:bg-violet/90 transition"
          >
            Insert Tail
          </button>
          <button
            onClick={handleDeleteHead}
            className="px-3 py-1 bg-rose-600 text-white font-medium rounded hover:bg-rose-500 transition"
          >
            Delete Head
          </button>
        </div>

        <div className="flex items-center gap-2 border-l border-line pl-3">
          <button
            onClick={handleReverse}
            className="px-3 py-1 bg-amber text-canvas font-medium rounded hover:bg-amber/90 transition"
          >
            Reverse List
          </button>
        </div>
      </div>

      {/* Visual Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8 space-y-3">
          <VisualizerCanvas
            metrics={[
              { label: 'List Length', value: `${curr.nodes.length} nodes`, color: 'var(--c-mint)' },
              { label: 'Head Value', value: curr.nodes[0] ? `${curr.nodes[0].value}` : 'null', color: 'var(--c-violet)' },
              { label: 'Tail Value', value: curr.nodes[curr.nodes.length - 1] ? `${curr.nodes[curr.nodes.length - 1].value}` : 'null', color: 'var(--c-amber)' },
            ]}
            legend={[
              { label: 'Node Payload', color: 'var(--c-steel)' },
              { label: 'Active Pointer', color: 'var(--c-amber)' },
              { label: 'Head / Rebuilt', color: 'var(--c-mint)' },
            ]}
          >
            <div data-testid="linkedlist-workbench" className="py-14 px-4 overflow-x-auto flex items-center justify-center">
              <div className="flex items-center gap-2 sm:gap-4 min-w-max">
                {curr.nodes.map((n, idx) => {
                  const isActive = curr.activeNodeIds.includes(n.id);
                  const ptrs = curr.pointers?.filter((p) => p.nodeId === n.id) || [];

                  return (
                    <React.Fragment key={n.id}>
                      <div className="flex flex-col items-center gap-1.5">
                        {/* Pointers */}
                        <div className="h-5 flex items-center gap-1">
                          {ptrs.map((p, pIdx) => (
                            <span
                              key={pIdx}
                              className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold text-canvas shadow"
                              style={{ backgroundColor: p.color }}
                            >
                              {p.label}
                            </span>
                          ))}
                        </div>

                        {/* Node Container (Data | Next) */}
                        <div
                          className={`flex rounded-xl border overflow-hidden font-mono transition-colors duration-150 ${
                            isActive
                              ? 'border-amber shadow-lg scale-105'
                              : 'border-line bg-surface'
                          }`}
                        >
                          {/* Data box */}
                          <div
                            className={`w-12 h-12 sm:w-14 sm:h-14 flex items-center justify-center font-bold text-base sm:text-lg border-r border-line ${
                              isActive ? 'bg-amber text-canvas' : 'text-ink'
                            }`}
                          >
                            {n.value}
                          </div>
                          {/* Next pointer box */}
                          <div className="w-6 sm:w-7 h-12 sm:h-14 bg-white/5 flex items-center justify-center text-muted">
                            <span className="text-[10px] font-mono">•</span>
                          </div>
                        </div>

                        <span className="font-mono text-[10px] text-muted">Node #{idx + 1}</span>
                      </div>

                      {/* Arrow */}
                      <div className="pt-5 flex items-center text-muted">
                        <ArrowRight className="w-5 h-5" />
                      </div>
                    </React.Fragment>
                  );
                })}

                {/* NULL terminator */}
                <div className="flex flex-col items-center gap-1.5 pt-5">
                  <div className="px-3 py-1.5 rounded-lg border border-dashed border-line text-muted font-mono text-xs">
                    NULL
                  </div>
                </div>
              </div>
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
            title="Linked List Operations"
            lines={[
              'node = new Node(value)',
              'node.next = head',
              'head = node  // Insert Head O(1)',
              'prev = null; curr = head',
              'while curr: next = curr.next; curr.next = prev; prev = curr; curr = next',
            ]}
            activeLine={curr.activeLine}
            timeComplexity="Insert O(1) · Reverse O(n)"
            spaceComplexity="O(1)"
            logs={frames.slice(0, frameIdx + 1).map((f) => f.log)}
          />
        </div>
      </div>
    </div>
  );
};
