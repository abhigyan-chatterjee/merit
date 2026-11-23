import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Award,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  Code2,
  FileText,
  MessagesSquare,
  Pause,
  Play,
  Send,
} from "lucide-react";
import { isEditorLang } from "../../data/languages";
import {
  InterviewCodingSnapshot,
  InterviewProblemSummary,
  InterviewSessionDetail,
} from "../../utils/api";
import { CodeRunner } from "../CodeRunner";
import { MarkdownStatement } from "../MarkdownStatement";
import { InterviewRubricCard } from "./InterviewRubricCard";
import { formatClock, shortStageLabel } from "./interviewConfig";

interface InterviewWorkspaceProps {
  session: InterviewSessionDetail;
  models: string[];
  hasCatalog: boolean;
  model: string;
  onModelChange: (model: string) => void;
  canChat: boolean;
  sending: boolean;
  suggestedStage?: string | null;
  error: string | null;
  elapsedSec: number;
  timerRunning: boolean;
  onToggleTimer: () => void;
  onSelectStage: (stageId: string) => void;
  onSendMessage: (message: string, opts?: { designNotes?: string }) => void;
  onEvaluate: (designNotes?: string) => void;
  onCodeChange: (slug: string, snapshot: InterviewCodingSnapshot) => void;
  onJudgeResult: (slug: string, snapshot: InterviewCodingSnapshot) => void;
  onBackToLobby: () => void;
  onStartNew: () => void;
}

