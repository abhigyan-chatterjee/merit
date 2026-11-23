import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../store/AuthContext';
import { ReviewDeck } from '../components/ReviewDeck';

export const ReviewPage: React.FC = () => {
  const { user, isLoading: authLoading } = useAuth();

  if (!authLoading && !user) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-[10px] font-mono text-muted">
          <Link to="/dashboard" className="text-mint hover:underline">dashboard</Link>
          <span>/</span>
          <span className="text-ink">review</span>
        </nav>
        <div className="p-8 rounded-xl border border-line bg-surface text-center space-y-3">
          <h1 className="text-lg font-bold text-ink">Spaced Review Deck</h1>
          <p className="text-xs text-muted">Sign in to review items due today.</p>
          <Link
            to="/login?next=%2Freview"
            className="inline-block px-4 py-2 rounded-lg bg-mint text-canvas text-xs font-semibold hover:brightness-110 transition"
          >
            Sign in to review
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-[10px] font-mono text-muted">
        <Link to="/dashboard" className="text-mint hover:underline">dashboard</Link>
        <span>/</span>
        <span className="text-ink">review</span>
      </nav>
      <h1 className="text-2xl font-bold tracking-tight text-ink">Spaced Review Deck</h1>
      <ReviewDeck />
    </div>
  );
};
