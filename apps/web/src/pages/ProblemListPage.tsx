import React, { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  Bookmark,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  Search,
  Sparkles,
} from 'lucide-react';
import { PROBLEMS, Problem } from '../data/problems';
import { TOPICS } from '../data/curriculum';
import { useProgress } from '../store/ProgressContext';

const TAG_LIMIT = 8;

const difficultyTone: Record<Problem['difficulty'], string> = {
  Easy: 'text-mint',
  Medium: 'text-amber',
  Hard: 'text-rose',
};

export const ProblemListPage: React.FC = () => {
  const { topic } = useParams<{ topic: string }>();
  const { state, toggleBookmark } = useProgress();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [showAllTags, setShowAllTags] = useState(false);
  const [expandedTopics, setExpandedTopics] = useState<string[]>(
    topic && TOPICS.some((item) => item.slug === topic) ? [topic] : []
  );

  const tagCounts = useMemo(() => {
    const counts = new Map<string, number>();
    PROBLEMS.forEach((problem) => {
      counts.set(problem.pattern, (counts.get(problem.pattern) ?? 0) + 1);
      counts.set(problem.topic, (counts.get(problem.topic) ?? 0) + 1);
    });
    return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }, []);

  const visibleTags = showAllTags ? tagCounts : tagCounts.slice(0, TAG_LIMIT);
  const filteredProblems = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    return PROBLEMS.filter((problem) => {
      const matchesSearch =
        !query ||
        problem.title.toLowerCase().includes(query) ||
        problem.pattern.toLowerCase().includes(query);
      const matchesTags =
        selectedTags.length === 0 ||
        selectedTags.some((tag) => tag === problem.topic || tag === problem.pattern);
      return matchesSearch && matchesTags;
    });
  }, [searchQuery, selectedTags]);

  const solvedCount = PROBLEMS.filter((problem) => state.progress[problem.slug] === 'Done').length;

  const toggleTag = (tag: string) => {
    setSelectedTags((current) =>
      current.includes(tag) ? current.filter((item) => item !== tag) : [...current, tag]
    );
  };

  const toggleTopic = (slug: string) => {
    setExpandedTopics((current) =>
      current.includes(slug) ? current.filter((item) => item !== slug) : [...current, slug]
    );
  };

  const topicTitle = (slug: string) => TOPICS.find((item) => item.slug === slug)?.title ?? slug;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <section className="rounded-2xl border border-line bg-surface p-6 md:p-8">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="max-w-2xl space-y-2">
            <span className="inline-flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-[0.2em] text-mint">
              <Sparkles className="w-3.5 h-3.5" />
              Problem set
            </span>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-ink">
              Master the patterns
            </h1>
            <p className="text-sm text-muted leading-relaxed">
              A focused, pattern-first path through the problems that matter most for technical
              interviews.
            </p>
          </div>

          <div className="flex items-center gap-6 font-mono">
            <div>
              <div className="text-lg font-bold text-mint tnum">
                {solvedCount}/{PROBLEMS.length}
              </div>
              <div className="text-[10px] uppercase tracking-[0.16em] text-muted">Solved</div>
            </div>
            <div>
              <div className="flex items-center gap-1.5 text-lg font-bold text-amber tnum">
                <Bookmark className="w-4 h-4 fill-amber" />
                {state.bookmarks.length}
              </div>
              <div className="text-[10px] uppercase tracking-[0.16em] text-muted">Starred</div>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-3" aria-label="Problem filters">
        <div className="relative">
          <Search className="w-4 h-4 text-muted absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="search"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search problems or patterns..."
            aria-label="Search problems"
            className="w-full rounded-xl border border-line bg-surface py-3 pl-10 pr-4 text-sm text-ink placeholder-muted focus:outline-none focus:border-mint"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-1 text-[10px] font-mono uppercase tracking-[0.16em] text-muted">
            Tags
          </span>
          {visibleTags.map(([tag, count]) => {
            const active = selectedTags.includes(tag);
            const label = TOPICS.find((item) => item.slug === tag)?.title ?? tag;
            return (
              <button
                key={tag}
                type="button"
                onClick={() => toggleTag(tag)}
                aria-pressed={active}
                className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-[11px] font-mono transition ${
                  active
                    ? 'border-mint bg-mint text-canvas font-semibold'
                    : 'border-line bg-surface text-muted hover:border-steel hover:text-ink'
                }`}
              >
                {label}
                <span className={active ? 'text-canvas/70' : 'text-muted'}>{count}</span>
              </button>
            );
          })}
          {tagCounts.length > TAG_LIMIT && (
            <button
              type="button"
              onClick={() => setShowAllTags((current) => !current)}
              className="inline-flex items-center gap-1 px-2 py-1.5 text-[11px] font-mono text-mint hover:text-ink"
            >
              {showAllTags ? 'Show fewer' : 'Expand'}
              {showAllTags ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          )}
        </div>
      </section>

      <section className="space-y-3" aria-label="Problem topics">
        {TOPICS.map((topicItem) => {
          const topicProblems = filteredProblems.filter((problem) => problem.topic === topicItem.slug);
          const allTopicProblems = PROBLEMS.filter((problem) => problem.topic === topicItem.slug);
          const doneCount = allTopicProblems.filter(
            (problem) => state.progress[problem.slug] === 'Done'
          ).length;
          const isExpanded = expandedTopics.includes(topicItem.slug);
          const progress = allTopicProblems.length
            ? (doneCount / allTopicProblems.length) * 100
            : 0;

          return (
            <article key={topicItem.slug} className="rounded-xl border border-line bg-surface overflow-hidden">
              <button
                type="button"
                onClick={() => toggleTopic(topicItem.slug)}
                aria-expanded={isExpanded}
                className="w-full flex items-center gap-3 p-4 text-left hover:bg-canvas/40 transition"
              >
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-mint shrink-0" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-muted shrink-0" />
                )}
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-semibold text-ink">{topicItem.title}</span>
                  <span className="block mt-0.5 text-[11px] text-muted">{topicItem.description}</span>
                </span>
                <span className="w-24 shrink-0 space-y-1.5">
                  <span className="block text-right text-[11px] font-mono text-muted tnum">
                    {doneCount}/{allTopicProblems.length}
                  </span>
                  <span className="block h-1.5 rounded-full bg-canvas overflow-hidden">
                    <span
                      className="block h-full rounded-full bg-mint transition-all"
                      style={{ width: `${progress}%` }}
                    />
                  </span>
                </span>
              </button>

              {isExpanded && (
                <div className="border-t border-line divide-y divide-line">
                  {topicProblems.length === 0 ? (
                    <p className="p-4 text-xs text-muted">
                      No problems match the current search and tag filters.
                    </p>
                  ) : (
                    topicProblems.map((problem) => {
                      const isDone = state.progress[problem.slug] === 'Done';
                      const isBookmarked = state.bookmarks.includes(problem.slug);
                      return (
                        <div
                          key={problem.id}
                          className="flex items-center gap-3 px-4 py-3 hover:bg-canvas/40 transition"
                        >
                          <span
                            aria-label={isDone ? 'Solved' : 'Not solved'}
                            className={`w-2 h-2 rounded-full shrink-0 ${isDone ? 'bg-mint' : 'bg-muted/50'}`}
                          />
                          <Link
                            to={`/problems/${problem.topic}/${problem.slug}`}
                            className="min-w-0 flex-1 text-sm text-ink hover:text-mint transition"
                          >
                            {problem.title}
                          </Link>
                          <span className={`text-[11px] font-mono font-semibold ${difficultyTone[problem.difficulty]}`}>
                            {problem.difficulty}
                          </span>
                          <button
                            type="button"
                            onClick={() => toggleBookmark(problem.slug)}
                            aria-label={`${isBookmarked ? 'Remove' : 'Add'} bookmark for ${problem.title}`}
                            aria-pressed={isBookmarked}
                            className={`p-1 rounded transition ${
                              isBookmarked ? 'text-amber' : 'text-muted hover:text-amber'
                            }`}
                          >
                            <Bookmark className={`w-4 h-4 ${isBookmarked ? 'fill-amber' : ''}`} />
                          </button>
                        </div>
                      );
                    })
                  )}
                </div>
              )}
            </article>
          );
        })}
      </section>

      <p className="text-center text-[11px] font-mono text-muted">
        Showing {filteredProblems.length} of {PROBLEMS.length} problems
        {selectedTags.length > 0 && ` across ${selectedTags.map(topicTitle).join(', ')}`}
      </p>
    </div>
  );
};
