import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  Clock,
  ExternalLink,
  Eye,
  EyeOff,
  FileText,
  History,
  Play,
  Shuffle,
  Trash2,
  Upload,
} from "lucide-react";
import {
  catalogIdForBaseUrl,
  getTutorSnapshot,
  loadTutorCatalog,
  useTutorKey,
} from "../../hooks/useTutorKey";
import {
  ApiError,
  InterviewDifficulty,
  InterviewSessionSummary,
  ResumeParseResponse,
  interviewApi,
} from "../../utils/api";
import { Problem } from "../../data/problems";
import { Panel } from "../ui/Panel";
import { InlineConfirm } from "../ui/InlineConfirm";
import { INTERVIEW_TIERS, TIER_BY_ID } from "./interviewConfig";

interface InterviewSetupLobbyProps {
  difficulty: InterviewDifficulty;
  onSelectDifficulty: (d: InterviewDifficulty) => void;
  selectedProblems: Problem[];
  onShuffleProblems: () => void;
  hideTitles: boolean;
  onToggleHideTitles: () => void;
  resumeData: ResumeParseResponse | null;
  onResumeParsed: (data: ResumeParseResponse | null) => void;
  projectBrief: string;
  onProjectBriefChange: (v: string) => void;
  onStartInterview: () => void;
  starting: boolean;
  startError: string | null;
  sessions: InterviewSessionSummary[];
  sessionsLoading: boolean;
  isAuthenticated: boolean;
  onResumeSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
}

const TIER_TONE: Record<InterviewDifficulty, string> = {
  easy: "border-mint/50 bg-mint/10 text-mint",
  medium: "border-violet/50 bg-violet/10 text-violet",
  hard: "border-amber/50 bg-amber/10 text-amber",
};

const TIER_DOT: Record<InterviewDifficulty, string> = {
  easy: "bg-mint",
  medium: "bg-violet",
  hard: "bg-amber",
};

