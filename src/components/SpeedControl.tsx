import React from 'react';

interface SpeedControlProps {
  speed: number;
  onChange: (newSpeed: number) => void;
}

const PRESETS = [0.25, 0.5, 1, 1.5, 2];

export const SpeedControl: React.FC<SpeedControlProps> = ({ speed, onChange }) => {
  return (
    <div className="flex items-center gap-3 pl-3 pr-2 py-1.5 rounded-lg border border-line bg-canvas">
      <span className="text-[9px] font-mono uppercase tracking-[0.16em] text-muted">Speed</span>

      <input
        type="range"
        min={0.25}
        max={2}
        step={0.25}
        value={speed}
        aria-label="Animation speed multiplier"
        aria-valuetext={`${speed} times`}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-20 accent-mint cursor-pointer"
      />

      {/* preset stops */}
      <div className="hidden sm:flex items-center gap-0.5">
        {PRESETS.map((p) => (
          <button
            key={p}
            onClick={() => onChange(p)}
            aria-label={`Set speed to ${p}x`}
            className={`px-1.5 py-0.5 rounded text-[10px] font-mono tnum transition cursor-pointer ${
              speed === p
                ? 'bg-mint/15 text-mint font-bold'
                : 'text-muted hover:text-ink'
            }`}
          >
            {p}×
          </button>
        ))}
      </div>

      <span className="text-[11px] font-mono font-bold text-ink tnum w-10 text-right sm:hidden">
        {speed}×
      </span>
    </div>
  );
};
