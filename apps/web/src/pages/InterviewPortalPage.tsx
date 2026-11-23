import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Problem } from "../data/problems";
import {
  catalogIdForBaseUrl,
  getTutorSnapshot,
  loadTutorCatalog,
  useTutorKey,
} from "../hooks/useTutorKey";
import { useAuth } from "../store/AuthContext";
import {
  ApiError,
  InterviewCodingSnapshot,
  InterviewDifficulty,
  InterviewMessage,
  InterviewSessionDetail,
  InterviewSessionSummary,
  ResumeParseResponse,
  interviewApi,
} from "../utils/api";
import { InterviewSetupLobby } from "../components/interview/InterviewSetupLobby";
import { InterviewWorkspace } from "../components/interview/InterviewWorkspace";
import { pickRandomProblemsForDifficulty } from "../components/interview/interviewConfig";

export const InterviewPortalPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();
  const { user, isLoading: authLoading } = useAuth();
  const { apiKey, baseUrl, model, setModel } = useTutorKey();

  // Setup lobby state
  const [difficulty, setDifficulty] = useState<InterviewDifficulty>("medium");
  const [selectedProblems, setSelectedProblems] = useState<Problem[]>(() =>
    pickRandomProblemsForDifficulty("medium"),
  );
  const [hideTitles, setHideTitles] = useState(true);
  const [resumeData, setResumeData] = useState<ResumeParseResponse | null>(null);
  const [projectBrief, setProjectBrief] = useState("");
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  // History list (signed-in DB sessions)
  const [sessions, setSessions] = useState<InterviewSessionSummary[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  // Active workspace state
  const [activeSession, setActiveSession] = useState<InterviewSessionDetail | null>(null);
  const [elapsedSec, setElapsedSec] = useState(0);
  const [timerRunning, setTimerRunning] = useState(false);
  const [sending, setSending] = useState(false);
  const [suggestedStage, setSuggestedStage] = useState<string | null>(null);
  const [turnError, setTurnError] = useState<string | null>(null);
  const [loadingSession, setLoadingSession] = useState(false);
  const [models, setModels] = useState<string[]>([]);

  const snapshotsRef = useRef<Record<string, InterviewCodingSnapshot>>({});
  const loadedSessionIdRef = useRef<string | null>(null);
  const elapsedRef = useRef(0);
  useEffect(() => {
    elapsedRef.current = elapsedSec;
  }, [elapsedSec]);

  const hasCatalog = Boolean(catalogIdForBaseUrl(baseUrl));
  useEffect(() => {
    if (!user) {
      setModels([]);
      return;
    }
    const catalogId = catalogIdForBaseUrl(baseUrl);
    if (!catalogId) {
      setModels([]);
      return;
    }
    let cancelled = false;
    void loadTutorCatalog(catalogId)
      .then((list) => {
        if (cancelled) return;
        setModels(list);
        if (list.length > 0 && !getTutorSnapshot().model.trim()) {
          setModel(list[0]);
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [baseUrl, user]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSelectDifficulty = (nextDiff: InterviewDifficulty) => {
    setDifficulty(nextDiff);
    setSelectedProblems(pickRandomProblemsForDifficulty(nextDiff));
    setStartError(null);
  };

  const refreshSessionsList = useCallback(async () => {
    if (!user) {
      setSessions([]);
      return;
    }
    setSessionsLoading(true);
    try {
      const list = await interviewApi.listSessions();
      setSessions(list);
    } catch {
      // Leave current list as-is on transient error
    } finally {
      setSessionsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    void refreshSessionsList();
  }, [refreshSessionsList]);

  useEffect(() => {
    if (!sessionId) {
      loadedSessionIdRef.current = null;
      setActiveSession(null);
      setSuggestedStage(null);
      setTimerRunning(false);
      return;
    }
    if (!user || loadedSessionIdRef.current === sessionId) return;
    let cancelled = false;
    setLoadingSession(true);
    setSuggestedStage(null);
    setTurnError(null);
    void interviewApi
      .getSession(sessionId)
      .then((detail) => {
        if (cancelled) return;
        loadedSessionIdRef.current = detail.id;
        setActiveSession(detail);
        snapshotsRef.current = detail.coding_snapshots ?? {};
        setElapsedSec(detail.elapsed_sec ?? 0);
        setTimerRunning(detail.status !== "completed");
      })
      .catch(() => {
        if (!cancelled) {
          setStartError("Could not load the requested interview session.");
          navigate("/interview", { replace: true });
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingSession(false);
      });
    return () => {
      cancelled = true;
    };
  }, [sessionId, user, navigate]);

  // Live countdown ticker
  useEffect(() => {
    if (!timerRunning || !activeSession || activeSession.status === "completed") return;
    if (elapsedSec >= activeSession.duration_sec) {
      setTimerRunning(false);
      return;
    }
    const timer = window.setTimeout(() => setElapsedSec((prev) => prev + 1), 1000);
    return () => window.clearTimeout(timer);
  }, [timerRunning, elapsedSec, activeSession]);

  // Periodic DB autosave for signed-in sessions
  const activeId = activeSession?.id;
  const activeStatus = activeSession?.status;
  useEffect(() => {
    if (!activeId || activeStatus === "completed") return;
    const interval = window.setInterval(() => {
      void interviewApi
        .updateSession(activeId, {
          elapsed_sec: elapsedRef.current,
          coding_snapshots: snapshotsRef.current,
        })
        .catch(() => undefined);
    }, 15_000);
    return () => window.clearInterval(interval);
  }, [activeId, activeStatus]);

  const executeTurn = async (
    targetSession: InterviewSessionDetail,
    opts: {
      action: "start" | "message" | "advance_stage" | "evaluate";
      message?: string;
      stageId?: string;
      designNotes?: string;
    },
  ) => {
    const snap = getTutorSnapshot();
    const liveKey = snap.apiKey.trim() || apiKey.trim();
    const liveBase = snap.baseUrl.trim() || baseUrl.trim();
    const liveModel = snap.model.trim() || model.trim();
    if (!liveKey || !liveModel) {
      setTurnError("Configure a BYOK API key and model in Account Settings before chatting.");
      return;
    }

    const stageId = opts.stageId ?? targetSession.current_stage;
    const stageDef =
      targetSession.stages.find((s) => s.id === stageId) ?? targetSession.stages[0];
    const activeProb =
      stageDef?.kind === "coding"
        ? (targetSession.problems[stageDef.problem_index ?? 0] ?? targetSession.problems[0] ?? null)
        : null;
    const codingSnap = activeProb ? snapshotsRef.current[activeProb.slug] : undefined;

    setTurnError(null);
    setSending(true);

    // Optimistically show user message & stage in workspace immediately
    const optimisticStage = opts.action === "evaluate" ? "rubric" : stageId;
    if (opts.action === "message" && opts.message) {
      const userTurn: InterviewMessage = {
        role: "user",
        content: opts.message,
        stage: optimisticStage,
        created_at: new Date().toISOString(),
      };
      setActiveSession((prev) =>
        prev
          ? {
              ...prev,
              current_stage: optimisticStage,
              messages: [...prev.messages, userTurn],
            }
          : prev,
      );
    } else if (opts.action === "advance_stage") {
      setActiveSession((prev) => (prev ? { ...prev, current_stage: stageId } : prev));
      setSuggestedStage(null);
    } else if (opts.action === "evaluate") {
      setSuggestedStage(null);
    }

    try {
      const res = await interviewApi.sendTurn(targetSession.id, {
        base_url: liveBase,
        api_key: liveKey,
        model: liveModel,
        action: opts.action,
        message: opts.message ?? "",
        stage: optimisticStage,
        elapsed_sec: elapsedRef.current,
        active_problem_slug: activeProb?.slug ?? null,
        coding_snapshot: codingSnap,
        design_notes: opts.designNotes,
      });
      setActiveSession(res.session);
      snapshotsRef.current = { ...(res.session.coding_snapshots ?? {}), ...snapshotsRef.current };
      if (opts.action === "advance_stage" || opts.action === "evaluate") {
        setSuggestedStage(null);
      } else {
        setSuggestedStage(res.suggested_stage ?? null);
      }
      if (res.session.status === "completed") {
        setTimerRunning(false);
        void refreshSessionsList();
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setTurnError(err.message || "Interviewer request failed. Please try again.");
      } else {
        setTurnError("Could not reach the interview service. Is the API server running?");
      }
    } finally {
      setSending(false);
    }
  };

  const handleStartInterview = async () => {
    setStartError(null);
    setSuggestedStage(null);
    const snap = getTutorSnapshot();
    const liveKey = snap.apiKey.trim() || apiKey.trim();
    const liveModel = snap.model.trim() || model.trim();
    if (!liveKey || !liveModel) {
      setStartError("Add a BYOK key and choose a model in Account Settings before starting.");
      return;
    }
    const slugs = selectedProblems.map((p) => p.slug);
    setStarting(true);
    try {
      const detail = await interviewApi.createSession({
        difficulty,
        problem_slugs: slugs,
        resume_filename: resumeData?.filename ?? null,
        resume_text: resumeData?.extracted_text ?? null,
        project_brief: projectBrief.trim() || null,
      });
      navigate(`/interview/${detail.id}`, { replace: false });
      void refreshSessionsList();
      loadedSessionIdRef.current = detail.id;
      snapshotsRef.current = detail.coding_snapshots ?? {};
      setActiveSession(detail);
      setElapsedSec(0);
      setTimerRunning(true);
      await executeTurn(detail, { action: "start", stageId: detail.current_stage });
    } catch (err) {
      if (err instanceof ApiError) {
        setStartError(err.message || "Could not create interview session.");
      } else {
        setStartError("Could not start the interview session.");
      }
    } finally {
      setStarting(false);
    }
  };

  const handleBackToLobby = () => {
    setTimerRunning(false);
    setSuggestedStage(null);
    setActiveSession(null);
    setTurnError(null);
    navigate("/interview");
    void refreshSessionsList();
  };

  const handleDeleteSession = async (targetId: string) => {
    try {
      await interviewApi.deleteSession(targetId);
      setSessions((prev) => prev.filter((item) => item.id !== targetId));
    } catch {
      setStartError("Failed to delete session.");
    }
  };

  const handleCodeSnapshot = (
    slug: string,
    snapshot: InterviewCodingSnapshot,
    flushImmediately: boolean,
  ) => {
    const prevSnap = snapshotsRef.current[slug];
    snapshotsRef.current = { ...snapshotsRef.current, [slug]: snapshot };
    if (
      flushImmediately ||
      !prevSnap ||
      prevSnap.language !== snapshot.language ||
      prevSnap.verdict !== snapshot.verdict ||
      prevSnap.passed_count !== snapshot.passed_count
    ) {
      setActiveSession((prev) =>
        prev
          ? { ...prev, coding_snapshots: { ...prev.coding_snapshots, [slug]: snapshot } }
          : prev,
      );
    }
    if (flushImmediately && activeSession) {
      void interviewApi
        .updateSession(activeSession.id, {
          elapsed_sec: elapsedRef.current,
          coding_snapshots: { [slug]: snapshot },
        })
        .catch(() => undefined);
    }
  };

  const canChat = Boolean(apiKey.trim() && model.trim());

  if (!authLoading && !user) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-ink">Mock Interview</h1>
            <p className="text-xs text-muted mt-1">
              Sign in to run live-judged mock interviews and save scorecards.
            </p>
          </div>
          <Link
            to="/login?next=/interview"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-mint/40 bg-mint/10 text-xs font-mono font-semibold text-mint hover:bg-mint/20 transition"
          >
            Sign in
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {loadingSession && !activeSession ? (
        <div className="p-10 text-center font-mono text-xs text-muted">
          Loading interview session…
        </div>
      ) : activeSession ? (
        <InterviewWorkspace
          session={activeSession}
          models={models}
          hasCatalog={hasCatalog}
          model={model}
          onModelChange={setModel}
          canChat={canChat}
          sending={sending}
          suggestedStage={suggestedStage}
          error={turnError}
          elapsedSec={elapsedSec}
          timerRunning={timerRunning}
          onToggleTimer={() => setTimerRunning((v) => !v)}
          onSelectStage={(stageId) => {
            if (!activeSession || sending) return;
            setSuggestedStage(null);
            if (activeSession.status === "completed") {
              setActiveSession((prev) => (prev ? { ...prev, current_stage: stageId } : prev));
              return;
            }
            void executeTurn(activeSession, {
              action: "advance_stage",
              stageId,
            });
          }}
          onSendMessage={(msg, opts) => {
            if (!activeSession || sending) return;
            void executeTurn(activeSession, {
              action: "message",
              message: msg,
              designNotes: opts?.designNotes,
            });
          }}
          onEvaluate={(designNotes) => {
            if (!activeSession || sending) return;
            setSuggestedStage(null);
            void executeTurn(activeSession, {
              action: "evaluate",
              stageId: "rubric",
              designNotes,
            });
          }}
          onCodeChange={(slug, snapshot) => handleCodeSnapshot(slug, snapshot, false)}
          onJudgeResult={(slug, snapshot) => handleCodeSnapshot(slug, snapshot, true)}
          onBackToLobby={handleBackToLobby}
          onStartNew={handleBackToLobby}
        />
      ) : (
        <InterviewSetupLobby
          difficulty={difficulty}
          onSelectDifficulty={handleSelectDifficulty}
          selectedProblems={selectedProblems}
          onShuffleProblems={() => setSelectedProblems(pickRandomProblemsForDifficulty(difficulty))}
          hideTitles={hideTitles}
          onToggleHideTitles={() => setHideTitles((v) => !v)}
          resumeData={resumeData}
          onResumeParsed={setResumeData}
          projectBrief={projectBrief}
          onProjectBriefChange={setProjectBrief}
          onStartInterview={() => void handleStartInterview()}
          starting={starting}
          startError={startError}
          sessions={sessions}
          sessionsLoading={sessionsLoading}
          isAuthenticated={Boolean(user)}
          onResumeSession={(id) => navigate(`/interview/${id}`)}
          onDeleteSession={(id) => void handleDeleteSession(id)}
        />
      )}
    </div>
  );
};
