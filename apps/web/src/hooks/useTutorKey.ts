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
  const normalized = baseUrl.trim().replace(/\/+$/, "");
  return TUTOR_PRESETS.find((preset) => preset.baseUrl === normalized)?.catalogId ?? null;
}

const LS_BASE_URL = "merit_tutor_base_url";
const LS_MODEL = "merit_tutor_model";
// The API key never goes in localStorage: that store is readable by any script
// on the origin and survives the session indefinitely. sessionStorage limits
// the exposure to a single tab's lifetime. The legacy localStorage key is
// scrubbed on read below.
const SS_API_KEY = "merit_tutor_api_key";
const LEGACY_LS_API_KEY = "merit_tutor_api_key";

function readSS(key: string): string | null {
  try {
    return window.sessionStorage.getItem(key);
  } catch {
    return null;
  }
}

function readLS(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

/** Removes the pre-fix persistent copy so it does not linger after upgrade. */
function scrubLegacyStoredKey() {
  try {
    window.localStorage.removeItem(LEGACY_LS_API_KEY);
  } catch {
    // Storage may be unavailable; nothing to scrub in that case.
  }
}

type TutorSnapshot = {
  baseUrl: string;
  apiKey: string;
  model: string;
  remember: boolean;
};

scrubLegacyStoredKey();

let snapshot: TutorSnapshot = {
  baseUrl: readLS(LS_BASE_URL) ?? TUTOR_DEFAULT_BASE_URL,
  apiKey: readSS(SS_API_KEY) ?? "",
  model: readLS(LS_MODEL) ?? "",
  remember: true,
};
const listeners = new Set<() => void>();

export function getTutorSnapshot(): TutorSnapshot {
  if (snapshot.remember) {
    const storedBaseUrl = readLS(LS_BASE_URL) ?? TUTOR_DEFAULT_BASE_URL;
    const storedApiKey = readSS(SS_API_KEY) ?? "";
    const storedModel = readLS(LS_MODEL) ?? "";
    if (
      storedBaseUrl !== snapshot.baseUrl ||
      storedApiKey !== snapshot.apiKey ||
      storedModel !== snapshot.model
    ) {
      snapshot = {
        ...snapshot,
        baseUrl: storedBaseUrl,
        apiKey: storedApiKey,
        model: storedModel,
      };
    }
  }
  return snapshot;
}

function update(patch: Partial<TutorSnapshot>) {
  snapshot = { ...snapshot, ...patch };
  try {
    // Non-secret preferences persist across sessions.
    if (snapshot.remember) {
      window.localStorage.setItem(LS_BASE_URL, snapshot.baseUrl);
      window.localStorage.setItem(LS_MODEL, snapshot.model);
    } else {
      window.localStorage.removeItem(LS_BASE_URL);
      window.localStorage.removeItem(LS_MODEL);
    }
    // The credential is session-scoped only.
    if (snapshot.remember && snapshot.apiKey) {
      window.sessionStorage.setItem(SS_API_KEY, snapshot.apiKey);
    } else {
      window.sessionStorage.removeItem(SS_API_KEY);
    }
    scrubLegacyStoredKey();
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
    getTutorSnapshot,
    getTutorSnapshot,
  );
  useEffect(() => {
    const storedKey = readSS(SS_API_KEY);
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
