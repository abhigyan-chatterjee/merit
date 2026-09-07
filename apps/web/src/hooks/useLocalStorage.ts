import { useState, useEffect, useCallback } from 'react';
import { z } from 'zod';

export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  schema?: z.ZodType<T>
): [T, (value: T | ((val: T) => T)) => void] {
  const readAndValidate = useCallback((): T => {
    try {
      const raw = window.localStorage.getItem(key);
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

  const setValue = useCallback(
    (value: T | ((val: T) => T)) => {
      try {
        setStoredValue((prev) => {
          const valueToStore = value instanceof Function ? value(prev) : value;
          if (schema) {
            const validated = schema.safeParse(valueToStore);
            if (!validated.success) {
              console.warn(`Refusing to store invalid data in "${key}":`, validated.error);
              return prev;
            }
            window.localStorage.setItem(key, JSON.stringify(validated.data));
            return validated.data;
          }
          window.localStorage.setItem(key, JSON.stringify(valueToStore));
          return valueToStore;
        });
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, schema]
  );

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
