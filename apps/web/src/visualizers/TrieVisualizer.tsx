import React, { useState, useEffect } from 'react';
import { ControlBar } from '../components/ControlBar';
import { VisualizerCanvas } from '../components/VisualizerCanvas';
import { PseudoCodePanel } from '../components/PseudoCodePanel';

interface TNode {
  children: Record<string, TNode>;
  isEnd: boolean;
}

interface Frame {
  word: string;
  kind: 'insert' | 'search' | 'prefix' | 'ready';
  reveal: number;
  created: boolean[];
  found: boolean | null;
  matches: string[];
  activeLine: number;
  log: string;
}

interface PlacedNode {
  id: string;
  ch: string;
  x: number;
  y: number;
  isEnd: boolean;
  parentId: string | null;
  created: boolean;
}

const STARTER_WORDS = ['car', 'cart', 'cat', 'dog', 'dot'];

const buildTrie = (words: string[]): TNode => {
  const root: TNode = { children: {}, isEnd: false };
  for (const w of words) {
    let node = root;
    for (const ch of w) {
      if (!node.children[ch]) node.children[ch] = { children: {}, isEnd: false };
      node = node.children[ch];
    }
    node.isEnd = true;
  }
  return root;
};

const countNodes = (node: TNode): number =>
  1 + Object.values(node.children).reduce((acc, c) => acc + countNodes(c), 0);

const readyFrame = (words: string[]): Frame => ({
  word: '',
  kind: 'ready',
  reveal: 0,
  created: [],
  found: null,
  matches: [],
  activeLine: -1,
  log: `Trie ready with ${words.length} words: ${words.join(', ')}.`,
});

function planInsert(existing: TNode, word: string): boolean[] {
  const created: boolean[] = [];
  let node: TNode | undefined = existing;
  for (const ch of word) {
    const next: TNode | undefined = node?.children[ch];
    created.push(!next);
    node = next ?? { children: {}, isEnd: false };
  }
  return created;
}

function walk(existing: TNode, word: string): { depth: number; full: boolean; isEnd: boolean } {
  let node: TNode | undefined = existing;
  let depth = 0;
  for (const ch of word) {
    node = node?.children[ch];
    if (!node) return { depth, full: false, isEnd: false };
    depth += 1;
  }
  return { depth, full: true, isEnd: node.isEnd };
}

function layoutTrie(root: TNode, createdFor: Record<string, boolean>): { nodes: PlacedNode[]; width: number; height: number } {
  const X = 46;
  const Y = 64;
  const nodes: PlacedNode[] = [];
  const place = (node: TNode, path: string, depth: number, parentId: string | null, cursor: { x: number }): number => {
    const keys = Object.keys(node.children).sort();
    if (keys.length === 0) {
      const x = cursor.x * X;
      cursor.x += 1;
      nodes.push({ id: path, ch: path.slice(-1) || '∅', x, y: depth * Y, isEnd: node.isEnd, parentId, created: !!createdFor[path] });
      return x;
    }
    const centers = keys.map((k) => place(node.children[k], path + k, depth + 1, path, cursor));
    const x = (Math.min(...centers) + Math.max(...centers)) / 2;
    nodes.push({ id: path, ch: path.slice(-1) || '∅', x, y: depth * Y, isEnd: node.isEnd, parentId, created: !!createdFor[path] });
    return x;
  };
  const maxDepth = (node: TNode, d: number): number =>
    Math.max(d, ...Object.values(node.children).map((c) => maxDepth(c, d + 1)));
  place(root, '', 0, null, { x: 0 });
  const width = Math.max(1, nodes.length) * X;
  return { nodes, width, height: maxDepth(root, 0) * Y + 60 };
}