function renderProblemStatement(problem: InterviewProblemSummary) {
  return (
    <div className="p-4 rounded-xl border border-line bg-surface space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <h2 className="text-base font-bold text-ink">{problem.title}</h2>
          <span className="px-2 py-0.5 rounded border border-line bg-canvas text-[10px] font-mono text-violet">
            {problem.difficulty}
          </span>
        </div>
        <span className="text-[11px] font-mono text-muted">{problem.topic}</span>
      </div>

      <MarkdownStatement statement={problem.statement} />

      {problem.examples.length > 0 && (
        <div className="space-y-2 pt-1">
          {problem.examples.map((ex, idx) => (
            <div
              key={idx}
              className="p-2.5 rounded-lg bg-canvas border border-line font-mono text-xs space-y-1"
            >
              <div className="text-muted font-semibold">Example {idx + 1}:</div>
              <div>
                <span className="text-muted">Input: </span>
                <span className="text-ink">{ex.input}</span>
              </div>
              <div>
                <span className="text-muted">Output: </span>
                <span className="text-mint">{ex.output}</span>
              </div>
              {ex.explanation && (
                <div className="text-muted text-[11px] pt-0.5">Explanation: {ex.explanation}</div>
              )}
            </div>
          ))}
        </div>
      )}

      {problem.constraints.length > 0 && (
        <div>
          <h3 className="text-[10px] font-mono uppercase tracking-wider text-muted mb-1">
            Constraints
          </h3>
          <ul className="list-disc list-inside text-xs font-mono text-ink space-y-0.5">
            {problem.constraints.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export const InterviewWorkspace: React.FC<InterviewWorkspaceProps> = ({
  session,
  models,
  hasCatalog,
  model,
  onModelChange,
  canChat,
  sending,
  suggestedStage,
  error,
  elapsedSec,
  timerRunning,
  onToggleTimer,
  onSelectStage,
  onSendMessage,
  onEvaluate,
  onCodeChange,
  onJudgeResult,
  onBackToLobby,
  onStartNew,
}) => {
  const [draft, setDraft] = useState("");
  const [designNotes, setDesignNotes] = useState("");
  const [mobilePane, setMobilePane] = useState<"problem" | "chat">("chat");
  const [statementCollapsed, setStatementCollapsed] = useState(false);
  const [showTranscriptInRubric, setShowTranscriptInRubric] = useState(false);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  const stageIdx = Math.max(
    0,
    session.stages.findIndex((s) => s.id === session.current_stage),
  );
  const currentStage = session.stages[stageIdx] ?? session.stages[0];
  const nextStage = stageIdx + 1 < session.stages.length ? session.stages[stageIdx + 1] : null;
  const remainingSec = Math.max(0, session.duration_sec - elapsedSec);

  const activeProblem: InterviewProblemSummary | null =
    currentStage?.kind === "coding"
      ? (session.problems[currentStage.problem_index ?? 0] ?? session.problems[0] ?? null)
      : null;

  const activeSnapshot = activeProblem ? session.coding_snapshots[activeProblem.slug] : undefined;

  const initialCodeByLang = useMemo(() => {
    if (!activeSnapshot || !activeSnapshot.code) return undefined;
    if (!isEditorLang(activeSnapshot.language)) return undefined;
    return { [activeSnapshot.language]: activeSnapshot.code };
  }, [activeProblem?.slug, activeSnapshot?.language]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const el = chatScrollRef.current;
    if (el && typeof el.scrollTo === "function") {
      el.scrollTo({ top: el.scrollHeight });
    } else if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [session.messages.length, sending]);

  useEffect(() => {
    setMobilePane(currentStage?.kind === "coding" ? "problem" : "chat");
  }, [currentStage?.id, currentStage?.kind]);

  const submitMessage = () => {
    const text = draft.trim();
    if (!text || !canChat || sending) return;
    setDraft("");
    onSendMessage(text, { designNotes: designNotes.trim() || undefined });
  };

  const modelOptions = model.trim() && !models.includes(model) ? [model, ...models] : models;

  const suggestedDef =
    suggestedStage && suggestedStage !== "rubric"
      ? (session.stages.find((s) => s.id === suggestedStage) ?? null)
      : null;
  const showSuggestion =
    Boolean(suggestedStage) &&
    suggestedStage !== session.current_stage &&
    session.status !== "completed" &&
    !sending;

  const chatPanel = (
    <div className="rounded-xl border border-line bg-surface flex flex-col overflow-hidden">
      <div className="px-4 py-3 border-b border-line bg-canvas flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs font-mono font-semibold text-violet">
          <MessagesSquare className="w-4 h-4" />
          <span>
            Interviewer · {currentStage ? shortStageLabel(currentStage.id, currentStage.label) : ""}
          </span>
        </div>
        {activeSnapshot && (
          <span className="px-2 py-0.5 rounded border border-line bg-surface text-[10px] font-mono text-muted">
            {activeSnapshot.language}
          </span>
        )}
      </div>

      <div
        ref={chatScrollRef}
        aria-label="Interview transcript"
        className="flex-1 p-3 space-y-2.5 max-h-[54vh] min-h-[280px] overflow-y-auto bg-canvas/50"
      >
        {session.messages.length === 0 && !sending && (
          <p className="text-xs font-mono text-muted text-center py-8">
            Connecting with your AI interviewer…
          </p>
        )}

        {session.messages.map((msg, idx) => (
          <div
            key={idx}
            className={`p-3 rounded-lg border text-xs font-mono leading-relaxed ${
              msg.role === "user"
                ? "bg-surface border-line text-ink ml-6 whitespace-pre-wrap"
                : "bg-violet/10 border-violet/30 text-ink mr-6"
            }`}
          >
            <div className="flex items-center justify-between gap-2 text-[10px] font-bold uppercase tracking-wider mb-1 text-violet">
              <span>{msg.role === "user" ? "Candidate (You)" : "Interviewer"}</span>
              <span className="font-normal text-muted">{shortStageLabel(msg.stage, msg.stage)}</span>
            </div>
            {msg.role === "user" ? (
              msg.content
            ) : (
              <MarkdownStatement
                statement={msg.content}
                stripHeading={false}
                className="text-xs font-mono text-ink leading-relaxed space-y-2"
              />
            )}
          </div>
        ))}

        {sending && (
          <div
            role="status"
            aria-label="Interviewer is responding"
            className="p-3 rounded-lg border bg-violet/10 border-violet/30 text-ink mr-6 text-xs font-mono"
          >
            <div className="text-[10px] font-bold uppercase tracking-wider mb-1 text-violet">
              Interviewer
            </div>
            <div className="inline-flex items-center gap-1.5 py-1" aria-hidden="true">
              <span className="w-1.5 h-1.5 rounded-full bg-violet animate-bounce [animation-delay:-0.3s]" />
              <span className="w-1.5 h-1.5 rounded-full bg-violet animate-bounce [animation-delay:-0.15s]" />
              <span className="w-1.5 h-1.5 rounded-full bg-violet animate-bounce" />
            </div>
          </div>
        )}
      </div>

      {error && (
        <div role="alert" className="px-4 py-2 border-t border-rose/30 bg-rose/10 text-xs font-mono text-rose">
          {error}
        </div>
      )}

      {showSuggestion && suggestedStage === "rubric" && (
        <div className="px-4 py-2.5 border-t border-violet/30 bg-violet/10 flex flex-wrap items-center justify-between gap-2">
          <span className="text-[11px] font-mono text-violet">Interviewer is ready to wrap up</span>
          <button
            type="button"
            onClick={() => onEvaluate(designNotes.trim() || undefined)}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-violet text-canvas font-mono text-[11px] font-semibold hover:brightness-110 cursor-pointer shrink-0"
          >
            <span>End & Score →</span>
          </button>
        </div>
      )}

      {showSuggestion && suggestedStage !== "rubric" && suggestedDef?.kind === "coding" && (
        <div className="px-4 py-2.5 border-t border-mint/30 bg-mint/10 flex flex-wrap items-center justify-between gap-2">
          <span className="text-[11px] font-mono text-mint">Ready for the coding round</span>
          <button
            type="button"
            onClick={() => onSelectStage(suggestedDef.id)}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-mint/40 bg-mint/10 text-mint font-mono text-[11px] font-semibold hover:bg-mint/20 cursor-pointer shrink-0"
          >
            <span>Open {shortStageLabel(suggestedDef.id, suggestedDef.label)} & Editor →</span>
          </button>
        </div>
      )}

      {showSuggestion && suggestedStage !== "rubric" && suggestedDef && suggestedDef.kind !== "coding" && (
        <div className="px-4 py-2.5 border-t border-mint/30 bg-mint/10 flex flex-wrap items-center justify-between gap-2">
          <span className="text-[11px] font-mono text-mint">Ready for the next round</span>
          <button
            type="button"
            onClick={() => onSelectStage(suggestedDef.id)}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-mint/40 bg-mint/10 text-mint font-mono text-[11px] font-semibold hover:bg-mint/20 cursor-pointer shrink-0"
          >
            <span>Move to {shortStageLabel(suggestedDef.id, suggestedDef.label)} →</span>
          </button>
        </div>
      )}

      {session.status !== "completed" && (
        <div className="p-3 border-t border-line bg-surface space-y-2">
          <div className="flex items-end gap-2">
            <textarea
              rows={2}
              aria-label="Your interview response"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submitMessage();
                }
              }}
              placeholder="Explain your reasoning, Big-O, architecture, or ask clarifying questions… (Enter to send)"
              className="flex-1 p-2.5 rounded-lg bg-canvas border border-line text-base sm:text-xs font-mono text-ink placeholder-muted resize-y focus:border-violet"
            />
            <button
              type="button"
              disabled={!canChat || !draft.trim() || sending}
              onClick={submitMessage}
              aria-label="Send response"
              className="inline-flex items-center gap-1.5 px-3.5 py-2.5 rounded-lg bg-violet text-canvas font-mono font-semibold text-xs disabled:opacity-50 cursor-pointer shrink-0"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{sending ? "Sending…" : "Send"}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-5">
      {/* Top Control Header */}
      <div className="p-4 rounded-xl border border-line bg-surface space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 text-xs font-mono">
            <button
              type="button"
              onClick={onBackToLobby}
              className="inline-flex items-center gap-1 text-muted hover:text-ink cursor-pointer transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Lobby</span>
            </button>
            <span aria-hidden="true" className="text-muted">·</span>
            <span className="uppercase font-bold text-violet">{session.difficulty}</span>
            <span aria-hidden="true" className="text-muted">·</span>
            <span className="inline-flex items-center gap-1 text-ink">
              <Clock className="w-3.5 h-3.5 text-violet" />
              <span aria-label="Interview timer" className="font-bold tnum">
                {formatClock(remainingSec)}
              </span>
              {session.status !== "completed" && (
                <button
                  type="button"
                  onClick={onToggleTimer}
                  aria-label={timerRunning ? "Pause timer" : "Resume timer"}
                  className="text-muted hover:text-ink cursor-pointer"
                >
                  {timerRunning ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                </button>
              )}
            </span>
          </div>

          {session.status !== "completed" && (
            <button
              type="button"
              disabled={!canChat || sending}
              onClick={() => onEvaluate(designNotes.trim() || undefined)}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-violet text-canvas font-mono text-xs font-semibold hover:brightness-110 disabled:opacity-50 cursor-pointer transition shrink-0"
            >
              <Award className="w-3.5 h-3.5" />
              <span>End & Score</span>
            </button>
          )}
        </div>

        {(hasCatalog && modelOptions.length > 0) ||
        (session.status !== "completed" && nextStage && nextStage.kind !== "rubric") ||
        (session.has_resume && session.resume_filename) ? (
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] font-mono text-muted">
            {hasCatalog && modelOptions.length > 0 && (
              <select
                aria-label="Workspace Model"
                value={model}
                onChange={(e) => onModelChange(e.target.value)}
                className="px-2 py-1 rounded-lg bg-canvas border border-line text-[11px] font-mono text-muted max-w-[155px]"
              >
                {modelOptions.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            )}
            {session.status !== "completed" && nextStage && nextStage.kind !== "rubric" && (
              <button
                type="button"
                disabled={!canChat || sending}
                onClick={() => onSelectStage(nextStage.id)}
                className="inline-flex items-center gap-1 text-muted hover:text-ink disabled:opacity-50 cursor-pointer transition shrink-0"
              >
                <span>Next Round</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
            {session.has_resume && session.resume_filename && (
              <span className="inline-flex items-center gap-1 truncate max-w-[200px]">
                <FileText className="w-3 h-3 shrink-0" />
                <span className="truncate">{session.resume_filename}</span>
              </span>
            )}
          </div>
        ) : null}
      </div>

      {/* Stage Stepper */}
      <nav aria-label="Interview rounds" className="flex flex-wrap items-center gap-1.5">
        {session.stages.map((st, idx) => {
          const active = st.id === currentStage?.id;
          const past = idx < stageIdx || session.status === "completed";
          return (
            <button
              key={st.id}
              type="button"
              disabled={sending || (!canChat && st.kind === "rubric")}
              aria-current={active ? "step" : undefined}
              onClick={() => {
                if (st.kind === "rubric") {
                  if (!session.rubric) onEvaluate(designNotes.trim() || undefined);
                  else onSelectStage(st.id);
                } else {
                  onSelectStage(st.id);
                }
              }}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border font-mono text-[11px] transition cursor-pointer disabled:opacity-50 ${
                active
                  ? "border-violet bg-violet text-canvas font-semibold"
                  : past
                    ? "border-mint/40 bg-mint/10 text-mint hover:border-mint"
                    : "border-line bg-surface text-muted hover:text-ink"
              }`}
            >
              {past && !active && <CheckCircle2 className="w-3 h-3" />}
              <span>{shortStageLabel(st.id, st.label)}</span>
            </button>
          );
        })}
      </nav>

      {/* Main Round Area */}
      {currentStage?.kind === "rubric" ? (
        <div className="space-y-5">
          {session.rubric ? (
            <>
              <InterviewRubricCard
                session={session}
                onBackToLobby={onBackToLobby}
                onStartNew={onStartNew}
                showTranscript={showTranscriptInRubric}
                onToggleTranscript={() => setShowTranscriptInRubric((v) => !v)}
              />
              {showTranscriptInRubric && chatPanel}
            </>
          ) : (
            <div className="p-8 rounded-xl border border-line bg-surface text-center space-y-3">
              {sending ? (
                <div role="status" aria-label="Interviewer is responding" className="space-y-2">
                  <p className="text-xs font-mono text-violet font-semibold">
                    Compiling your hiring rubric across all rounds…
                  </p>
                  <div className="inline-flex items-center gap-1.5" aria-hidden="true">
                    <span className="w-2 h-2 rounded-full bg-violet animate-bounce [animation-delay:-0.3s]" />
                    <span className="w-2 h-2 rounded-full bg-violet animate-bounce [animation-delay:-0.15s]" />
                    <span className="w-2 h-2 rounded-full bg-violet animate-bounce" />
                  </div>
                </div>
              ) : (
                <>
                  <p className="text-xs font-mono text-muted">
                    Ready to score this interview against the {session.difficulty} hiring rubric.
                  </p>
                  <button
                    type="button"
                    disabled={!canChat}
                    onClick={() => onEvaluate(designNotes.trim() || undefined)}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-violet text-canvas font-mono text-xs font-semibold cursor-pointer"
                  >
                    <Award className="w-4 h-4" />
                    <span>Generate Final Rubric</span>
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      ) : currentStage?.kind === "coding" && activeProblem ? (
        <div className="space-y-4">
          {/* Mobile Pane Switcher */}
          <div className="flex lg:hidden items-center gap-1 p-1 rounded-lg border border-line bg-surface">
            <button
              type="button"
              onClick={() => setMobilePane("problem")}
              aria-pressed={mobilePane === "problem"}
              className={`flex-1 py-2 rounded-md text-xs font-mono cursor-pointer ${
                mobilePane === "problem" ? "bg-mint text-canvas font-semibold" : "text-muted"
              }`}
            >
              Problem & Code Editor
            </button>
            <button
              type="button"
              onClick={() => setMobilePane("chat")}
              aria-pressed={mobilePane === "chat"}
              className={`flex-1 py-2 rounded-md text-xs font-mono cursor-pointer ${
                mobilePane === "chat" ? "bg-violet text-canvas font-semibold" : "text-muted"
              }`}
            >
              Interviewer ({session.messages.length})
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
            {/* Left: Problem Statement + Embedded CodeRunner */}
            <div className={`lg:col-span-7 space-y-4 ${mobilePane === "chat" ? "hidden lg:block" : ""}`}>
              <div className="rounded-xl border border-line bg-surface overflow-hidden">
                <button
                  type="button"
                  onClick={() => setStatementCollapsed((v) => !v)}
                  className="w-full flex items-center justify-between px-4 py-2.5 border-b border-line bg-canvas text-xs font-mono text-ink cursor-pointer"
                >
                  <span className="inline-flex items-center gap-2 font-semibold">
                    <Code2 className="w-4 h-4 text-mint" />
                    <span>
                      {activeProblem.title} ({activeProblem.difficulty})
                    </span>
                  </span>
                  {statementCollapsed ? (
                    <ChevronDown className="w-4 h-4 text-muted" />
                  ) : (
                    <ChevronUp className="w-4 h-4 text-muted" />
                  )}
                </button>
                {!statementCollapsed && <div className="p-1">{renderProblemStatement(activeProblem)}</div>}
              </div>

              <CodeRunner
                key={activeProblem.slug}
                problemSlug={activeProblem.slug}
                starterCode={activeProblem.starter_code.javascript ?? ""}
                starterCodePython={activeProblem.starter_code.python ?? ""}
                starterCodeJava={activeProblem.starter_code.java ?? ""}
                starterCodeCpp={activeProblem.starter_code.cpp ?? ""}
                functionName={activeProblem.function_name}
                sampleInput={activeProblem.test_cases[0]?.input}
                initialCodeByLang={initialCodeByLang}
                tutorEnabled={false}
                onCodeChange={(code, language) =>
                  onCodeChange(activeProblem.slug, {
                    language,
                    code,
                    verdict: activeSnapshot?.verdict ?? null,
                    passed_count: activeSnapshot?.passed_count ?? null,
                    total_count: activeSnapshot?.total_count ?? null,
                  })
                }
                onJudgeResult={(res) =>
                  onJudgeResult(activeProblem.slug, {
                    language: res.language,
                    code: res.code,
                    verdict: res.verdict,
                    passed_count: res.passedCount,
                    total_count: res.totalCount,
                  })
                }
              />
            </div>

            {/* Right: Live Interviewer */}
            <div className={`lg:col-span-5 ${mobilePane === "problem" ? "hidden lg:block" : ""}`}>
              {chatPanel}
            </div>
          </div>
        </div>
      ) : currentStage?.kind === "project" || currentStage?.kind === "system_design" ? (
        /* Project / System Design: 2-column split with side rail */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          <div className="lg:col-span-8">{chatPanel}</div>

          <div className="lg:col-span-4 space-y-4">
            <div className="p-4 rounded-xl border border-line bg-surface space-y-2">
              <label className="block space-y-1.5">
                <span className="text-xs font-mono font-semibold text-ink">
                  {currentStage.kind === "system_design"
                    ? "Architecture & Capacity Scratchpad"
                    : "Project Architecture Notes"}
                </span>
                <textarea
                  rows={6}
                  aria-label="Architecture scratchpad"
                  value={designNotes}
                  onChange={(e) => setDesignNotes(e.target.value)}
                  placeholder="Jot down API endpoints, schema entities, QPS math, caching strategy, or failure modes — sent automatically with your next message."
                  className="w-full p-2.5 rounded-lg bg-canvas border border-line text-xs font-mono text-ink placeholder-muted focus:border-violet"
                />
              </label>
            </div>

            {(session.resume_filename || session.project_brief) && (
              <div className="p-4 rounded-xl border border-line bg-surface space-y-1.5 text-xs font-mono">
                {session.resume_filename && (
                  <div className="text-muted truncate">{session.resume_filename}</div>
                )}
                {session.project_brief && (
                  <p className="text-[11px] text-muted line-clamp-4">{session.project_brief}</p>
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Theory / Wrap-up: Centered chat panel */
        <div className="max-w-4xl mx-auto">{chatPanel}</div>
      )}
    </div>
  );
};
