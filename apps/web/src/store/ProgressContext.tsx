import React, { createContext, useContext, useEffect, useCallback, useRef } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { useStreak } from '../hooks/useStreak';
import { useAuth } from './AuthContext';
import { ApiError, progressApi, ProgressSummary, DailyGoalPayload } from '../utils/api';
import {
  EMPTY_INITIAL_STATE,
  DAILY_GOAL_PRESETS,
  DailyGoal,
  ProgressStateSchema,
  ProgressStateZodSchema,
  ProblemStatus,
  LastVisitedItem,
} from './schema';

export type { ProblemStatus, LastVisitedItem, ProgressStateSchema, DailyGoal };
export { DAILY_GOAL_PRESETS };

interface ProgressContextType {
  state: ProgressStateSchema;
  theme: 'dark' | 'light';
  toggleTheme: () => void;
  setProblemStatus: (slug: string, status: ProblemStatus) => void;
  saveQuizScore: (topic: string, score: number) => void;
  saveNote: (slug: string, text: string) => void;
  toggleBookmark: (id: string) => void;
  dailyGoal: DailyGoal | null;
  dailyGoalProgressToday: number;
  isDailyGoalDone: boolean;
  setDailyGoal: (goal: DailyGoal | null, opts?: { permanent?: boolean }) => void;
  clearDailyGoal: () => void;
  unpinDailyGoal: () => void;
  toggleDailyGoal: () => void;
  setLastVisited: (item: LastVisitedItem) => void;
  recordVisualizerVisit: (id: string) => void;
  currentStreak: number;
  resetAllData: () => void;
  syncWithBackend: () => Promise<void>;
}

const ProgressContext = createContext<ProgressContextType | undefined>(undefined);

const GOAL_KINDS = ['problems', 'quiz-score', 'custom'] as const;

/**
 * Bookmark ids as the local store holds them (bare problem slugs). The server
 * returns `{item_type, item_id}` pairs; `toggleBookmark` only ever writes
 * problems, so question bookmarks are not representable locally and are
 * dropped rather than shown as un-removable entries.
 */
const bookmarksFromServer = (
  bookmarks: ProgressSummary['bookmarks'] | undefined,
): string[] => {
  const ids = (bookmarks ?? [])
    .filter((b) => b && b.item_type === 'problem' && typeof b.item_id === 'string')
    .map((b) => b.item_id);
  return Array.from(new Set(ids));
};

const normalizeGoal = (
  raw: ProgressSummary['daily_goal'] | undefined,
): NonNullable<ProgressStateSchema['dailyGoal']> | null => {
  if (!raw) return null;
  const kind = GOAL_KINDS.find((k) => k === raw.kind);
  if (!kind) return null;
  return {
    kind,
    label: String(raw.label ?? ''),
    target: Number(raw.target) || 0,
    permanent: raw.permanent ?? false,
  };
};

/**
 * Maps a progress payload onto the state slice. Fields the server did not send
 * are omitted entirely rather than defaulted, so a partial/truncated response
 * cannot silently blank a section the client already knows about; the merge in
 * the provider then keeps the local value for those fields.
 */
const toStateSlice = (summary: Partial<ProgressSummary>): Partial<ProgressStateSchema> => {
  const slice: Partial<ProgressStateSchema> = {};
  if (summary.progress) {
    slice.progress = summary.progress as Record<string, ProblemStatus>;
  }
  if (summary.notes) {
    slice.notes = summary.notes;
  }
  if (summary.activity_days) {
    slice.streak = Object.keys(summary.activity_days);
  }
  if (summary.visited_visualizers) {
    slice.visitedVisualizers = summary.visited_visualizers;
  }
  if (summary.bookmarks) {
    slice.bookmarks = bookmarksFromServer(summary.bookmarks);
  }
  if (summary.quiz_scores) {
    slice.quizzes = { ...summary.quiz_scores };
  }
  if (summary.daily_goal !== undefined) {
    slice.dailyGoal = normalizeGoal(summary.daily_goal);
  }
  return slice;
};

