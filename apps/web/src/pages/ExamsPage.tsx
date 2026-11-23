import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Play, Briefcase } from 'lucide-react';
import { TARGETED_EXAMS, TargetedExam } from '../data/exams';
import { Panel } from '../components/ui/Panel';

const CATEGORY_TABS: Array<{ id: TargetedExam['category'] | 'all'; label: string }> = [
  { id: 'all', label: 'All' },
  { id: 'company', label: 'Recruiter Mocks' },
  { id: 'screening', label: 'Screening' },
  { id: 'dsa', label: 'DSA Topics' },
];

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
        <h1 className="text-2xl font-bold tracking-tight text-ink">Exams</h1>
        <p className="text-xs text-muted">Strict countdown, server-graded.</p>
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
          <Panel key={exam.id} bracket>
            <div className="flex flex-col gap-4 h-full">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  {exam.company && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-mint/40 bg-mint/10 font-mono text-[10px] uppercase text-mint">
                      <Briefcase className="w-3 h-3" />
                      {exam.company}
                    </span>
                  )}
                  <span className="text-[10px] font-mono uppercase tracking-[0.12em] text-muted">
                    {exam.level}
                  </span>
                </div>
                <h2 className="text-base font-bold text-ink">{exam.title}</h2>
                <p className="text-xs text-muted leading-relaxed">{exam.description}</p>
              </div>

              <p className="text-[11px] font-mono text-muted">
                {exam.questionCount} MCQs · {formatDuration(exam.durationSec)}
              </p>

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
