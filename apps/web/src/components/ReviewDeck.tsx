import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { RotateCcw, RefreshCw } from 'lucide-react';
import { revisionApi, ScheduledReview } from '../utils/api';
import { useProgress } from '../store/ProgressContext';

export const ReviewDeck: React.FC = () => {
  const { setDueTodayCount } = useProgress();
  const [items, setItems] = useState<ScheduledReview[]>([]);
  const [total, setTotal] = useState(0);
  const [done, setDone] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [isRating, setIsRating] = useState(false);

  const loadDue = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const res = await revisionApi.getDue(50);
      setItems(res.items || []);
      setTotal((res.items || []).length);
      setDone(0);
      setRevealed(false);
      setDueTodayCount(res.count);
    } catch {
      setLoadError('Could not load due reviews. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [setDueTodayCount]);

  useEffect(() => {
    void loadDue();
  }, [loadDue, reloadKey]);

  const rate = async (grade: number) => {
    const current = items[0];
    if (!current || isRating) return;
    setIsRating(true);
    try {
      await revisionApi.review(current.item_type, current.item_id, grade);
      setItems((prev) => prev.slice(1));
      setDone((d) => d + 1);
      setDueTodayCount((c) => Math.max(0, c - 1));
      setRevealed(false);
    } catch {
      // Keep the card in place; the next attempt retries the rating.
    } finally {
      setIsRating(false);
    }
  };

  if (isLoading) {
    return (
      <div role="status" className="p-8 rounded-xl border border-line bg-surface text-center space-y-3">
        <RefreshCw className="w-6 h-6 text-mint animate-spin mx-auto" />
        <p className="text-xs text-muted">Loading due reviews…</p>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="p-8 rounded-xl border border-rose/40 bg-rose/10 text-center space-y-3">
        <p role="alert" className="text-sm text-rose">{loadError}</p>
        <button
          type="button"
          onClick={() => setReloadKey((k) => k + 1)}
          className="px-4 py-2 rounded-lg bg-mint text-canvas text-xs font-semibold hover:brightness-110 transition cursor-pointer"
        >
          Retry
        </button>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="p-8 rounded-xl border border-line bg-surface text-center space-y-3">
        <RotateCcw className="w-6 h-6 text-mint mx-auto" />
        <h2 className="text-base font-bold text-ink">All caught up for today!</h2>
        <p className="text-xs text-muted">No more reviews due. Keep the streak going.</p>
        <div className="flex items-center justify-center gap-3">
          <Link to="/dashboard" className="px-4 py-2 rounded-lg bg-mint text-canvas text-xs font-semibold hover:brightness-110 transition">
            Dashboard
          </Link>
          <Link to="/problems" className="px-4 py-2 rounded-lg border border-line bg-canvas text-xs font-mono text-ink hover:border-mint transition">
            Problems
          </Link>
        </div>
      </div>
    );
  }

  const current = items[0];
  const fallbackLink =
    current.link ||
    (current.item_type === 'problem' ? `/problems/${current.topic}/${current.item_id}` : `/quiz/${current.topic}`);
  const typeLabel = current.item_type === 'problem' ? 'PROBLEM' : 'CONCEPT';

  return (
    <div className="p-6 rounded-xl border border-line bg-surface space-y-4">
      <div className="flex items-center justify-between gap-3 text-[11px] font-mono text-muted">
        <span>Card {done + 1} of {total}</span>
        <span className="px-1.5 py-0.5 rounded border border-amber/40 text-amber">SM-2</span>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <span className="px-2 py-0.5 rounded border border-line text-[10px] font-mono font-semibold text-ink">{typeLabel}</span>
        <span className="px-2 py-0.5 rounded-full bg-violet/10 border border-violet/30 text-[10px] font-mono text-violet">{current.topic}</span>
        {current.difficulty && (
          <span className="px-2 py-0.5 rounded-full bg-canvas border border-line text-[10px] font-mono text-muted">{current.difficulty}</span>
        )}
        <span className="text-[10px] font-mono text-muted">reps {current.reps} · every {current.interval_days}d</span>
      </div>
      <h2 className="text-base font-bold text-ink">{current.title}</h2>
      <p className="text-xs text-muted leading-relaxed">
        {current.prompt && current.prompt.trim().length > 0
          ? current.prompt.slice(0, 400)
          : 'Open the full item for context, then rate your recall.'}
      </p>
      <Link to={fallbackLink} className="inline-block text-xs font-mono text-mint hover:underline">
        Open full item →
      </Link>
      {!revealed ? (
        <button
          type="button"
          onClick={() => setRevealed(true)}
          className="block px-4 py-2 rounded-lg bg-mint text-canvas text-xs font-semibold hover:brightness-110 transition cursor-pointer"
        >
          Reveal Answer
        </button>
      ) : (
        <div className="space-y-3">
          <div className="p-4 rounded-lg border border-violet/40 bg-violet/10 text-xs leading-relaxed text-ink">
            {current.answer_summary && current.answer_summary.trim().length > 0
              ? current.answer_summary
              : 'No summary is stored for this item yet — open the full item to review it, then rate your recall.'}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <button
              type="button"
              disabled={isRating}
              onClick={() => void rate(1)}
              className="px-3 py-2 rounded-lg border border-rose/40 text-rose text-xs font-semibold hover:bg-rose/10 transition disabled:opacity-40 cursor-pointer"
            >
              Again
              <span className="block text-[10px] font-mono font-normal opacity-80">Resets to 1d</span>
            </button>
            <button
              type="button"
              disabled={isRating}
              onClick={() => void rate(3)}
              className="px-3 py-2 rounded-lg border border-amber/40 text-amber text-xs font-semibold hover:bg-amber/10 transition disabled:opacity-40 cursor-pointer"
            >
              Hard
            </button>
            <button
              type="button"
              disabled={isRating}
              onClick={() => void rate(4)}
              className="px-3 py-2 rounded-lg border border-mint/40 text-mint text-xs font-semibold hover:bg-mint/10 transition disabled:opacity-40 cursor-pointer"
            >
              Good
            </button>
            <button
              type="button"
              disabled={isRating}
              onClick={() => void rate(5)}
              className="px-3 py-2 rounded-lg border border-violet/40 text-violet text-xs font-semibold hover:bg-violet/10 transition disabled:opacity-40 cursor-pointer"
            >
              Easy
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
