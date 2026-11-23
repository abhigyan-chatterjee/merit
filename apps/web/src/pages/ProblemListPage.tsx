import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import {
  Bookmark,
  Check,
  ChevronDown,
  ChevronRight,
  Search,
} from 'lucide-react';
import { PROBLEM_MANIFEST, ProblemManifestItem } from '../data/problemManifest';
import { TOPICS } from '../data/curriculum';
import { useProgress } from '../store/ProgressContext';

const TAG_LIMIT = 8;
const COMPANY_LIMIT = 10;

type DifficultyFilter = 'All' | ProblemManifestItem['difficulty'];
type StatusFilter = 'All' | 'Todo' | 'Done' | 'Starred';

const DIFFICULTY_OPTIONS: DifficultyFilter[] = ['All', 'Easy', 'Medium', 'Hard'];
const STATUS_OPTIONS: StatusFilter[] = ['All', 'Todo', 'Done', 'Starred'];

const difficultyTone: Record<ProblemManifestItem['difficulty'], string> = {
  Easy: 'text-mint',
  Medium: 'text-amber',
  Hard: 'text-rose',
};

export const ProblemListPage: React.FC = () => {
  const { topic } = useParams<{ topic: string }>();
  const { state, toggleBookmark } = useProgress();
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [difficulty, setDifficulty] = useState<DifficultyFilter>('All');
  const [status, setStatus] = useState<StatusFilter>('All');
  const [showAllTags, setShowAllTags] = useState(false);
  const [showAllCompanies, setShowAllCompanies] = useState(false);
  const [expandedTopics, setExpandedTopics] = useState<string[]>(
    topic && TOPICS.some((item) => item.slug === topic) ? [topic] : []
  );
  const prevTopicParamRef = useRef<string | undefined>(topic);
  useEffect(() => {
    if (prevTopicParamRef.current === topic) return;
    prevTopicParamRef.current = topic;
    if (topic && TOPICS.some((item) => item.slug === topic)) {
      setExpandedTopics((prev) => (prev.includes(topic) ? prev : [...prev, topic]));
    }
  }, [topic]);

  // Selected companies live in the URL (`?company=TCS[&company=...]`) so a
  // badge link from a problem page lands pre-filtered and filters are
  // shareable / survive a refresh.
  const companyFilterKey = searchParams.getAll('company').join('\0');
  const selectedCompanies = useMemo(
    () => (companyFilterKey ? companyFilterKey.split('\0') : []),
    [companyFilterKey],
  );

  const tagCounts = useMemo(() => {
    const counts = new Map<string, number>();
    PROBLEM_MANIFEST.forEach((problem) => {
      counts.set(problem.pattern, (counts.get(problem.pattern) ?? 0) + 1);
      counts.set(problem.topic, (counts.get(problem.topic) ?? 0) + 1);
    });
    return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }, []);

  const companyCounts = useMemo(() => {
    const counts = new Map<string, number>();
    PROBLEM_MANIFEST.forEach((problem) => {
      problem.companies.forEach((company) => {
        counts.set(company, (counts.get(company) ?? 0) + 1);
      });
    });
    return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }, []);

  const visibleTags = showAllTags ? tagCounts : tagCounts.slice(0, TAG_LIMIT);
  // Selected companies beyond the top 10 stay visible so the active filter is
  // never hidden inside the collapsed strip.
  const visibleCompanies = showAllCompanies
    ? companyCounts
    : companyCounts
        .slice(0, COMPANY_LIMIT)
        .concat(companyCounts.slice(COMPANY_LIMIT).filter(([company]) => selectedCompanies.includes(company)));

  const filteredProblems = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    return PROBLEM_MANIFEST.filter((problem) => {
      const matchesSearch =
        !query ||
        problem.title.toLowerCase().includes(query) ||
        problem.pattern.toLowerCase().includes(query) ||
        problem.companies.some((company) => company.toLowerCase().includes(query));
      const matchesTags =
        selectedTags.length === 0 ||
        selectedTags.some((tag) => tag === problem.topic || tag === problem.pattern);
      const matchesCompanies =
        selectedCompanies.length === 0 ||
        selectedCompanies.some((company) => problem.companies.includes(company));
      const matchesDifficulty = difficulty === 'All' || problem.difficulty === difficulty;
      const problemStatus = state.progress[problem.slug] ?? 'Todo';
      const matchesStatus =
        status === 'All' ||
        (status === 'Starred'
          ? state.bookmarks.includes(problem.slug)
          : problemStatus === status);
      return matchesSearch && matchesTags && matchesCompanies && matchesDifficulty && matchesStatus;
    });
  }, [searchQuery, selectedTags, selectedCompanies, difficulty, status, state.progress, state.bookmarks]);

  const hasActiveFilter =
    searchQuery.trim().length > 0 ||
    selectedTags.length > 0 ||
    selectedCompanies.length > 0 ||
    difficulty !== 'All' ||
    status !== 'All';
  const matchingTopics = TOPICS.filter((item) =>
    filteredProblems.some((problem) => problem.topic === item.slug)
  );

  const filterSignature = `${searchQuery.trim()}|${selectedTags.join(',')}|${companyFilterKey}|${difficulty}|${status}`;
  const lastExpandedFilterRef = useRef<string>('');

  useEffect(() => {
    if (!hasActiveFilter) {
      lastExpandedFilterRef.current = '';
      return;
    }
    if (lastExpandedFilterRef.current === filterSignature) return;
    lastExpandedFilterRef.current = filterSignature;
    const matches = TOPICS.filter((item) =>
      filteredProblems.some((problem) => problem.topic === item.slug)
    ).map((item) => item.slug);
    setExpandedTopics((current) => {
      const next = Array.from(new Set([...current, ...matches]));
      return next.length === current.length ? current : next;
    });
  }, [hasActiveFilter, filterSignature, filteredProblems]);

  const solvedCount = PROBLEM_MANIFEST.filter((problem) => state.progress[problem.slug] === 'Done').length;
  const starredCount = state.bookmarks.length;

  const toggleTag = (tag: string) => {
    setSelectedTags((current) =>
      current.includes(tag) ? current.filter((item) => item !== tag) : [...current, tag]
    );
  };

  const toggleCompany = (company: string) => {
    const next = new URLSearchParams(searchParams.toString());
    const current = next.getAll('company');
    next.delete('company');
    const updated = current.includes(company)
      ? current.filter((item) => item !== company)
      : [...current, company];
    updated.forEach((item) => next.append('company', item));
    setSearchParams(next);
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedTags([]);
    setDifficulty('All');
    setStatus('All');
    setShowAllTags(false);
    setShowAllCompanies(false);
    const next = new URLSearchParams(searchParams.toString());
    next.delete('company');
    setSearchParams(next);
  };

  const toggleTopic = (slug: string) => {
    setExpandedTopics((current) =>
      current.includes(slug) ? current.filter((item) => item !== slug) : [...current, slug]
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-ink">Problems</h1>
        <p className="text-xs text-muted font-mono">
          {filteredProblems.length} problems · {solvedCount} done · {starredCount} starred
        </p>
      </div>

      <section className="space-y-3" aria-label="Problem filters">
        <div className="relative">
          <Search className="w-4 h-4 text-muted absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="search"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search problems or patterns..."
            aria-label="Search problems"
            className="w-full rounded-xl border border-line bg-surface py-3 pl-10 pr-4 text-base sm:text-sm text-ink placeholder-muted focus:border-mint"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-1 text-[10px] font-mono uppercase tracking-[0.16em] text-muted">
            Tags
          </span>
          {visibleTags.map(([tag]) => {
            const active = selectedTags.includes(tag);
            const label = TOPICS.find((item) => item.slug === tag)?.title ?? tag;
            return (
              <button
                key={tag}
                type="button"
                onClick={() => toggleTag(tag)}
                aria-pressed={active}
                className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 min-h-9 sm:min-h-0 sm:py-1.5 text-[11px] font-mono transition ${
                  active
                    ? 'border-mint bg-mint text-canvas font-semibold'
                    : 'border-line bg-surface text-muted hover:border-steel hover:text-ink'
                }`}
              >
                {label}
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
            </button>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-1 text-[10px] font-mono uppercase tracking-[0.16em] text-muted">
            Companies
          </span>
          {visibleCompanies.map(([company]) => {
            const active = selectedCompanies.includes(company);
            return (
              <button
                key={company}
                type="button"
                onClick={() => toggleCompany(company)}
                aria-pressed={active}
                className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 min-h-9 sm:min-h-0 sm:py-1.5 text-[11px] font-mono transition ${
                  active
                    ? 'border-mint bg-mint text-canvas font-semibold'
                    : 'border-line bg-surface text-muted hover:border-steel hover:text-ink'
                }`}
              >
                {company}
              </button>
            );
          })}
          {companyCounts.length > COMPANY_LIMIT && (
            <button
              type="button"
              onClick={() => setShowAllCompanies((current) => !current)}
              className="inline-flex items-center gap-1 px-2 py-1.5 text-[11px] font-mono text-mint hover:text-ink"
            >
{showAllCompanies ? 'Fewer' : 'All companies'}
            </button>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-1 text-[10px] font-mono uppercase tracking-[0.16em] text-muted">
            Difficulty
          </span>
          {DIFFICULTY_OPTIONS.map((option) => {
            const active = difficulty === option;
            return (
              <button
                key={option}
                type="button"
                onClick={() => setDifficulty(option)}
                aria-pressed={active}
                className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 min-h-9 sm:min-h-0 sm:py-1.5 text-[11px] font-mono transition ${
                  active
                    ? 'border-mint bg-mint text-canvas font-semibold'
                    : 'border-line bg-surface text-muted hover:border-steel hover:text-ink'
                }`}
              >
                {option}
              </button>
            );
          })}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-1 text-[10px] font-mono uppercase tracking-[0.16em] text-muted">
            Status
          </span>
          {STATUS_OPTIONS.map((option) => {
            const active = status === option;
            return (
              <button
                key={option}
                type="button"
                onClick={() => setStatus(option)}
                aria-pressed={active}
                className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 min-h-9 sm:min-h-0 sm:py-1.5 text-[11px] font-mono transition ${
                  active
                    ? 'border-mint bg-mint text-canvas font-semibold'
                    : 'border-line bg-surface text-muted hover:border-steel hover:text-ink'
                }`}
              >
                {option}
              </button>
            );
          })}
          {hasActiveFilter && (
            <button
              type="button"
              onClick={clearFilters}
              className="inline-flex items-center gap-1 px-2 min-h-9 sm:min-h-0 sm:py-1.5 text-[11px] font-mono text-rose hover:text-ink"
            >
              Clear filters
            </button>
          )}
        </div>
      </section>

      {hasActiveFilter && filteredProblems.length === 0 && (
        <div className="rounded-xl border border-line bg-surface p-8 text-center">
          <p className="text-sm font-semibold text-ink">No problems match your filters</p>
          <p className="text-xs text-muted mt-1">Try a different search or clear the filters.</p>
        </div>
      )}

      <section className="space-y-3" aria-label="Problem topics">
        {(hasActiveFilter ? matchingTopics : TOPICS).map((topicItem) => {
          const topicProblems = filteredProblems.filter((problem) => problem.topic === topicItem.slug);
          const allTopicProblems = PROBLEM_MANIFEST.filter((problem) => problem.topic === topicItem.slug);
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
                </span>
                <span className="w-24 shrink-0 space-y-1.5">
                  <span className="block text-right text-[11px] font-mono text-muted tnum">
                    {doneCount}/{allTopicProblems.length}
                  </span>
                  <span className="block h-1.5 rounded-full bg-canvas overflow-hidden">
                    <span
                      className="block h-full w-full rounded-full bg-mint origin-left transition-transform duration-300 ease-quart motion-reduce:transition-none"
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
                          {isDone ? (
                            <Check className="w-3.5 h-3.5 text-mint shrink-0" aria-label="Solved" />
                          ) : (
                            <span className="w-2 h-2 rounded-full bg-muted/50 shrink-0" aria-hidden="true" />
                          )}
                          <span className="sr-only">{isDone ? 'Solved' : 'Not solved'}</span>
                          <Link
                            to={`/problems/${problem.topic}/${problem.slug}`}
                            className="min-w-0 flex-1 py-2.5 text-sm text-ink hover:text-mint transition"
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
                            className={`-mr-2 p-3 rounded transition ${
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
        {filteredProblems.length} / {PROBLEM_MANIFEST.length}
      </p>
    </div>
  );
};
