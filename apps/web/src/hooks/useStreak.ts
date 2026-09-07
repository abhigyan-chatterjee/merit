import { useMemo } from 'react';

/**
 * Returns YYYY-MM-DD string according to the user's local timezone.
 * Avoids UTC boundary bugs when user's timezone differs from UTC.
 */
export function getLocalDateString(d: Date = new Date()): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/** Legacy alias for backward compatibility, now returning local date */
export function getTodayISO(): string {
  return getLocalDateString(new Date());
}

export function useStreak(streakDates: string[], recordActivityDate: (date: string) => void) {
  const today = getLocalDateString();

  const currentStreak = useMemo(() => {
    if (!streakDates || streakDates.length === 0) return 0;
    const uniqueSorted = Array.from(new Set(streakDates)).sort().reverse();
    let streak = 0;
    const d = new Date();

    const todayStr = getLocalDateString(d);
    const yesterdayDate = new Date(d.getFullYear(), d.getMonth(), d.getDate() - 1);
    const yesterdayStr = getLocalDateString(yesterdayDate);

    const checkDate = uniqueSorted.includes(todayStr)
      ? new Date(d.getFullYear(), d.getMonth(), d.getDate())
      : uniqueSorted.includes(yesterdayStr)
      ? yesterdayDate
      : null;

    if (!checkDate) return 0;

    while (true) {
      const localStr = getLocalDateString(checkDate);
      if (uniqueSorted.includes(localStr)) {
        streak++;
        checkDate.setDate(checkDate.getDate() - 1);
      } else {
        break;
      }
    }
    return streak;
  }, [streakDates]);

  const markTodayActive = () => {
    if (!streakDates.includes(today)) {
      recordActivityDate(today);
    }
  };

  return { currentStreak, markTodayActive, today };
}
