import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AiTutor } from "../src/components/AiTutor";
import { catalogIdForBaseUrl } from "../src/hooks/useTutorKey";

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
  });

  it("does not apply a preset catalog to custom providers", () => {
    expect(catalogIdForBaseUrl("https://custom.example.test/v1")).toBeNull();
    expect(catalogIdForBaseUrl("https://api.openai.com/v1")).toBe("openai");
  });

  it("shows an account setup prompt when no key is configured", () => {
    render(<AiTutor problemSlug="two-sum" />);
    expandPanel();
    expect(screen.getByText(/set up a provider and key on your account/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /open account/i })).toHaveAttribute("href", "/profile#tutor");
  });

  it("preloads the provider catalog before a key exists", async () => {
    mockFetch();
    render(<AiTutor problemSlug="two-sum" />);
    expandPanel();
    await waitFor(() => {
      expect(screen.getByRole("option", { name: "gpt-4o-mini" })).toBeInTheDocument();
    });
    expect(screen.queryByText(/check models to load/i)).not.toBeInTheDocument();
  });

  it("sends chat with a configured key and clears request errors on the next action", async () => {
    mockFetch();
    window.localStorage.setItem("merit_tutor_api_key", TEST_KEY);
    window.localStorage.setItem("merit_tutor_model", "gpt-4o-mini");
    render(<AiTutor problemSlug="two-sum" code="def solve(): pass" />);
    expandPanel();
    await waitFor(() => expect(screen.getByRole("option", { name: "gpt-4o-mini" })).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText(/your question/i), { target: { value: "Give me a nudge." } });
    fireEvent.click(screen.getByRole("button", { name: /send question/i }));
    await waitFor(() => expect(screen.getByText(REPLY)).toBeInTheDocument());
    expect(screen.getByText("Give me a nudge.")).toBeInTheDocument();
  });
});
