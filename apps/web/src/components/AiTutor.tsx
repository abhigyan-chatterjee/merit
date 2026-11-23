import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bot, ChevronDown, ChevronUp, ExternalLink, Send } from "lucide-react";
import { catalogIdForBaseUrl, getTutorSnapshot, loadTutorCatalog, useTutorKey } from "../hooks/useTutorKey";
import { ApiError, apiRequest } from "../utils/api";

interface AiTutorProps {
  problemSlug: string;
  code?: string;
  failedAttempts?: number;
  defaultOpen?: boolean;
}

interface ChatMessage {
  role: "user" | "tutor";
  content: string;
}
export type TutorMode = "socratic" | "hint" | "code_review" | "interview";
type TutorStatus = "idle" | "key-set" | "models-loaded" | "chatting" | "error";

const MODE_TABS: Array<{ mode: TutorMode; label: string }> = [
  { mode: "socratic", label: "Socratic" },
  { mode: "hint", label: "Step Hint" },
  { mode: "code_review", label: "Code Review" },
  { mode: "interview", label: "Mock Interview" },
];
const INTERVIEW_SECONDS = 1800;
const INTERVIEW_START_PROMPT =
  "Let's begin the 30-minute mock interview. Act as my technical interviewer: set the stage briefly and ask me your opening question on clarifying assumptions, constraints, and my initial approach.";
const RUBRIC_PROMPT = "Evaluate my mock interview and current code with the 4-dimension placement rubric (/20) and Hire Verdict.";
const INTERVIEW_STAGES: Array<{ label: string; prompt: string }> = [
  {
    label: "1. Clarify",
    prompt: "Stage 1 (Clarify): Probe me on input constraints, edge cases, and assumptions I should clarify before designing an algorithm.",
  },
  {
    label: "2. Approach & Big-O",
    prompt: "Stage 2 (Approach & Big-O): Ask me to explain my proposed algorithm and defend its time and space complexity before coding.",
  },
  {
    label: "3. Dry-Run & Edge Cases",
    prompt: "Stage 3 (Dry-Run & Edge Cases): Challenge my current code and reasoning with a tricky test case or boundary condition.",
  },
  {
    label: "4. Rubric",
    prompt: RUBRIC_PROMPT,
  },
];

function formatClock(totalSeconds: number): string {
  return `${String(Math.floor(totalSeconds / 60)).padStart(2, "0")}:${String(totalSeconds % 60).padStart(2, "0")}`;
}

export function stripThinking(text: string): string {
  return text
    .replace(/<(thought|think)>[\s\S]*?<\/\1>/gi, "")
    .replace(/<(thought|think)>[\s\S]*$/gi, "")
    .replace(/<\/(thought|think)>/gi, "")
    .trim();
}

