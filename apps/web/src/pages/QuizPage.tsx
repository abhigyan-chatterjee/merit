import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { QUIZZES, QUIZ_TOPICS } from '../data/quizzes';
import { QuizEngine } from '../components/QuizEngine';
import { useProgress } from '../store/ProgressContext';
import { BrainCircuit, Shuffle } from 'lucide-react';
import { NotFound } from '../components/NotFound';

export const QuizPage: React.FC = () => {
  const { topic = 'arrays' } = useParams<{ topic: string }>();
  const { saveQuizScore } = useProgress();

  const currentTopic = QUIZ_TOPICS.find((t) => t.id === topic);
  if (!currentTopic) {
    return (
      <NotFound
        title="Quiz Not Found"
        message={`We couldn't find a quiz for topic "${topic}". Please pick an assessment topic from our curriculum.`}
        backTo="/dashboard"
        backLabel="Dashboard"
      />
    );
  }
  const questions = QUIZZES[currentTopic.id] || [];

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
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

      {/* Topic switcher */}
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="text-[10px] font-mono uppercase tracking-[0.16em] text-muted mr-1">
          Topic
        </span>
        {QUIZ_TOPICS.map((qt) => {
          const active = qt.id === currentTopic.id;
          const isMixed = qt.id === 'mixed';
          return (
            <Link
              key={qt.id}
              to={`/quiz/${qt.id}`}
              aria-current={active ? 'page' : undefined}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition cursor-pointer border ${
                active
                  ? 'bg-violet text-canvas border-violet font-semibold'
                  : 'bg-surface text-muted border-line hover:text-ink hover:border-steel'
              }`}
            >
              {isMixed && <Shuffle className="w-3 h-3" />}
              {qt.title}
            </Link>
          );
        })}
      </div>

      {/* Interactive Quiz Engine */}
      <QuizEngine
        topicTitle={currentTopic.title}
        questions={questions}
        onComplete={(pct) => saveQuizScore(currentTopic.id, pct)}
      />
    </div>
  );
};
