import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Shield,
  CheckCircle,
  XCircle,
  Layers,
  BarChart3,
  ListChecks,
  AlertTriangle,
  RefreshCw,
  Clock,
  MessageSquare,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../store/AuthContext';
import { adminApi, AdminStats, AdminFeedbackItem } from '../utils/api';

export const AdminPage: React.FC = () => {
  const { user, isLoading: authLoading } = useAuth();

  const [activeTab, setActiveTab] = useState<'stats' | 'feedback' | 'queue' | 'coverage' | 'audit'>('stats');
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [feedbacks, setFeedbacks] = useState<AdminFeedbackItem[]>([]);
  const [feedbackFilter, setFeedbackFilter] = useState<'all' | 'open' | 'resolved' | 'dismissed'>('all');
  const [queue, setQueue] = useState<any[]>([]);
  const [queueType, setQueueType] = useState<'questions' | 'problems'>('questions');
  const [coverage, setCoverage] = useState<{ matrix: Record<string, Record<string, number>>; total_verified: number } | null>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setActionSuccess(null);
    try {
      if (activeTab === 'stats') {
        const data = await adminApi.getStats();
        setStats(data);
      } else if (activeTab === 'feedback') {
        const data = await adminApi.getFeedbacks(feedbackFilter === 'all' ? undefined : feedbackFilter);
        setFeedbacks(data);
      } else if (activeTab === 'queue') {
        const data = await adminApi.getReviewQueue(queueType);
        setQueue(data);
      } else if (activeTab === 'coverage') {
        const data = await adminApi.getCoverage();
        setCoverage(data);
      } else if (activeTab === 'audit') {
        const data = await adminApi.getAuditLogs();
        setAuditLogs(data);
      }
    } catch (err: any) {
      console.error('Failed to load admin data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedbackStatus = async (id: string, newStatus: 'open' | 'resolved' | 'dismissed') => {
    try {
      await adminApi.updateFeedbackStatus(id, newStatus);
      setActionSuccess(`Feedback status updated to ${newStatus}!`);
      const data = await adminApi.getFeedbacks(feedbackFilter === 'all' ? undefined : feedbackFilter);
      setFeedbacks(data);
    } catch (err: any) {
      alert(`Failed to update status: ${err.message}`);
    }
  };

  const handleReviewQuestion = async (id: string, action: 'approved' | 'rejected') => {
    try {
      await adminApi.reviewQuestion(id, action, `Reviewed by ${user?.display_name || 'admin'}`);
      setActionSuccess(`Question successfully ${action}!`);
      // Refresh review queue
      const data = await adminApi.getReviewQueue(queueType);
      setQueue(data);
    } catch (err: any) {
      alert(`Action failed: ${err.message}`);
    }
  };

  const handleReviewProblem = async (slug: string, action: 'approved' | 'rejected') => {
    try {
      await adminApi.reviewProblem(slug, action, `Reviewed by ${user?.display_name || 'admin'}`);
      setActionSuccess(`Problem ${slug} successfully ${action}!`);
      const data = await adminApi.getReviewQueue(queueType);
      setQueue(data);
    } catch (err: any) {
      alert(`Action failed: ${err.message}`);
    }
  };

  useEffect(() => {
    if (user?.role === 'admin') {
      void loadData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, activeTab, queueType, feedbackFilter]);

  if (authLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <RefreshCw className="w-8 h-8 text-mint animate-spin mx-auto mb-3" />
        <p className="text-xs font-mono text-muted">Checking administrative authorization...</p>
      </div>
    );
  }

  if (!user || user.role !== 'admin') {
    return (
      <div className="max-w-md mx-auto px-4 py-20 text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-rose/10 border border-rose/20 grid place-items-center text-rose mx-auto">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h1 className="text-lg font-bold text-ink">Administrative Privileges Required</h1>
        <p className="text-xs text-muted leading-relaxed">
          The content moderation, coverage matrix, and system aggregate consoles are restricted to designated administrator accounts.
        </p>
        <div className="pt-2">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-surface border border-line text-xs font-semibold text-ink hover:border-mint transition"
          >
            Return to Learning Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Admin Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-line">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-mint/15 text-mint border border-mint/30">
            <Shield className="w-3 h-3" />
            Verified Content Console
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Admin Control Center</h1>
          <p className="text-xs text-muted">
            Logged in as <span className="font-mono text-ink font-semibold">{user.email}</span> ({user.role})
          </p>
        </div>

        <button
          onClick={loadData}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-line bg-surface text-xs font-mono text-muted hover:text-ink transition cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh Data
        </button>
      </div>

      {actionSuccess && (
        <div className="p-3.5 rounded-xl bg-mint/10 border border-mint/30 text-xs font-mono text-mint flex items-center gap-2">
          <CheckCircle className="w-4 h-4" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-line pb-2">
        {[
          { id: 'stats', label: 'Aggregate Stats', icon: BarChart3 },
          { id: 'feedback', label: 'User Feedback', icon: MessageSquare },
          { id: 'queue', label: 'Review Queue', icon: ListChecks },
          { id: 'coverage', label: 'Coverage Matrix', icon: Layers },
          { id: 'audit', label: 'Audit Logs', icon: Clock },
        ].map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition cursor-pointer ${
                active
                  ? 'bg-mint text-canvas shadow-sm'
                  : 'bg-surface text-muted border border-line hover:text-ink'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab 1: Stats */}
      {activeTab === 'stats' && stats && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-xl border border-line bg-surface">
              <div className="text-[10px] font-mono text-muted uppercase">Registered Users</div>
              <div className="text-3xl font-bold font-mono text-ink mt-1">{stats.users_count}</div>
            </div>
            <div className="p-5 rounded-xl border border-line bg-surface">
              <div className="text-[10px] font-mono text-muted uppercase">Total Submissions</div>
              <div className="text-3xl font-bold font-mono text-violet mt-1">
                {stats.total_submissions}
              </div>
              <div className="text-[10px] font-mono text-mint mt-1">
                AC Rate: {stats.ac_rate_pct}% ({stats.ac_submissions} AC)
              </div>
            </div>
            <div className="p-5 rounded-xl border border-line bg-surface">
              <div className="text-[10px] font-mono text-muted uppercase">Verified Questions</div>
              <div className="text-3xl font-bold font-mono text-mint mt-1">
                {stats.verified_questions}
              </div>
              <div className="text-[10px] font-mono text-muted mt-1">
                {stats.draft_questions} pending review
              </div>
            </div>
            <div className="p-5 rounded-xl border border-line bg-surface">
              <div className="text-[10px] font-mono text-muted uppercase">Quiz Attempts</div>
              <div className="text-3xl font-bold font-mono text-amber mt-1">
                {stats.total_quiz_attempts}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Feedback */}
      {activeTab === 'feedback' && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              {(['all', 'open', 'resolved', 'dismissed'] as const).map((filter) => (
                <button
                  key={filter}
                  onClick={() => setFeedbackFilter(filter)}
                  className={`px-3 py-1 rounded-md text-xs font-mono capitalize transition cursor-pointer ${
                    feedbackFilter === filter
                      ? 'bg-mint text-canvas font-semibold'
                      : 'bg-surface text-muted border border-line hover:text-ink'
                  }`}
                >
                  {filter}
                </button>
              ))}
            </div>
            <div className="text-xs font-mono text-muted">
              {feedbacks.length} reports {feedbackFilter !== 'all' ? `(${feedbackFilter})` : ''}
            </div>
          </div>

          {feedbacks.length === 0 ? (
            <div className="p-8 text-center rounded-xl border border-line bg-surface text-muted text-xs font-mono">
              No feedback submissions found in this view.
            </div>
          ) : (
            <div className="space-y-3">
              {feedbacks.map((item) => (
                <div key={item.id} className="p-4 rounded-xl border border-line bg-surface space-y-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase ${
                            item.category === 'bug'
                              ? 'bg-red-500/15 text-red-400 border border-red-500/30'
                              : item.category === 'testcase'
                              ? 'bg-amber/15 text-amber border border-amber/30'
                              : item.category === 'feature'
                              ? 'bg-mint/15 text-mint border border-mint/30'
                              : 'bg-surface text-muted border border-line'
                          }`}
                        >
                          {item.category}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold capitalize ${
                            item.status === 'open'
                              ? 'bg-amber/15 text-amber'
                              : item.status === 'resolved'
                              ? 'bg-mint/15 text-mint'
                              : 'bg-surface text-muted'
                          }`}
                        >
                          {item.status}
                        </span>
                        <span className="text-[10px] font-mono text-muted">
                          {new Date(item.created_at).toLocaleString()}
                        </span>
                      </div>
                      <h3 className="text-sm font-bold text-ink">{item.title}</h3>
                    </div>

                    <div className="flex items-center gap-2">
                      {item.github_issue_url && (
                        <a
                          href={item.github_issue_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-mono text-mint border border-mint/30 bg-mint/10 hover:bg-mint/20 transition"
                        >
                          <span>Issue #{item.github_issue_number}</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                      {item.status === 'open' ? (
                        <>
                          <button
                            onClick={() => handleFeedbackStatus(item.id, 'resolved')}
                            className="px-2.5 py-1 rounded-md text-xs font-mono bg-mint text-canvas font-semibold hover:bg-mint/90 transition cursor-pointer"
                          >
                            Resolve
                          </button>
                          <button
                            onClick={() => handleFeedbackStatus(item.id, 'dismissed')}
                            className="px-2.5 py-1 rounded-md text-xs font-mono bg-surface text-muted border border-line hover:text-ink transition cursor-pointer"
                          >
                            Dismiss
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => handleFeedbackStatus(item.id, 'open')}
                          className="px-2.5 py-1 rounded-md text-xs font-mono bg-surface text-muted border border-line hover:text-ink transition cursor-pointer"
                        >
                          Reopen
                        </button>
                      )}
                    </div>
                  </div>

                  <p className="text-xs text-muted leading-relaxed whitespace-pre-wrap bg-canvas p-3 rounded-lg border border-line font-mono">
                    {item.description}
                  </p>

                  {(item.problem_slug || item.page_url || item.email) && (
                    <div className="flex flex-wrap items-center gap-3 text-[10px] font-mono text-muted pt-1">
                      {item.problem_slug && (
                        <span>
                          Problem: <span className="text-ink font-semibold">{item.problem_slug}</span>
                        </span>
                      )}
                      {item.page_url && (
                        <span className="truncate max-w-xs">
                          URL: <span className="text-ink">{item.page_url}</span>
                        </span>
                      )}
                      {item.email && (
                        <span>
                          Submitter: <span className="text-mint">{item.email}</span>
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Review Queue */}
      {activeTab === 'queue' && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setQueueType('questions')}
              className={`px-3 py-1 rounded-md text-xs font-mono transition cursor-pointer ${
                queueType === 'questions'
                  ? 'bg-violet text-canvas font-semibold'
                  : 'bg-surface text-muted border border-line'
              }`}
            >
              Draft Questions ({queueType === 'questions' ? queue.length : '...'})
            </button>
            <button
              onClick={() => setQueueType('problems')}
              className={`px-3 py-1 rounded-md text-xs font-mono transition cursor-pointer ${
                queueType === 'problems'
                  ? 'bg-violet text-canvas font-semibold'
                  : 'bg-surface text-muted border border-line'
              }`}
            >
              Draft Problems ({queueType === 'problems' ? queue.length : '...'})
            </button>
          </div>

          {queue.length === 0 ? (
            <div className="p-12 rounded-xl border border-dashed border-line bg-surface text-center space-y-2">
              <CheckCircle className="w-8 h-8 text-mint mx-auto" />
              <h3 className="text-sm font-semibold text-ink">Review Queue Clear</h3>
              <p className="text-xs text-muted">
                All {queueType} in the repository are currently verified and published.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {queue.map((item) => (
                <div
                  key={item.id || item.slug}
                  className="p-5 rounded-xl border border-line bg-surface space-y-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-canvas border border-line font-mono text-[10px] uppercase text-violet">
                        {item.topic}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-canvas border border-line font-mono text-[10px] uppercase text-muted">
                        {item.difficulty}
                      </span>
                      {item.source && (
                        <span className="font-mono text-[10px] text-muted">
                          Source: {item.source}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() =>
                          queueType === 'questions'
                            ? handleReviewQuestion(item.id, 'approved')
                            : handleReviewProblem(item.slug, 'approved')
                        }
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-mint text-canvas font-semibold text-xs hover:brightness-110 transition cursor-pointer"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        Approve & Verify
                      </button>
                      <button
                        onClick={() =>
                          queueType === 'questions'
                            ? handleReviewQuestion(item.id, 'rejected')
                            : handleReviewProblem(item.slug, 'rejected')
                        }
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose/40 bg-rose/10 text-rose font-semibold text-xs hover:bg-rose/20 transition cursor-pointer"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        Reject
                      </button>
                    </div>
                  </div>

                  <h3 className="text-sm font-semibold text-ink">
                    {item.prompt || item.title}
                  </h3>

                  {item.options && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2">
                      {item.options.map((opt: string, oIdx: number) => (
                        <div
                          key={oIdx}
                          className={`p-2.5 rounded-lg border text-xs font-mono flex items-center gap-2 ${
                            oIdx === item.correct_index
                              ? 'border-mint bg-mint/10 text-mint font-semibold'
                              : 'border-line bg-canvas text-ink'
                          }`}
                        >
                          <span className="w-5 h-5 rounded-full border border-current grid place-items-center text-[10px] shrink-0">
                            {String.fromCharCode(65 + oIdx)}
                          </span>
                          <span className="truncate">{opt}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {item.explanation && (
                    <div className="p-3 rounded-lg bg-canvas border border-line text-xs space-y-1">
                      <span className="font-mono text-[10px] text-muted uppercase">Explanation:</span>
                      <p className="text-ink leading-relaxed">{item.explanation}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Coverage Matrix */}
      {activeTab === 'coverage' && coverage && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-ink uppercase tracking-wider">
              Topic × Difficulty Coverage ({coverage.total_verified} Verified Total)
            </h3>
          </div>

          <div className="overflow-x-auto rounded-xl border border-line bg-surface">
            <table className="w-full text-left border-collapse text-xs font-mono">
              <thead>
                <tr className="border-b border-line bg-canvas text-muted uppercase text-[10px]">
                  <th className="p-3.5">Topic</th>
                  <th className="p-3.5 text-center">Easy</th>
                  <th className="p-3.5 text-center">Medium</th>
                  <th className="p-3.5 text-center">Hard</th>
                  <th className="p-3.5 text-right font-bold text-ink">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line text-ink">
                {Object.entries(coverage.matrix).map(([topic, counts]) => (
                  <tr key={topic} className="hover:bg-canvas/50 transition">
                    <td className="p-3.5 font-semibold capitalize">{topic}</td>
                    <td className="p-3.5 text-center text-mint font-medium">{counts.easy}</td>
                    <td className="p-3.5 text-center text-violet font-medium">{counts.medium}</td>
                    <td className="p-3.5 text-center text-amber font-medium">{counts.hard}</td>
                    <td className="p-3.5 text-right font-bold text-ink">{counts.total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Audit Logs */}
      {activeTab === 'audit' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-ink uppercase tracking-wider">
              Administrative Audit Log (Tamper-evident trail)
            </h3>
          </div>

          <div className="overflow-x-auto rounded-xl border border-line bg-surface">
            <table className="w-full text-left border-collapse text-xs font-mono">
              <thead>
                <tr className="border-b border-line bg-canvas text-muted uppercase text-[10px]">
                  <th className="p-3">Timestamp</th>
                  <th className="p-3">Action</th>
                  <th className="p-3">Target</th>
                  <th className="p-3">Admin ID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line text-ink">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-canvas/50 transition">
                    <td className="p-3 text-muted">{new Date(log.created_at).toLocaleString()}</td>
                    <td className="p-3 font-semibold text-mint">{log.action}</td>
                    <td className="p-3 text-ink truncate max-w-xs">{log.target}</td>
                    <td className="p-3 text-muted text-[10px]">{log.admin_id.slice(0, 8)}...</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
