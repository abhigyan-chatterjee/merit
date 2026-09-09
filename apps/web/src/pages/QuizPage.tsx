import React from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { QUIZZES, QUIZ_TOPICS } from '../data/quizzes';
import { QuizEngine } from '../components/QuizEngine';
import { useProgress } from '../store/ProgressContext';
import { BrainCircuit } from 'lucide-react';
import { NotFound } from '../components/NotFound';
import { LessonNav } from '../components/LessonNav';

export const QuizPage: React.FC = () => {
  const { topic = 'mixed' } = useParams<{ topic: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isMock = searchParams.get('mock') === 'true';
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
      {/* Guided Path Lesson Navigation */}
      <LessonNav currentType="quiz" currentId={currentTopic.id} />

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

      {/* Topic selector (compact dropdown, defaults to Mixed) */}
      <div className="flex flex-wrap items-center gap-2">
        <label
          htmlFor="quiz-topic"
          className="text-[10px] font-mono uppercase tracking-[0.16em] text-muted"
        >
          Topic
        </label>
        <select
          id="quiz-topic"
          value={currentTopic.id}
          onChange={(e) => navigate(`/quiz/${e.target.value}`)}
          className="px-3 py-2 rounded-lg bg-surface border border-line text-xs font-mono text-ink hover:border-steel cursor-pointer focus:outline-none focus:border-violet"
        >
          {QUIZ_TOPICS.map((qt) => (
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
        onComplete={(pct) => saveQuizScore(currentTopic.id, pct)}
      />
    </div>
  );
};

