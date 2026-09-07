import React, { useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, ChevronRight } from 'lucide-react';
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
    </div>
  );
};
