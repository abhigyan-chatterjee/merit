import { useState, useEffect, useCallback, useRef } from 'react';
import { z } from 'zod';

export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  schema?: z.ZodType<T>
): [T, (value: T | ((val: T) => T)) => void] {
  const readAndValidate = useCallback((): T => {
    try {
      let raw = window.localStorage.getItem(key);
      if (raw === null && key.startsWith('merit_')) {
        const legacyKey = key.replace(/^merit_/, 'algovista_');
        const legacyRaw = window.localStorage.getItem(legacyKey);
        if (legacyRaw !== null) {
          raw = legacyRaw;
          try {
            window.localStorage.setItem(key, legacyRaw);
            window.localStorage.removeItem(legacyKey);
          } catch {
            // ignore migration storage write failure
          }
        }
      }
      if (raw === null) return initialValue;

      const parsed = JSON.parse(raw);
      if (schema) {
        const result = schema.safeParse(parsed);
        if (!result.success) {
          console.warn(`Validation failed for localStorage key "${key}". Backing up and resetting.`, result.error);
          try {
            window.localStorage.setItem(`${key}.backup`, raw);
          } catch {
            // ignore backup failure
          }
          window.localStorage.setItem(key, JSON.stringify(initialValue));
          return initialValue;
        }
        return result.data;
      }
      return parsed;
    } catch (error) {
      console.warn(`Corrupted localStorage key "${key}". Backing up and resetting.`, error);
      try {
        const raw = window.localStorage.getItem(key);
        if (raw !== null) {
          window.localStorage.setItem(`${key}.backup`, raw);
        }
      } catch {
        // ignore
      }
      try {
        window.localStorage.setItem(key, JSON.stringify(initialValue));
      } catch {
        // ignore
      }
      return initialValue;
    }
  }, [key, initialValue, schema]);

  const [storedValue, setStoredValue] = useState<T>(readAndValidate);

  /**
   * Guards the persistence effect below: the value read from storage on mount
   * is already persisted, so it must not be written back.
   */
  const hasUpdatedRef = useRef(false);

  const setValue = useCallback(
    (value: T | ((val: T) => T)) => {
      // The updater must stay pure — StrictMode invokes it twice in
      // development and any localStorage write here would be duplicated (and,
      // with a non-idempotent payload, could persist a value React discards).
      // Persistence happens once per committed value in the effect below.
      hasUpdatedRef.current = true;
      setStoredValue((prev) => {
        const valueToStore = value instanceof Function ? value(prev) : value;
        if (schema) {
          const validated = schema.safeParse(valueToStore);
          if (!validated.success) {
            console.warn(`Refusing to store invalid data in "${key}":`, validated.error);
            return prev;
          }
          return validated.data;
        }
        return valueToStore;
      });
    },
    [key, schema]
  );

  useEffect(() => {
    if (!hasUpdatedRef.current) return;
    try {
      window.localStorage.setItem(key, JSON.stringify(storedValue));
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === key && e.newValue) {
        try {
          const parsed = JSON.parse(e.newValue);
          if (schema) {
            const validated = schema.safeParse(parsed);
            if (validated.success) {
              setStoredValue(validated.data);
            }
          } else {
            setStoredValue(parsed);
          }
        } catch {
          // ignore external parse errors
        }
      }
    };
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key, schema]);

  return [storedValue, setValue];
}
