import React, { createContext, useContext, useEffect } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { useStreak } from '../hooks/useStreak';
import {
  EMPTY_INITIAL_STATE,
  ProgressStateSchema,
  ProgressStateZodSchema,
  ProblemStatus,
  LastVisitedItem,
} from './schema';

export type { ProblemStatus, LastVisitedItem, ProgressStateSchema };

interface ProgressContextType {
  state: ProgressStateSchema;
  theme: 'dark' | 'light';
  toggleTheme: () => void;
  setProblemStatus: (slug: string, status: ProblemStatus) => void;
  saveQuizScore: (topic: string, score: number) => void;
  saveNote: (slug: string, text: string) => void;
  toggleBookmark: (id: string) => void;
  toggleDailyGoal: () => void;
  isDailyGoalDone: boolean;
  setLastVisited: (item: LastVisitedItem) => void;
  recordVisualizerVisit: (id: string) => void;
  currentStreak: number;
  resetAllData: () => void;
}

const ProgressContext = createContext<ProgressContextType | undefined>(undefined);

export const ProgressProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useLocalStorage<ProgressStateSchema>(
    'algovista_store_v1',
    EMPTY_INITIAL_STATE,
    ProgressStateZodSchema
  );
  const [theme, setTheme] = useLocalStorage<'dark' | 'light'>('algovista_theme_v1', 'dark');

  const recordActivityDate = (dateStr: string) => {
    setState((prev) => {
      if (prev.streak.includes(dateStr)) return prev;
      return { ...prev, streak: [...prev.streak, dateStr] };
    });
  };

  const { currentStreak, markTodayActive, today } = useStreak(state.streak, recordActivityDate);

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
    setState((prev) => ({
      ...prev,
      progress: { ...prev.progress, [slug]: status },
    }));
  };

  const saveQuizScore = (topic: string, score: number) => {
    markTodayActive();
    setState((prev) => ({
      ...prev,
      quizzes: {
        ...prev.quizzes,
        [topic]: Math.max(prev.quizzes[topic] || 0, score),
      },
    }));
  };

  const saveNote = (slug: string, text: string) => {
    markTodayActive();
    setState((prev) => ({
      ...prev,
      notes: { ...prev.notes, [slug]: text },
    }));
  };

  const toggleBookmark = (id: string) => {
    setState((prev) => {
      const exists = prev.bookmarks.includes(id);
      const next = exists ? prev.bookmarks.filter((x) => x !== id) : [...prev.bookmarks, id];
      return { ...prev, bookmarks: next };
    });
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
  };

  const resetAllData = () => {
    setState(EMPTY_INITIAL_STATE);
  };

  const isDailyGoalDone = Boolean(state.dailyGoalDone[today]);

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
        toggleDailyGoal,
        isDailyGoalDone,
        setLastVisited,
        recordVisualizerVisit,
        currentStreak,
        resetAllData,
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
