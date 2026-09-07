import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { PROBLEMS } from '../data/problems';
import { TOPICS } from '../data/curriculum';
import { ProblemTable } from '../components/ProblemTable';
import { Code2, BrainCircuit } from 'lucide-react';
import { useProgress } from '../store/ProgressContext';

export const ProblemListPage: React.FC = () => {
  const { topic = 'arrays' } = useParams<{ topic: string }>();
  const { state } = useProgress();

  const currentTopic = TOPICS.find((t) => t.slug === topic) || TOPICS[0];
  const topicProblems = PROBLEMS.filter((p) => p.topic === currentTopic.slug);
  const doneCount = topicProblems.filter((p) => state.progress[p.slug] === 'Done').length;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      {/* Topic Navigation Tabs */}
      <div className="flex flex-wrap items-center gap-1.5 pb-4 border-b border-line">
        {TOPICS.map((t) => {
          const active = t.slug === currentTopic.slug;
          return (
            <Link
              key={t.slug}
              to={`/problems/${t.slug}`}
              className={`px-3.5 py-2 rounded-lg text-xs font-mono font-semibold transition ${
                active
                  ? 'bg-mint text-canvas'
                  : 'bg-surface text-muted border border-line hover:text-ink'
              }`}
            >
              {t.title.split('&')[0].trim()}
            </Link>
          );
        })}
      </div>

      {/* Header Info & Topic Quiz Shortcut */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-xl border border-line bg-surface">
        <div>
          <h1 className="text-xl font-bold text-ink flex items-center gap-2">
            <Code2 className="w-5 h-5 text-mint" />
            {currentTopic.title} Problems
          </h1>
          <p className="text-xs text-muted mt-1">{currentTopic.description}</p>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right font-mono">
            <div className="text-sm font-bold text-mint">
              {doneCount} / {topicProblems.length} Solved
            </div>
            <div className="text-[11px] text-muted">Topic Completion</div>
          </div>

          <Link
            to={`/quiz/${currentTopic.slug}`}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-violet text-canvas font-semibold text-xs hover:brightness-110 transition"
          >
            <BrainCircuit className="w-4 h-4" />
            Topic quiz
          </Link>
        </div>
      </div>

      {/* Problem Table */}
      <ProblemTable problems={topicProblems} topicTitle={currentTopic.title} />
    </div>
  );
};
