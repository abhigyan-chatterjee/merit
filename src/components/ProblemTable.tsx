import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Search, ArrowUpDown, X, ArrowUpRight } from 'lucide-react';
import { Problem } from '../data/problems';
import { useProgress, ProblemStatus } from '../store/ProgressContext';
import { EmptyState } from './EmptyState';

interface ProblemTableProps {
  problems: Problem[];
  topicTitle?: string;
}

const STATUS_STYLE: Record<ProblemStatus, string> = {
  Done: 'text-mint border-mint/40 bg-mint/10',
  Doing: 'text-amber border-amber/40 bg-amber/10',
  Todo: 'text-muted border-line bg-canvas'
};

const DIFF_STYLE = {
  Easy: 'text-mint',
  Medium: 'text-amber',
  Hard: 'text-rose'
} as const;

export const ProblemTable: React.FC<ProblemTableProps> = ({ problems }) => {
  const { state, setProblemStatus } = useProgress();
  const [searchQuery, setSearchQuery] = useState('');
  const [diffFilter, setDiffFilter] = useState<'All' | 'Easy' | 'Medium' | 'Hard'>('All');
  const [statusFilter, setStatusFilter] = useState<'All' | ProblemStatus>('All');
  const [sortBy, setSortBy] = useState<'default' | 'difficulty' | 'title'>('default');

  const filteredProblems = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return problems
      .filter((p) => {
        if (q && !p.title.toLowerCase().includes(q) && !p.pattern.toLowerCase().includes(q)) {
          return false;
        }
        if (diffFilter !== 'All' && p.difficulty !== diffFilter) return false;
        const st = state.progress[p.slug] || 'Todo';
        if (statusFilter !== 'All' && st !== statusFilter) return false;
        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'title') return a.title.localeCompare(b.title);
        if (sortBy === 'difficulty') {
          const rank = { Easy: 1, Medium: 2, Hard: 3 };
          return rank[a.difficulty] - rank[b.difficulty];
        }
        return 0;
      });
  }, [problems, searchQuery, diffFilter, statusFilter, sortBy, state.progress]);

  const clearAll = () => {
    setSearchQuery('');
    setDiffFilter('All');
    setStatusFilter('All');
    setSortBy('default');
  };

  const selectCls =
    'px-2.5 py-1.5 rounded-lg bg-surface border border-line text-[11px] font-mono text-ink hover:border-steel cursor-pointer focus:outline-none';

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="w-3.5 h-3.5 text-muted absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Filter by title or pattern…"
            aria-label="Filter problems"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-8 py-1.5 rounded-lg bg-surface border border-line text-xs text-ink placeholder-muted focus:outline-none focus:border-mint transition-colors"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              aria-label="Clear search"
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted hover:text-ink cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <select
          value={diffFilter}
          aria-label="Filter by difficulty"
          onChange={(e) => setDiffFilter(e.target.value as any)}
          className={selectCls}
        >
          <option value="All">All difficulties</option>
          <option value="Easy">Easy</option>
          <option value="Medium">Medium</option>
          <option value="Hard">Hard</option>
        </select>

        <select
          value={statusFilter}
          aria-label="Filter by status"
          onChange={(e) => setStatusFilter(e.target.value as any)}
          className={selectCls}
        >
          <option value="All">All statuses</option>
          <option value="Todo">Todo</option>
          <option value="Doing">Doing</option>
          <option value="Done">Done</option>
        </select>

        <button
          onClick={() =>
            setSortBy((prev) =>
              prev === 'default' ? 'difficulty' : prev === 'difficulty' ? 'title' : 'default'
            )
          }
          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-surface border border-line text-[11px] font-mono text-muted hover:text-ink hover:border-steel cursor-pointer"
        >
          <ArrowUpDown className="w-3.5 h-3.5" />
          {sortBy === 'default' ? 'Sort' : sortBy}
        </button>

        <span className="text-[10px] font-mono text-muted tnum ml-auto">
          {filteredProblems.length}/{problems.length} shown
        </span>
      </div>

      {/* Table */}
      {filteredProblems.length === 0 ? (
        <EmptyState
          title="No problems match those filters"
          description="Try loosening the difficulty or status filter, or clear the search query."
          actionLabel="Clear all filters"
          onAction={clearAll}
        />
      ) : (
        <>
          {/* Desktop table (hidden on mobile) */}
          <div className="hidden sm:block rounded-xl border border-line bg-surface overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[680px]">
              <thead>
                <tr className="border-b border-line text-[9px] font-mono uppercase tracking-[0.16em] text-muted">
                  <th scope="col" className="py-2.5 px-4 font-normal w-32">Status</th>
                  <th scope="col" className="py-2.5 px-4 font-normal">Problem</th>
                  <th scope="col" className="py-2.5 px-4 font-normal">Pattern</th>
                  <th scope="col" className="py-2.5 px-4 font-normal w-24">Level</th>
                  <th scope="col" className="py-2.5 px-4 font-normal w-16 text-right">Open</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {filteredProblems.map((p, i) => {
                  const st = (state.progress[p.slug] || 'Todo') as ProblemStatus;
                  return (
                    <tr key={p.id} className="group hover:bg-canvas transition-colors">
                      <td className="py-2.5 px-4">
                        <select
                          value={st}
                          aria-label={`Status for ${p.title}`}
                          onChange={(e) => setProblemStatus(p.slug, e.target.value as ProblemStatus)}
                          className={`px-2 py-0.5 rounded border text-[10px] font-mono font-semibold cursor-pointer focus:outline-none ${STATUS_STYLE[st]}`}
                        >
                          <option value="Todo">Todo</option>
                          <option value="Doing">Doing</option>
                          <option value="Done">Done</option>
                        </select>
                      </td>

                      <td className="py-2.5 px-4">
                        <Link
                          to={`/problems/${p.topic}/${p.slug}`}
                          className="flex items-baseline gap-2.5 text-xs font-medium text-ink hover:text-mint transition-colors"
                        >
                          <span className="font-mono text-[10px] text-muted tnum w-4">
                            {String(i + 1).padStart(2, '0')}
                          </span>
                          {p.title}
                        </Link>
                      </td>

                      <td className="py-2.5 px-4">
                        <span className="text-[10px] font-mono text-violet">{p.pattern}</span>
                      </td>

                      <td className="py-2.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1.5 text-[11px] font-mono font-semibold ${DIFF_STYLE[p.difficulty]}`}
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-current" />
                          {p.difficulty}
                        </span>
                      </td>

                      <td className="py-2.5 px-4 text-right">
                        <Link
                          to={`/problems/${p.topic}/${p.slug}`}
                          aria-label={`Open ${p.title}`}
                          className="inline-grid place-items-center w-7 h-7 rounded-md border border-line text-muted group-hover:text-mint group-hover:border-mint/40 transition"
                        >
                          <ArrowUpRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Mobile card list (hidden on sm+) */}
          <div className="sm:hidden space-y-2">
            {filteredProblems.map((p, i) => {
              const st = (state.progress[p.slug] || 'Todo') as ProblemStatus;
              return (
                <div
                  key={p.id}
                  className="rounded-xl border border-line bg-surface p-3.5 space-y-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <Link
                      to={`/problems/${p.topic}/${p.slug}`}
                      className="flex-1 text-sm font-semibold text-ink hover:text-mint transition-colors leading-snug min-w-0"
                    >
                      <span className="font-mono text-[10px] text-muted tnum mr-1.5">
                        {String(i + 1).padStart(2, '0')}
                      </span>
                      {p.title}
                    </Link>
                    <span
                      className={`shrink-0 inline-flex items-center gap-1 text-[10px] font-mono font-semibold ${DIFF_STYLE[p.difficulty]}`}
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-current" />
                      {p.difficulty}
                    </span>
                  </div>

                  <div className="text-[10px] font-mono text-violet truncate">{p.pattern}</div>

                  <div className="flex items-center justify-between gap-2 pt-2 border-t border-line">
                    <select
                      value={st}
                      aria-label={`Status for ${p.title}`}
                      onChange={(e) => setProblemStatus(p.slug, e.target.value as ProblemStatus)}
                      className={`px-2 py-1 rounded border text-[10px] font-mono font-semibold cursor-pointer focus:outline-none ${STATUS_STYLE[st]}`}
                    >
                      <option value="Todo">Todo</option>
                      <option value="Doing">Doing</option>
                      <option value="Done">Done</option>
                    </select>

                    <Link
                      to={`/problems/${p.topic}/${p.slug}`}
                      aria-label={`Open ${p.title}`}
                      className="inline-flex items-center gap-1 px-3 py-1 rounded-md border border-line text-muted hover:text-mint hover:border-mint/40 text-[11px] font-mono transition"
                    >
                      Open <ArrowUpRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};