export const InterviewSetupLobby: React.FC<InterviewSetupLobbyProps> = ({
  difficulty,
  onSelectDifficulty,
  selectedProblems,
  onShuffleProblems,
  hideTitles,
  onToggleHideTitles,
  resumeData,
  onResumeParsed,
  projectBrief,
  onProjectBriefChange,
  onStartInterview,
  starting,
  startError,
  sessions,
  sessionsLoading,
  isAuthenticated,
  onResumeSession,
  onDeleteSession,
}) => {
  const { apiKey, baseUrl, model, setModel } = useTutorKey();
  const [models, setModels] = useState<string[]>([]);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [resumeError, setResumeError] = useState<string | null>(null);
  const [showResumePreview, setShowResumePreview] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const hasCatalog = Boolean(catalogIdForBaseUrl(baseUrl));
  const modelOptions = model.trim() && !models.includes(model) ? [model, ...models] : models;

  useEffect(() => {
    const catalogId = catalogIdForBaseUrl(baseUrl);
    if (!catalogId) {
      setModels([]);
      return;
    }
    let cancelled = false;
    setCatalogError(null);
    void loadTutorCatalog(catalogId)
      .then((list) => {
        if (cancelled) return;
        setModels(list);
        if (list.length > 0 && !getTutorSnapshot().model.trim()) {
          setModel(list[0]);
        }
      })
      .catch(() => {
        if (!cancelled) setCatalogError("Could not load model catalog.");
      });
    return () => {
      cancelled = true;
    };
  }, [baseUrl]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setResumeError(null);
    setUploadingResume(true);
    try {
      const parsed = await interviewApi.parseResume(file);
      onResumeParsed(parsed);
      setShowResumePreview(false);
    } catch (err) {
      if (err instanceof ApiError) {
        setResumeError(err.message || "Could not parse PDF resume.");
      } else {
        setResumeError("Failed to upload resume. Is the API server running?");
      }
    } finally {
      setUploadingResume(false);
    }
  };

  const activeTier = TIER_BY_ID[difficulty];
  const canStart = Boolean(apiKey.trim() && model.trim() && selectedProblems.length > 0);

  return (
    <div className="space-y-8">
      {/* Header & BYOK Bar */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">
            Mock Interview
          </h1>
          <p className="text-xs text-muted mt-1">
            Timed CS theory, live coding & system design.
          </p>
        </div>

        <div className="w-full sm:w-auto flex flex-wrap items-center gap-2">
          {hasCatalog && modelOptions.length > 0 ? (
            <select
              aria-label="Interviewer Model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="min-w-[200px] px-3 py-2 rounded-lg bg-surface border border-line text-xs font-mono text-ink"
            >
              {modelOptions.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              aria-label="Interviewer Model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="Enter model id"
              className="min-w-[200px] px-3 py-2 rounded-lg bg-surface border border-line text-xs font-mono text-ink"
            />
          )}
          <Link
            to="/profile#tutor"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-line bg-surface text-xs font-mono text-violet hover:border-violet transition"
          >
            <span>Settings</span>
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>
      </div>

      {!apiKey.trim() && (
        <div
          role="status"
          className="p-4 rounded-xl border border-amber/40 bg-amber/10 flex flex-wrap items-center justify-between gap-3 text-xs font-mono"
        >
          <span className="text-ink">
            Configure a BYOK provider key (OpenAI, Gemini, or Groq) in Account Settings before
            starting an AI interview.
          </span>
          <Link
            to="/profile#tutor"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet text-canvas font-semibold"
          >
            <span>Configure Key</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {catalogError && <p className="text-xs font-mono text-amber">{catalogError}</p>}

      {/* Difficulty Tier Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {INTERVIEW_TIERS.map((tier) => {
          const selected = difficulty === tier.id;
          return (
            <button
              key={tier.id}
              type="button"
              aria-pressed={selected}
              onClick={() => onSelectDifficulty(tier.id)}
              className={`text-left p-4 rounded-xl border transition cursor-pointer flex flex-col justify-between space-y-3 ${
                selected
                  ? "border-violet bg-violet/10 shadow-sm"
                  : "border-line bg-surface hover:border-steel"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="inline-flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${TIER_DOT[tier.id]}`} aria-hidden="true" />
                  <span className="text-base font-bold text-ink">{tier.title}</span>
                </div>
                <span className="inline-flex items-center gap-1 text-[11px] font-mono text-muted">
                  <Clock className="w-3 h-3" />
                  {tier.durationLabel}
                </span>
              </div>
              <p className="text-xs text-muted">{tier.tagline}</p>
              <div className="pt-2 border-t border-line/60 text-[11px] font-mono text-muted">
                {tier.stages.length} rounds · /{tier.maxScore}
              </div>
            </button>
          );
        })}
      </div>

      {/* Problems & Context (optional) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <Panel
          label="Problems"
          className="lg:col-span-5"
          bracket
          action={
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onToggleHideTitles}
                className="inline-flex items-center gap-1 text-[10px] font-mono text-muted hover:text-ink cursor-pointer"
              >
                {hideTitles ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                <span>{hideTitles ? "Reveal titles" : "Hide titles"}</span>
              </button>
              <button
                type="button"
                onClick={onShuffleProblems}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-line bg-canvas text-[10px] font-mono text-mint hover:border-mint cursor-pointer"
              >
                <Shuffle className="w-3 h-3" />
                <span>Shuffle</span>
              </button>
            </div>
          }
        >
          <div className="space-y-2">
            {selectedProblems.map((p, idx) => (
              <div
                key={p.slug}
                className="p-2.5 rounded-lg border border-line bg-canvas flex items-center justify-between gap-2 text-xs font-mono"
              >
                <div className="font-semibold text-ink truncate">
                  <span className="text-muted mr-2">#{idx + 1}</span>
                  {hideTitles ? "Hidden problem" : p.title}
                </div>
                <span className="px-2 py-0.5 rounded border border-line bg-surface text-[10px] text-violet shrink-0">
                  {p.difficulty}
                </span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel label="Context (optional)" className="lg:col-span-7" bracket>
          <div className="space-y-3">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              aria-label="Upload CV PDF"
              onChange={(e) => void handleFileChange(e)}
              className="hidden"
            />
            {resumeData ? (
              <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-lg border border-mint/40 bg-mint/5 text-xs font-mono">
                <div className="flex items-center gap-2 text-ink min-w-0">
                  <FileText className="w-3.5 h-3.5 text-mint shrink-0" />
                  <span className="font-semibold text-mint truncate">{resumeData.filename}</span>
                  <span className="text-[10px] text-muted">({resumeData.pages}p)</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setShowResumePreview((v) => !v)}
                    className="text-[11px] text-violet hover:underline cursor-pointer"
                  >
                    {showResumePreview ? "Hide" : "Preview"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      onResumeParsed(null);
                      setShowResumePreview(false);
                    }}
                    className="text-[11px] text-rose hover:underline cursor-pointer"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-mono text-muted">Resume PDF · &le; 2 MB</span>
                <button
                  type="button"
                  disabled={uploadingResume}
                  onClick={() => fileInputRef.current?.click()}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-violet/40 bg-violet/10 text-violet font-mono text-xs font-semibold hover:bg-violet/20 disabled:opacity-50 cursor-pointer transition"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>{uploadingResume ? "Parsing PDF…" : "Upload PDF"}</span>
                </button>
              </div>
            )}

            {resumeError && (
              <p role="alert" className="text-xs font-mono text-rose">
                {resumeError}
              </p>
            )}

            {showResumePreview && resumeData && (
              <pre className="max-h-36 overflow-y-auto p-2.5 rounded bg-canvas border border-line text-[11px] font-mono text-muted whitespace-pre-wrap">
                {resumeData.extracted_text}
              </pre>
            )}

            <textarea
              rows={2}
              value={projectBrief}
              onChange={(e) => onProjectBriefChange(e.target.value)}
              placeholder="Project or stack notes (optional)…"
              className="w-full p-2.5 rounded-lg bg-canvas border border-line text-xs font-mono text-ink placeholder-muted focus:border-violet"
            />
          </div>
        </Panel>
      </div>

      {/* Start Action Strip */}
      <div className="flex flex-wrap items-center justify-end gap-3 pt-2">
        {startError && (
          <p role="alert" className="text-xs font-mono text-rose mr-auto">
            {startError}
          </p>
        )}
        <div className="flex items-center gap-2 text-xs font-mono text-muted">
          <span>
            {activeTier.title} · {activeTier.durationLabel} · {selectedProblems.length}{" "}
            {selectedProblems.length === 1 ? "problem" : "problems"}
          </span>
          {resumeData && (
            <span className="px-1.5 py-0.5 rounded border border-mint/40 bg-mint/10 text-mint text-[10px]">
              CV
            </span>
          )}
        </div>
        <button
          type="button"
          disabled={!canStart || starting}
          onClick={onStartInterview}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-violet text-canvas font-mono font-semibold text-xs hover:brightness-110 disabled:opacity-50 cursor-pointer transition shadow-sm"
        >
          <Play className="w-3.5 h-3.5" />
          <span>{starting ? "Starting Interview…" : `Start ${activeTier.durationLabel} Interview`}</span>
        </button>
      </div>

      {/* Past Interviews (DB History) */}
      <Panel label="History" bracket>
        {!isAuthenticated ? (
          <div className="flex flex-wrap items-center justify-between gap-3 py-2 text-xs font-mono text-muted">
            <span>Sign in to save interview transcripts and scorecards across devices.</span>
            <Link
              to="/login?next=/interview"
              className="px-3 py-1.5 rounded-lg border border-mint/40 bg-mint/10 text-mint font-semibold hover:bg-mint/20 transition"
            >
              Sign In
            </Link>
          </div>
        ) : sessionsLoading ? (
          <p className="text-xs font-mono text-muted py-2">Loading past interview sessions…</p>
        ) : sessions.length === 0 ? (
          <div className="flex items-center gap-2 py-2 text-xs font-mono text-muted">
            <History className="w-4 h-4" />
            <span>No saved interviews yet.</span>
          </div>
        ) : (
          <div className="divide-y divide-line">
            {sessions.map((s) => (
              <div
                key={s.id}
                className="py-2.5 first:pt-0 last:pb-0 flex flex-wrap items-center justify-between gap-3 text-xs font-mono"
              >
                <div className="flex flex-wrap items-center gap-2 min-w-0">
                  <span
                    className={`px-2 py-0.5 rounded border text-[10px] uppercase font-bold shrink-0 ${TIER_TONE[s.difficulty]}`}
                  >
                    {s.difficulty}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] uppercase shrink-0 ${
                      s.status === "completed"
                        ? "bg-mint/15 text-mint"
                        : "bg-surface border border-line text-muted"
                    }`}
                  >
                    {s.status === "completed" ? "Completed" : s.current_stage}
                  </span>
                  {s.overall_verdict && (
                    <span className="font-semibold text-ink shrink-0">
                      {s.overall_verdict} ({s.overall_score}/{s.max_score})
                    </span>
                  )}
                  {s.has_resume && s.resume_filename && (
                    <span className="text-[10px] text-violet truncate max-w-[160px] hidden sm:inline">
                      CV: {s.resume_filename}
                    </span>
                  )}
                  <span className="text-[11px] text-muted truncate hidden md:inline">
                    {new Date(s.updated_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={() => onResumeSession(s.id)}
                    className="px-3 py-1 rounded-lg border border-violet/40 bg-violet/10 text-violet hover:bg-violet/20 font-semibold cursor-pointer transition text-xs"
                  >
                    {s.status === "completed" ? "View Scorecard" : "Resume"}
                  </button>
                  {confirmDeleteId === s.id ? (
                    <InlineConfirm
                      title="Delete this interview session?"
                      confirmLabel="Delete"
                      cancelLabel="Cancel"
                      onConfirm={() => {
                        setConfirmDeleteId(null);
                        onDeleteSession(s.id);
                      }}
                      onCancel={() => setConfirmDeleteId(null)}
                    />
                  ) : (
                    <button
                      type="button"
                      aria-label={`Delete ${s.difficulty} interview`}
                      onClick={() => setConfirmDeleteId(s.id)}
                      className="p-1 rounded-lg border border-line bg-canvas text-muted hover:text-rose hover:border-rose/40 cursor-pointer transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
};
