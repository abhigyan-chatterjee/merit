import { useEffect, useSyncExternalStore } from "react";

export const TUTOR_DEFAULT_BASE_URL = "https://api.openai.com/v1";

export interface TutorPreset {
  id: string;
  label: string;
  baseUrl: string;
  catalogId: string;
}

export const TUTOR_PRESETS: TutorPreset[] = [
  { id: "openai", label: "OpenAI", baseUrl: TUTOR_DEFAULT_BASE_URL, catalogId: "openai" },
  {
    id: "gemini",
    label: "Gemini (OpenAI-compatible)",
    baseUrl: "https://generativelanguage.googleapis.com/v1beta/openai",
    catalogId: "google",
  },
  { id: "groq", label: "Groq", baseUrl: "https://api.groq.com/openai/v1", catalogId: "groq" },
];

export function catalogIdForBaseUrl(baseUrl: string): string | null {
  return TUTOR_PRESETS.find((preset) => preset.baseUrl === baseUrl)?.catalogId ?? null;
}

const LS_BASE_URL = "merit_tutor_base_url";
const LS_API_KEY = "merit_tutor_api_key";
const LS_MODEL = "merit_tutor_model";

function readLS(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

type TutorSnapshot = {
  baseUrl: string;
  apiKey: string;
  model: string;
  remember: boolean;
};

let snapshot: TutorSnapshot = {
  baseUrl: readLS(LS_BASE_URL) ?? TUTOR_DEFAULT_BASE_URL,
  apiKey: readLS(LS_API_KEY) ?? "",
  model: readLS(LS_MODEL) ?? "",
  remember: readLS(LS_API_KEY) !== null || readLS(LS_BASE_URL) !== null || readLS(LS_MODEL) !== null,
};
const listeners = new Set<() => void>();

function update(patch: Partial<TutorSnapshot>) {
  snapshot = { ...snapshot, ...patch };
  try {
    if (snapshot.remember) {
      window.localStorage.setItem(LS_BASE_URL, snapshot.baseUrl);
      window.localStorage.setItem(LS_API_KEY, snapshot.apiKey);
      window.localStorage.setItem(LS_MODEL, snapshot.model);
    } else {
      window.localStorage.removeItem(LS_BASE_URL);
      window.localStorage.removeItem(LS_API_KEY);
      window.localStorage.removeItem(LS_MODEL);
    }
  } catch {
    // Storage is optional; credentials remain memory-only.
  }
  listeners.forEach((listener) => listener());
}

export async function loadTutorCatalog(catalogId: string): Promise<string[]> {
  const res = await fetch("https://models.dev/api.json");
  if (!res.ok) throw new Error("Could not load the model catalog.");
  const catalog = (await res.json()) as Record<string, { models?: Record<string, { id?: string }> }>;
  const models = catalog[catalogId]?.models ?? {};
  return Object.values(models)
    .map((entry) => entry.id)
    .filter((id): id is string => typeof id === "string");
}

export interface TutorKeyState extends TutorSnapshot {
  setBaseUrl: (value: string) => void;
  setApiKey: (value: string) => void;
  setModel: (value: string) => void;
  setRemember: (value: boolean) => void;
  clear: () => void;
}

export function useTutorKey(): TutorKeyState {
  const current = useSyncExternalStore(
    (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    () => snapshot,
    () => snapshot,
  );
  useEffect(() => {
    const storedKey = readLS(LS_API_KEY);
    if (storedKey !== null && !snapshot.remember) {
      update({
        baseUrl: readLS(LS_BASE_URL) ?? snapshot.baseUrl,
        apiKey: storedKey,
        model: readLS(LS_MODEL) ?? snapshot.model,
        remember: true,
      });
    }
  }, []);
  return {
    ...current,
    setBaseUrl: (baseUrl) => update({ baseUrl }),
    setApiKey: (apiKey) => update({ apiKey }),
    setModel: (model) => update({ model }),
    setRemember: (remember) => update({ remember }),
    clear: () => update({ apiKey: "", model: "" }),
  };
}