/**
 * Overlays `local` keys written while the sync was in flight on top of the
 * server snapshot, so a change the user made in the ~200ms before the response
 * landed is never reverted. Keys absent locally were explicitly cleared by the
 * user, so they stay cleared.
 */
function mergeRecord<T>(
  local: Record<string, T>,
  server: Record<string, T>,
  prefix: string,
  written: ReadonlySet<string>,
): Record<string, T> {
  const out: Record<string, T> = { ...server };
  const keys = new Set([...Object.keys(server), ...Object.keys(local)]);
  keys.forEach((key) => {
    if (!written.has(`${prefix}:${key}`)) return;
    if (key in local) {
      out[key] = local[key];
    } else {
      delete out[key];
    }
  });
  return out;
}

function mergeQuizScores(
  local: Record<string, number>,
  server: Record<string, number>,
  written: ReadonlySet<string>,
): Record<string, number> {
  const out: Record<string, number> = { ...server };
  Object.keys(local).forEach((key) => {
    if (key.startsWith('exam:')) {
      out[key] = local[key];
    } else if (typeof local[key] === 'number') {
      const serverVal = out[key] ?? 0;
      if (local[key] > serverVal || written.has(`quiz:${key}`)) {
        out[key] = Math.max(local[key], serverVal);
      }
    }
  });
  return out;
}

const mergeSlice = (
  prev: ProgressStateSchema,
  slice: Partial<ProgressStateSchema>,
  written: ReadonlySet<string>,
): ProgressStateSchema => {
  const next: ProgressStateSchema = { ...prev, ...slice };

  if (slice.progress) {
    next.progress = mergeRecord(prev.progress, slice.progress, 'progress', written);
  }
  if (slice.notes) {
    next.notes = mergeRecord(prev.notes, slice.notes, 'note', written);
  }
  if (slice.quizzes) {
    next.quizzes = mergeQuizScores(prev.quizzes, slice.quizzes, written);
  }
  if (slice.streak) {
    next.streak = written.has('streak') ? prev.streak : slice.streak;
  }
  if (slice.bookmarks) {
    next.bookmarks = written.has('bookmarks') ? prev.bookmarks : slice.bookmarks;
  }
  if (slice.visitedVisualizers) {
    next.visitedVisualizers = written.has('visited')
      ? prev.visitedVisualizers
      : slice.visitedVisualizers;
  }
  if (slice.dailyGoal !== undefined && written.has('dailyGoal')) {
    next.dailyGoal = prev.dailyGoal;
  }
  return next;
};

/* ------------------------------------------------------------------ *
 * Pending writes
 *
 * Every mutation is fire-and-forget against the API. Offline (or on a 5xx)
 * those requests used to vanish. They are now queued — persisted, so a reload
 * does not lose them — and replayed at the start of the next sync.
 * ------------------------------------------------------------------ */

const PENDING_WRITES_KEY = 'merit_pending_writes_v1';

type PendingWrite =
  | { kind: 'problem'; key: string; slug: string; status: ProblemStatus; localDate: string }
  | { kind: 'note'; key: string; slug: string; text: string; localDate: string }
  | { kind: 'bookmark'; key: string; itemType: string; itemId: string }
  | { kind: 'visualizer'; key: string; id: string }
  | { kind: 'dailyGoal'; key: string; goal: DailyGoalPayload | null; unpin?: boolean };

const isPendingWrite = (value: unknown): value is PendingWrite => {
  if (!value || typeof value !== 'object') return false;
  const rec = value as Record<string, unknown>;
  return typeof rec.kind === 'string' && typeof rec.key === 'string';
};

const loadPendingWrites = (): PendingWrite[] => {
  try {
    const raw = window.localStorage.getItem(PENDING_WRITES_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isPendingWrite);
  } catch {
    return [];
  }
};

