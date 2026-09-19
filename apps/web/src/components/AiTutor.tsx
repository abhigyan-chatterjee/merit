import React, { useEffect, useRef, useState } from "react";
import {
  Bot,
  ChevronDown,
  ChevronUp,
  KeyRound,
  RefreshCw,
  Send,
} from "lucide-react";
import { useTutorKey } from "../hooks/useTutorKey";

interface AiTutorProps {
  problemSlug: string;
  /**
   * Current editor code sent as `code` in the chat request.
   * Defaults to "" (backend renders "(no code shared yet)"). The live editor
   * textarea is owned by CodeRunner, which is out of scope for this ticket
   * (ProblemDetailPage change is mount-only), so pass live code here once
   * CodeRunner lifts it.
   */
  code?: string;
  /**
   * Fallback for `failed_attempts`. The panel first tries the existing judge
   * submissions data flow (`GET /api/v1/judge/submissions/:slug`, the same
   * endpoint CodeRunner reads) and counts non-AC verdicts; if that fetch
   * fails (guest/offline) it falls back to this prop (default 0).
   */
  failedAttempts?: number;
}

interface ChatMessage {
  role: "user" | "tutor";
  content: string;
}

async function readErrorMessage(res: Response, fallback: string): Promise<string> {
  try {
    const data = await res.json();
    const detail = (data as { detail?: unknown }).detail;
    if (detail && typeof detail === "object") {
      const msg = (detail as { message?: unknown }).message;
      if (typeof msg === "string" && msg) return msg;
    } else if (typeof detail === "string" && detail) {
      return detail;
    }
    const error = (data as { error?: unknown }).error;
    if (error && typeof error === "object") {
      const msg = (error as { message?: unknown }).message;
      if (typeof msg === "string" && msg) return msg;
    }
  } catch {
    // non-JSON error body
  }
  return `${fallback} (HTTP ${res.status})`;
}

