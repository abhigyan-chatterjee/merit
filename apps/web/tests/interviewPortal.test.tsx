import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { InterviewPortalPage } from "../src/pages/InterviewPortalPage";
import { AuthProvider } from "../src/store/AuthContext";
import { ProgressProvider } from "../src/store/ProgressContext";
import {
  TIER_BY_ID,
  pickRandomProblemsForDifficulty,
  problemToInterviewSummary,
} from "../src/components/interview/interviewConfig";
import { InterviewSessionDetail } from "../src/utils/api";

const GEMINI_CATALOG = {
  google: {
    models: {
      "gemini-3.1-flash-live-preview": { id: "gemini-3.1-flash-live-preview" },
      "gemma-4-31b-it": { id: "gemma-4-31b-it" },
    },
  },
};

const PROFILE = {
  id: "u1",
  email: "abhi@nullbit.in",
  display_name: "Abhi",
  role: "student",
  created_at: "2026-11-01T00:00:00Z",
};

const PROGRESS = { due_today_count: 0, activity_days: {}, quiz_scores: {} };

const RUBRIC = {
  dimensions: [
    { name: "CS Fundamentals", score: 4, max_score: 5, comment: "Clear answers" },
    { name: "Problem Solving & Approach", score: 5, max_score: 5, comment: "Optimal" },
  ],
  total: 9,
  max_total: 10,
  verdict: "Strong Hire",
  strengths: ["Fast Big-O explanation"],
  improvements: ["Talk through base cases early"],
  summary: "Strong fundamentals and clean coding.",
};

const NOW = "2026-11-24T00:00:00Z";

function makeDetail(): InterviewSessionDetail {
  const tier = TIER_BY_ID.easy;
  const problems = pickRandomProblemsForDifficulty("easy");
  return {
    id: "sess-live",
    difficulty: "easy",
    status: "in_progress",
    current_stage: "theory",
    duration_sec: tier.durationSec,
    elapsed_sec: 0,
    problem_slugs: problems.map((p) => p.slug),
    has_resume: false,
    resume_filename: null,
    resume_text: null,
    project_brief: null,
    stages: tier.stages,
    problems: problems.map(problemToInterviewSummary),
    messages: [],
    coding_snapshots: {},
    max_score: tier.maxScore,
    created_at: NOW,
    updated_at: NOW,
  };
}

function withMessage(session: InterviewSessionDetail, reply: string, stage: string): InterviewSessionDetail {
  return {
    ...session,
    messages: [
      ...session.messages,
      { role: "interviewer", content: reply, stage, created_at: NOW },
    ],
  };
}

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function renderPortal(initialEntry = "/interview") {
  return render(
    <AuthProvider>
      <ProgressProvider>
        <MemoryRouter initialEntries={[initialEntry]}>
          <Routes>
            <Route path="/interview" element={<InterviewPortalPage />} />
            <Route path="/interview/:sessionId" element={<InterviewPortalPage />} />
          </Routes>
        </MemoryRouter>
      </ProgressProvider>
    </AuthProvider>,
  );
}

