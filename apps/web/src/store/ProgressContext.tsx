import React, { createContext, useContext, useEffect } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { useStreak } from '../hooks/useStreak';

export type ProblemStatus = 'Todo' | 'Doing' | 'Done';

export interface LastVisitedItem {
  type: 'visualizer' | 'problem';
  title: string;
  path: string;
  subtitle: string;
}

export interface ProgressStateSchema {
  progress: Record<string, ProblemStatus>;
  quizzes: Record<string, number>;
  streak: string[];
  notes: Record<string, string>;
  bookmarks: string[];
  dailyGoalDone: Record<string, boolean>;
  lastVisited: LastVisitedItem;
}

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
  currentStreak: number;
  resetAllData: () => void;
}

// Generate initial streak dates over the last 30 days so the GitHub heatmap has realistic activity
function getInitialStreakDates(): string[] {
  const dates: string[] = [];
  const today = new Date();
  const offsets = [0, 1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 14, 15, 16, 19, 20, 22, 24, 25, 28];
  for (const offset of offsets) {
    const d = new Date(today);
    d.setDate(today.getDate() - offset);
    dates.push(d.toISOString().split('T')[0]);
  }
  return dates;
}

const INITIAL_STATE: ProgressStateSchema = {
  progress: {
    'two-sum': 'Done',
    'maximum-subarray': 'Done',
    'valid-anagram': 'Done',
    'reverse-linked-list': 'Done',
    'maximum-depth-of-binary-tree': 'Doing'
  },
  quizzes: {
    arrays: 90,
    trees: 80,
    graphs: 60,
    dp: 50
  },
  streak: getInitialStreakDates(),
  notes: {
    'two-sum': 'Use Map to store seen[nums[i]] = i. Check complement = target - nums[i] in O(1).'
  },
  bookmarks: ['sorting', 'two-sum', 'graph'],
  dailyGoalDone: {},
  lastVisited: {
    type: 'visualizer',
    title: 'Sorting Algorithms (Quick & Merge)',
    path: '/visualizers/sorting',
    subtitle: 'Step Debugger'
  }
};

const ProgressContext = createContext<ProgressContextType | undefined>(undefined);

export const ProgressProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useLocalStorage<ProgressStateSchema>('algovista_store_v1', INITIAL_STATE);
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
      progress: { ...prev.progress, [slug]: status }
    }));
  };

  const saveQuizScore = (topic: string, score: number) => {
    markTodayActive();
    setState((prev) => ({
      ...prev,
      quizzes: {
        ...prev.quizzes,
        [topic]: Math.max(prev.quizzes[topic] || 0, score)
      }
    }));
  };

  const saveNote = (slug: string, text: string) => {
    markTodayActive();
    setState((prev) => ({
      ...prev,
      notes: { ...prev.notes, [slug]: text }
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
        [today]: !prev.dailyGoalDone[today]
      }
    }));
  };

  const setLastVisited = (item: LastVisitedItem) => {
    setState((prev) => ({
      ...prev,
      lastVisited: item
    }));
  };

  const resetAllData = () => {
    setState(INITIAL_STATE);
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
        currentStreak,
        resetAllData
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
