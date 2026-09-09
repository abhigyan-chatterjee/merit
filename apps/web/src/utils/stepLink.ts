import { PathStep } from '../data/learningPaths';
import { PROBLEMS } from '../data/problems';
import { VISUALIZERS } from '../data/curriculum';
import { QUIZZES, QUIZ_TOPICS } from '../data/quizzes';

export interface ResolvedStep {
  step: PathStep;
  title: string;
  subtitle: string;
  link: string;
}

/**
 * Resolves a learning-path step into a human-readable title, a one-line
 * subtitle, and the route to open it.
 */
export function resolveStep(step: PathStep): ResolvedStep {
  if (step.type === 'visualizer') {
    const viz = VISUALIZERS.find((v) => v.id === step.id);
    return {
      step,
      title: step.title ?? viz?.title ?? step.id,
      subtitle: viz ? `${viz.category} · avg ${viz.timeComplexity.avg}` : 'Interactive workbench',
      link: `/visualizers/${step.id}`
    };
  }

  if (step.type === 'problem') {
    const problem = PROBLEMS.find((p) => p.slug === step.id);
    return {
      step,
      title: problem?.title ?? step.id,
      subtitle: problem ? `${problem.difficulty} · ${problem.pattern}` : 'Coding problem',
      link: problem ? `/problems/${problem.topic}/${problem.slug}` : '/problems/arrays-hashing'
    };
  }

  // quiz
  const quizTopic = QUIZ_TOPICS.find((t) => t.id === step.id);
  return {
    step,
    title: step.title ?? quizTopic?.title ?? 'Quiz',
    subtitle: quizTopic ? `${QUIZZES[quizTopic.id]?.length ?? 10} questions` : '10 questions',
    link: `/quiz/${step.id}`
  };
}