export const AiTutor: React.FC<AiTutorProps> = ({
  problemSlug,
  code = "",
  failedAttempts = 0,
}) => {
  const {
    baseUrl,
    apiKey,
    model,
    remember,
    setBaseUrl,
    setApiKey,
    setModel,
    setRemember,
  } = useTutorKey();

  const [open, setOpen] = useState(false);
  const [models, setModels] = useState<string[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [sending, setSending] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [failedCount, setFailedCount] = useState<number>(failedAttempts);
  // Uncontrolled key field (ref): the secret stays a live input property and
  // is never written back into serialized markup as a value attribute.
  // The initial value is snapshotted so re-renders (e.g. after typing, which
  // updates hook state) never echo the secret into `defaultValue`.
  const keyInputRef = useRef<HTMLInputElement>(null);
  const initialApiKeyRef = useRef(apiKey);

  // Resolve failed_attempts from the existing submissions data flow when the
  // panel is opened. Falls back to the `failedAttempts` prop (default 0).
  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(
          `/api/v1/judge/submissions/${encodeURIComponent(problemSlug)}`,
          { credentials: "include" }
        );
        if (!res.ok) return;
        const subs = (await res.json()) as Array<{ verdict?: unknown }>;
        if (!cancelled && Array.isArray(subs)) {
          setFailedCount(subs.filter((s) => s.verdict !== "AC").length);
        }
      } catch {
        // Guest / offline: keep the fallback count.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open, problemSlug]);

  const handleCheckModels = async () => {
    setModelsLoading(true);
    setModelsError(null);
    try {
      // The key travels in the POST body only — never in the URL.
      const res = await fetch("/api/v1/tutor/models", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ base_url: baseUrl, api_key: apiKey }),
      });
      if (!res.ok) {
        setModelsError(await readErrorMessage(res, "Could not load models"));
        return;
      }
      const data = (await res.json()) as { models?: unknown };
      const list = Array.isArray(data.models)
        ? data.models.filter((m): m is string => typeof m === "string")
        : [];
      setModels(list);
      if (list.length > 0 && !list.includes(model)) {
        setModel(list[0]);
      }
    } catch {
      setModelsError("Could not reach the tutor service. Is the API server up?");
    } finally {
      setModelsLoading(false);
    }
  };

  const handleSend = async () => {
    const q = question.trim();
    if (!q || !apiKey || !model || sending) return;
    setSending(true);
    setChatError(null);
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setQuestion("");
    try {
      const res = await fetch("/api/v1/tutor/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          base_url: baseUrl,
          api_key: apiKey,
          model,
          problem_slug: problemSlug,
          code,
          question: q,
          failed_attempts: failedCount,
        }),
      });
      if (!res.ok) {
        setChatError(await readErrorMessage(res, "Tutor request failed"));
        return;
      }
      const data = (await res.json()) as { reply?: unknown };
      if (typeof data.reply !== "string" || !data.reply.trim()) {
        setChatError("Tutor returned an empty reply. Try again.");
        return;
      }
      setMessages((prev) => [...prev, { role: "tutor", content: data.reply as string }]);
    } catch {
      setChatError("Could not reach the tutor service. Is the API server up?");
    } finally {
      setSending(false);
    }
  };

  const canChat = apiKey.trim().length > 0 && model.trim().length > 0;

  // Copy-only provider presets for the base URL field (no logic beyond
  // filling the text input): OpenAI default, Gemini via its
  // OpenAI-compatible endpoint. Exactly two options.
  const PRESETS = [
    { label: "OpenAI", url: "https://api.openai.com/v1" },
    {
      label: "Gemini (OpenAI-compatible)",
      url: "https://generativelanguage.googleapis.com/v1beta/openai/",
    },
  ];

  return (
    <div className="rounded-xl border border-line bg-surface overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="w-full flex items-center justify-between p-4 text-xs font-mono font-semibold text-violet hover:bg-canvas/40 transition cursor-pointer"
      >
        <span className="flex items-center gap-2">
          <Bot className="w-4 h-4" />
          Ask the tutor
        </span>
        {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {open && (
        <div className="p-4 pt-0 space-y-4 border-t border-line">
          {/* BYOK credentials */}
          <div className="space-y-2 pt-3">
            <label className="block text-xs font-mono">
              <span className="text-muted">Provider preset</span>
              <select
                aria-label="Provider preset"
                value={
                  PRESETS.some((p) => p.url === baseUrl)
                    ? baseUrl
                    : PRESETS[0].url
                }
                onChange={(e) => setBaseUrl(e.target.value)}
                className="mt-1 w-full p-2 rounded-lg bg-canvas border border-line text-xs font-mono text-ink focus:outline-none focus:border-violet cursor-pointer"
              >
                {PRESETS.map((p) => (
                  <option key={p.url} value={p.url}>
                    {p.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-xs font-mono">
              <span className="text-muted">Provider base URL</span>
              <input
                type="text"
                aria-label="Provider base URL"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                spellCheck={false}
                className="mt-1 w-full p-2 rounded-lg bg-canvas border border-line text-xs font-mono text-ink focus:outline-none focus:border-violet"
              />
            </label>
            <label className="block text-xs font-mono">
              <span className="text-muted flex items-center gap-1.5">
                <KeyRound className="w-3.5 h-3.5" />
                API key
              </span>
              <input
                type="password"
                aria-label="API key"
                defaultValue={initialApiKeyRef.current}
                ref={keyInputRef}
                onChange={() => setApiKey(keyInputRef.current?.value ?? "")}
                placeholder="sk-…"
                autoComplete="off"
                spellCheck={false}
                className="mt-1 w-full p-2 rounded-lg bg-canvas border border-line text-xs font-mono text-ink placeholder-muted focus:outline-none focus:border-violet"
              />
            </label>
            <p className="text-[11px] font-mono text-muted">
              No key? Get a free one at AI Studio (aistudio.google.com):
              Gemini Flash has a free tier.
            </p>
            <p className="text-[11px] font-mono text-muted">
              Your key stays on your device + provider: it is sent only to the
              provider above via our proxy and never stored on our servers.
            </p>
            <label className="flex items-center gap-2 text-xs font-mono text-muted cursor-pointer">
              <input
                type="checkbox"
                aria-label="Remember on this device"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="accent-violet"
              />
              Remember on this device
            </label>
          </div>

          {/* Model picker */}
          <div className="flex flex-wrap items-end gap-2">
            <label className="flex-1 min-w-40 block text-xs font-mono">
              <span className="text-muted">Model</span>
              <select
                aria-label="Model"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                disabled={models.length === 0}
                className="mt-1 w-full p-2 rounded-lg bg-canvas border border-line text-xs font-mono text-ink focus:outline-none focus:border-violet disabled:opacity-60 cursor-pointer"
              >
                {models.length === 0 ? (
                  <option value="">Check models to load…</option>
                ) : (
                  models.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))
                )}
              </select>
            </label>
            <button
              onClick={handleCheckModels}
              disabled={modelsLoading || apiKey.trim().length === 0}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-surface border border-line text-xs font-mono text-ink hover:border-violet hover:text-violet transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${modelsLoading ? "animate-spin" : ""}`} />
              {modelsLoading ? "Checking…" : "Check models"}
            </button>
          </div>
          {modelsError && (
            <p role="alert" className="text-xs font-mono text-rose">
              {modelsError}
            </p>
          )}

          {/* Chat log */}
          <div
            aria-label="Tutor chat log"
            className="space-y-2 max-h-72 overflow-y-auto p-2 rounded-lg bg-canvas border border-line"
          >
            {messages.length === 0 ? (
              <p className="text-[11px] font-mono text-muted text-center py-4">
                {canChat
                  ? "Ask about the problem — the tutor sees the statement and your code."
                  : "Enter your API key and pick a model to start chatting."}
              </p>
            ) : (
              messages.map((m, i) => (
                <div
                  key={i}
                  className={`p-2.5 rounded-lg border text-xs font-mono leading-relaxed whitespace-pre-wrap ${
                    m.role === "user"
                      ? "bg-surface border-line text-ink ml-6"
                      : "bg-violet/10 border-violet/30 text-ink mr-6"
                  }`}
                >
                  <div
                    className={`text-[10px] font-bold uppercase tracking-wider mb-1 ${
                      m.role === "user" ? "text-muted" : "text-violet"
                    }`}
                  >
                    {m.role === "user" ? "You" : "Tutor"}
                  </div>
                  {m.content}
                </div>
              ))
            )}
          </div>
          {chatError && (
            <p role="alert" className="text-xs font-mono text-rose">
              {chatError}
            </p>
          )}

          {/* Composer */}
          <div className="flex items-center gap-2">
            <input
              type="text"
              aria-label="Your question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
              placeholder="Ask about this problem…"
              className="flex-1 p-2 rounded-lg bg-canvas border border-line text-xs font-mono text-ink placeholder-muted focus:outline-none focus:border-violet"
            />
            <button
              onClick={handleSend}
              disabled={!canChat || question.trim().length === 0 || sending}
              aria-label="Send question"
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-violet text-white font-mono font-semibold text-xs transition disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              {sending ? "Sending…" : "Send"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
