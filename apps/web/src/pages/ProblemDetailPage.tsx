import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { PROBLEMS } from '../data/problems';
import { CodeRunner } from '../components/CodeRunner';
import { AiTutor } from '../components/AiTutor';
import {
  ArrowLeft,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  BookOpen,
  FileText,
  Bookmark,
  CheckCircle2,
  GraduationCap,
  ExternalLink,
} from 'lucide-react';
import { useProgress, ProblemStatus } from '../store/ProgressContext';
import { NotFound } from '../components/NotFound';
import { LessonNav } from '../components/LessonNav';

export const ProblemDetailPage: React.FC = () => {
  const { topic = 'arrays-hashing', slug = 'two-sum' } = useParams<{ topic: string; slug: string }>();
  const { state, setProblemStatus, saveNote, toggleBookmark, setLastVisited } = useProgress();

  const problem = PROBLEMS.find((p) => p.slug === slug && p.topic === topic);
  const [hintsOpen, setHintsOpen] = useState(false);
  const [editorialOpen, setEditorialOpen] = useState(false);
  const [activeSolutionTab, setActiveSolutionTab] = useState<number | null>(null);
  const [noteText, setNoteText] = useState(problem ? state.notes[problem.slug] || '' : '');

  useEffect(() => {
    if (problem) {
      setNoteText(state.notes[problem.slug] || '');
      setLastVisited({
        type: 'problem',
        title: problem.title,
        path: `/problems/${problem.topic}/${problem.slug}`,
        subtitle: `${problem.difficulty} • ${problem.pattern}`
      });
    }
  }, [problem?.slug, problem?.topic]);


  if (!problem) {
    return (
      <NotFound
        title="Problem Not Found"
        message={`The problem "${slug}" was not found under topic "${topic}".`}
        backTo="/problems"
        backLabel="All Problems"
      />
    );
  }

  const currentStatus = state.progress[problem.slug] || 'Todo';
  const isBookmarked = state.bookmarks.includes(problem.slug);

  const handleNoteChange = (val: string) => {
    setNoteText(val);
    saveNote(problem.slug, val);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Guided Path Lesson Navigation */}
      <LessonNav currentType="problem" currentId={problem.slug} />

      {/* Prev / Next in category sequence */}
      {(problem.prevSlug || problem.nextSlug) && (
        <nav aria-label="Sequence" className="flex items-center justify-between gap-3 text-xs font-mono">
          {problem.prevSlug ? (
            <Link
              to={`/problems/${problem.topic}/${problem.prevSlug}`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-line bg-surface text-muted hover:text-ink hover:border-steel transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Previous in {problem.topic}
            </Link>
          ) : (
            <span />
          )}
          {problem.nextSlug && (
            <Link
              to={`/problems/${problem.topic}/${problem.nextSlug}`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-line bg-surface text-muted hover:text-ink hover:border-steel transition"
            >
              Next in {problem.topic}
              <ArrowLeft className="w-3.5 h-3.5 rotate-180" />
            </Link>
          )}
        </nav>
      )}

      {/* Top Breadcrumb & Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-line">
        <div className="flex items-center gap-3">
          <Link
            to={`/problems/${topic}`}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-line bg-surface text-xs font-mono text-muted hover:text-ink"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to {topic}
          </Link>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-ink">{problem.title}</h1>
              <span className="px-2 py-0.5 rounded bg-canvas border border-line text-[11px] font-mono text-violet">
                {problem.pattern}
              </span>
            </div>
          </div>
        </div>


        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-surface border border-line">
            <CheckCircle2 className="w-4 h-4 text-mint" />
            <span className="text-xs font-mono text-muted">Status:</span>
            <select
              aria-label="Problem Status"
              value={currentStatus}
              onChange={(e) => setProblemStatus(problem.slug, e.target.value as ProblemStatus)}
              className="bg-transparent text-xs font-mono text-ink focus:outline-none cursor-pointer"
            >
              <option value="Todo" className="bg-surface">Todo</option>
              <option value="Doing" className="bg-surface">Doing</option>
              <option value="Done" className="bg-surface">Done</option>
            </select>
          </div>

          <button
            onClick={() => toggleBookmark(problem.slug)}
            aria-label="Bookmark problem"
            className={`p-2 rounded-lg border border-line bg-surface cursor-pointer ${
              isBookmarked ? 'text-amber' : 'text-muted'
            }`}
          >
            <Bookmark className={`w-4 h-4 ${isBookmarked ? 'fill-amber' : ''}`} />
          </button>
        </div>
      </div>

      {/* Main Split Grid: Left = Statement, Hints, Solutions, Notes | Right = Interactive CodeRunner */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column */}
        <div className="lg:col-span-5 space-y-5">
          {/* Statement & Examples Card */}
          <div className="p-5 rounded-xl border border-line bg-surface space-y-4">
            <p className="text-sm text-ink leading-relaxed">{problem.statement}</p>

            {/* Examples */}
            <div className="space-y-3 pt-2">
              {problem.examples.map((ex, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-canvas border border-line font-mono text-xs space-y-1"
                >
                  <div className="text-muted font-semibold">Example {idx + 1}:</div>
                  <div>
                    <span className="text-muted">Input: </span>
                    <span className="text-ink">{ex.input}</span>
                  </div>
                  <div>
                    <span className="text-muted">Output: </span>
                    <span className="text-mint">{ex.output}</span>
                  </div>
                  {ex.explanation && (
                    <div className="text-muted text-[11px] pt-1">
                      Explanation: {ex.explanation}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Constraints */}
            <div className="pt-2">
              <h4 className="text-xs font-mono uppercase tracking-wider text-muted mb-2">
                Constraints:
              </h4>
              <ul className="list-disc list-inside text-xs font-mono text-ink space-y-1">
                {problem.constraints.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Progressive Hints Accordion */}
          <div className="rounded-xl border border-line bg-surface overflow-hidden">
            <button
              onClick={() => setHintsOpen((o) => !o)}
              className="w-full flex items-center justify-between p-4 text-xs font-mono font-semibold text-amber hover:bg-canvas/40 transition cursor-pointer"
            >
              <span className="flex items-center gap-2">
                <Lightbulb className="w-4 h-4" />
                 Progressive Algorithmic Hints ({problem.hints.length})
              </span>
              {hintsOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {hintsOpen && (
              <div className="p-4 pt-0 space-y-2 border-t border-line text-xs">
                {problem.hints.map((h, i) => (
                  <div
                    key={i}
                    className="p-2.5 rounded bg-canvas border border-line text-ink font-mono"
                  >
                    <span className="text-amber font-bold mr-2">Hint #{i + 1}:</span>
                    {h}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Solution Tabs (Brute Force vs Optimal) */}
          <div className="p-4 rounded-xl border border-line bg-surface space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-semibold text-violet flex items-center gap-1.5">
                <BookOpen className="w-4 h-4" />
                Reference Solutions & Big-O
              </span>
              <div className="flex items-center gap-1.5">
                {problem.solutions.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => setActiveSolutionTab(activeSolutionTab === idx ? null : idx)}
                    className={`px-2.5 py-1 rounded text-xs font-mono border cursor-pointer ${
                      activeSolutionTab === idx
                        ? 'border-violet bg-violet/15 text-ink'
                        : 'border-line bg-canvas text-muted'
                    }`}
                  >
                    {idx === 0 ? 'Brute Force' : 'Optimal Solution'}
                  </button>
                ))}
              </div>
            </div>

            {activeSolutionTab !== null && problem.solutions[activeSolutionTab] && (
              <div className="space-y-2 pt-2">
                <div className="text-xs font-mono text-mint">
                  {problem.solutions[activeSolutionTab].complexity}
                </div>
                <pre className="p-3 rounded-lg bg-canvas border border-line font-mono text-xs text-ink overflow-x-auto">
                  {problem.solutions[activeSolutionTab].code}
                </pre>
              </div>
            )}
          </div>

          {/* Editorial Accordion (approach → why optimal → pitfalls) */}
          {problem.editorial && (
            <div className="rounded-xl border border-line bg-surface overflow-hidden">
              <button
                onClick={() => setEditorialOpen((o) => !o)}
                className="w-full flex items-center justify-between p-4 text-xs font-mono font-semibold text-mint hover:bg-canvas/40 transition cursor-pointer"
              >
                <span className="flex items-center gap-2">
                  <GraduationCap className="w-4 h-4" />
                  <h3 className="text-xs font-mono font-semibold">Editorial</h3>
                </span>
                {editorialOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {editorialOpen && (
                <div className="p-4 pt-0 space-y-3 border-t border-line text-xs">
                  <p className="text-ink leading-relaxed">{problem.editorial.approach}</p>
                  <div className="p-2.5 rounded bg-mint/10 border border-mint/30 text-ink font-mono">
                    <span className="text-mint font-bold mr-2">Why optimal:</span>
                    {problem.editorial.why_optimal}
                  </div>
                  <div>
                    <div className="text-muted font-semibold mb-1">Pitfalls:</div>
                    <ul className="list-disc list-inside text-ink font-mono space-y-1">
                      <li>{problem.editorial.pitfalls}</li>
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Further reading (max 3 outbound links) */}
          {problem.readingLinks && problem.readingLinks.length > 0 && (
            <div className="p-4 rounded-xl border border-line bg-surface space-y-2">
              <div>
                <h3 className="text-xs font-mono font-semibold text-ink flex items-center gap-1.5">
                  <ExternalLink className="w-4 h-4 text-mint" />
                  Further reading
                </h3>
              </div>
              <ul className="space-y-1.5">
                {problem.readingLinks.slice(0, 3).map((url) => (
                  <li key={url}>
                    <a
                      href={url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs font-mono text-mint hover:underline break-all"
                    >
                      {url}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Personal Notes Box */}
          <div className="p-4 rounded-xl border border-line bg-surface space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-mono font-semibold text-ink flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-mint" />
                Revision Notes
              </label>
            </div>
            <textarea
              rows={3}
              placeholder="Write down edge cases, time complexity notes, or key invariants..."
              value={noteText}
              onChange={(e) => handleNoteChange(e.target.value)}
              className="w-full p-3 rounded-lg bg-canvas border border-line text-xs font-mono text-ink placeholder-muted focus:outline-none focus:border-mint"
            />
          </div>
        </div>

        {/* Right Column: Interactive Sandbox Code Runner */}
        <div className="lg:col-span-7">
          <CodeRunner
              problemSlug={problem.slug}
              starterCode={problem.starterCode}
              functionName={problem.functionName}
              testCases={problem.testCases}
              onAllPassed={() => setProblemStatus(problem.slug, 'Done')}
              tutorEnabled={false}
            />
          {/* BYOK tutor: mount-only. AiTutor sends code="" (no live editor
              access — CodeRunner owns the textarea) and resolves
              failed_attempts itself from the judge submissions endpoint. */}
          <div className="mt-4">
            <AiTutor problemSlug={problem.slug} />
          </div>
        </div>
      </div>
    </div>
  );
};
