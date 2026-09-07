import React, { useState, useMemo, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Layers,
  Code2,
  BrainCircuit,
  Search,
  Flame,
  X,
  CornerDownLeft,
  Route
} from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { useProgress } from '../store/ProgressContext';
import { PROBLEMS } from '../data/problems';
import { VISUALIZERS } from '../data/curriculum';
import { LEARNING_PATHS } from '../data/learningPaths';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { currentStreak } = useProgress();
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen((open) => !open);
      }
      if (e.key === 'Escape') setSearchOpen(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    document.body.style.overflow = searchOpen ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [searchOpen]);

  const searchResults = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q)
      return {
        paths: LEARNING_PATHS.slice(0, 2),
        visualizers: VISUALIZERS.slice(0, 4),
        problems: PROBLEMS.slice(0, 5)
      };
    return {
      paths: LEARNING_PATHS.filter(
        (p) => p.title.toLowerCase().includes(q) || p.blurb.toLowerCase().includes(q)
      ),
      visualizers: VISUALIZERS.filter(
        (v) => v.title.toLowerCase().includes(q) || v.category.toLowerCase().includes(q)
      ),
      problems: PROBLEMS.filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          p.pattern.toLowerCase().includes(q) ||
          p.topic.toLowerCase().includes(q)
      )
    };
  }, [query]);

  const totalResults =
    searchResults.paths.length + searchResults.visualizers.length + searchResults.problems.length;

  const navLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/learn', label: 'Paths', icon: Route },
    { to: '/visualizers', label: 'Visualizers', icon: Layers },
    { to: '/problems/arrays', label: 'Problems', icon: Code2 },
    { to: '/quiz/mixed', label: 'Quizzes', icon: BrainCircuit }
  ];

  const isActive = (path: string) => {
    if (path.startsWith('/learn') && location.pathname.startsWith('/learn')) return true;
    if (path.startsWith('/problems') && location.pathname.startsWith('/problems')) return true;
    if (path.startsWith('/quiz') && location.pathname.startsWith('/quiz')) return true;
    if (path.startsWith('/visualizers') && location.pathname.startsWith('/visualizers')) return true;
    return location.pathname === path;
  };

  const difficultyDot = (d: string) =>
    d === 'Easy' ? 'bg-mint' : d === 'Medium' ? 'bg-amber' : 'bg-rose';

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-line bg-canvas/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between gap-3">
          {/* Wordmark */}
          <Link to="/" className="flex items-center gap-2.5 group shrink-0">
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
                ALGOVISTA
              </span>
              <span className="text-[9px] font-mono uppercase tracking-[0.18em] text-muted mt-0.5 hidden sm:inline">
                dsa workbench
              </span>
            </div>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-0.5">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const active = isActive(link.to);
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`relative inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium transition-colors duration-200 ${
                    active ? 'text-ink' : 'text-muted hover:text-ink'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${active ? 'text-mint' : ''}`} />
                  {link.label}
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

          {/* Right rail */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => setSearchOpen(true)}
              aria-label="Open global search"
              className="flex items-center gap-2 pl-2.5 pr-2 py-1.5 rounded-lg border border-line bg-surface text-xs text-muted hover:border-steel hover:text-ink transition cursor-pointer"
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
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-line bg-surface text-xs font-mono hover:border-mint transition"
            >
              <Flame className="w-3.5 h-3.5 text-mint" />
              <span className="font-bold text-ink tnum">{currentStreak}</span>
              <span className="hidden sm:inline text-muted text-[10px] uppercase tracking-wider">d</span>
            </Link>

            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Mobile bottom tab bar */}
      <nav className="fixed bottom-0 left-0 right-0 z-40 md:hidden border-t border-line bg-canvas/95 backdrop-blur-md">
        <div className="grid grid-cols-4">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const active = isActive(link.to);
            return (
              <Link
                key={link.to}
                to={link.to}
                className={`relative flex flex-col items-center justify-center gap-1 h-14 text-[10px] font-mono tracking-wide ${
                  active ? 'text-mint' : 'text-muted'
                }`}
              >
                {active && <span className="absolute top-0 w-8 h-px bg-mint" />}
                <Icon className="w-4 h-4" />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Command palette */}
      {searchOpen && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center pt-[12vh] px-4 bg-canvas/80 backdrop-blur-sm"
          onClick={() => setSearchOpen(false)}
          role="dialog"
          aria-modal="true"
          aria-label="Global search"
        >
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.99 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-xl rounded-xl border border-line bg-surface shadow-2xl overflow-hidden"
          >
            <div className="flex items-center gap-2.5 px-4 h-12 border-b border-line">
              <Search className="w-4 h-4 text-mint shrink-0" />
              <input
                type="text"
                autoFocus
                placeholder="Search structures, problems or patterns…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="flex-1 bg-transparent text-sm text-ink placeholder-muted focus:outline-none"
              />
              <span className="text-[10px] font-mono text-muted tnum hidden sm:inline">
                {totalResults} hits
              </span>
              <button
                onClick={() => setSearchOpen(false)}
                aria-label="Close search"
                className="text-muted hover:text-ink cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="max-h-[52vh] overflow-y-auto p-2">
              {totalResults === 0 && (
                <div className="py-10 text-center">
                  <p className="text-xs text-muted font-mono">
                    No matches for “{query}”
                  </p>
                </div>
              )}

              {searchResults.paths.length > 0 && (
                <div className="mb-2">
                  <div className="px-3 py-2 text-[10px] font-mono uppercase tracking-[0.16em] text-muted">
                    Learning paths
                  </div>
                  {searchResults.paths.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => {
                        setSearchOpen(false);
                        navigate(`/learn/${p.id}`);
                      }}
                      className="group w-full text-left px-3 py-2 rounded-lg hover:bg-canvas flex items-center justify-between gap-3 cursor-pointer"
                    >
                      <span className="flex items-center gap-2.5 min-w-0">
                        <Route className="w-3.5 h-3.5 text-mint shrink-0" />
                        <span className="text-xs font-medium text-ink truncate">{p.title}</span>
                      </span>
                      <span className="font-mono text-[10px] text-muted shrink-0">
                        {p.steps.length} steps
                      </span>
                    </button>
                  ))}
                </div>
              )}

              {searchResults.visualizers.length > 0 && (
                <div className="mb-2">
                  <div className="px-3 py-2 text-[10px] font-mono uppercase tracking-[0.16em] text-muted">
                    Visualizers
                  </div>
                  {searchResults.visualizers.map((v) => (
                    <button
                      key={v.id}
                      onClick={() => {
                        setSearchOpen(false);
                        navigate(`/visualizers/${v.id}`);
                      }}
                      className="group w-full text-left px-3 py-2 rounded-lg hover:bg-canvas flex items-center justify-between gap-3 cursor-pointer"
                    >
                      <span className="flex items-center gap-2.5 min-w-0">
                        <Layers className="w-3.5 h-3.5 text-mint shrink-0" />
                        <span className="text-xs font-medium text-ink truncate">{v.title}</span>
                      </span>
                      <span className="flex items-center gap-2 shrink-0">
                        <span className="font-mono text-[10px] uppercase tracking-wider text-muted">
                          {v.category}
                        </span>
                        <CornerDownLeft className="w-3 h-3 text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
                      </span>
                    </button>
                  ))}
                </div>
              )}

              {searchResults.problems.length > 0 && (
                <div>
                  <div className="px-3 py-2 text-[10px] font-mono uppercase tracking-[0.16em] text-muted">
                    Problems
                  </div>
                  {searchResults.problems.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => {
                        setSearchOpen(false);
                        navigate(`/problems/${p.topic}/${p.slug}`);
                      }}
                      className="group w-full text-left px-3 py-2 rounded-lg hover:bg-canvas flex items-center justify-between gap-3 cursor-pointer"
                    >
                      <span className="flex items-center gap-2.5 min-w-0">
                        <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${difficultyDot(p.difficulty)}`} />
                        <span className="text-xs font-medium text-ink truncate">{p.title}</span>
                        <span className="text-[10px] font-mono text-violet truncate hidden sm:inline">
                          {p.pattern}
                        </span>
                      </span>
                      <CornerDownLeft className="w-3 h-3 text-muted opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                    </button>
                  ))}
                </div>
              )}
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
    </>
  );
};
