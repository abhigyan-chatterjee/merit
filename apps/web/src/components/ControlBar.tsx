import React from 'react';
import { Play, Pause, SkipBack, SkipForward, RotateCcw, Shuffle } from 'lucide-react';
import { SpeedControl } from './SpeedControl';

interface ControlBarProps {
  isPlaying: boolean;
  onPlayPause: () => void;
  onStep?: () => void;
  onStepForward?: () => void;
  onStepBack?: () => void;
  onReset: () => void;
  onRandomize: () => void;
  speed: number;
  onSpeedChange: (speed: number) => void;
  disabledStep?: boolean;
  disabledBack?: boolean;
}

export const ControlBar: React.FC<ControlBarProps> = ({
  isPlaying,
  onPlayPause,
  onStep,
  onStepForward,
  onStepBack,
  onReset,
  onRandomize,
  speed,
  onSpeedChange,
  disabledStep = false,
  disabledBack = false
}) => {
  const ghostBtn =
    'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-line bg-canvas text-xs font-mono text-muted hover:text-ink hover:border-steel disabled:opacity-35 disabled:pointer-events-none transition cursor-pointer';

  const stepForward = onStepForward ?? onStep;

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 p-2.5 rounded-xl border border-line bg-surface">
      <div className="flex flex-wrap items-center gap-2">
        {/* status lamp */}
        <span className="hidden sm:flex items-center gap-2 pl-1.5 pr-3 mr-1 border-r border-line">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              isPlaying ? 'bg-mint animate-pulse-dot' : 'bg-muted/50'
            }`}
          />
          <span className="text-[9px] font-mono uppercase tracking-[0.16em] text-muted">
            {isPlaying ? 'running' : 'paused'}
          </span>
        </span>

        <button
          onClick={onPlayPause}
          aria-label={isPlaying ? 'Pause visualization' : 'Play visualization'}
          className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-mint text-canvas font-semibold text-xs hover:brightness-110 transition cursor-pointer"
        >
          {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          {isPlaying ? 'Pause' : 'Play'}
        </button>

        {onStepBack && (
          <button
            onClick={onStepBack}
            disabled={isPlaying || disabledBack}
            aria-label="Step back"
            className={ghostBtn}
          >
            <SkipBack className="w-3.5 h-3.5 text-violet" />
            Back
          </button>
        )}

        <button
          onClick={stepForward}
          disabled={isPlaying || disabledStep || !stepForward}
          aria-label="Step forward"
          className={ghostBtn}
        >
          <SkipForward className="w-3.5 h-3.5 text-mint" />
          Step
        </button>

        <button onClick={onReset} aria-label="Reset to first frame" className={ghostBtn}>
          <RotateCcw className="w-3.5 h-3.5 text-violet" />
          Reset
        </button>

        <button onClick={onRandomize} aria-label="Randomize dataset" className={ghostBtn}>
          <Shuffle className="w-3.5 h-3.5 text-amber" />
          Randomize
        </button>
      </div>

      <SpeedControl speed={speed} onChange={onSpeedChange} />
    </div>
  );
};
