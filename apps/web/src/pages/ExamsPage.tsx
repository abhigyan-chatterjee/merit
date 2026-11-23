import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Play, ListChecks, Gauge, Briefcase } from 'lucide-react';
import { TARGETED_EXAMS, TargetedExam } from '../data/exams';
import { TOPICS } from '../data/curriculum';
import { Panel } from '../components/ui/Panel';

const LEVEL_TONE: Record<string, string> = {
  Beginner: 'text-mint border-mint/40 bg-mint/10',
  Intermediate: 'text-violet border-violet/40 bg-violet/10',
  Advanced: 'text-amber border-amber/40 bg-amber/10',
};

const CATEGORY_TABS: Array<{ id: TargetedExam['category'] | 'all'; label: string }> = [
  { id: 'all', label: 'All' },
  { id: 'company', label: 'Recruiter Mocks' },
  { id: 'screening', label: 'Screening' },
  { id: 'dsa', label: 'DSA Topics' },
];

const TOPIC_TITLES = new Map(TOPICS.map((t) => [t.slug, t.title]));
const formatTopic = (slug: string) => TOPIC_TITLES.get(slug) ?? slug.replace(/-/g, ' ');

function formatDuration(sec: number): string {
  const m = Math.round(sec / 60);
  return `${m} min`;
}

export const ExamsPage: React.FC = () => {
  const [category, setCategory] = useState<TargetedExam['category'] | 'all'>('all');
  const exams = category === 'all' ? TARGETED_EXAMS : TARGETED_EXAMS.filter((e) => e.category === category);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <div className="space-y-1.5">
        <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-violet">
          Timed assessments
        </span>
        <h1 className="text-2xl font-bold tracking-tight text-ink">Targeted exams</h1>
        <p className="text-xs text-muted max-w-2xl">
          Focused exam sets with a strict countdown timer and server-side grading.
          Pick a track, beat the clock, then retry only what you missed.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {CATEGORY_TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setCategory(tab.id)}
            className={`px-3 py-1.5 rounded-lg border font-mono text-[11px] uppercase tracking-[0.12em] transition cursor-pointer ${
              category === tab.id
                ? 'bg-violet text-canvas border-violet'
                : 'bg-surface text-muted border-line hover:border-steel'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {exams.map((exam) => (
          <Panel key={exam.id} label={exam.level} bracket>
            <div className="flex flex-col gap-4 h-full">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-0.5 rounded border font-mono text-[10px] uppercase ${LEVEL_TONE[exam.level]}`}
                  >
                    {exam.level}
                  </span>
                  {exam.company && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-mint/40 bg-mint/10 font-mono text-[10px] uppercase text-mint">
                      <Briefcase className="w-3 h-3" />
                      {exam.company}
                    </span>
                  )}
                </div>
                <h2 className="text-base font-bold text-ink">{exam.title}</h2>
                <p className="text-xs text-muted leading-relaxed">{exam.description}</p>
              </div>

              <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-muted">
                <span className="inline-flex items-center gap-1.5">
                  <ListChecks className="w-3.5 h-3.5 text-mint" />
                  {exam.questionCount} MCQs{exam.coding.length > 0 && ` · ${exam.coding.length} coding`} · {formatDuration(exam.durationSec)}
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <Gauge className="w-3.5 h-3.5 text-violet" />
                  {exam.topics.map(formatTopic).join(' · ')}
                </span>
              </div>

              <Link
                to={`/exams/${exam.id}`}
                className="mt-auto inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-violet text-canvas font-semibold text-xs hover:brightness-110 transition cursor-pointer"
              >
                <Play className="w-3.5 h-3.5" />
                Start exam
              </Link>
            </div>
          </Panel>
        ))}
      </div>
    </div>
  );
};
