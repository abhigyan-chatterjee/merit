import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { FeedbackModal } from './FeedbackModal';

const COLUMNS: { title: string; links: { to: string; label: string }[] }[] = [
  {
    title: 'Visualize',
    links: [
      { to: '/visualizers/sorting', label: 'Sorting' },
      { to: '/visualizers/graph', label: 'Graph BFS / DFS' },
      { to: '/visualizers/bst', label: 'Binary Search Tree' },
      { to: '/visualizers/hashmap', label: 'Hash Map' }
    ]
  },
  {
    title: 'Learn',
    links: [
      { to: '/learn', label: 'Guided paths' },
      { to: '/problems/arrays-hashing', label: 'Arrays' },
      { to: '/problems/graphs', label: 'Graphs' },
      { to: '/problems/dynamic-programming', label: 'Dynamic Programming' }
    ]
  },
  {
    title: 'Assess',
    links: [
      { to: '/quiz/mixed', label: 'Mixed quiz' },
      { to: '/quiz/arrays-hashing', label: 'Arrays quiz' },
      { to: '/quiz/graphs', label: 'Graphs quiz' },
      { to: '/dashboard', label: 'Progress dashboard' }
    ]
  },
  {
    title: 'Legal',
    links: [
      { to: '/privacy', label: 'Privacy policy' },
      { to: '/terms', label: 'Terms of service' }
    ]
  }
];

export const Footer: React.FC = () => {
  const [feedbackOpen, setFeedbackOpen] = useState(false);

  return (
    <>
      <footer className="mt-20 border-t border-line bg-surface/40 pb-20 md:pb-0">
        <div className="max-w-7xl mx-auto px-4 py-12 grid grid-cols-2 md:grid-cols-6 gap-8">
          {/* Brand */}
          <div className="col-span-2 space-y-3">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg border border-line bg-surface grid place-items-center">
                <svg viewBox="0 0 20 20" className="w-3.5 h-3.5" aria-hidden="true">
                  <rect x="2" y="11" width="3" height="7" rx="1" className="fill-steel" />
                  <rect x="6.5" y="7" width="3" height="11" rx="1" className="fill-mint" />
                  <rect x="11" y="9" width="3" height="9" rx="1" className="fill-steel" />
                  <rect x="15.5" y="3" width="3" height="15" rx="1" className="fill-mint" />
                </svg>
              </div>
              <span className="font-mono font-bold text-sm tracking-[-0.02em] text-ink">
                MERIT
              </span>
            </Link>
            <p className="text-xs text-muted leading-relaxed max-w-xs">
              Step through the execution, not the explanation.
            </p>
            <p className="text-xs text-muted leading-relaxed max-w-xs">
              Built by{' '}
              <a
                href="https://nullbit.in"
                target="_blank"
                rel="noreferrer"
                className="text-ink hover:text-mint transition-colors"
              >
                Abhigyan Chatterjee
              </a>{' '}
              ·{' '}
              <a
                href="https://github.com/abhigyan-chatterjee"
                target="_blank"
                rel="noreferrer"
                className="text-ink hover:text-mint transition-colors"
              >
                GitHub
              </a>
            </p>
            <div className="pt-1">
              <button
                type="button"
                onClick={() => setFeedbackOpen(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-line bg-surface text-xs font-mono text-muted hover:border-mint hover:text-mint transition cursor-pointer"
              >
                <span>Report Bug / Feedback</span>
              </button>
            </div>
          </div>

          {COLUMNS.map((col) => (
            <div key={col.title} className="space-y-3">
              <h3 className="text-[10px] font-mono uppercase tracking-[0.16em] text-muted">
                {col.title}
              </h3>
              <ul className="space-y-2">
                {col.links.map((l) => (
                  <li key={l.to}>
                    <Link
                      to={l.to}
                      className="text-xs text-muted hover:text-mint transition-colors"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-line">
          <div className="max-w-7xl mx-auto px-4 h-12 flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono text-muted">
            <div className="flex items-center gap-3">
              <span>MERIT — Make the merit list.</span>
              <span>·</span>
              <button
                type="button"
                onClick={() => setFeedbackOpen(true)}
                className="hover:text-mint transition-colors cursor-pointer underline underline-offset-4"
              >
                Report a bug
              </button>
            </div>
            <span>Algorithms, visualised.</span>
          </div>
        </div>
      </footer>
      <FeedbackModal isOpen={feedbackOpen} onClose={() => setFeedbackOpen(false)} />
    </>
  );
};
