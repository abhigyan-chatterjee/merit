import React, { useState, useEffect } from 'react';
import { Bug, X, Send, CheckCircle2, Loader2, ExternalLink } from 'lucide-react';

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultProblemSlug?: string;
  defaultCategory?: 'bug' | 'testcase' | 'feature' | 'other';
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  isOpen,
  onClose,
  defaultProblemSlug,
  defaultCategory = 'bug',
}) => {
  const [category, setCategory] = useState<'bug' | 'testcase' | 'feature' | 'other'>(defaultCategory);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [email, setEmail] = useState('');
  const [problemSlug, setProblemSlug] = useState(defaultProblemSlug || '');
  const [pageUrl, setPageUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successData, setSuccessData] = useState<{ message: string; issueUrl?: string } | null>(null);

  useEffect(() => {
    if (isOpen) {
      setPageUrl(window.location.href);
      if (defaultProblemSlug) {
        setProblemSlug(defaultProblemSlug);
      } else {
        // Auto-detect problem slug from URL if on problem detail page
        const match = window.location.pathname.match(/\/problems\/([^/?#]+)/);
        if (match && match[1] && !['arrays-hashing', 'two-pointers', 'sliding-window', 'stack', 'binary-search', 'linked-list', 'trees', 'tries', 'heap-priority-queue', 'backtracking', 'graphs', 'advanced-graphs', '1d-dynamic-programming', '2d-dynamic-programming', 'greedy', 'intervals', 'math-geometry', 'bit-manipulation'].includes(match[1])) {
          setProblemSlug(match[1]);
        }
      }
      setErrorMsg(null);
      setSuccessData(null);
    }
  }, [isOpen, defaultProblemSlug]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (title.trim().length < 3) {
      setErrorMsg('Title must be at least 3 characters.');
      return;
    }
    if (description.trim().length < 5) {
      setErrorMsg('Description must be at least 5 characters.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const res = await fetch('/api/v1/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title.trim(),
          description: description.trim(),
          category,
          page_url: pageUrl || undefined,
          problem_slug: problemSlug.trim() || undefined,
          email: email.trim() || undefined,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Failed to submit feedback. Please try again.');
      }

      const data = await res.json();
      setSuccessData({
        message: data.message || 'Feedback submitted successfully!',
        issueUrl: data.issue_url || undefined,
      });
      setTitle('');
      setDescription('');
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'An error occurred while submitting.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="feedback-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150"
    >
      <div
        className="w-full max-w-lg rounded-2xl border border-line bg-surface shadow-2xl p-6 relative overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-line">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg border border-line bg-canvas grid place-items-center text-mint">
              <Bug className="w-4 h-4" />
            </div>
            <div>
              <h2 id="feedback-modal-title" className="text-sm font-bold text-ink">
                Feedback & Bug Report
              </h2>
              <p className="text-[11px] text-muted">
                Report test case edge cases, visual bugs, or suggest improvements.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="p-1 rounded-lg text-muted hover:text-ink hover:bg-canvas transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        {successData ? (
          <div className="py-8 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-mint/10 border border-mint/30 grid place-items-center text-mint mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-ink">Thank you for your report!</h3>
              <p className="text-xs text-muted max-w-xs mx-auto">
                {successData.message}
              </p>
            </div>
            {successData.issueUrl && (
              <a
                href={successData.issueUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-mono text-mint hover:underline"
              >
                <span>View tracked issue on GitHub</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
            <div className="pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-5 py-2 rounded-xl bg-mint text-canvas text-xs font-semibold hover:brightness-110 transition cursor-pointer"
              >
                Done
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-4 space-y-4">
            {errorMsg && (
              <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-xs text-red-400">
                {errorMsg}
              </div>
            )}

            {/* Category selection */}
            <div>
              <label className="block text-[11px] font-mono text-muted uppercase tracking-wider mb-1.5">
                Feedback Type
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
                {[
                  { id: 'bug', label: 'Bug' },
                  { id: 'testcase', label: 'Test Case' },
                  { id: 'feature', label: 'Feature' },
                  { id: 'other', label: 'General' },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setCategory(item.id as any)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition cursor-pointer text-center ${
                      category === item.id
                        ? 'bg-mint text-canvas border-mint font-semibold'
                        : 'bg-canvas text-muted border-line hover:text-ink'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Title */}
            <div>
              <label className="block text-[11px] font-mono text-muted uppercase tracking-wider mb-1.5">
                Summary / Title <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Empty input test case causes crash in Two Sum"
                maxLength={150}
                required
                className="w-full px-3 py-2 rounded-xl bg-canvas border border-line text-xs text-ink placeholder:text-muted/60 focus:outline-none focus:border-mint"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-[11px] font-mono text-muted uppercase tracking-wider mb-1.5">
                Details <span className="text-red-400">*</span>
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Provide steps to reproduce or details on what needs fixing..."
                rows={4}
                required
                className="w-full px-3 py-2 rounded-xl bg-canvas border border-line text-xs text-ink placeholder:text-muted/60 focus:outline-none focus:border-mint resize-none"
              />
            </div>

            {/* Context & Email in 2 cols */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-mono text-muted uppercase tracking-wider mb-1.5">
                  Problem Context (Optional)
                </label>
                <input
                  type="text"
                  value={problemSlug}
                  onChange={(e) => setProblemSlug(e.target.value)}
                  placeholder="e.g. two-sum"
                  className="w-full px-3 py-1.5 rounded-lg bg-canvas border border-line text-xs font-mono text-ink placeholder:text-muted/60 focus:outline-none focus:border-mint"
                />
              </div>
              <div>
                <label className="block text-[11px] font-mono text-muted uppercase tracking-wider mb-1.5">
                  Your Email (Optional)
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="for follow-up"
                  className="w-full px-3 py-1.5 rounded-lg bg-canvas border border-line text-xs text-ink placeholder:text-muted/60 focus:outline-none focus:border-mint"
                />
              </div>
            </div>

            {/* Submit button */}
            <div className="pt-2 flex items-center justify-end gap-2 border-t border-line">
              <button
                type="button"
                onClick={onClose}
                className="px-3.5 py-1.5 rounded-lg text-xs text-muted hover:text-ink transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-mint text-canvas text-xs font-semibold hover:brightness-110 disabled:opacity-50 transition cursor-pointer"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Submitting…</span>
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    <span>Submit Report</span>
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
