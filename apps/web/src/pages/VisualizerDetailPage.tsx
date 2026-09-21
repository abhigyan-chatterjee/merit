import React, { useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, ChevronRight, ExternalLink } from 'lucide-react';
import { VISUALIZERS } from '../data/curriculum';
import { SortingVisualizer } from '../visualizers/SortingVisualizer';
import { GraphVisualizer } from '../visualizers/GraphVisualizer';
import { TreeVisualizer } from '../visualizers/TreeVisualizer';
import { ArrayVisualizer } from '../visualizers/ArrayVisualizer';
import { LinkedListVisualizer } from '../visualizers/LinkedListVisualizer';
import { StackVisualizer } from '../visualizers/StackVisualizer';
import { QueueVisualizer } from '../visualizers/QueueVisualizer';
import { HashMapVisualizer } from '../visualizers/HashMapVisualizer';
import { SearchingVisualizer } from '../visualizers/SearchingVisualizer';
import { RecursionTreeVisualizer } from '../visualizers/RecursionTreeVisualizer';
import { LinearVisualizer } from '../visualizers/LinearVisualizer';
import { useProgress } from '../store/ProgressContext';
import { NotFound } from '../components/NotFound';
import { LessonNav } from '../components/LessonNav';

const VISUALIZER_READING: Record<string, { label: string; url: string }[]> = {
  sorting: [
    { label: 'Wikipedia: Sorting algorithm', url: 'https://en.wikipedia.org/wiki/Sorting_algorithm' },
    { label: 'VisuAlgo: Sorting', url: 'https://visualgo.net/en/sorting' },
  ],
  array: [
    { label: 'Wikipedia: Array data structure', url: 'https://en.wikipedia.org/wiki/Array_data_structure' },
    { label: 'MDN: JavaScript Array', url: 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array' },
  ],
  'linked-list': [
    { label: 'Wikipedia: Linked list', url: 'https://en.wikipedia.org/wiki/Linked_list' },
    { label: 'VisuAlgo: List', url: 'https://visualgo.net/en/list' },
  ],
  stack: [
    { label: 'Wikipedia: Stack (abstract data type)', url: 'https://en.wikipedia.org/wiki/Stack_(abstract_data_type)' },
    { label: 'MDN: JavaScript Array', url: 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array' },
  ],
  queue: [
    { label: 'Wikipedia: Queue (abstract data type)', url: 'https://en.wikipedia.org/wiki/Queue_(abstract_data_type)' },
    { label: 'VisuAlgo: Queue', url: 'https://visualgo.net/en/list' },
  ],
  'binary-tree': [
    { label: 'Wikipedia: Tree traversal', url: 'https://en.wikipedia.org/wiki/Tree_traversal' },
    { label: 'VisuAlgo: Binary tree', url: 'https://visualgo.net/en/bst' },
  ],
  bst: [
    { label: 'Wikipedia: Binary search tree', url: 'https://en.wikipedia.org/wiki/Binary_search_tree' },
    { label: 'VisuAlgo: Binary search tree', url: 'https://visualgo.net/en/bst' },
  ],
  heap: [
    { label: 'Wikipedia: Heap (data structure)', url: 'https://en.wikipedia.org/wiki/Heap_(data_structure)' },
    { label: 'VisuAlgo: Heap', url: 'https://visualgo.net/en/heap' },
  ],
  hashmap: [
    { label: 'Wikipedia: Hash table', url: 'https://en.wikipedia.org/wiki/Hash_table' },
    { label: 'MDN: Map', url: 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Map' },
  ],
  graph: [
    { label: 'Wikipedia: Graph traversal', url: 'https://en.wikipedia.org/wiki/Graph_traversal' },
    { label: 'VisuAlgo: Graph traversal', url: 'https://visualgo.net/en/graphds' },
  ],
  searching: [
    { label: 'Wikipedia: Binary search algorithm', url: 'https://en.wikipedia.org/wiki/Binary_search_algorithm' },
    { label: 'CP-Algorithms: Binary search', url: 'https://cp-algorithms.com/num_methods/binary_search.html' },
  ],
  'recursion-tree': [
    { label: 'Wikipedia: Recursion (computer science)', url: 'https://en.wikipedia.org/wiki/Recursion_(computer_science)' },
    { label: 'CP-Algorithms: Dynamic programming', url: 'https://cp-algorithms.com/dynamic_programming/intro-to-dp.html' },
  ],
};

export const VisualizerDetailPage: React.FC = () => {
  const { id = 'sorting' } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { setLastVisited, recordVisualizerVisit } = useProgress();

  const currentItem = VISUALIZERS.find((v) => v.id === id);

  useEffect(() => {
    if (currentItem) {
      recordVisualizerVisit(currentItem.id);
      setLastVisited({
        type: 'visualizer',
        title: currentItem.title,
        path: `/visualizers/${currentItem.id}`,
        subtitle: `${currentItem.category} workbench · avg ${currentItem.timeComplexity.avg}`
      });
    }
  }, [currentItem?.id]);

  if (!currentItem) {
    return (
      <NotFound
        title="Visualizer Not Found"
        message={`We couldn't find a visualizer for "${id}". Check out our curriculum for all available visualizers.`}
        backTo="/visualizers"
        backLabel="All Visualizers"
      />
    );
  }

  const renderWorkbench = () => {
    switch (id) {
      case 'sorting':
        return <SortingVisualizer />;
      case 'array':
        return <ArrayVisualizer />;
      case 'linked-list':
        return <LinkedListVisualizer />;
      case 'stack':
        return <StackVisualizer />;
      case 'queue':
        return <QueueVisualizer />;
      case 'binary-tree':
        return <TreeVisualizer variant="binary-tree" />;
      case 'bst':
        return <TreeVisualizer variant="bst" />;
      case 'heap':
        return <TreeVisualizer variant="heap" />;
      case 'hashmap':
        return <HashMapVisualizer />;
      case 'graph':
        return <GraphVisualizer />;
      case 'searching':
        return <SearchingVisualizer />;
      case 'recursion-tree':
        return <RecursionTreeVisualizer />;
      default:
        return <LinearVisualizer id={id} />;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-5">
      {/* Guided Path Lesson Navigation */}
      <LessonNav currentType="visualizer" currentId={currentItem.id} />

      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-[10px] font-mono text-muted">
        <Link to="/visualizers" className="hover:text-mint transition-colors">
          visualizers
        </Link>
        <ChevronRight className="w-3 h-3" />
        <span className="text-ink">{currentItem.id}</span>
      </nav>

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4 pb-5 border-b border-line">
        <div className="flex items-start gap-3 min-w-0">
          <Link
            to="/visualizers"
            aria-label="Back to all visualizers"
            className="mt-0.5 grid place-items-center w-8 h-8 rounded-lg border border-line bg-surface text-muted hover:text-ink hover:border-steel transition shrink-0"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>

          <div className="min-w-0 space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-ink">{currentItem.title}</h1>
              <span className="px-1.5 py-0.5 rounded border border-line bg-surface text-[9px] font-mono uppercase tracking-[0.14em] text-mint">
                {currentItem.category}
              </span>
            </div>
            <p className="text-xs text-muted max-w-2xl">{currentItem.description}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <label
            htmlFor="viz-switch"
            className="text-[9px] font-mono uppercase tracking-[0.16em] text-muted"
          >
            Jump to
          </label>
          <select
            id="viz-switch"
            value={id}
            onChange={(e) => navigate(`/visualizers/${e.target.value}`)}
            className="px-2.5 py-1.5 rounded-lg bg-surface border border-line text-[11px] font-mono text-ink hover:border-steel cursor-pointer focus:outline-none"
          >
            {VISUALIZERS.map((v) => (
              <option key={v.id} value={v.id}>
                {v.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {renderWorkbench()}

      <section className="p-4 rounded-xl border border-line bg-surface space-y-2">
        <h2 className="text-xs font-mono font-semibold text-ink flex items-center gap-1.5">
          <ExternalLink className="w-4 h-4 text-mint" />
          Further Reading &amp; References
        </h2>
        <ul className="space-y-1.5">
          {(VISUALIZER_READING[currentItem.id] || []).map((reference) => (
            <li key={reference.url}>
              <a
                href={reference.url}
                target="_blank"
                rel="noreferrer"
                className="text-xs font-mono text-mint hover:underline break-all"
              >
                {reference.label}
              </a>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
};
