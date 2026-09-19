import { useCallback, useEffect, useState } from "react";

export const TUTOR_DEFAULT_BASE_URL = "https://api.openai.com/v1";

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

export interface TutorKeyState {
  baseUrl: string;
  apiKey: string;
  model: string;
  /** Opt-in persistence. Default unchecked → memory only. */
  remember: boolean;
  setBaseUrl: (v: string) => void;
  setApiKey: (v: string) => void;
  setModel: (v: string) => void;
  setRemember: (v: boolean) => void;
  clear: () => void;
}

/**
 * BYOK credential store for the AI tutor.
 *
 * Credentials live in React state (memory) by default and are written to
 * localStorage ONLY when the user opts in via the "remember on this device"
 * checkbox (default unchecked). The key is never placed in URLs — it travels
 * exclusively in POST JSON bodies to `/api/v1/tutor/*`.
 */
export function useTutorKey(): TutorKeyState {
  const [baseUrl, setBaseUrl] = useState<string>(
    () => readLS(LS_BASE_URL) ?? TUTOR_DEFAULT_BASE_URL
  );
  const [apiKey, setApiKey] = useState<string>(() => readLS(LS_API_KEY) ?? "");
  const [model, setModel] = useState<string>(() => readLS(LS_MODEL) ?? "");
  const [remember, setRemember] = useState<boolean>(
    () =>
      readLS(LS_API_KEY) !== null ||
      readLS(LS_BASE_URL) !== null ||
      readLS(LS_MODEL) !== null
  );

  useEffect(() => {
    try {
      if (remember) {
        window.localStorage.setItem(LS_BASE_URL, baseUrl);
        window.localStorage.setItem(LS_API_KEY, apiKey);
        window.localStorage.setItem(LS_MODEL, model);
      } else {
        window.localStorage.removeItem(LS_BASE_URL);
        window.localStorage.removeItem(LS_API_KEY);
        window.localStorage.removeItem(LS_MODEL);
      }
    } catch {
      // Storage unavailable (private mode, etc.): stay memory-only.
    }
  }, [remember, baseUrl, apiKey, model]);

  const clear = useCallback(() => {
    setApiKey("");
    setModel("");
    try {
      window.localStorage.removeItem(LS_API_KEY);
      window.localStorage.removeItem(LS_MODEL);
    } catch {
      // ignore
    }
  }, []);

  return {
    baseUrl,
    apiKey,
    model,
    remember,
    setBaseUrl,
    setApiKey,
    setModel,
    setRemember,
    clear,
  };
}
