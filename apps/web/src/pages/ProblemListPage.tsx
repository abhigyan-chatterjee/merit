import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { PROBLEMS } from '../data/problems';
import { TOPICS } from '../data/curriculum';
import { ProblemTable } from '../components/ProblemTable';
import { Code2, BrainCircuit } from 'lucide-react';
import { useProgress } from '../store/ProgressContext';

export const ProblemListPage: React.FC = () => {
  const { topic = 'arrays-hashing' } = useParams<{ topic: string }>();
  const navigate = useNavigate();
  const { state } = useProgress();

  const currentTopic = TOPICS.find((t) => t.slug === topic) || TOPICS[0];
  const topicProblems = PROBLEMS.filter((p) => p.topic === currentTopic.slug);
  const doneCount = topicProblems.filter((p) => state.progress[p.slug] === 'Done').length;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      {/* Topic selector (compact dropdown) */}
      <div className="flex flex-wrap items-center gap-2 pb-4 border-b border-line">
        <label
          htmlFor="problem-topic"
          className="text-[10px] font-mono uppercase tracking-[0.16em] text-muted"
        >
          Topic
        </label>
        <select
          id="problem-topic"
          value={currentTopic.slug}
          onChange={(e) => navigate(`/problems/${e.target.value}`)}
          className="px-3 py-2 rounded-lg bg-surface border border-line text-xs font-mono text-ink hover:border-steel cursor-pointer focus:outline-none focus:border-mint"
        >
          {TOPICS.map((t) => (
            <option key={t.slug} value={t.slug}>
              {t.title}
            </option>
          ))}
        </select>
        <span className="text-[11px] font-mono text-muted ml-auto tnum">
          {doneCount} / {topicProblems.length} solved
        </span>
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
