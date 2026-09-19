import React, { createContext, useContext, useEffect, useCallback } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { useStreak } from '../hooks/useStreak';
import { useAuth } from './AuthContext';
import { progressApi } from '../utils/api';
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

export const ProgressProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [state, setState] = useLocalStorage<ProgressStateSchema>(
    'merit_store_v1',
    EMPTY_INITIAL_STATE,
    ProgressStateZodSchema
  );
  const [theme, setTheme] = useLocalStorage<'dark' | 'light'>('merit_theme_v1', 'dark');

  const recordActivityDate = (dateStr: string) => {
    setState((prev) => {
      if (prev.streak.includes(dateStr)) return prev;
      return { ...prev, streak: [...prev.streak, dateStr] };
    });
  };

  const { currentStreak, markTodayActive, today } = useStreak(state.streak, recordActivityDate);

  const syncWithBackend = useCallback(async () => {
    if (!user) return;
    try {
      const summary = await progressApi.getSummary();
      // NOTE: intentionally reads `state` from closure; callers invoke this
      // on explicit user/login transitions only, never from render effects
      // that would loop. Keep the dep list in sync if this changes.
      if (!summary.has_imported_local) {
        // One-time merge of local progress
        const hasLocalData =
          Object.keys(state.progress).length > 0 ||
          Object.keys(state.notes).length > 0 ||
          state.streak.length > 0 ||
          state.visitedVisualizers.length > 0;

        if (hasLocalData) {
          const merged = await progressApi.importLocal({
            progress: state.progress,
            notes: state.notes,
            quizzes: state.quizzes,
            streak: currentStreak,
            activity_days: state.streak,
            visited_visualizers: state.visitedVisualizers,
            local_date: today,
          });
          setState((prev) => ({
            ...prev,
            progress: merged.progress as Record<string, ProblemStatus>,
            notes: merged.notes,
            streak: Object.keys(merged.activity_days),
            visitedVisualizers: merged.visited_visualizers,
          }));
          return;
        }
      }

      // Update state from server summary
      setState((prev) => ({
        ...prev,
        progress: summary.progress as Record<string, ProblemStatus>,
        notes: summary.notes,
        streak: Object.keys(summary.activity_days),
        visitedVisualizers: summary.visited_visualizers,
      }));
    } catch {
      // Offline / guest fallback
    }
  }, [user, state, currentStreak, today, setState]);

  useEffect(() => {
    if (user) {
      syncWithBackend();
    }
  }, [user]); // eslint-disable-line react-hooks/exhaustive-deps

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
    setState((prev) => {
      const wasDone = prev.progress[slug] === 'Done';
      const next: ProgressStateSchema = {
        ...prev,
        progress: { ...prev.progress, [slug]: status },
      };
      if (!wasDone && status === 'Done' && prev.dailyGoal?.kind === 'problems') {
        const key = today;
        next.dailyGoalProgress = {
          ...prev.dailyGoalProgress,
          [key]: (prev.dailyGoalProgress?.[key] ?? 0) + 1,
        };
      }
      return next;
    });

    if (user) {
      progressApi.updateProblem(slug, status, today).catch(() => {});
    }
  };

  const saveQuizScore = (topic: string, score: number) => {
    markTodayActive();
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
      if (
        prev.dailyGoal?.kind === 'quiz-score' &&
        score >= prev.dailyGoal.target &&
        prevBest < prev.dailyGoal.target
      ) {
        const key = today;
        next.dailyGoalProgress = {
          ...prev.dailyGoalProgress,
          [key]: (prev.dailyGoalProgress?.[key] ?? 0) + prev.dailyGoal.target,
        };
      }
      return next;
    });
  };

  const saveNote = (slug: string, text: string) => {
    markTodayActive();
    setState((prev) => ({
      ...prev,
      notes: { ...prev.notes, [slug]: text },
    }));

    if (user) {
      progressApi.updateNote(slug, text, today).catch(() => {});
    }
  };

  const toggleBookmark = (id: string) => {
    setState((prev) => {
      const exists = prev.bookmarks.includes(id);
      const next = exists ? prev.bookmarks.filter((x) => x !== id) : [...prev.bookmarks, id];
      return { ...prev, bookmarks: next };
    });

    if (user) {
      progressApi.toggleBookmark('problem', id).catch(() => {});
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
    setState((prev) => {
      // A pinned goal survives a "clear": clearing with a pinned goal restores it.
      if (goal === null && prev.dailyGoal?.permanent && !opts?.permanent) {
        return prev;
      }
      const next: ProgressStateSchema = {
        ...prev,
        dailyGoal: goal ? { ...goal, permanent: opts?.permanent ?? goal.permanent ?? false } : null,
      };
      return next;
    });

    if (user && (goal !== null || opts?.permanent === true)) {
      progressApi
        .saveDailyGoal(goal ? { ...goal, permanent: opts?.permanent ?? goal.permanent ?? false } : null)
        .catch(() => {});
    }
  };

  const clearDailyGoal = () => {
    setState((prev) => {
      // Pinned goals are sticky: an explicit unpin is required to remove them.
      if (prev.dailyGoal?.permanent) return prev;
      return { ...prev, dailyGoal: null };
    });
    if (user) {
      progressApi.saveDailyGoal(null).catch(() => {});
    }
  };

  const unpinDailyGoal = () => {
    setState((prev) => ({ ...prev, dailyGoal: null }));
    if (user) {
      progressApi.saveDailyGoal(null).catch(() => {});
    }
  };

  const dailyGoal = state.dailyGoal ?? null;
  const dailyGoalProgressToday = state.dailyGoalProgress?.[today] ?? 0;

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
    setState((prev) => {
      const visited = prev.visitedVisualizers || [];
      if (visited.includes(id)) return prev;
      return {
        ...prev,
        visitedVisualizers: [...visited, id],
      };
    });

    if (user) {
      progressApi.visitVisualizer(id).catch(() => {});
    }
  };

  const resetAllData = () => {
    setState(EMPTY_INITIAL_STATE);
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
