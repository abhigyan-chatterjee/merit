import React from 'react';
import { Link } from 'react-router-dom';
import {
  CheckSquare,
  Square,
  RotateCcw,
  Play,
  Target,
  Route,
  ArrowRight
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  CartesianGrid
} from 'recharts';
import { useProgress } from '../store/ProgressContext';
import { StreakHeatmap } from '../components/StreakHeatmap';
import { ProgressRing } from '../components/ProgressRing';
import { Panel } from '../components/ui/Panel';
import { SectionLabel } from '../components/ui/SectionLabel';
import { Reveal } from '../components/ui/Reveal';
import { PROBLEMS } from '../data/problems';
import { TOPICS } from '../data/curriculum';
import { LEARNING_PATHS } from '../data/learningPaths';

export const DashboardPage: React.FC = () => {
  const { state, currentStreak, isDailyGoalDone, toggleDailyGoal, resetAllData } = useProgress();

  const solvedCount = Object.values(state.progress).filter((s) => s === 'Done').length;
  const inProgress = Object.values(state.progress).filter((s) => s === 'Doing').length;
  const totalProblems = PROBLEMS.length;
  const notesCount = Object.values(state.notes).filter((n) => n.trim().length > 0).length;

  const chartData = TOPICS.map((t) => {
    const topicProblems = PROBLEMS.filter((p) => p.topic === t.slug);
    const done = topicProblems.filter((p) => state.progress[p.slug] === 'Done').length;
    return {
      name: t.title.split('&')[0].trim(),
      solved: done,
      total: topicProblems.length
    };
  });

  const weakTopics = Object.entries(state.quizzes).sort(([, a], [, b]) => a - b).slice(0, 4);

  const scoreTone = (s: number) =>
    s >= 80 ? 'text-mint' : s >= 60 ? 'text-amber' : 'text-rose';
  const barTone = (s: number) =>
    s >= 80 ? 'bg-mint' : s >= 60 ? 'bg-amber' : 'bg-rose';

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-10">
      {/* ===== Header ===== */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-1.5">
          <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-mint">
            Control room
          </span>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Learning dashboard</h1>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={toggleDailyGoal}
            aria-pressed={isDailyGoalDone}
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg border text-xs font-medium transition cursor-pointer ${
              isDailyGoalDone
                ? 'border-mint/50 bg-mint/10 text-mint'
                : 'border-line bg-surface text-muted hover:text-ink hover:border-steel'
            }`}
          >
            {isDailyGoalDone ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4" />}
            Daily goal
            {isDailyGoalDone && <span className="font-mono text-[10px]">✓ done</span>}
          </button>

          <button
            onClick={resetAllData}
            title="Reset all locally stored progress"
            aria-label="Reset all locally stored progress"
            className="p-2 rounded-lg border border-line bg-surface text-muted hover:text-rose hover:border-rose/40 transition cursor-pointer"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* ===== KPI strip ===== */}
      <div className="grid grid-cols-2 lg:grid-cols-4 border-t border-l border-line">
        {[
          { v: `${solvedCount}/${totalProblems}`, l: 'Problems solved', c: 'text-mint' },
          { v: inProgress, l: 'In progress', c: 'text-amber' },
          { v: `${currentStreak}d`, l: 'Day streak', c: 'text-violet' },
          { v: notesCount, l: 'Saved notes', c: 'text-ink' }
        ].map((k, i) => (
          <Reveal key={k.l} delay={i * 0.04}>
            <div className="border-r border-b border-line p-5 bg-surface/40">
              <div className={`text-3xl font-bold font-mono tracking-tighter tnum ${k.c}`}>{k.v}</div>
              <div className="mt-1.5 text-xs font-medium text-ink">{k.l}</div>
            </div>
          </Reveal>
        ))}
      </div>

      {/* ===== Ring / Resume / Weak topics ===== */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <Panel label="Curriculum completion" className="lg:col-span-4" bracket>
          <div className="flex items-center gap-5">
            <ProgressRing completed={solvedCount} total={totalProblems} size={116} strokeWidth={8} />
            <div className="space-y-2.5 min-w-0">
              <p className="text-xs text-muted leading-relaxed">
                Six core patterns. Finish them all to cover the standard interview surface area.
              </p>
              <div className="space-y-1.5">
                {chartData.slice(0, 3).map((c) => (
                  <div key={c.name} className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-muted w-16 truncate">{c.name}</span>
                    <span className="flex-1 h-1 rounded-full bg-line overflow-hidden">
                      <span
                        className="block h-full bg-mint transition-all duration-300"
                        style={{ width: `${(c.solved / c.total) * 100}%` }}
                      />
                    </span>
                    <span className="text-[10px] font-mono text-ink tnum">
                      {c.solved}/{c.total}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Panel>

        <Panel label="Resume session" className="lg:col-span-4" bracket>
          <div className="flex flex-col justify-between h-full gap-4">
            <div className="space-y-1.5">
              <span className="inline-block px-2 py-0.5 rounded border border-line bg-canvas text-[10px] font-mono uppercase tracking-wider text-violet">
                {state.lastVisited.type}
              </span>
              <h3 className="text-base font-bold text-ink leading-snug">
                {state.lastVisited.title}
              </h3>
              <p className="text-xs text-muted">{state.lastVisited.subtitle}</p>
            </div>

            <Link
              to={state.lastVisited.path}
              className="group inline-flex items-center justify-between px-4 py-2.5 rounded-lg bg-mint text-canvas font-semibold text-xs hover:brightness-110 transition"
            >
              <span className="inline-flex items-center gap-2">
                <Play className="w-3.5 h-3.5" />
                Continue where you left off
              </span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>
        </Panel>

        <Panel
          label="Weakest topics"
          className="lg:col-span-4"
          action={<Target className="w-3.5 h-3.5 text-amber" />}
          bracket
        >
          <div className="space-y-2.5">
            {weakTopics.map(([slug, score]) => (
              <div key={slug} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="capitalize text-ink font-medium">{slug}</span>
                  <div className="flex items-center gap-2.5">
                    <span className={`font-mono font-bold tnum ${scoreTone(score)}`}>{score}%</span>
                    <Link
                      to={`/quiz/${slug}`}
                      className="text-[10px] font-mono text-muted hover:text-mint transition-colors"
                    >
                      retake →
                    </Link>
                  </div>
                </div>
                <span className="block h-1 rounded-full bg-line overflow-hidden">
                  <span
                    className={`block h-full transition-all duration-300 ${barTone(score)}`}
                    style={{ width: `${score}%` }}
                  />
                </span>
              </div>
            ))}

            <Link
              to="/quiz/mixed"
              className="mt-3 flex items-center justify-between gap-2 px-3 py-2 rounded-lg border border-dashed border-line text-xs font-medium text-muted hover:text-violet hover:border-violet/50 transition-colors"
            >
              <span>Take a mixed quiz</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </Panel>
      </div>

      {/* ===== Heatmap ===== */}
      <div className="space-y-5">
        <SectionLabel index="01" title="Consistency" />
        <StreakHeatmap streakDates={state.streak} currentStreak={currentStreak} />
      </div>

      {/* ===== Guided paths ===== */}
      <div className="space-y-5">
        <SectionLabel index="02" title="Guided paths" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {LEARNING_PATHS.map((p) => (
            <Link
              key={p.id}
              to={`/learn/${p.id}`}
              className="group flex items-center justify-between gap-3 p-4 rounded-xl border border-line bg-surface hover:border-mint/50 transition-colors"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <Route className="w-3.5 h-3.5 text-mint shrink-0" />
                  <span className="text-xs font-semibold text-ink truncate group-hover:text-mint transition-colors">
                    {p.title}
                  </span>
                </div>
                <div className="text-[10px] font-mono text-muted mt-0.5">
                  {p.steps.length} steps
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-muted group-hover:text-mint group-hover:translate-x-0.5 transition-all shrink-0" />
            </Link>
          ))}
        </div>
      </div>

      {/* ===== Breakdown ===== */}
      <div className="space-y-5">
        <SectionLabel index="03" title="Coverage by module" />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <Panel label="Solved per topic" className="lg:col-span-7">
            <div className="h-60 w-full -ml-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
                  <CartesianGrid stroke="var(--c-line)" vertical={false} />
                  <XAxis
                    dataKey="name"
                    stroke="var(--c-muted)"
                    fontSize={10}
                    tickLine={false}
                    axisLine={{ stroke: 'var(--c-line)' }}
                    interval={0}
                    angle={-12}
                    textAnchor="end"
                    height={46}
                  />
                  <YAxis
                    stroke="var(--c-muted)"
                    fontSize={10}
                    allowDecimals={false}
                    tickLine={false}
                    axisLine={false}
                    domain={[0, 5]}
                  />
                  <Tooltip
                    cursor={{ fill: 'var(--c-line)', opacity: 0.35 }}
                    contentStyle={{
                      backgroundColor: 'var(--c-surface)',
                      border: '1px solid var(--c-line)',
                      borderRadius: '8px',
                      fontSize: '11px',
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--c-ink)'
                    }}
                    labelStyle={{ color: 'var(--c-muted)' }}
                  />
                  <Bar dataKey="solved" radius={[4, 4, 0, 0]} maxBarSize={44}>
                    {chartData.map((d, index) => (
                      <Cell
                        key={index}
                        fill={d.solved === d.total ? 'var(--c-mint)' : 'var(--c-violet)'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Panel>

          <Panel label="Modules" className="lg:col-span-5" flush>
            <div className="divide-y divide-line">
              {TOPICS.map((t) => {
                const solved = PROBLEMS.filter(
                  (p) => p.topic === t.slug && state.progress[p.slug] === 'Done'
                ).length;
                const complete = solved === 5;
                return (
                  <Link
                    key={t.slug}
                    to={`/problems/${t.slug}`}
                    className="group flex items-center justify-between gap-3 px-4 py-3 hover:bg-canvas transition-colors"
                  >
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-ink group-hover:text-mint transition-colors truncate">
                        {t.title}
                      </div>
                      <div className="text-[10px] text-muted truncate">{t.description}</div>
                    </div>
                    <span
                      className={`shrink-0 font-mono text-[11px] font-bold tnum px-2 py-0.5 rounded border ${
                        complete
                          ? 'text-mint border-mint/40 bg-mint/10'
                          : 'text-muted border-line bg-canvas'
                      }`}
                    >
                      {solved}/5
                    </span>
                  </Link>
                );
              })}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
};
