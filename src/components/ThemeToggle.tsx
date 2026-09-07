import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useProgress } from '../store/ProgressContext';

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useProgress();
  const isDark = theme === 'dark';

  return (
    <button
      onClick={toggleTheme}
      role="switch"
      aria-checked={!isDark}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} theme`}
      title={`Switch to ${isDark ? 'light' : 'dark'} theme`}
      className="relative flex items-center h-8 w-[58px] rounded-lg border border-line bg-surface p-0.5 hover:border-steel transition-colors cursor-pointer"
    >
      {/* sliding knob */}
      <span
        className="absolute top-0.5 bottom-0.5 w-[26px] rounded-md bg-canvas border border-line transition-transform duration-200 ease-out"
        style={{ transform: isDark ? 'translateX(0)' : 'translateX(26px)' }}
        aria-hidden="true"
      />
      <span className="relative z-10 grid place-items-center w-[26px]">
        <Moon className={`w-3.5 h-3.5 ${isDark ? 'text-violet' : 'text-muted'}`} />
      </span>
      <span className="relative z-10 grid place-items-center w-[26px]">
        <Sun className={`w-3.5 h-3.5 ${!isDark ? 'text-amber' : 'text-muted'}`} />
      </span>
    </button>
  );
};
