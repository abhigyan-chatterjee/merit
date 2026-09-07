import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Bookmark, ArrowUpRight } from 'lucide-react';
import { VISUALIZERS } from '../data/curriculum';
import { Reveal } from '../components/ui/Reveal';
import { useProgress } from '../store/ProgressContext';

const CATEGORY_TONE: Record<string, string> = {
  Algorithms: 'text-mint',
  Linear: 'text-violet',
  Trees: 'text-amber',
  Graphs: 'text-rose',
  Hashing: 'text-ink'
};

export const VisualizersListPage: React.FC = () => {
  const { state, toggleBookmark } = useProgress();
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const categories = ['All', 'Algorithms', 'Linear', 'Trees', 'Graphs', 'Hashing'];
  const filtered = VISUALIZERS.filter((v) =>
    selectedCategory === 'All' ? true : v.category === selectedCategory
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-7">
      {/* Header */}
      <div className="space-y-1.5">
        <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-mint">
          Workbenches
        </span>
        <h1 className="text-2xl font-bold tracking-tight text-ink">
          Twelve interactive structures
        </h1>
        <p className="text-xs text-muted max-w-2xl">
          A step-debuggable canvas, synchronised pseudocode and a live operation log for every
          structure.
        </p>
      </div>

      {/* Filter rail */}
      <div className="flex flex-wrap items-center gap-2 border-y border-line py-2.5">
        <span className="text-[10px] font-mono uppercase tracking-[0.16em] text-muted mr-1">
          Filter
        </span>
        {categories.map((cat) => {
          const active = selectedCategory === cat;
          const count =
            cat === 'All'
              ? VISUALIZERS.length
              : VISUALIZERS.filter((v) => v.category === cat).length;
          return (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              aria-pressed={active}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-mono transition cursor-pointer border ${
                active
                  ? 'bg-mint text-canvas border-mint font-semibold'
                  : 'bg-surface text-muted border-line hover:text-ink hover:border-steel'
              }`}
            >
              {cat}
              <span className={active ? 'text-canvas/70' : 'text-muted'}>{count}</span>
            </button>
          );
        })}
      </div>

      {/* Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filtered.map((item, idx) => {
          const isBookmarked = state.bookmarks.includes(item.id);
          const tone = CATEGORY_TONE[item.category] ?? 'text-mint';

          return (
            <Reveal key={item.id} delay={Math.min(idx, 8) * 0.03}>
              <article className="bracketed group relative h-full flex flex-col rounded-xl border border-line bg-surface hover:border-steel transition-colors duration-200">
                {/* head */}
                <div className="flex items-center justify-between px-4 h-9 border-b border-line">
                  <span
                    className={`text-[9px] font-mono uppercase tracking-[0.16em] ${tone}`}
                  >
                    {item.category}
                  </span>
                  <button
                    onClick={() => toggleBookmark(item.id)}
                    aria-label={`${isBookmarked ? 'Remove' : 'Add'} bookmark for ${item.title}`}
                    aria-pressed={isBookmarked}
                    className={`p-1 rounded transition cursor-pointer ${
                      isBookmarked ? 'text-amber' : 'text-muted hover:text-muted'
                    }`}
                  >
                    <Bookmark className={`w-3.5 h-3.5 ${isBookmarked ? 'fill-amber' : ''}`} />
                  </button>
                </div>

                {/* body */}
                <div className="flex-1 p-4 space-y-3">
                  <h2 className="text-sm font-bold text-ink group-hover:text-mint transition-colors">
                    {item.title}
                  </h2>
                  <p className="text-xs text-muted leading-relaxed">{item.description}</p>

                  <div className="flex flex-wrap gap-1">
                    {item.keyOperations.map((op, i) => (
                      <span
                        key={i}
                        className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-canvas text-muted border border-line"
                      >
                        {op}
                      </span>
                    ))}
                  </div>
                </div>

                {/* complexity readout */}
                <div className="grid grid-cols-3 divide-x divide-line border-t border-line">
                  {[
                    { k: 'best', v: item.timeComplexity.best },
                    { k: 'avg', v: item.timeComplexity.avg },
                    { k: 'space', v: item.spaceComplexity }
                  ].map((c) => (
                    <div key={c.k} className="px-2 py-2 text-center">
                      <div className="text-[9px] font-mono uppercase tracking-[0.14em] text-muted">
                        {c.k}
                      </div>
                      <div className="text-[11px] font-mono font-bold text-ink tnum truncate">
                        {c.v}
                      </div>
                    </div>
                  ))}
                </div>

                {/* action */}
                <Link
                  to={`/visualizers/${item.id}`}
                  className="flex items-center justify-between px-4 h-11 border-t border-line text-xs font-semibold text-ink hover:bg-mint hover:text-canvas transition-colors duration-200 rounded-b-xl"
                >
                  Open workbench
                  <ArrowUpRight className="w-4 h-4" />
                </Link>
              </article>
            </Reveal>
          );
        })}
      </div>
    </div>
  );
};