const persistPendingWrites = (queue: PendingWrite[]): void => {
  try {
    if (queue.length === 0) {
      window.localStorage.removeItem(PENDING_WRITES_KEY);
    } else {
      window.localStorage.setItem(PENDING_WRITES_KEY, JSON.stringify(queue));
    }
  } catch {
    // Storage unavailable: the in-memory queue still retries this session.
  }
};

const sendPendingWrite = async (write: PendingWrite): Promise<void> => {
  switch (write.kind) {
    case 'problem':
      await progressApi.updateProblem(write.slug, write.status, write.localDate);
      return;
    case 'note':
      await progressApi.updateNote(write.slug, write.text, write.localDate);
      return;
    case 'bookmark':
      await progressApi.toggleBookmark(write.itemType, write.itemId);
      return;
    case 'visualizer':
      await progressApi.visitVisualizer(write.id);
      return;
    case 'dailyGoal':
      if (write.unpin) {
        await progressApi.unpinDailyGoal();
      } else {
        await progressApi.saveDailyGoal(write.goal);
      }
      return;
  }
};

/** Which local state keys a queued write is authoritative for. */
const stateKeysForWrite = (write: PendingWrite): string[] => {
  switch (write.kind) {
    case 'problem':
      return [`progress:${write.slug}`];
    case 'note':
      return [`note:${write.slug}`];
    case 'bookmark':
      return ['bookmarks'];
    case 'visualizer':
      return ['visited'];
    case 'dailyGoal':
      return ['dailyGoal'];
  }
};

/** Progress within a goal is scoped to that goal, not just to the day. */
const goalProgressKey = (goal: DailyGoal | null, day: string): string =>
  goal ? `${goal.kind}:${goal.target}:${day}` : day;

