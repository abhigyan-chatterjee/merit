import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AiTutor } from "../src/components/AiTutor";
import { catalogIdForBaseUrl, useTutorKey } from "../src/hooks/useTutorKey";
import { useEffect } from "react";

const authState = vi.hoisted(() => ({ user: { id: "u1" } as { id: string } | null }));

vi.mock("../src/store/AuthContext", () => ({
  useAuth: () => ({ user: authState.user }),
}));

function SetCustomBaseUrl() {
  const tutor = useTutorKey();
  useEffect(() => {
    tutor.setBaseUrl("https://custom.example.test/v1");
    tutor.setModel("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return null;
}

function SetPresetTutor() {
  const tutor = useTutorKey();
  useEffect(() => {
    tutor.setBaseUrl("https://api.openai.com/v1");
    tutor.setModel("gpt-4o-mini");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return null;
}

const TEST_KEY = "sk-test-sentinel-9f8e7d6c5b4a";
const REPLY = "What information would a hash map let you remember?";

function jsonOk(payload: unknown): Response {
  return { ok: true, status: 200, json: async () => payload } as Response;
}

function mockFetch() {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    if (url === "https://models.dev/api.json") {
      return jsonOk({ openai: { models: { mini: { id: "gpt-4o-mini" }, full: { id: "gpt-4o" } } } });
    }
    if (url.includes("/api/v1/tutor/chat")) {
      const body = JSON.parse(String((init as RequestInit)?.body ?? "{}"));
      expect(body.api_key).toBe(TEST_KEY);
      return jsonOk({ reply: REPLY });
    }
    return jsonOk([]);
  });
}

function expandPanel() {
  fireEvent.click(screen.getByRole("button", { name: /ask the tutor/i }));
}

describe("AiTutor", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    authState.user = { id: "u1" };
    window.localStorage.clear();
    window.sessionStorage.clear();
  });

  it("does not apply a preset catalog to custom providers", () => {
    expect(catalogIdForBaseUrl("https://custom.example.test/v1")).toBeNull();
    expect(catalogIdForBaseUrl("https://api.openai.com/v1")).toBe("openai");
  });

  it("shows an account setup prompt when no key is configured", () => {
    render(
      <MemoryRouter>
        <AiTutor problemSlug="two-sum" />
      </MemoryRouter>,
    );
    expandPanel();
    expect(screen.getByText(/set up a provider and key on your account/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /open account/i })).toHaveAttribute("href", "/profile#tutor");
  });

  it("shows a sign-in gate and makes no tutor request when signed out", () => {
    authState.user = null;
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(async () => jsonOk([]));
    render(
      <MemoryRouter initialEntries={["/problems/arrays-hashing/two-sum?tab=code"]}>
        <AiTutor problemSlug="two-sum" defaultOpen />
      </MemoryRouter>,
    );
    expect(screen.getByText(/sign in to use the ai tutor/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute(
      "href",
      `/login?next=${encodeURIComponent("/problems/arrays-hashing/two-sum?tab=code")}`,
    );
    expect(screen.queryByLabelText(/your question/i)).not.toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("switching problemSlug resets chat messages", async () => {
    mockFetch();
    window.sessionStorage.setItem("merit_tutor_api_key", TEST_KEY);
    window.localStorage.setItem("merit_tutor_model", "gpt-4o-mini");
    const { rerender } = render(
      <MemoryRouter>
        <AiTutor problemSlug="two-sum" code="def solve(): pass" />
      </MemoryRouter>,
    );
    expandPanel();
    await waitFor(() => expect(screen.getByRole("option", { name: "gpt-4o-mini" })).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText(/your question/i), { target: { value: "nudge one" } });
    fireEvent.click(screen.getByRole("button", { name: /send question/i }));
    await waitFor(() => expect(screen.getByText(REPLY)).toBeInTheDocument());
    rerender(
      <MemoryRouter>
        <AiTutor problemSlug="other-problem" code="def solve(): pass" />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.queryByText(REPLY)).not.toBeInTheDocument();
      expect(screen.queryByText("nudge one")).not.toBeInTheDocument();
    });
  });

  it("preloads the provider catalog before a key exists", async () => {
    mockFetch();
    render(
      <MemoryRouter>
        <AiTutor problemSlug="two-sum" />
      </MemoryRouter>,
    );
    expandPanel();
    await waitFor(() => {
      expect(screen.getByRole("option", { name: "gpt-4o-mini" })).toBeInTheDocument();
    });
    expect(screen.queryByText(/check models to load/i)).not.toBeInTheDocument();
  });

  it("sends chat with a configured key and clears request errors on the next action", async () => {
    mockFetch();
    // The credential lives in sessionStorage only; localStorage is reserved for
    // the non-secret provider preferences.
    window.sessionStorage.setItem("merit_tutor_api_key", TEST_KEY);
    window.localStorage.setItem("merit_tutor_model", "gpt-4o-mini");
    render(
      <MemoryRouter>
        <AiTutor problemSlug="two-sum" code="def solve(): pass" />
      </MemoryRouter>,
    );
    expandPanel();
    await waitFor(() => expect(screen.getByRole("option", { name: "gpt-4o-mini" })).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText(/your question/i), { target: { value: "Give me a nudge." } });
    fireEvent.click(screen.getByRole("button", { name: /send question/i }));
    await waitFor(() => expect(screen.getByText(REPLY)).toBeInTheDocument());
    expect(screen.getByText("Give me a nudge.")).toBeInTheDocument();
    // The key must never be written to persistent storage.
    expect(window.localStorage.getItem("merit_tutor_api_key")).toBeNull();
  });

  it("custom baseUrl renders editable Model text input", async () => {
    mockFetch();
    window.sessionStorage.setItem("merit_tutor_api_key", TEST_KEY);
    render(
      <MemoryRouter>
        <SetCustomBaseUrl />
        <AiTutor problemSlug="two-sum" />
      </MemoryRouter>,
    );
    expandPanel();
    expect(await screen.findByLabelText("Model")).toBeInTheDocument();
    expect(screen.getByLabelText("Model")).toHaveAttribute("type", "text");
    fireEvent.change(screen.getByLabelText("Model"), { target: { value: "llama3.2" } });
    expect(screen.getByLabelText("Model")).toHaveValue("llama3.2");
  });

  it("sends prior turns as history with the active mode and clears the chat log", async () => {
    const bodies: Array<Record<string, unknown>> = [];
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url === "https://models.dev/api.json") {
        return jsonOk({ openai: { models: { mini: { id: "gpt-4o-mini" } } } });
      }
      if (url.includes("/api/v1/tutor/chat")) {
        bodies.push(JSON.parse(String((init as RequestInit)?.body ?? "{}")));
        return jsonOk({ reply: REPLY });
      }
      return jsonOk([]);
    });
    window.sessionStorage.setItem("merit_tutor_api_key", TEST_KEY);
    render(
      <MemoryRouter>
        <SetPresetTutor />
        <AiTutor problemSlug="two-sum" code="def solve(): pass" />
      </MemoryRouter>,
    );
    expandPanel();
    await waitFor(() => expect(screen.getByRole("option", { name: "gpt-4o-mini" })).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText(/your question/i), { target: { value: "first question" } });
    fireEvent.click(screen.getByRole("button", { name: /send question/i }));
    await waitFor(() => expect(bodies).toHaveLength(1));
    await waitFor(() => expect(screen.getByText(REPLY)).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText(/your question/i), { target: { value: "second question" } });
    fireEvent.click(screen.getByRole("button", { name: /send question/i }));
    await waitFor(() => expect(bodies).toHaveLength(2));

    expect(bodies[0]).toMatchObject({ mode: "socratic", history: [] });
    expect(bodies[1]).toMatchObject({
      mode: "socratic",
      history: [
        { role: "user", content: "first question" },
        { role: "assistant", content: REPLY },
      ],
    });

    fireEvent.click(screen.getByRole("button", { name: /clear chat/i }));
    expect(screen.queryByText("first question")).not.toBeInTheDocument();
    expect(screen.queryByText("second question")).not.toBeInTheDocument();
    expect(screen.queryByText(REPLY)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /clear chat/i })).not.toBeInTheDocument();
  });

  it("runs the mock interview timer and sends the rubric evaluation prompt", async () => {
    const RUBRIC_REPLY =
      "Problem Clarification 4/5 · Algorithmic Approach 3/5 · Code & Edge Cases 3/5 · Communication & Big-O 4/5 · Total 14/20 · Verdict: Hire.";
    const bodies: Array<Record<string, unknown>> = [];
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url === "https://models.dev/api.json") {
        return jsonOk({ openai: { models: { mini: { id: "gpt-4o-mini" } } } });
      }
      if (url.includes("/api/v1/tutor/chat")) {
        bodies.push(JSON.parse(String((init as RequestInit)?.body ?? "{}")));
        return jsonOk({ reply: RUBRIC_REPLY });
      }
      return jsonOk([]);
    });
    window.sessionStorage.setItem("merit_tutor_api_key", TEST_KEY);
    render(
      <MemoryRouter>
        <SetPresetTutor />
        <AiTutor problemSlug="two-sum" code="def solve(): pass" />
      </MemoryRouter>,
    );
    expandPanel();
    await waitFor(() => expect(screen.getByRole("option", { name: "gpt-4o-mini" })).toBeInTheDocument());
    expect(screen.queryByText("30:00")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Mock Interview" }));
    expect(screen.getByText("30:00")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /start mock/i })).toBeInTheDocument();
    fireEvent.click(screen.getByText(/Stages & scoring/i));
    expect(screen.getByText("1. Clarify")).toBeInTheDocument();
    expect(screen.getByText("2. Approach & Big-O")).toBeInTheDocument();
    expect(screen.getByText("3. Dry-Run & Edge Cases")).toBeInTheDocument();
    expect(screen.getByText("4. Rubric")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /score my interview \(rubric\)/i }));
    await waitFor(() => expect(bodies).toHaveLength(1));
    expect(bodies[0]).toMatchObject({
      mode: "interview",
      question: "Evaluate my mock interview and current code with the 4-dimension placement rubric (/20) and Hire Verdict.",
    });
    await waitFor(() => expect(screen.getByText(RUBRIC_REPLY)).toBeInTheDocument());
  });

  it("pins the model configured in settings instead of resetting to the catalog's first entry", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url === "https://models.dev/api.json") {
        return jsonOk({
          google: {
            models: {
              live: { id: "gemini-3.1-flash-live-preview" },
              gemma: { id: "gemma-4-31b-it" },
            },
          },
        });
      }
      return jsonOk([]);
    });
    window.localStorage.setItem("merit_tutor_base_url", "https://generativelanguage.googleapis.com/v1beta/openai");
    window.localStorage.setItem("merit_tutor_model", "gemma-4-31b-it");
    window.sessionStorage.setItem("merit_tutor_api_key", TEST_KEY);

    render(
      <MemoryRouter>
        <AiTutor problemSlug="two-sum" defaultOpen />
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByRole("option", { name: "gemini-3.1-flash-live-preview" })).toBeInTheDocument());
    expect(screen.getByLabelText("Model")).toHaveValue("gemma-4-31b-it");
  });

  it("renders a three-dot loading placeholder while the tutor is responding", async () => {
    let resolveChat: ((value: Response) => void) | undefined;
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url === "https://models.dev/api.json") {
        return Promise.resolve(jsonOk({ openai: { models: { mini: { id: "gpt-4o-mini" } } } }));
      }
      if (url.includes("/api/v1/tutor/chat")) {
        return new Promise<Response>((resolve) => {
          resolveChat = resolve;
        });
      }
      return Promise.resolve(jsonOk([]));
    });
    window.sessionStorage.setItem("merit_tutor_api_key", TEST_KEY);
    window.localStorage.setItem("merit_tutor_model", "gpt-4o-mini");

    render(
      <MemoryRouter>
        <AiTutor problemSlug="two-sum" defaultOpen />
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByLabelText("Model")).toHaveValue("gpt-4o-mini"));
    fireEvent.change(screen.getByLabelText(/your question/i), { target: { value: "How do I start?" } });
    fireEvent.click(screen.getByRole("button", { name: /send question/i }));

    expect(await screen.findByRole("status", { name: /tutor is responding/i })).toBeInTheDocument();
    resolveChat?.(jsonOk({ reply: REPLY }));
    await waitFor(() => expect(screen.getByText(REPLY)).toBeInTheDocument());
    expect(screen.queryByRole("status", { name: /tutor is responding/i })).not.toBeInTheDocument();
  });

  it("starts an interactive mock interview session when clicking Start mock", async () => {
    const INTERVIEW_OPENING = "Welcome! Before you write any code for Two Sum, what clarifying questions do you have about the input constraints?";
    const bodies: Array<Record<string, unknown>> = [];
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url === "https://models.dev/api.json") {
        return jsonOk({ openai: { models: { mini: { id: "gpt-4o-mini" } } } });
      }
      if (url.includes("/api/v1/tutor/chat")) {
        bodies.push(JSON.parse(String((init as RequestInit)?.body ?? "{}")));
        return jsonOk({ reply: INTERVIEW_OPENING });
      }
      return jsonOk([]);
    });
    window.sessionStorage.setItem("merit_tutor_api_key", TEST_KEY);
    window.localStorage.setItem("merit_tutor_model", "gpt-4o-mini");

    render(
      <MemoryRouter>
        <AiTutor problemSlug="two-sum" defaultOpen />
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByLabelText("Model")).toHaveValue("gpt-4o-mini"));
    fireEvent.click(screen.getByRole("button", { name: "Mock Interview" }));
    fireEvent.click(screen.getByRole("button", { name: /start mock/i }));

    await waitFor(() => expect(bodies).toHaveLength(1));
    expect(bodies[0]).toMatchObject({ mode: "interview" });
    await waitFor(() => expect(screen.getByText(INTERVIEW_OPENING)).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Pause" })).toBeInTheDocument();
  });

  it("resets the chat log when switching coaching modes", async () => {
    mockFetch();
    window.sessionStorage.setItem("merit_tutor_api_key", TEST_KEY);
    window.localStorage.setItem("merit_tutor_model", "gpt-4o-mini");

    render(
      <MemoryRouter>
        <AiTutor problemSlug="two-sum" defaultOpen />
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByLabelText("Model")).toHaveValue("gpt-4o-mini"));
    fireEvent.change(screen.getByLabelText(/your question/i), { target: { value: "First mode question" } });
    fireEvent.click(screen.getByRole("button", { name: /send question/i }));
    await waitFor(() => expect(screen.getByText(REPLY)).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Step Hint" }));
    expect(screen.queryByText("First mode question")).not.toBeInTheDocument();
    expect(screen.queryByText(REPLY)).not.toBeInTheDocument();
  });
});
