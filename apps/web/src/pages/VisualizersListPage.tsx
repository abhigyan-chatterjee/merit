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

  const categories = ['All', ...Array.from(new Set(VISUALIZERS.map((v) => v.category)))];
  const filtered = VISUALIZERS.filter((v) =>
    selectedCategory === 'All' ? true : v.category === selectedCategory
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-7">
      {/* Header */}
      <div className="space-y-1.5">
        <h1 className="text-2xl font-bold tracking-tight text-ink">Visualizers</h1>
        <p className="text-xs text-muted">Step through each structure.</p>
      </div>

      {/* Filter rail */}
      <div className="flex flex-wrap items-center gap-2 border-y border-line py-2.5">
        {categories.map((cat) => {
          const active = selectedCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              aria-pressed={active}
              className={`px-2.5 py-1 rounded-md text-[11px] font-mono transition cursor-pointer border ${
                active
                  ? 'bg-mint text-canvas border-mint font-semibold'
                  : 'bg-surface text-muted border-line hover:text-ink hover:border-steel'
              }`}
            >
              {cat}
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
                    className={`relative p-1 rounded transition cursor-pointer before:absolute before:-inset-1.5 before:content-[''] ${
                      isBookmarked ? 'text-amber' : 'text-muted hover:text-muted'
                    }`}
                  >
                    <Bookmark className={`w-3.5 h-3.5 ${isBookmarked ? 'fill-amber' : ''}`} />
                  </button>
                </div>

                {/* body */}
                <div className="flex-1 p-4 space-y-2">
                  <h2 className="text-sm font-bold text-ink group-hover:text-mint transition-colors">
                    {item.title}
                  </h2>
                  <p className="text-xs text-muted leading-relaxed line-clamp-2">{item.description}</p>
                  <p className="text-[11px] font-mono text-muted">
                    avg {item.timeComplexity.avg} · space {item.spaceComplexity}
                  </p>
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