export const ProgressProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [state, setState] = useLocalStorage<ProgressStateSchema>(
    'merit_store_v1',
    EMPTY_INITIAL_STATE,
    ProgressStateZodSchema
  );
  const [theme, setTheme] = useLocalStorage<'dark' | 'light'>('merit_theme_v1', 'dark');

  // Latest committed state, for async code that must not read a stale closure.
  const stateRef = useRef(state);
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  const currentUserIdRef = useRef<string | null>(null);
  const lastUserIdRef = useRef<string | null>(null);

  // Write tracking: `writtenAt` records the sequence number at which each key
  // was last touched locally. A sync snapshots the sequence before it starts,
  // so anything written afterwards is known to be newer than the server view.
  const writeSeqRef = useRef(0);
  const writtenAtRef = useRef<Map<string, number>>(new Map());

  const markWritten = useCallback((keys: string[]) => {
    writeSeqRef.current += 1;
    const seq = writeSeqRef.current;
    keys.forEach((key) => writtenAtRef.current.set(key, seq));
  }, []);

  const writtenSince = useCallback((seq: number): Set<string> => {
    const keys = new Set<string>();
    writtenAtRef.current.forEach((value, key) => {
      if (value > seq) keys.add(key);
    });
    return keys;
  }, []);

  const recordActivityDate = useCallback(
    (dateStr: string) => {
      markWritten(['streak']);
      setState((prev) => {
        if (prev.streak.includes(dateStr)) return prev;
        return { ...prev, streak: [...prev.streak, dateStr] };
      });
    },
    [markWritten, setState],
  );

  const { currentStreak, markTodayActive, today } = useStreak(state.streak, recordActivityDate);

  const queueRef = useRef<PendingWrite[] | null>(null);
  const flushingRef = useRef(false);
  const syncingRef = useRef(false);
  const getQueue = (): PendingWrite[] => {
    if (queueRef.current === null) queueRef.current = loadPendingWrites();
    return queueRef.current;
  };

  const clearPendingWrites = useCallback(() => {
    queueRef.current = [];
    persistPendingWrites([]);
  }, []);

  const flushPendingWrites = useCallback(async (): Promise<void> => {
    if (flushingRef.current) return;
    const queue = getQueue();
    if (queue.length === 0) return;
    flushingRef.current = true;
    try {
      while (queue.length > 0) {
        try {
          await sendPendingWrite(queue[0]);
        } catch (err) {
          if (
            err instanceof ApiError &&
            err.status >= 400 &&
            err.status < 500 &&
            err.status !== 401 &&
            err.status !== 408 &&
            err.status !== 429
          ) {
            console.warn('Dropping unrecoverable pending write:', queue[0], err);
            queue.shift();
            persistPendingWrites(queue);
            continue;
          }
          // Still offline / server unhappy: keep the head entry (and order)
          // for the next flush instead of dropping or reordering writes.
          break;
        }
        // A delivered write is newer than any snapshot taken before it landed:
        // keep the local value if a sync response is about to be merged in.
        markWritten(stateKeysForWrite(queue[0]));
        queue.shift();
        persistPendingWrites(queue);
      }
    } finally {
      flushingRef.current = false;
    }
  }, [markWritten]);

  const enqueueWrite = useCallback(
    (write: PendingWrite) => {
      const queue = getQueue();
      const existing = queue.findIndex((entry) => entry.key === write.key);
      // A bookmark write is a toggle, so two queued toggles for one item are a
      // no-op; every other kind is last-write-wins for its key.
      const cancelled = write.kind === 'bookmark' && existing >= 0;
      if (cancelled) {
        queue.splice(existing, 1);
      } else if (existing >= 0) {
        queue.splice(existing, 1, write);
      } else {
        queue.push(write);
      }
      persistPendingWrites(queue);
      void flushPendingWrites();
    },
    [flushPendingWrites],
  );

  const syncWithBackend = useCallback(async () => {
    const userId = user?.id ?? null;
    if (!userId) return;
    if (syncingRef.current) return;
    syncingRef.current = true;
    const syncStartSeq = writeSeqRef.current;
    try {
      let localState = stateRef.current;

      const storedOwner = localState.ownerUserId ?? null;
      if (storedOwner !== null && storedOwner !== userId) {
        // The cache belongs to a different account. `importLocal` is one-shot
        // and irreversible, and queued writes would land on the new account
        // too, so both are dropped before anything is sent.
        const cleared: ProgressStateSchema = { ...EMPTY_INITIAL_STATE, ownerUserId: userId };
        setState(cleared);
        stateRef.current = cleared;
        clearPendingWrites();
        localState = cleared;
      } else {
        // Replay anything the last session failed to deliver before pulling
        // the summary, so the snapshot includes those writes.
        await flushPendingWrites();
        if (currentUserIdRef.current !== userId) return;
      }

      const hasLocalData =
        Object.keys(localState.progress).length > 0 ||
        Object.keys(localState.notes).length > 0 ||
        localState.streak.length > 0 ||
        localState.visitedVisualizers.length > 0;

      // Never import a cache that was explicitly produced by another account.
      const owner = localState.ownerUserId ?? null;
      const ownerMatches = owner === null || owner === userId;

      const summary = await progressApi.getSummary();
      if (currentUserIdRef.current !== userId) return;

      if (!summary.has_imported_local && ownerMatches && hasLocalData) {
        const merged = await progressApi.importLocal({
          progress: localState.progress,
          notes: localState.notes,
          activity_days: localState.streak,
          visited_visualizers: localState.visitedVisualizers,
          local_date: today,
        });
        if (currentUserIdRef.current !== userId) return;
        const written = writtenSince(syncStartSeq);
        const slice = toStateSlice(merged);
        setState((prev) => ({
          ...mergeSlice(prev, slice, written),
          ownerUserId: userId,
        }));
        return;
      }

      const written = writtenSince(syncStartSeq);
      const slice = toStateSlice(summary);
      setState((prev) => ({
        ...mergeSlice(prev, slice, written),
        ownerUserId: userId,
      }));
    } catch {
      // Offline / server error: keep the local snapshot and retry next time.
    } finally {
      syncingRef.current = false;
    }
  }, [user, today, setState, flushPendingWrites, clearPendingWrites, writtenSince]);

  useEffect(() => {
    const nextId = user?.id ?? null;
    if (lastUserIdRef.current !== null && nextId === null) {
      // Signed out (or account deleted): everything account-scoped goes, so a
      // later login — possibly as somebody else — starts from a clean cache.
      // UI preferences survive: the theme lives under its own key
      // (`merit_theme_v1`) and the preferred language is stored server-side.
      setState(EMPTY_INITIAL_STATE);
      stateRef.current = EMPTY_INITIAL_STATE;
      clearPendingWrites();
      writtenAtRef.current.clear();
    }
    lastUserIdRef.current = nextId;
    currentUserIdRef.current = nextId;
  }, [user, setState, clearPendingWrites]);

  useEffect(() => {
    if (user) {
      syncWithBackend();
    }
  }, [user]); // eslint-disable-line react-hooks/exhaustive-deps

  // Retry queued writes as soon as connectivity returns.
  useEffect(() => {
    const onOnline = () => {
      void flushPendingWrites();
    };
    window.addEventListener('online', onOnline);
    return () => window.removeEventListener('online', onOnline);
  }, [flushPendingWrites]);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const setProblemStatus = (slug: string, status: ProblemStatus) => {
    markTodayActive();
    markWritten([`progress:${slug}`]);
    setState((prev) => {
      const wasDone = prev.progress[slug] === 'Done';
      const next: ProgressStateSchema = {
        ...prev,
        progress: { ...prev.progress, [slug]: status },
      };
      const goal = prev.dailyGoal ?? null;
      if (!wasDone && status === 'Done' && goal?.kind === 'problems') {
        const key = goalProgressKey(goal, today);
        next.dailyGoalProgress = {
          ...prev.dailyGoalProgress,
          [key]: (prev.dailyGoalProgress?.[key] ?? 0) + 1,
        };
      }
      return next;
    });

    if (user) {
      enqueueWrite({
        kind: 'problem',
        key: `problem:${slug}`,
        slug,
        status,
        localDate: today,
      });
    }
  };

  const saveQuizScore = (topic: string, score: number) => {
    markTodayActive();
    markWritten([`quiz:${topic}`]);
    setState((prev) => {
      const prevBest = prev.quizzes[topic] || 0;
      const nextBest = Math.max(prevBest, score);
      const next: ProgressStateSchema = {
        ...prev,
        quizzes: {
          ...prev.quizzes,
          [topic]: nextBest,
        },
      };
      const goal = prev.dailyGoal ?? null;
      if (
        goal?.kind === 'quiz-score' &&
        score >= goal.target &&
        prevBest < goal.target
      ) {
        const key = goalProgressKey(goal, today);
        next.dailyGoalProgress = {
          ...prev.dailyGoalProgress,
          [key]: (prev.dailyGoalProgress?.[key] ?? 0) + goal.target,
        };
      }
      return next;
    });
  };

  const saveNote = (slug: string, text: string) => {
    markTodayActive();
    markWritten([`note:${slug}`]);
    setState((prev) => ({
      ...prev,
      notes: { ...prev.notes, [slug]: text },
    }));

    if (user) {
      enqueueWrite({ kind: 'note', key: `note:${slug}`, slug, text, localDate: today });
    }
  };

  const toggleBookmark = (id: string) => {
    markWritten(['bookmarks']);
    setState((prev) => {
      const exists = prev.bookmarks.includes(id);
      const next = exists ? prev.bookmarks.filter((x) => x !== id) : [...prev.bookmarks, id];
      return { ...prev, bookmarks: next };
    });

    if (user) {
      enqueueWrite({
        kind: 'bookmark',
        key: `bookmark:problem:${id}`,
        itemType: 'problem',
        itemId: id,
      });
    }
  };

  const toggleDailyGoal = () => {
    markTodayActive();
    setState((prev) => ({
      ...prev,
      dailyGoalDone: {
        ...prev.dailyGoalDone,
        [today]: !prev.dailyGoalDone[today],
      },
    }));
  };

  const setDailyGoal = (goal: DailyGoal | null, opts?: { permanent?: boolean }) => {
    markWritten(['dailyGoal']);
    setState((prev) => {
      // A pinned goal survives a "clear": clearing with a pinned goal restores it.
      if (goal === null && prev.dailyGoal?.permanent && !opts?.permanent) {
        return prev;
      }
      const resolved = goal
        ? { ...goal, permanent: opts?.permanent ?? goal.permanent ?? false }
        : null;
      return { ...prev, dailyGoal: resolved };
    });

    if (user && (goal !== null || opts?.permanent === true)) {
      const resolved =
        goal === null
          ? null
          : { ...goal, permanent: opts?.permanent ?? goal.permanent ?? false };
      enqueueWrite({
        kind: 'dailyGoal',
        key: 'dailyGoal',
        goal: resolved,
      });
    }
  };

  const clearDailyGoal = () => {
    markWritten(['dailyGoal']);
    setState((prev) => {
      // Pinned goals are sticky: an explicit unpin is required to remove them.
      if (prev.dailyGoal?.permanent) return prev;
      return { ...prev, dailyGoal: null };
    });
    if (user) {
      enqueueWrite({ kind: 'dailyGoal', key: 'dailyGoal', goal: null, unpin: false });
    }
  };

  const unpinDailyGoal = () => {
    markWritten(['dailyGoal']);
    setState((prev) => ({ ...prev, dailyGoal: null }));
    if (user) {
      enqueueWrite({ kind: 'dailyGoal', key: 'dailyGoal', goal: null, unpin: true });
    }
  };

  const dailyGoal = state.dailyGoal ?? null;
  const dailyGoalProgressToday = dailyGoal
    ? state.dailyGoalProgress?.[goalProgressKey(dailyGoal, today)] ?? 0
    : 0;

  const isDailyGoalDone = (() => {
    if (state.dailyGoalDone[today]) return true;
    if (!dailyGoal) return false;
    if (dailyGoal.kind === 'custom') return false;
    return dailyGoalProgressToday >= dailyGoal.target;
  })();

  const setLastVisited = (item: LastVisitedItem) => {
    setState((prev) => ({
      ...prev,
      lastVisited: item,
    }));
  };

  const recordVisualizerVisit = (id: string) => {
    markTodayActive();
    markWritten(['visited']);
    setState((prev) => {
      const visited = prev.visitedVisualizers || [];
      if (visited.includes(id)) return prev;
      return {
        ...prev,
        visitedVisualizers: [...visited, id],
      };
    });

    if (user) {
      enqueueWrite({ kind: 'visualizer', key: `visit:${id}`, id });
    }
  };

  const resetAllData = () => {
    setState(EMPTY_INITIAL_STATE);
    stateRef.current = EMPTY_INITIAL_STATE;
    clearPendingWrites();
  };

  return (
    <ProgressContext.Provider
      value={{
        state,
        theme,
        toggleTheme,
        setProblemStatus,
        saveQuizScore,
        saveNote,
        toggleBookmark,
        dailyGoal,
        dailyGoalProgressToday,
        isDailyGoalDone,
        setDailyGoal,
        clearDailyGoal,
        unpinDailyGoal,
        toggleDailyGoal,
        setLastVisited,
        recordVisualizerVisit,
        currentStreak,
        resetAllData,
        syncWithBackend,
      }}
    >
      {children}
    </ProgressContext.Provider>
  );
};

export const useProgress = () => {
  const ctx = useContext(ProgressContext);
  if (!ctx) throw new Error('useProgress must be used within a ProgressProvider');
  return ctx;
};

export const useTheme = (): 'dark' | 'light' => {
  const ctx = useContext(ProgressContext);
  if (ctx) return ctx.theme;
  if (typeof document !== 'undefined' && document.documentElement.classList.contains('light')) {
    return 'light';
  }
  return 'dark';
};