describe("InterviewPortalPage", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
    window.localStorage.setItem(
      "merit_tutor_base_url",
      "https://generativelanguage.googleapis.com/v1beta/openai",
    );
    window.localStorage.setItem("merit_tutor_model", "gemma-4-31b-it");
    window.sessionStorage.setItem("merit_tutor_api_key", "sk-test-interview-key");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("gates the portal behind sign-in and creates no interview session", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/api/v1/auth/me") || url.includes("/api/v1/auth/refresh")) {
        return new Response(JSON.stringify({ detail: { code: "UNAUTHORIZED" } }), { status: 401 });
      }
      return new Response("{}", { status: 200 });
    });

    renderPortal();

    expect(
      await screen.findByText(/sign in to run live-judged mock interviews and save scorecards/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute(
      "href",
      "/login?next=/interview",
    );
    expect(
      fetchSpy.mock.calls.some(([input]) => String(input).includes("/api/v1/interview/")),
    ).toBe(false);
  });

  it("pins configured model, switches difficulties, and uploads CV PDF", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/api/v1/auth/me")) {
        return jsonResponse(PROFILE);
      }
      if (url.includes("/api/v1/progress/summary")) {
        return jsonResponse(PROGRESS);
      }
      if (url.endsWith("/api/v1/interview/sessions")) {
        return jsonResponse([]);
      }
      if (url === "https://models.dev/api.json") {
        return jsonResponse(GEMINI_CATALOG);
      }
      if (url.endsWith("/api/v1/interview/parse-resume")) {
        return jsonResponse({
          filename: "abhi_resume.pdf",
          pages: 1,
          char_count: 1420,
          truncated: false,
          extracted_text: "Built sharded task queue in Go & Redis.",
        });
      }
      return jsonResponse({});
    });

    renderPortal();

    const modelSelect = await screen.findByLabelText("Interviewer Model");
    await waitFor(() => expect((modelSelect as HTMLSelectElement).value).toBe("gemma-4-31b-it"));

    await user.click(screen.getByRole("button", { name: /^Hard/i }));
    expect(screen.getByText(/6 rounds · \/30/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Start 60m Interview/i })).toBeInTheDocument();

    const fileInput = screen.getByLabelText("Upload CV PDF") as HTMLInputElement;
    const pdfFile = new File(["%PDF-1.4 resume"], "abhi_resume.pdf", { type: "application/pdf" });
    fireEvent.change(fileInput, { target: { files: [pdfFile] } });

    expect(await screen.findByText("abhi_resume.pdf")).toBeInTheDocument();
  });

  it("rejects a resume larger than 2 MB before uploading", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/api/v1/auth/me")) return jsonResponse(PROFILE);
      if (url.includes("/api/v1/progress/summary")) return jsonResponse(PROGRESS);
      if (url.endsWith("/api/v1/interview/sessions")) return jsonResponse([]);
      if (url === "https://models.dev/api.json") return jsonResponse(GEMINI_CATALOG);
      return jsonResponse({});
    });

    renderPortal();
    await screen.findByLabelText("Interviewer Model");

    const fileInput = screen.getByLabelText("Upload CV PDF") as HTMLInputElement;
    const bigPdf = new File([new Uint8Array(2 * 1024 * 1024 + 1)], "big.pdf", {
      type: "application/pdf",
    });
    fireEvent.change(fileInput, { target: { files: [bigPdf] } });

    expect(await screen.findByText("Resume PDF must be 2 MB or smaller.")).toBeInTheDocument();
    expect(globalThis.fetch).not.toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/interview/parse-resume"),
      expect.anything(),
    );
  });

  it("runs the signed-in interview loop from kickoff to coding stage and final rubric", async () => {
    const user = userEvent.setup();
    let live = makeDetail();
    let resolveTurn!: (reply: string) => void;
    const capturedTurns: Array<Record<string, unknown>> = [];

    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/api/v1/auth/me")) {
        return jsonResponse(PROFILE);
      }
      if (url.includes("/api/v1/progress/summary")) {
        return jsonResponse(PROGRESS);
      }
      if (url.endsWith("/api/v1/interview/sessions") && init?.method === "POST") {
        live = makeDetail();
        return jsonResponse(live);
      }
      if (url.endsWith("/api/v1/interview/sessions") && (!init?.method || init.method === "GET")) {
        return jsonResponse([]);
      }
      if (url.endsWith("/api/v1/interview/sessions/sess-live")) {
        return jsonResponse(live);
      }
      if (url === "https://models.dev/api.json") {
        return jsonResponse(GEMINI_CATALOG);
      }
      if (url.endsWith("/api/v1/interview/sessions/sess-live/turn")) {
        const parsed = JSON.parse(String(init?.body ?? "{}"));
        capturedTurns.push(parsed);
        if (parsed.action === "start") {
          return new Promise<Response>((resolve) => {
            resolveTurn = (reply) => {
              live = withMessage(live, reply, "theory");
              resolve(jsonResponse({ reply, session: live }));
            };
          });
        }
        if (parsed.action === "advance_stage") {
          const reply = "Let's solve the coding problem in the editor.";
          live = { ...withMessage(live, reply, "coding_1"), current_stage: "coding_1" };
          return jsonResponse({ reply, session: live });
        }
        if (parsed.action === "message") {
          const reply = "What is the time complexity of your solution?";
          live = withMessage(live, reply, "coding_1");
          return jsonResponse({ reply, session: live });
        }
        if (parsed.action === "evaluate") {
          const reply = "Strong fundamentals and clean coding.";
          live = {
            ...withMessage(live, reply, "rubric"),
            status: "completed",
            current_stage: "rubric",
            rubric: RUBRIC,
          };
          return jsonResponse({ reply, session: live });
        }
      }
      return jsonResponse({});
    });

    renderPortal();
    await user.click(screen.getByRole("button", { name: /^Easy/i }));
    await user.click(screen.getByRole("button", { name: /Start 30m Interview/i }));

    expect(await screen.findByRole("status", { name: "Interviewer is responding" })).toBeInTheDocument();

    resolveTurn("Welcome! Explain how hash maps handle collisions.");

    expect(
      await screen.findByText("Welcome! Explain how hash maps handle collisions."),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Next Round/i }));
    expect(
      await screen.findByText("Let's solve the coding problem in the editor."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Code Editor")).toBeInTheDocument();

    const responseBox = screen.getByLabelText("Your interview response");
    await user.type(responseBox, "My approach is O(n) with a hash map.");
    await user.click(screen.getByRole("button", { name: /Send response/i }));
    await waitFor(() => expect(capturedTurns.some((t) => t.action === "message")).toBe(true));
    const msgTurn = capturedTurns.find((t) => t.action === "message");
    expect((msgTurn?.coding_snapshot as { language?: string })?.language).toBeTruthy();

    await user.click(screen.getByRole("button", { name: /End & Score/i }));
    expect(await screen.findByTestId("rubric-verdict")).toHaveTextContent("Strong Hire");
    expect(screen.getByText("CS Fundamentals")).toBeInTheDocument();
  });

  it("shows inline stage-transition CTA and renders interviewer Markdown", async () => {
    const user = userEvent.setup();
    let live = makeDetail();
    const capturedTurns: Array<Record<string, unknown>> = [];

    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/api/v1/auth/me")) {
        return jsonResponse(PROFILE);
      }
      if (url.includes("/api/v1/progress/summary")) {
        return jsonResponse(PROGRESS);
      }
      if (url.endsWith("/api/v1/interview/sessions") && init?.method === "POST") {
        live = makeDetail();
        return jsonResponse(live);
      }
      if (url.endsWith("/api/v1/interview/sessions") && (!init?.method || init.method === "GET")) {
        return jsonResponse([]);
      }
      if (url.endsWith("/api/v1/interview/sessions/sess-live")) {
        return jsonResponse(live);
      }
      if (url === "https://models.dev/api.json") {
        return jsonResponse(GEMINI_CATALOG);
      }
      if (url.endsWith("/api/v1/interview/sessions/sess-live/turn")) {
        const parsed = JSON.parse(String(init?.body ?? "{}"));
        capturedTurns.push(parsed);
        if (parsed.action === "start") {
          const reply = "**Problem:** Use `nums` to find the pair";
          live = withMessage(live, reply, "theory");
          return jsonResponse({ reply, suggested_stage: "coding_1", session: live });
        }
        if (parsed.action === "advance_stage") {
          const reply = "Let's code it up.";
          live = { ...withMessage(live, reply, "coding_1"), current_stage: "coding_1" };
          return jsonResponse({ reply, session: live });
        }
      }
      return jsonResponse({});
    });

    renderPortal();
    await user.click(screen.getByRole("button", { name: /^Easy/i }));
    await user.click(screen.getByRole("button", { name: /Start 30m Interview/i }));

    const transcript = await screen.findByLabelText("Interview transcript");
    await waitFor(() => expect(transcript.querySelector("strong")).not.toBeNull());
    expect(transcript.querySelector("strong")).toHaveTextContent("Problem:");
    expect(transcript.querySelector("code")).toHaveTextContent("nums");
    expect(transcript.textContent).not.toContain("**");

    const cta = await screen.findByRole("button", { name: /Open Coding.*Editor/i });
    expect(cta).toBeInTheDocument();

    await user.click(cta);
    await waitFor(() =>
      expect(capturedTurns.some((t) => t.action === "advance_stage" && t.stage === "coding_1")).toBe(
        true,
      ),
    );
    expect(await screen.findByLabelText("Code Editor")).toBeInTheDocument();
  });

  it("shows signed-in DB interview history and supports resuming and deleting", async () => {
    const user = userEvent.setup();
    let sessionsState = [
      {
        id: "sess-123",
        difficulty: "medium",
        status: "completed",
        current_stage: "rubric",
        duration_sec: 2700,
        elapsed_sec: 2400,
        problem_slugs: ["two-sum", "lru-cache"],
        has_resume: true,
        resume_filename: "cv.pdf",
        overall_verdict: "Hire",
        overall_score: 21,
        max_score: 25,
        created_at: "2026-11-23T12:00:00Z",
        updated_at: "2026-11-23T12:40:00Z",
        completed_at: "2026-11-23T12:40:00Z",
      },
    ];

    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/api/v1/auth/me")) {
        return jsonResponse(PROFILE);
      }
      if (url.includes("/api/v1/progress/summary")) {
        return jsonResponse(PROGRESS);
      }
      if (url.endsWith("/api/v1/interview/sessions") && (!init?.method || init.method === "GET")) {
        return jsonResponse(sessionsState);
      }
      if (url.endsWith("/api/v1/interview/sessions/sess-123") && init?.method === "DELETE") {
        sessionsState = [];
        return new Response(null, { status: 204 });
      }
      if (url === "https://models.dev/api.json") {
        return jsonResponse(GEMINI_CATALOG);
      }
      return jsonResponse({});
    });

    renderPortal();
    expect(await screen.findByText(/Hire \(21\/25\)/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "View Scorecard" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Delete medium interview" }));
    await user.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => expect(screen.queryByText(/Hire \(21\/25\)/i)).not.toBeInTheDocument());
  });
});
