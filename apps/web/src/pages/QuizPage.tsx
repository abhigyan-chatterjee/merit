import React from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { QUIZZES, QUIZ_TOPICS } from '../data/quizzes';
import { QuizEngine } from '../components/QuizEngine';
import { useProgress } from '../store/ProgressContext';
import { BrainCircuit } from 'lucide-react';
import { LessonNav } from '../components/LessonNav';

const prettifyTopic = (topic: string) =>
  topic
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');

const QUICK_TOPICS = ['aptitude', 'verbal', 'sql', 'cs-fundamentals', 'mixed'] as const;

const DSA_TOPICS = QUIZ_TOPICS.filter((t) => t.category === 'dsa');

export const QuizPage: React.FC = () => {
  const { topic = 'mixed' } = useParams<{ topic: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isMock = searchParams.get('mock') === 'true';
  const { saveQuizScore } = useProgress();


  const staticTopic = QUIZ_TOPICS.find((t) => t.id === topic);
  const currentTopic = staticTopic ?? {
    id: topic,
    title: prettifyTopic(topic),
    description: 'Targeted review drawn live from the placement question bank.',
  };
  const questions = QUIZZES[currentTopic.id] || [];
  const isDsaTopic = DSA_TOPICS.some((t) => t.id === currentTopic.id);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Guided Path Lesson Navigation */}
      <LessonNav currentType={isMock ? 'mock' : 'quiz'} currentId={currentTopic.id} />

      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-[10px] font-mono text-muted">
        <span className="text-mint">assessment</span>
        <span>/</span>
        <span className="text-ink">{currentTopic.id}</span>
      </nav>

      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4 pb-4 border-b border-line">
        <div className="space-y-1.5">
          <h1 className="text-2xl font-bold tracking-tight text-ink flex items-center gap-2.5">
            <BrainCircuit className="w-6 h-6 text-violet" />
            {currentTopic.title}
          </h1>
          <p className="text-xs text-muted">{currentTopic.description}</p>
        </div>
      </div>

      {/* Unified Topic Bar: Screening & Mixed pills + DSA topics dropdown */}
      <div className="flex flex-wrap items-center gap-2">
        {QUICK_TOPICS.map((id) => {
          const meta = QUIZ_TOPICS.find((t) => t.id === id)!;
          const active = currentTopic.id === id;
          return (
            <button
              key={id}
              type="button"
              aria-pressed={active}
              onClick={() => navigate(`/quiz/${id}`)}
              className={`px-3 py-1.5 rounded-full border font-mono text-[11px] transition cursor-pointer ${
                active
                  ? 'bg-mint text-canvas border-mint font-semibold'
                  : 'bg-surface text-muted border-line hover:border-steel hover:text-ink'
              }`}
            >
              {meta.title}
            </button>
          );
        })}

        <span className="hidden sm:inline-block h-5 w-px bg-line" aria-hidden="true" />

        <select
          id="quiz-dsa-topic"
          aria-label="DSA topic"
          value={isDsaTopic ? currentTopic.id : ''}
          onChange={(e) => {
            if (e.target.value) navigate(`/quiz/${e.target.value}`);
          }}
          className={`px-3 py-1.5 rounded-full border font-mono text-[11px] transition cursor-pointer focus:border-violet ${
            isDsaTopic
              ? 'border-mint bg-mint/10 text-mint font-semibold'
              : 'border-line bg-surface text-muted hover:border-steel hover:text-ink'
          }`}
        >
          <option value="" disabled>
            DSA topics ({DSA_TOPICS.length})…
          </option>
          {DSA_TOPICS.map((qt) => (
            <option key={qt.id} value={qt.id}>
              {qt.title}
            </option>
          ))}
        </select>
      </div>

      {/* Interactive Quiz Engine */}
      <QuizEngine
        key={currentTopic.id}
        topicTitle={currentTopic.title}
        topicId={currentTopic.id}
        questions={questions}
        isMock={isMock}
        examTopics={staticTopic ? undefined : [topic]}
        onComplete={(pct) => saveQuizScore(currentTopic.id, pct)}
      />
    </div>
  );
};
