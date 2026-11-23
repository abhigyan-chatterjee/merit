import React, { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Layers,
  Code2,
  BrainCircuit,
  GraduationCap,
  Search,
  Flame,
  X,
  CornerDownLeft,
  Route,
  LogIn,
  Bug,
  RotateCcw
} from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { UserDropdown } from './UserDropdown';
import { FeedbackModal } from './FeedbackModal';
import { useProgress } from '../store/ProgressContext';
import { useAuth } from '../store/AuthContext';
import { useDialogFocus } from '../hooks/useDialogFocus';
import { PROBLEM_MANIFEST, ProblemManifestItem } from '../data/problemManifest';
import { VISUALIZERS } from '../data/curriculum';
import { LEARNING_PATHS } from '../data/learningPaths';
import { TARGETED_EXAMS } from '../data/exams';

const QUIZ_TRACKS = [
  { id: 'aptitude', title: 'Aptitude', description: 'Quant, logical reasoning, and verbal for screening rounds.' },
  { id: 'verbal', title: 'Verbal Ability', description: 'Grammar correction, vocabulary in context, para-jumbles, and inference.' },
  { id: 'sql', title: 'SQL & Databases', description: 'Queries, joins, grouping, NULL traps, and window functions.' },
  { id: 'cs-fundamentals', title: 'CS Fundamentals', description: 'Operating systems, memory management, networks, and DBMS.' },
  { id: 'mixed', title: 'Mixed Mastery', description: 'Adaptive placement assessment drawn across all verified items.' },
] as const;

const scoreMatch = (title: string, q: string, extra: string[] = [], blurb?: string) => {
  const t = title.toLowerCase();
  if (t === q) return 5;
  if (t.startsWith(q)) return 4;
  if (t.includes(q)) return 3;
  if (extra.some((f) => f.toLowerCase().includes(q))) return 2;
  if (blurb && blurb.toLowerCase().includes(q)) return 1;
  return 0;
};

const KindBadge: React.FC<{ label: string }> = ({ label }) => (
  <span className="px-1.5 py-0.5 rounded border border-line text-[9px] font-mono uppercase tracking-wider text-muted shrink-0">
    {label}
  </span>
);