export const AiTutor: React.FC<AiTutorProps> = ({ problemSlug, code = "", failedAttempts = 0, defaultOpen = false }) => {
  const { apiKey, baseUrl, model, setModel } = useTutorKey();
  const [open, setOpen] = useState(defaultOpen);
  const [models, setModels] = useState<string[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [failedCount, setFailedCount] = useState(failedAttempts);
  const [status, setStatus] = useState<TutorStatus>(apiKey.trim() ? "key-set" : "idle");
  const [mode, setMode] = useState<TutorMode>("socratic");
  const [interviewSeconds, setInterviewSeconds] = useState(INTERVIEW_SECONDS);
  const [interviewRunning, setInterviewRunning] = useState(false);

  useEffect(() => {
    if (!apiKey.trim()) setStatus("idle");
    else if (models.length === 0) setStatus("key-set");
  }, [apiKey, models.length]);

  useEffect(() => {
    if (!open) return;
    const catalogId = catalogIdForBaseUrl(baseUrl);
    if (!catalogId) {
      setModels([]);
      setStatus(apiKey.trim() ? "key-set" : "idle");
      return;
    }
    let cancelled = false;
    void loadTutorCatalog(catalogId)
      .then((list) => {
        if (!cancelled) {
          setModels(list);
          setStatus(list.length > 0 ? "models-loaded" : apiKey.trim() ? "key-set" : "idle");
          if (list.length > 0 && !getTutorSnapshot().model.trim()) setModel(list[0]);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setStatus("error");
          setError("Could not load the model catalog. You can try again from Account.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [open, baseUrl]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setMessages([]);
    setError(null);
    setFailedCount(failedAttempts);
    setInterviewRunning(false);
    setInterviewSeconds(INTERVIEW_SECONDS);
  }, [problemSlug]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!interviewRunning) return;
    if (interviewSeconds === 0) {
      setInterviewRunning(false);
      return;
    }
    const id = window.setTimeout(() => setInterviewSeconds((value) => value - 1), 1000);
    return () => window.clearTimeout(id);
  }, [interviewRunning, interviewSeconds]);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    // Routed through apiRequest so an expired 15-minute access token is
    // silently refreshed (single 401 retry) instead of surfacing
    // "Authentication credentials missing" for a logged-in user.
    void apiRequest<Array<{ verdict?: unknown }>>(
      `/api/v1/judge/submissions/${encodeURIComponent(problemSlug)}`,
      { method: "GET" }
    )
      .then((subs) => {
        if (!cancelled && Array.isArray(subs)) setFailedCount(subs.filter((s) => s.verdict !== "AC").length);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [open, problemSlug]);

  const sendMessage = async (text: string) => {
    setError(null);
    setStatus(apiKey.trim() ? (models.length > 0 ? "models-loaded" : "key-set") : "idle");
    if (!apiKey.trim()) {
      setError("Add a tutor key in Account settings before chatting.");
      setStatus("error");
      return;
    }
    if (!text || !model || sending) return;
    setSending(true);
    setStatus("chatting");
    const history = messages.slice(-12).map((message) => ({ role: message.role === "tutor" ? "assistant" : "user", content: message.content }));
    setMessages((previous) => [...previous, { role: "user", content: text }]);
    try {
      // apiRequest refreshes an expired access token once on 401, so a
      // stale 15-minute cookie retries transparently instead of failing
      // with "Authentication credentials missing".
      const data = await apiRequest<{ reply?: unknown }>("/api/v1/tutor/chat", {
        method: "POST",
        body: JSON.stringify({ base_url: baseUrl, api_key: apiKey, model, problem_slug: problemSlug, code, question: text, failed_attempts: failedCount, mode, history }),
      });
      if (typeof data.reply !== "string" || !data.reply.trim()) {
        setError("Tutor returned an empty reply. Try again.");
        setStatus("error");
        return;
      }
      setMessages((previous) => [...previous, { role: "tutor", content: stripThinking(data.reply as string) }]);
    } catch (err) {
      // Surface the server's message verbatim (ApiError carries
      // error.message / detail.message); network failures get a hint.
      if (err instanceof ApiError) {
        setError(err.message || "Tutor request failed. Try again.");
      } else {
        setError("Could not reach the tutor service. Is the API server up?");
      }
      setStatus("error");
    } finally {
      setSending(false);
    }
  };

  const handleSend = () => {
    const q = question.trim();
    if (q && !sending && apiKey.trim() && model) setQuestion("");
    void sendMessage(q);
  };

  const canChat = Boolean(apiKey.trim() && model.trim());
  const hasCatalog = Boolean(catalogIdForBaseUrl(baseUrl));
  const modelOptions = model.trim() && !models.includes(model) ? [model, ...models] : models;
  return (
    <div data-tutor-status={status} className="rounded-xl border border-line bg-surface overflow-hidden">
      <button onClick={() => setOpen((value) => !value)} aria-expanded={open} className="w-full flex items-center justify-between p-4 text-xs font-mono font-semibold text-violet hover:bg-canvas/40 transition cursor-pointer">
        <span className="flex items-center gap-2"><Bot className="w-4 h-4" /> Ask the tutor {model && <span className="text-muted font-normal">· {model}</span>}</span>
        {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>
      {open && (
        <div className="p-4 pt-0 space-y-3 border-t border-line">
          {!apiKey.trim() && (
            <div className="pt-3 text-xs font-mono text-muted">
              Set up a provider and key on your account to start a guided session.{" "}
              <Link to="/profile#tutor" className="inline-flex items-center gap-1 text-violet hover:underline">Open account <ExternalLink className="w-3 h-3" /></Link>
            </div>
          )}
          {hasCatalog && modelOptions.length > 0 && (
            <label className="block pt-3 text-xs font-mono">
              <span className="text-muted">Model</span>
              <select aria-label="Model" value={model} onChange={(event) => { setError(null); setStatus("models-loaded"); setModel(event.target.value); }} className="mt-1 w-full p-2 rounded-lg bg-canvas border border-line text-xs font-mono text-ink">
                {modelOptions.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
          )}
          {open && apiKey.trim() && !hasCatalog && models.length === 0 && (
            <label className="block pt-3 text-xs font-mono">
              <span className="text-muted">Model</span>
              <input type="text" aria-label="Model" value={model} onChange={(e) => { setError(null); setModel(e.target.value); }} placeholder="Enter model id (e.g. llama3.2)" className="mt-1 w-full p-2 rounded-lg bg-canvas border border-line text-xs font-mono text-ink" />
            </label>
          )}
          <div role="tablist" aria-label="Coaching mode" className="flex flex-wrap gap-1.5">
            {MODE_TABS.map((tab) => (
              <button
                key={tab.mode}
                aria-pressed={mode === tab.mode}
                onClick={() => {
                  if (tab.mode !== mode) {
                    setMode(tab.mode);
                    setMessages([]);
                    setQuestion("");
                    setInterviewRunning(false);
                    setInterviewSeconds(INTERVIEW_SECONDS);
                  }
                  setError(null);
                }}
                className={`px-2.5 py-1.5 rounded-lg border font-mono text-[11px] cursor-pointer ${mode === tab.mode ? "bg-violet text-canvas border-violet" : "bg-canvas text-muted border-line hover:text-ink"}`}
              >
                {tab.label}
              </button>
            ))}
          </div>
          {mode === "interview" && (
            <div className="rounded-lg border border-violet/30 bg-violet/10 p-2.5 space-y-2">
              <div className="flex items-center justify-between gap-2">
                <span aria-label="Interview timer" className="font-mono text-sm font-semibold text-violet">{formatClock(interviewSeconds)}</span>
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => {
                      if (interviewRunning) {
                        setInterviewRunning(false);
                        return;
                      }
                      setInterviewRunning(true);
                      if (messages.length === 0 && !sending) {
                        void sendMessage(INTERVIEW_START_PROMPT);
                      }
                    }}
                    disabled={!canChat && !interviewRunning}
                    className="px-2.5 py-1.5 rounded-lg bg-violet text-canvas font-mono font-semibold text-[11px] disabled:opacity-50 cursor-pointer"
                  >
                    {interviewRunning ? "Pause" : messages.length > 0 ? "Resume" : "Start 30m Interview"}
                  </button>
                  <button onClick={() => { setInterviewRunning(false); setInterviewSeconds(INTERVIEW_SECONDS); }} className="px-2.5 py-1.5 rounded-lg border border-line bg-canvas font-mono text-[11px] text-muted hover:text-ink cursor-pointer">Reset Timer</button>
                </div>
              </div>
              <div className="flex flex-wrap gap-1 font-mono text-[10px] text-muted">
                {INTERVIEW_STAGES.map((stage) => (
                  <button
                    key={stage.label}
                    type="button"
                    disabled={!canChat || sending}
                    onClick={() => {
                      if (!interviewRunning && stage.label !== "4. Rubric") setInterviewRunning(true);
                      void sendMessage(stage.prompt);
                    }}
                    className="px-1.5 py-0.5 rounded-full border border-line bg-canvas hover:border-violet hover:text-ink disabled:opacity-50 cursor-pointer transition"
                  >
                    {stage.label}
                  </button>
                ))}
              </div>
              <button onClick={() => void sendMessage(RUBRIC_PROMPT)} disabled={!canChat || sending} className="w-full px-2.5 py-1.5 rounded-lg border border-violet/40 bg-canvas font-mono text-[11px] font-semibold text-violet disabled:opacity-50 cursor-pointer">Score My Interview (Rubric)</button>
            </div>
          )}
          {messages.length > 0 && (
            <div className="flex justify-end">
              <button onClick={() => { setMessages([]); setError(null); }} className="px-2 py-1 rounded-lg border border-line bg-canvas font-mono text-[10px] text-muted hover:text-ink cursor-pointer">Clear chat</button>
            </div>
          )}
          <div aria-label="Tutor chat log" className="space-y-2 max-h-72 overflow-y-auto p-2 rounded-lg bg-canvas border border-line">
            {messages.length === 0 ? <p className="text-[11px] font-mono text-muted text-center py-4">{canChat ? "Ask about the problem — your tutor will guide your reasoning." : "Choose a model and configure a key to start chatting."}</p> : messages.map((message, index) => <div key={index} className={`p-2.5 rounded-lg border text-xs font-mono leading-relaxed whitespace-pre-wrap ${message.role === "user" ? "bg-surface border-line text-ink ml-6" : "bg-violet/10 border-violet/30 text-ink mr-6"}`}><div className="text-[10px] font-bold uppercase tracking-wider mb-1 text-violet">{message.role === "user" ? "You" : "Tutor"}</div>{message.content}</div>)}
            {sending && (
              <div role="status" aria-label="Tutor is responding" className="p-2.5 rounded-lg border bg-violet/10 border-violet/30 text-ink mr-6 text-xs font-mono">
                <div className="text-[10px] font-bold uppercase tracking-wider mb-1 text-violet">Tutor</div>
                <div className="inline-flex items-center gap-1.5 py-1" aria-hidden="true">
                  <span className="w-1.5 h-1.5 rounded-full bg-violet animate-bounce [animation-delay:-0.3s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-violet animate-bounce [animation-delay:-0.15s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-violet animate-bounce" />
                </div>
              </div>
            )}
          </div>
          {error && <p role="alert" className="text-xs font-mono text-rose">{error}</p>}
          <div className="flex items-center gap-2">
            <input type="text" aria-label="Your question" value={question} onChange={(event) => { setError(null); setStatus(apiKey.trim() ? (models.length > 0 ? "models-loaded" : "key-set") : "idle"); setQuestion(event.target.value); }} onKeyDown={(event) => { if (event.key === "Enter") void handleSend(); }} placeholder="Ask about this problem…" className="flex-1 p-2 rounded-lg bg-canvas border border-line text-base sm:text-xs font-mono text-ink placeholder-muted" />
            <button onClick={() => void handleSend()} disabled={!canChat || !question.trim() || sending} aria-label="Send question" className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-violet text-canvas font-mono font-semibold text-xs disabled:opacity-50 cursor-pointer"><Send className="w-3.5 h-3.5" />{sending ? "Sending…" : "Send"}</button>
          </div>
        </div>
      )}
    </div>
  );
};
