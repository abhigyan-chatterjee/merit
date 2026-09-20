import React, { useEffect, useState } from "react";
import { Bot, ChevronDown, ChevronUp, ExternalLink, Send } from "lucide-react";
import { catalogIdForBaseUrl, loadTutorCatalog, useTutorKey } from "../hooks/useTutorKey";

interface AiTutorProps {
  problemSlug: string;
  code?: string;
  failedAttempts?: number;
}

interface ChatMessage {
  role: "user" | "tutor";
  content: string;
}
type TutorStatus = "idle" | "key-set" | "models-loaded" | "chatting" | "error";

async function readErrorMessage(res: Response, fallback: string): Promise<string> {
  try {
    const data = await res.json();
    const detail = (data as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail) return detail;
    if (detail && typeof detail === "object" && typeof (detail as { message?: unknown }).message === "string") {
      return (detail as { message: string }).message;
    }
  } catch {
    // Use the status fallback for non-JSON responses.
  }
  return `${fallback} (HTTP ${res.status})`;
}

export const AiTutor: React.FC<AiTutorProps> = ({ problemSlug, code = "", failedAttempts = 0 }) => {
  const { apiKey, baseUrl, model, setModel } = useTutorKey();
  const [open, setOpen] = useState(false);
  const [models, setModels] = useState<string[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [failedCount, setFailedCount] = useState(failedAttempts);
  const [status, setStatus] = useState<TutorStatus>(apiKey.trim() ? "key-set" : "idle");

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
          if (list.length > 0 && !list.includes(model)) setModel(list[0]);
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
    if (!open) return;
    let cancelled = false;
    void fetch(`/api/v1/judge/submissions/${encodeURIComponent(problemSlug)}`, { credentials: "include" })
      .then((res) => (res.ok ? res.json() : []))
      .then((subs: Array<{ verdict?: unknown }>) => {
        if (!cancelled && Array.isArray(subs)) setFailedCount(subs.filter((s) => s.verdict !== "AC").length);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [open, problemSlug]);

  const handleSend = async () => {
    const q = question.trim();
    setError(null);
    setStatus(apiKey.trim() ? (models.length > 0 ? "models-loaded" : "key-set") : "idle");
    if (!apiKey.trim()) {
      setError("Add a tutor key in Account settings before chatting.");
      setStatus("error");
      return;
    }
    if (!q || !model || sending) return;
    setSending(true);
    setStatus("chatting");
    setMessages((previous) => [...previous, { role: "user", content: q }]);
    setQuestion("");
    try {
      const res = await fetch("/api/v1/tutor/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ base_url: baseUrl, api_key: apiKey, model, problem_slug: problemSlug, code, question: q, failed_attempts: failedCount }),
      });
      if (!res.ok) {
        setError(await readErrorMessage(res, "Tutor request failed"));
        setStatus("error");
        return;
      }
      const data = (await res.json()) as { reply?: unknown };
      if (typeof data.reply !== "string" || !data.reply.trim()) {
        setError("Tutor returned an empty reply. Try again.");
        setStatus("error");
        return;
      }
      setMessages((previous) => [...previous, { role: "tutor", content: data.reply as string }]);
    } catch {
      setError("Could not reach the tutor service. Is the API server up?");
      setStatus("error");
    } finally {
      setSending(false);
    }
  };

  const canChat = Boolean(apiKey.trim() && model.trim());
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
              <a href="/profile#tutor" className="inline-flex items-center gap-1 text-violet hover:underline">Open Account <ExternalLink className="w-3 h-3" /></a>
            </div>
          )}
          {models.length > 0 && (
            <label className="block pt-3 text-xs font-mono">
              <span className="text-muted">Model</span>
              <select aria-label="Model" value={model} onChange={(event) => { setError(null); setStatus("models-loaded"); setModel(event.target.value); }} className="mt-1 w-full p-2 rounded-lg bg-canvas border border-line text-xs font-mono text-ink">
                {models.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
          )}
          <div aria-label="Tutor chat log" className="space-y-2 max-h-72 overflow-y-auto p-2 rounded-lg bg-canvas border border-line">
            {messages.length === 0 ? <p className="text-[11px] font-mono text-muted text-center py-4">{canChat ? "Ask about the problem — your tutor will guide your reasoning." : "Choose a model and configure a key to start chatting."}</p> : messages.map((message, index) => <div key={index} className={`p-2.5 rounded-lg border text-xs font-mono leading-relaxed whitespace-pre-wrap ${message.role === "user" ? "bg-surface border-line text-ink ml-6" : "bg-violet/10 border-violet/30 text-ink mr-6"}`}><div className="text-[10px] font-bold uppercase tracking-wider mb-1 text-violet">{message.role === "user" ? "You" : "Tutor"}</div>{message.content}</div>)}
          </div>
          {error && <p role="alert" className="text-xs font-mono text-rose">{error}</p>}
          <div className="flex items-center gap-2">
            <input type="text" aria-label="Your question" value={question} onChange={(event) => { setError(null); setStatus(apiKey.trim() ? (models.length > 0 ? "models-loaded" : "key-set") : "idle"); setQuestion(event.target.value); }} onKeyDown={(event) => { if (event.key === "Enter") void handleSend(); }} placeholder="Ask about this problem…" className="flex-1 p-2 rounded-lg bg-canvas border border-line text-xs font-mono text-ink placeholder-muted" />
            <button onClick={() => void handleSend()} disabled={!canChat || !question.trim() || sending} aria-label="Send question" className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-violet text-white font-mono font-semibold text-xs disabled:opacity-50 cursor-pointer"><Send className="w-3.5 h-3.5" />{sending ? "Sending…" : "Send"}</button>
          </div>
        </div>
      )}
    </div>
  );
};