export const TrieVisualizer: React.FC = () => {
  const [words, setWords] = useState<string[]>(STARTER_WORDS);
  const [input, setInput] = useState('care');
  const [frames, setFrames] = useState<Frame[]>([readyFrame(STARTER_WORDS)]);
  const [frameIdx, setFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [result, setResult] = useState(`Preloaded dictionary: ${STARTER_WORDS.join(', ')}.`);

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

  const play = (generated: Frame[], nextWords: string[], message: string) => {
    setWords(nextWords);
    setFrames(generated);
    setFrameIdx(0);
    setIsPlaying(true);
    setResult(message);
  };

  const cleanInput = (): string => input.trim().toLowerCase();

  const handleInsert = () => {
    const word = cleanInput();
    if (!word) return;
    const trie = buildTrie(words);
    const created = planInsert(trie, word);
    const nextWords = words.includes(word) ? words : [...words, word].sort();
    const generated: Frame[] = Array.from({ length: word.length + 1 }, (_, reveal) => ({
      word,
      kind: 'insert' as const,
      reveal,
      created,
      found: null,
      matches: [],
      activeLine: reveal < word.length ? 2 : 4,
      log:
        reveal < word.length
          ? `insert("${word}"): step to '${word[reveal]}' — ${created[reveal] ? 'create node' : 'reuse node'}.`
          : words.includes(word)
            ? `insert("${word}"): word already present, confirmed terminal marker.`
            : `insert("${word}"): terminal marker set (isEnd = true).`,
    }));
    play(generated, nextWords, `Inserted "${word}" — terminal marker set.`);
  };

  const handleSearch = () => {
    const word = cleanInput();
    if (!word) return;
    const { depth, full, isEnd } = walk(buildTrie(words), word);
    const stop = full ? word.length : depth;
    const generated: Frame[] = Array.from({ length: stop + 1 }, (_, reveal) => ({
      word,
      kind: 'search' as const,
      reveal,
      created: Array.from({ length: word.length }, () => false),
      found: null,
      matches: [],
      activeLine: 6,
      log:
        reveal < stop
          ? `search("${word}"): step to '${word[reveal]}'.`
          : !full
            ? `search("${word}"): missing link at '${word[depth]}' — not in trie.`
            : isEnd
              ? `search("${word}"): full walk, isEnd = true — word found.`
              : `search("${word}"): full walk but isEnd = false — prefix only, not a word.`,
    }));
    generated.push({
      word,
      kind: 'search',
      reveal: stop,
      created: Array.from({ length: word.length }, () => false),
      found: full && isEnd,
      matches: [],
      activeLine: 7,
      log: full && isEnd ? `search("${word}"): FOUND.` : `search("${word}"): NOT FOUND.`,
    });
    const message = full && isEnd
      ? `Found "${word}" — full word present (isEnd).`
      : `Not found: "${word}" is ${full ? 'prefix-only' : 'absent'}.`;
    play(generated, words, message);
  };

  const handlePrefix = () => {
    const prefix = cleanInput();
    if (!prefix) return;
    const { full } = walk(buildTrie(words), prefix);
    const matches = full ? words.filter((w) => w.startsWith(prefix)) : [];
    const generated: Frame[] = Array.from({ length: prefix.length + 1 }, (_, reveal) => ({
      word: prefix,
      kind: 'prefix' as const,
      reveal,
      created: Array.from({ length: prefix.length }, () => false),
      found: full,
      matches,
      activeLine: reveal < prefix.length ? 8 : 9,
      log:
        reveal < prefix.length
          ? `startsWith("${prefix}"): step to '${prefix[reveal]}'.`
          : full
            ? `startsWith("${prefix}"): ${matches.length} match(es) — ${matches.join(', ') || 'none'}.`
            : `startsWith("${prefix}"): prefix missing — 0 matches.`,
    }));
    play(
      generated,
      words,
      full ? `Prefix "${prefix}": ${matches.length} match(es) — ${matches.join(', ') || 'none'}.` : `Prefix "${prefix}": 0 matches.`
    );
  };

  const handleReset = () => {
    setWords(STARTER_WORDS);
    setFrames([readyFrame(STARTER_WORDS)]);
    setFrameIdx(0);
    setIsPlaying(false);
    setResult(`Preloaded dictionary: ${STARTER_WORDS.join(', ')}.`);
  };

  const curr = frames[frameIdx] ?? readyFrame(words);
  const displayTrie = buildTrie(words);
  const createdFor: Record<string, boolean> = {};
  if (curr.kind === 'insert') {
    let prefix = '';
    curr.word.split('').forEach((ch, i) => {
      prefix += ch;
      if (curr.created[i]) createdFor[prefix] = true;
    });
  }
  const { nodes, width, height } = layoutTrie(displayTrie, createdFor);
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const activeIds = new Set<string>();
  if (curr.kind !== 'ready') {
    for (let i = 0; i <= curr.reveal; i++) activeIds.add(curr.word.slice(0, i));
  }
  const nodeCount = countNodes(displayTrie);

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
        onReset={handleReset}
        onRandomize={() => {
          const pool = ['ace', 'ape', 'apple', 'cab', 'carts', 'dove', 'down'];
          const pick = pool[Math.floor(Math.random() * pool.length)];
          setInput(pick);
        }}
        speed={speed}
        onSpeedChange={setSpeed}
      />

      <div className="flex flex-wrap items-center gap-3 p-3 bg-surface/50 border border-line rounded-xl text-xs">
        <div className="flex items-center gap-2">
          <label htmlFor="trie-input" className="font-mono text-muted">Word</label>
          <input
            id="trie-input"
            type="text"
            value={input}
            maxLength={8}
            onChange={(e) => setInput(e.target.value.replace(/[^a-z]/g, '').slice(0, 8))}
            className="w-28 px-2 py-1 bg-surface border border-line rounded text-ink text-center font-mono"
            placeholder="a-z, max 8"
          />
          <button
            onClick={handleInsert}
            className="px-3 py-1 bg-mint text-canvas font-medium rounded hover:bg-mint/90 transition"
          >
            Insert Word
          </button>
          <button
            onClick={handleSearch}
            className="px-3 py-1 bg-violet text-canvas font-medium rounded hover:bg-violet/90 transition"
          >
            Search Word
          </button>
          <button
            onClick={handlePrefix}
            className="px-3 py-1 bg-amber text-canvas font-medium rounded hover:bg-amber/90 transition"
          >
            StartsWith Prefix
          </button>
        </div>

        <div className="flex items-center gap-2 border-l border-line pl-3">
          {['car', 'ca', 'care', 'dot', 'done'].map((w) => (
            <button
              key={w}
              onClick={() => setInput(w)}
              className="px-2 py-1 bg-canvas text-muted border border-line font-mono rounded hover:text-ink hover:border-steel transition"
            >
              {w}
            </button>
          ))}
          <button
            onClick={handleReset}
            className="px-3 py-1 bg-canvas text-muted border border-line font-medium rounded hover:text-ink hover:border-steel transition"
          >
            Reset Trie
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8 space-y-3">
          <VisualizerCanvas
            metrics={[
              { label: 'Words', value: `${words.length}`, color: 'var(--c-mint)' },
              { label: 'Trie Nodes', value: `${nodeCount}`, color: 'var(--c-violet)' },
              { label: 'Matches', value: `${curr.matches.length}`, color: 'var(--c-amber)' },
            ]}
            legend={[
              { label: 'Active Path', color: 'var(--c-amber)' },
              { label: 'New Node', color: 'var(--c-violet)' },
              { label: 'Terminal (isEnd)', color: 'var(--c-mint)' },
            ]}
          >
            <div data-testid="trie-workbench" className="py-4 px-2 space-y-3">
              <svg viewBox={`-30 -30 ${Math.max(width + 60, 300)} ${height + 60}`} className="w-full select-none" style={{ minHeight: 220 }}>
                {nodes.filter((n) => n.parentId !== null).map((n) => {
                  const p = byId.get(n.parentId!)!;
                  const active = activeIds.has(n.id) && activeIds.has(n.parentId!);
                  return (
                    <line
                      key={`e-${n.id}`}
                      x1={p.x}
                      y1={p.y}
                      x2={n.x}
                      y2={n.y - 18}
                      stroke={active ? 'var(--c-amber)' : 'var(--c-steel)'}
                      strokeWidth={active ? 3 : 2}
                    />
                  );
                })}
                {nodes.map((n) => {
                  const active = activeIds.has(n.id);
                  const fill = active ? 'var(--c-amber)' : n.isEnd ? 'var(--c-mint)' : 'var(--c-surface)';
                  return (
                    <g key={n.id}>
                      {n.isEnd && (
                        <circle cx={n.x} cy={n.y} r={22} fill="none" stroke="var(--c-mint)" strokeWidth={1.5} strokeDasharray={n.created ? '3 2' : undefined} />
                      )}
                      <circle
                        cx={n.x}
                        cy={n.y}
                        r={17}
                        fill={fill}
                        stroke={n.created ? 'var(--c-violet)' : active ? 'var(--c-amber)' : 'var(--c-steel)'}
                        strokeWidth={n.created || active ? 3 : 2}
                      />
                      <text
                        x={n.x}
                        y={n.y + 5}
                        textAnchor="middle"
                        fontSize={13}
                        fontWeight={700}
                        fill={active || n.isEnd ? 'var(--c-canvas)' : 'var(--c-ink)'}
                      >
                        {n.ch}
                      </text>
                      {n.isEnd && (
                        <text x={n.x} y={n.y + 34} textAnchor="middle" fontSize={9} fill="var(--c-mint)">
                          isEnd
                        </text>
                      )}
                    </g>
                  );
                })}
              </svg>

              <div className="flex flex-wrap gap-2 items-center font-mono text-[11px]">
                <span className="text-muted">words:</span>
                {words.map((w) => (
                  <span key={w} className="px-2 py-0.5 rounded border border-mint text-ink bg-mint/10">
                    {w}
                  </span>
                ))}
              </div>
              {curr.matches.length > 0 && (
                <div data-testid="trie-matches" className="flex flex-wrap gap-2 items-center font-mono text-[11px]">
                  <span className="text-muted">autocomplete:</span>
                  {curr.matches.map((w) => (
                    <span key={w} className="px-2 py-0.5 rounded border border-amber text-ink bg-amber/10">
                      {w}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </VisualizerCanvas>

          <div className="p-3 bg-surface/40 border border-line rounded-xl font-mono text-xs text-muted flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-mint shrink-0" />
            <span>{curr.log}</span>
          </div>
          <div className="p-3 bg-surface/40 border border-line rounded-xl font-mono text-xs text-ink">
            {result}
          </div>
        </div>

        <div className="lg:col-span-4">
          <PseudoCodePanel
            title="Trie (Prefix Tree)"
            lines={[
              'function insert(word):',
              '  node = root',
              '  for ch in word:',
              '    node = child(ch) or create',
              '  node.isEnd = true',
              'function search(word):',
              '  node = walk(word)',
              '  return node and node.isEnd',
              'function startsWith(prefix):',
              '  return collect(walk(prefix))',
            ]}
            activeLine={curr.activeLine}
            timeComplexity="O(L) per word"
            spaceComplexity="O(Σ·N·L)"
            logs={frames.slice(0, frameIdx + 1).map((f) => f.log)}
          />
        </div>
      </div>
    </div>
  );
};
