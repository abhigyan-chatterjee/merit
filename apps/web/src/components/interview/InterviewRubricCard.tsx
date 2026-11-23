import React, { useState } from "react";
import { RotateCcw, Sparkles } from "lucide-react";
import { InterviewSessionDetail } from "../../utils/api";
import { formatRubricMarkdown } from "./interviewConfig";

interface InterviewRubricCardProps {
  session: InterviewSessionDetail;
  onBackToLobby: () => void;
  onStartNew: () => void;
  showTranscript?: boolean;
  onToggleTranscript?: () => void;
}

const VERDICT_STYLE: Record<string, string> = {
  "Strong Hire": "border-mint/50 bg-mint/15 text-mint",
  Hire: "border-mint/40 bg-mint/10 text-mint",
  "Leaning Hire": "border-amber/40 bg-amber/10 text-amber",
  "No Hire": "border-rose/40 bg-rose/10 text-rose",
};

export const InterviewRubricCard: React.FC<InterviewRubricCardProps> = ({
  session,
  onBackToLobby,
  onStartNew,
  showTranscript = false,
  onToggleTranscript,
}) => {
  const [copied, setCopied] = useState(false);
  const rubric = session.rubric;

  if (!rubric) return null;

  const handleCopy = async () => {
    const text = formatRubricMarkdown(session);
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
      } catch {
        // best effort
      }
      document.body.removeChild(ta);
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  return (
    <div className="rounded-xl border border-line bg-surface p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-line">
        <h2 className="text-xl font-bold text-ink">Scorecard · {rubric.total}/{rubric.max_total}</h2>
        <span
          data-testid="rubric-verdict"
          className={`px-3 py-1.5 rounded-lg border font-mono text-xs font-bold ${
            VERDICT_STYLE[rubric.verdict] ?? "border-line bg-canvas text-ink"
          }`}
        >
          {rubric.verdict}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {rubric.dimensions.map((dim) => {
          const pct = dim.max_score > 0 ? Math.round((dim.score / dim.max_score) * 100) : 0;
          const barTone =
            pct >= 80 ? "bg-mint" : pct >= 60 ? "bg-violet" : pct >= 40 ? "bg-amber" : "bg-rose";
          return (
            <div key={dim.name} className="p-3.5 rounded-lg border border-line bg-canvas space-y-2">
              <div className="flex items-center justify-between gap-2 text-xs font-mono">
                <span className="font-semibold text-ink">{dim.name}</span>
                <span className="font-bold text-ink tnum">
                  {dim.score}/{dim.max_score}
                </span>
              </div>
              <div className="h-1.5 rounded-full bg-surface overflow-hidden">
                <div className={`h-full ${barTone}`} style={{ width: `${pct}%` }} />
              </div>
              <p className="text-xs text-muted leading-relaxed">{dim.comment}</p>
            </div>
          );
        })}
      </div>

      {(rubric.strengths.length > 0 || rubric.improvements.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {rubric.strengths.length > 0 && (
            <div className="p-4 rounded-lg border border-mint/30 bg-mint/5 space-y-2">
              <h3 className="text-xs font-mono font-semibold text-mint uppercase tracking-wider">
                Key Strengths
              </h3>
              <ul className="list-disc list-inside space-y-1 text-xs text-ink">
                {rubric.strengths.map((s, idx) => (
                  <li key={idx}>{s}</li>
                ))}
              </ul>
            </div>
          )}

          {rubric.improvements.length > 0 && (
            <div className="p-4 rounded-lg border border-amber/30 bg-amber/5 space-y-2">
              <h3 className="text-xs font-mono font-semibold text-amber uppercase tracking-wider">
                Actionable Improvements
              </h3>
              <ul className="list-disc list-inside space-y-1 text-xs text-ink">
                {rubric.improvements.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {rubric.summary && (
        <div className="p-4 rounded-lg border border-line bg-canvas space-y-1.5">
          <h3 className="text-[10px] font-mono uppercase tracking-wider text-muted flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-violet" />
            Interviewer Summary
          </h3>
          <p className="text-xs text-ink leading-relaxed whitespace-pre-wrap">{rubric.summary}</p>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono text-muted">
          <button
            type="button"
            onClick={() => void handleCopy()}
            className="hover:text-ink transition cursor-pointer"
          >
            {copied ? "Copied!" : "Copy report"}
          </button>
          {onToggleTranscript && (
            <button
              type="button"
              onClick={onToggleTranscript}
              className="hover:text-ink transition cursor-pointer"
            >
              {showTranscript ? "Hide Transcript" : "Transcript"}
            </button>
          )}
          <button
            type="button"
            onClick={onBackToLobby}
            className="hover:text-ink transition cursor-pointer"
          >
            Lobby
          </button>
        </div>

        <button
          type="button"
          onClick={onStartNew}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-violet text-canvas text-xs font-mono font-semibold hover:brightness-110 transition cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>New interview</span>
        </button>
      </div>
    </div>
  );
};