export const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { currentStreak, dueTodayCount } = useProgress();
  const { user, isLoading: authLoading } = useAuth();
  const [searchOpen, setSearchOpen] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const searchTriggerRef = useRef<HTMLButtonElement>(null);

  // The palette can be opened by ⌘K from anywhere, so there is no reliable
  // "previously focused" element to return to. It always returns to the
  // search button that advertises the shortcut instead of dropping the user
  // at the top of the document.
  const closeSearch = useCallback(() => {
    setSearchOpen(false);
    requestAnimationFrame(() => searchTriggerRef.current?.focus());
  }, []);

  const searchRef = useDialogFocus<HTMLDivElement>(searchOpen, closeSearch);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen((open) => !open);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const isTyped = query.trim().length > 0;

  type PaletteEntry =
    | { kind: 'path'; path: (typeof LEARNING_PATHS)[number]; score: number; navigate: () => void }
    | { kind: 'visualizer'; viz: (typeof VISUALIZERS)[number]; score: number; navigate: () => void }
    | { kind: 'problem'; problem: ProblemManifestItem; score: number; navigate: () => void }
    | { kind: 'exam'; exam: (typeof TARGETED_EXAMS)[number]; score: number; navigate: () => void }
    | { kind: 'quiz'; quiz: (typeof QUIZ_TRACKS)[number]; score: number; navigate: () => void }
    | { kind: 'review'; score: number; navigate: () => void };

  const entries = useMemo<PaletteEntry[]>(() => {
    const q = query.trim().toLowerCase();
    if (!q) {
      const out: PaletteEntry[] = [];
      LEARNING_PATHS.slice(0, 2).forEach((p) =>
        out.push({
          kind: 'path',
          path: p,
          score: 0,
          navigate: () => {
            setSearchOpen(false);
            navigate(`/learn/${p.id}`);
          }
        })
      );
      VISUALIZERS.slice(0, 4).forEach((v) =>
        out.push({
          kind: 'visualizer',
          viz: v,
          score: 0,
          navigate: () => {
            setSearchOpen(false);
            navigate(`/visualizers/${v.id}`);
          }
        })
      );
      const seenTopics = new Set<string>();
      PROBLEM_MANIFEST.filter((p) => {
        if (seenTopics.has(p.topic)) return false;
        seenTopics.add(p.topic);
        return true;
      })
        .slice(0, 5)
        .forEach((p) =>
          out.push({
            kind: 'problem',
            problem: p,
            score: 0,
            navigate: () => {
              setSearchOpen(false);
              navigate(`/problems/${p.topic}/${p.slug}`);
            }
          })
        );
      return out;
    }
    const pathHits: PaletteEntry[] = LEARNING_PATHS.filter(
      (p) => p.title.toLowerCase().includes(q) || p.blurb.toLowerCase().includes(q)
    )
      .map((p) => ({
        kind: 'path',
        path: p,
        score: scoreMatch(p.title, q, [], p.blurb),
        navigate: () => {
          setSearchOpen(false);
          navigate(`/learn/${p.id}`);
        }
      }));
    const vizHits: PaletteEntry[] = VISUALIZERS.filter(
      (v) => v.title.toLowerCase().includes(q) || v.category.toLowerCase().includes(q)
    )
      .map((v) => ({
        kind: 'visualizer',
        viz: v,
        score: scoreMatch(v.title, q, [v.category]),
        navigate: () => {
          setSearchOpen(false);
          navigate(`/visualizers/${v.id}`);
        }
      }));
    const probHits: PaletteEntry[] = PROBLEM_MANIFEST.filter(
      (p) =>
        p.title.toLowerCase().includes(q) ||
        p.pattern.toLowerCase().includes(q) ||
        p.topic.toLowerCase().includes(q)
    )
      .map((p) => ({
        kind: 'problem',
        problem: p,
        score: scoreMatch(p.title, q, [p.pattern, p.topic]),
        navigate: () => {
          setSearchOpen(false);
          navigate(`/problems/${p.topic}/${p.slug}`);
        }
      }));
    const examHits: PaletteEntry[] = TARGETED_EXAMS.filter(
      (e) =>
        e.title.toLowerCase().includes(q) ||
        e.description.toLowerCase().includes(q) ||
        (e.company && e.company.toLowerCase().includes(q)) ||
        e.category.toLowerCase().includes(q)
    ).map((e) => ({
      kind: 'exam',
      exam: e,
      score: scoreMatch(e.title, q, [e.company ?? '', e.category], e.description),
      navigate: () => {
        setSearchOpen(false);
        navigate(`/exams/${e.id}`);
      }
    }));
    const quizHits: PaletteEntry[] = QUIZ_TRACKS.filter(
      (quiz) =>
        quiz.title.toLowerCase().includes(q) ||
        quiz.description.toLowerCase().includes(q) ||
        quiz.id.toLowerCase().includes(q)
    ).map((quiz) => ({
      kind: 'quiz',
      quiz,
      score: scoreMatch(quiz.title, q, [quiz.id], quiz.description),
      navigate: () => {
        setSearchOpen(false);
        navigate(`/quiz/${quiz.id}`);
      }
    }));
    const reviewHits: PaletteEntry[] =
      q.includes('review') || q.includes('spaced') || q.includes('sm-2')
        ? [
            {
              kind: 'review',
              score: scoreMatch('Spaced Review Deck', q, ['review', 'spaced', 'sm-2']),
              navigate: () => {
                setSearchOpen(false);
                navigate('/review');
              },
            },
          ]
        : [];
    const combined = [...pathHits, ...vizHits, ...probHits, ...examHits, ...quizHits, ...reviewHits];
    const kindRank = (e: PaletteEntry) => {
      switch (e.kind) {
        case 'path':
          return 0;
        case 'visualizer':
          return 1;
        case 'exam':
          return 2;
        case 'quiz':
          return 3;
        case 'review':
          return 4;
        case 'problem':
          return 5;
      }
    };
    const titleOf = (e: PaletteEntry) => {
      switch (e.kind) {
        case 'path':
          return e.path.title;
        case 'visualizer':
          return e.viz.title;
        case 'problem':
          return e.problem.title;
        case 'exam':
          return e.exam.title;
        case 'quiz':
          return e.quiz.title;
        case 'review':
          return 'Spaced Review Deck';
      }
    };
    combined.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      const kr = kindRank(a) - kindRank(b);
      if (kr !== 0) return kr;
      return titleOf(a).localeCompare(titleOf(b));
    });
    return combined.slice(0, 40);
  }, [query, navigate]);

  const totalResults = entries.length;

  // Reset the active row whenever the result set changes.
  useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  const navLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/learn', label: 'Paths', icon: Route },
    { to: '/visualizers', label: 'Visualizers', icon: Layers },
    { to: '/problems/arrays-hashing', label: 'Problems', icon: Code2 },
    { to: '/quiz/mixed', label: 'Quizzes', icon: BrainCircuit },
    { to: '/exams', label: 'Exams', icon: GraduationCap }
  ];

  const isActive = (path: string) => {
    if (path.startsWith('/exams') && location.pathname.startsWith('/exams')) return true;
    if (path.startsWith('/learn') && location.pathname.startsWith('/learn')) return true;
    if (path.startsWith('/problems') && location.pathname.startsWith('/problems')) return true;
    if (path.startsWith('/quiz') && location.pathname.startsWith('/quiz')) return true;
    if (path.startsWith('/visualizers') && location.pathname.startsWith('/visualizers')) return true;
    return location.pathname === path;
  };

  const difficultyDot = (d: string) =>
    d === 'Easy' ? 'bg-mint' : d === 'Medium' ? 'bg-amber' : 'bg-rose';

  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((i) => (entries.length === 0 ? 0 : Math.min(i + 1, entries.length - 1)));
      return;
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((i) => (entries.length === 0 ? 0 : Math.max(i - 1, 0)));
      return;
    }
    if (e.key !== 'Enter') return;
    e.preventDefault();
    const r = entries[activeIndex];
    if (r) r.navigate();
    else closeSearch();
  };

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-line bg-canvas/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 h-14 flex items-center justify-between gap-2 sm:gap-3">
          {/* Wordmark */}
          <Link to="/" className="flex items-center gap-2.5 group min-w-0">
            <div className="relative w-8 h-8 rounded-lg border border-line bg-surface grid place-items-center overflow-hidden">
              {/* tiny algorithm glyph */}
              <svg viewBox="0 0 20 20" className="w-4 h-4" aria-hidden="true">
                <rect x="2" y="11" width="3" height="7" rx="1" className="fill-steel" />
                <rect x="6.5" y="7" width="3" height="11" rx="1" className="fill-mint" />
                <rect x="11" y="9" width="3" height="9" rx="1" className="fill-steel" />
                <rect x="15.5" y="3" width="3" height="15" rx="1" className="fill-mint" />
              </svg>
            </div>
            <div className="flex flex-col leading-none">
              <span className="font-mono font-bold text-sm tracking-[-0.02em] text-ink">
                MERIT
              </span>
              <span className="text-[9px] font-mono uppercase tracking-[0.18em] text-muted mt-0.5 hidden sm:inline">
                placement prep
              </span>
            </div>
          </Link>

          {/* Desktop nav. Recomposed for tablet: the six labels measured 605px,
              which collided with the 398px rail anywhere below ~1100px and
              pushed the document past the viewport at 768 and 1024. From md
              through xl the links collapse to their glyphs, so navigation
              stays present on a tablet instead of being hidden behind the
              phone tab bar. Labels return at xl where the width is earned. */}
          <nav className="hidden md:flex items-center gap-0.5" aria-label="Primary">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const active = isActive(link.to);
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  aria-label={link.label}
                  aria-current={active ? 'page' : undefined}
                  title={link.label}
                  className={`relative inline-flex items-center gap-2 px-3 xl:px-3.5 py-2.5 xl:py-2 rounded-lg text-xs font-medium transition-colors duration-200 before:absolute before:-inset-1.5 before:content-[''] ${
                    active ? 'text-ink' : 'text-muted hover:text-ink'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 shrink-0 ${active ? 'text-mint' : ''}`} />
                  <span className="hidden xl:inline">{link.label}</span>
                  {active && (
                    <motion.span
                      layoutId="nav-active"
                      className="absolute left-2 right-2 -bottom-[9px] h-px bg-mint"
                      transition={{ duration: 0.2, ease: 'easeOut' }}
                    />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Right rail — must be allowed to shrink. At shrink-0 it held
              290px beside the wordmark and forced a 399px document on every
              phone-width route, clipping Sign In. Secondary controls now drop
              out below sm rather than pushing the row wider than the screen. */}
          <div className="flex items-center gap-1.5 sm:gap-2 min-w-0">
            <button
              ref={searchTriggerRef}
              onClick={() => setSearchOpen(true)}
              aria-label="Open global search"
              className="relative flex items-center gap-2 pl-2.5 pr-2 py-1.5 rounded-lg border border-line bg-surface text-xs text-muted hover:border-steel hover:text-ink transition cursor-pointer before:absolute before:-inset-2 before:content-['']"
            >
              <Search className="w-3.5 h-3.5" />
              <span className="hidden lg:inline font-mono">Search…</span>
              <kbd className="hidden lg:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-canvas rounded border border-line text-muted">
                ⌘K
              </kbd>
            </button>

            <Link
              to="/dashboard"
              title={`${currentStreak} day learning streak`}
              aria-label={`Learning streak: ${currentStreak} days`}
              className="hidden sm:flex relative items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-line bg-surface text-xs font-mono hover:border-mint transition before:absolute before:-inset-2 before:content-['']"
            >
              <Flame className="w-3.5 h-3.5 text-mint" />
              <span className="font-bold text-ink tnum">{currentStreak}</span>
              <span className="text-muted text-[10px] uppercase tracking-wider">d</span>
            </Link>

            {user && dueTodayCount > 0 && (
              <Link
                to="/review"
                aria-label={`${dueTodayCount} due for review today`}
                className="hidden sm:flex relative items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-amber/40 bg-amber/10 text-xs font-mono text-amber hover:border-amber transition before:absolute before:-inset-2 before:content-['']"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span className="font-bold tnum">{dueTodayCount}</span>
                <span className="hidden sm:inline text-[10px] uppercase tracking-wider">due</span>
              </Link>
            )}

            <ThemeToggle />

            {/* The bug report lives in the footer on phones, so it is not
                duplicated into the cramped top rail. */}
            <button
              type="button"
              onClick={() => setFeedbackOpen(true)}
              title="Report Bug / Feedback"
              aria-label="Report Bug or Feedback"
              className="hidden md:inline-flex relative p-1.5 rounded-lg border border-line bg-surface text-muted hover:text-ink hover:border-mint transition cursor-pointer before:absolute before:-inset-2.5 before:content-['']"
            >
              <Bug className="w-3.5 h-3.5 text-mint" />
            </button>

            {user ? (
              <div className="flex items-center gap-1.5 pl-1 border-l border-line">
                <UserDropdown />
              </div>
            ) : authLoading ? null : (
              <Link
                to="/login"
                className="shrink-0 inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-line bg-surface text-xs font-mono text-ink hover:border-mint hover:text-mint transition"
              >
                <LogIn className="w-3.5 h-3.5 text-mint" />
                <span>Sign In</span>
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* Mobile bottom tab bar */}
      <nav aria-label="Mobile navigation" className="fixed bottom-0 left-0 right-0 z-40 md:hidden border-t border-line bg-canvas/95 backdrop-blur-md">
        <div className="grid grid-cols-6">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const active = isActive(link.to);
            return (
              <Link
                key={link.to}
                to={link.to}
                aria-current={active ? 'page' : undefined}
                className={`relative flex flex-col items-center justify-center gap-1 h-14 font-sans text-[11px] font-medium ${
                  active ? 'text-mint' : 'text-muted'
                }`}
              >
                {active && <span className="absolute top-0 w-8 h-px bg-mint" />}
                <Icon className="w-4 h-4" />
                <span className="truncate max-w-full px-0.5">{link.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* AnimatePresence keeps the palette mounted through its exit, so the
          dismissal is animated rather than an instant disappearance. */}
      <AnimatePresence>
        {searchOpen && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center pt-[12vh] px-4 bg-canvas/80 backdrop-blur-sm"
          onClick={closeSearch}
        >
          <motion.div
            ref={searchRef}
            tabIndex={-1}
            role="dialog"
            aria-modal="true"
            aria-label="Global search"
            initial={{ opacity: 0, y: -8, scale: 0.99 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.99, transition: { duration: 0.12 } }}
            transition={{ duration: 0.18, ease: [0.25, 1, 0.5, 1] }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-xl rounded-xl border border-line bg-surface shadow-2xl overflow-hidden"
          >
            <div className="flex items-center gap-2.5 px-4 h-12 border-b border-line">
              <Search className="w-4 h-4 text-mint shrink-0" />
              <input
                type="text"
                role="combobox"
                aria-expanded={searchOpen}
                aria-controls="global-search-options"
                aria-activedescendant={entries.length > 0 ? `search-option-${activeIndex}` : undefined}
                aria-autocomplete="list"
                autoFocus
                placeholder="Search structures, problems or patterns…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleSearchKeyDown}
                className="flex-1 bg-transparent text-base sm:text-xs text-ink placeholder-muted"
              />
              <span className="text-[10px] font-mono text-muted tnum hidden sm:inline">
                {isTyped ? `${totalResults} ${totalResults === 1 ? 'result' : 'results'}` : ''}
              </span>
              <button
                onClick={closeSearch}
                aria-label="Close search"
                className="text-muted hover:text-ink cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div id="global-search-options" role="listbox" aria-label="Search results" className="max-h-[52vh] overflow-y-auto p-2">
              {isTyped && totalResults === 0 && (
                <div className="py-10 text-center">
                  <p className="text-xs text-muted font-mono">
                    No matches for “{query}”. Try a pattern name like “sliding window”.
                  </p>
                </div>
              )}

              {!isTyped && totalResults > 0 && (
                <div className="px-3 py-2 text-[10px] font-mono uppercase tracking-[0.16em] text-muted">
                  Suggested
                </div>
              )}

              {entries.map((entry, i) => {
                const isActiveRow = i === activeIndex;
                const cls = `group w-full text-left px-3 py-2 rounded-lg flex items-center justify-between gap-3 cursor-pointer border-l-2 ${
                  isActiveRow ? 'bg-canvas/60 border-mint' : 'border-transparent hover:bg-canvas'
                }`;
                if (entry.kind === 'path') {
                  const p = entry.path;
                  return (
                    <button
                      key={`path-${p.id}`}
                      id={`search-option-${i}`}
                      role="option"
                      aria-selected={isActiveRow}
                      onClick={entry.navigate}
                      onMouseEnter={() => setActiveIndex(i)}
                      className={cls}
                    >
                      <span className="flex items-center gap-2.5 min-w-0">
                        <Route className="w-3.5 h-3.5 text-mint shrink-0" />
                        <span className="text-xs font-medium text-ink truncate">{p.title}</span>
                      </span>
                      <span className="flex items-center gap-2 shrink-0">
                        <KindBadge label="Path" />
                        <span className="font-mono text-[10px] text-muted">
                          {p.steps.length} steps
                        </span>
                      </span>
                    </button>
                  );
                }
                if (entry.kind === 'visualizer') {
                  const v = entry.viz;
                  return (
                    <button
                      key={`viz-${v.id}`}
                      id={`search-option-${i}`}
                      role="option"
                      aria-selected={isActiveRow}
                      onClick={entry.navigate}
                      onMouseEnter={() => setActiveIndex(i)}
                      className={cls}
                    >
                      <span className="flex items-center gap-2.5 min-w-0">
                        <Layers className="w-3.5 h-3.5 text-mint shrink-0" />
                        <span className="text-xs font-medium text-ink truncate">{v.title}</span>
                      </span>
                      <span className="flex items-center gap-2 shrink-0">
                        <KindBadge label="Visualizer" />
                        <span className="font-mono text-[10px] uppercase tracking-wider text-muted">
                          {v.category}
                        </span>
                        <CornerDownLeft className="w-3 h-3 text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
                      </span>
                    </button>
                  );
                }
                if (entry.kind === 'exam') {
                  const exam = entry.exam;
                  return (
                    <button
                      key={`exam-${exam.id}`}
                      id={`search-option-${i}`}
                      role="option"
                      aria-selected={isActiveRow}
                      onClick={entry.navigate}
                      onMouseEnter={() => setActiveIndex(i)}
                      className={cls}
                    >
                      <span className="flex items-center gap-2.5 min-w-0">
                        <GraduationCap className="w-3.5 h-3.5 text-mint shrink-0" />
                        <span className="text-xs font-medium text-ink truncate">{exam.title}</span>
                        {exam.company && (
                          <span className="text-[10px] font-mono text-violet truncate hidden sm:inline">
                            {exam.company}
                          </span>
                        )}
                      </span>
                      <span className="flex items-center gap-2 shrink-0">
                        <KindBadge label="Exam" />
                        <span className="font-mono text-[10px] uppercase tracking-wider text-muted">
                          {exam.category}
                        </span>
                        <CornerDownLeft className="w-3 h-3 text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
                      </span>
                    </button>
                  );
                }
                if (entry.kind === 'quiz') {
                  const quiz = entry.quiz;
                  return (
                    <button
                      key={`quiz-${quiz.id}`}
                      id={`search-option-${i}`}
                      role="option"
                      aria-selected={isActiveRow}
                      onClick={entry.navigate}
                      onMouseEnter={() => setActiveIndex(i)}
                      className={cls}
                    >
                      <span className="flex items-center gap-2.5 min-w-0">
                        <BrainCircuit className="w-3.5 h-3.5 text-mint shrink-0" />
                        <span className="text-xs font-medium text-ink truncate">{quiz.title}</span>
                      </span>
                      <span className="flex items-center gap-2 shrink-0">
                        <KindBadge label="Quiz" />
                        <CornerDownLeft className="w-3 h-3 text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
                      </span>
                    </button>
                  );
                }
                if (entry.kind === 'review') {
                  return (
                    <button
                      key="review-deck"
                      id={`search-option-${i}`}
                      role="option"
                      aria-selected={isActiveRow}
                      onClick={entry.navigate}
                      onMouseEnter={() => setActiveIndex(i)}
                      className={cls}
                    >
                      <span className="flex items-center gap-2.5 min-w-0">
                        <RotateCcw className="w-3.5 h-3.5 text-amber shrink-0" />
                        <span className="text-xs font-medium text-ink truncate">Spaced Review Deck</span>
                      </span>
                      <span className="flex items-center gap-2 shrink-0">
                        <KindBadge label="Review" />
                        <CornerDownLeft className="w-3 h-3 text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
                      </span>
                    </button>
                  );
                }
                const p = entry.problem;
                return (
                  <button
                    key={`problem-${p.id}`}
                    id={`search-option-${i}`}
                    role="option"
                    aria-selected={isActiveRow}
                    onClick={entry.navigate}
                    onMouseEnter={() => setActiveIndex(i)}
                    className={cls}
                  >
                    <span className="flex items-center gap-2.5 min-w-0">
                      <span className="flex items-center gap-1.5 shrink-0">
                        <span
                          aria-hidden="true"
                          className={`w-1.5 h-1.5 rounded-full ${difficultyDot(p.difficulty)}`}
                        />
                        <span className="text-[10px] font-mono uppercase text-muted">
                          {p.difficulty}
                        </span>
                      </span>
                      <span className="text-xs font-medium text-ink truncate">{p.title}</span>
                      <span className="text-[10px] font-mono text-violet truncate hidden sm:inline">
                        {p.pattern}
                      </span>
                    </span>
                    <span className="flex items-center gap-2 shrink-0">
                      <KindBadge label="Problem" />
                      <CornerDownLeft className="w-3 h-3 text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
                    </span>
                  </button>
                );
              })}
            </div>

            <div className="flex items-center gap-4 px-4 h-9 border-t border-line bg-canvas text-[10px] font-mono text-muted">
              <span className="flex items-center gap-1.5">
                <kbd className="px-1 py-0.5 border border-line rounded bg-surface">esc</kbd> close
              </span>
              <span className="flex items-center gap-1.5">
                <kbd className="px-1 py-0.5 border border-line rounded bg-surface">⌘K</kbd> toggle
              </span>
              <span className="ml-auto text-mint">press ↵ to jump</span>
            </div>
          </motion.div>
        </div>
        )}
      </AnimatePresence>

      <FeedbackModal isOpen={feedbackOpen} onClose={() => setFeedbackOpen(false)} />
    </>
  );
};
