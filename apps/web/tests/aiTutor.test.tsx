import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AiTutor } from "../src/components/AiTutor";
import { catalogIdForBaseUrl, useTutorKey } from "../src/hooks/useTutorKey";
import { useEffect } from "react";

function SetCustomBaseUrl() {
  const tutor = useTutorKey();
  useEffect(() => {
    tutor.setBaseUrl("https://custom.example.test/v1");
    tutor.setModel("");
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
});
