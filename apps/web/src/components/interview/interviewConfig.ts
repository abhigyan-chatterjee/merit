import { PROBLEMS, Problem } from "../../data/problems";
import {
  InterviewDifficulty,
  InterviewProblemSummary,
  InterviewSessionDetail,
  InterviewStageDef,
} from "../../utils/api";

export interface InterviewTierSpec {
  id: InterviewDifficulty;
  title: string;
  tagline: string;
  durationSec: number;
  durationLabel: string;
  codingSlots: Array<"Easy" | "Medium" | "Hard">;
  maxScore: number;
  stages: InterviewStageDef[];
}

export const INTERVIEW_TIERS: InterviewTierSpec[] = [
  {
    id: "easy",
    title: "Easy",
    tagline: "CS basics · 1 Easy coding",
    durationSec: 1800,
    durationLabel: "30m",
    codingSlots: ["Easy"],
    maxScore: 20,
    stages: [
      { id: "theory", label: "Theory", kind: "theory" },
      { id: "coding_1", label: "Coding", kind: "coding", problem_index: 0 },
      { id: "wrapup", label: "Wrap-up", kind: "wrapup" },
      { id: "rubric", label: "Rubric", kind: "rubric" },
    ],
  },
  {
    id: "medium",
    title: "Medium",
    tagline: "Core CS · 2 coding · Project",
    durationSec: 2700,
    durationLabel: "45m",
    codingSlots: ["Easy", "Medium"],
    maxScore: 25,
    stages: [
      { id: "theory", label: "Theory", kind: "theory" },
      { id: "coding_1", label: "Coding 1", kind: "coding", problem_index: 0 },
      { id: "coding_2", label: "Coding 2", kind: "coding", problem_index: 1 },
      { id: "project", label: "Project", kind: "project" },
      { id: "rubric", label: "Rubric", kind: "rubric" },
    ],
  },
  {
    id: "hard",
    title: "Hard",
    tagline: "Deep CS · 2 coding · Project · System Design",
    durationSec: 3600,
    durationLabel: "60m",
    codingSlots: ["Medium", "Hard"],
    maxScore: 30,
    stages: [
      { id: "theory", label: "Deep CS", kind: "theory" },
      { id: "coding_1", label: "Coding 1", kind: "coding", problem_index: 0 },
      { id: "coding_2", label: "Coding 2", kind: "coding", problem_index: 1 },
      { id: "project", label: "Project", kind: "project" },
      { id: "system_design", label: "System Design", kind: "system_design" },
      { id: "rubric", label: "Rubric", kind: "rubric" },
    ],
  },
];

export const TIER_BY_ID: Record<InterviewDifficulty, InterviewTierSpec> = {
  easy: INTERVIEW_TIERS[0],
  medium: INTERVIEW_TIERS[1],
  hard: INTERVIEW_TIERS[2],
};

export function pickRandomProblemsForDifficulty(difficulty: InterviewDifficulty): Problem[] {
  const tier = TIER_BY_ID[difficulty];
  const chosen: Problem[] = [];
  const used = new Set<string>();
  for (const targetDiff of tier.codingSlots) {
    const pool = PROBLEMS.filter((p) => p.difficulty === targetDiff && !used.has(p.slug));
    if (pool.length === 0) continue;
    const picked = pool[Math.floor(Math.random() * pool.length)];
    chosen.push(picked);
    used.add(picked.slug);
  }
  return chosen;
}

export function problemToInterviewSummary(p: Problem): InterviewProblemSummary {
  return {
    slug: p.slug,
    title: p.title,
    topic: p.topic,
    difficulty: p.difficulty,
    pattern: p.pattern,
    statement: p.statement,
    examples: p.examples,
    constraints: p.constraints,
    starter_code: {
      javascript: p.starterCode,
      python: p.starterCodePython,
      java: p.starterCodeJava,
      cpp: p.starterCodeCpp,
    },
    function_name: p.functionName,
    test_cases: p.testCases.map((tc) => ({
      label: tc.label,
      input: tc.input,
      expected: tc.expected,
    })),
  };
}

export function formatClock(totalSeconds: number): string {
  const safe = Math.max(0, Math.floor(totalSeconds));
  const mins = Math.floor(safe / 60);
  const secs = safe % 60;
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

export function shortStageLabel(stageId: string, fallback: string): string {
  switch (stageId) {
    case "theory":
      return fallback.includes("Deep CS") ? "Deep CS" : "Theory";
    case "coding_1":
      return fallback.includes("#1") || fallback.includes("Coding 1") ? "Coding 1" : "Coding";
    case "coding_2":
      return "Coding 2";
    case "project":
      return "Project";
    case "system_design":
      return "System Design";
    case "wrapup":
      return "Wrap-up";
    case "rubric":
      return "Rubric";
    default:
      return fallback;
  }
}

export function formatRubricMarkdown(session: InterviewSessionDetail): string {
  const r = session.rubric;
  if (!r) return "";
  const lines: string[] = [
    `# Merit AI Mock Interview Scorecard (${session.difficulty.toUpperCase()})`,
    `**Verdict:** ${r.verdict} (${r.total} / ${r.max_total})`,
    session.resume_filename ? `**CV Attached:** ${session.resume_filename}` : "",
    "",
    "## Dimension Breakdown",
    ...r.dimensions.map((d) => `- **${d.name}:** ${d.score}/${d.max_score} — ${d.comment}`),
  ].filter(Boolean);

  if (r.strengths.length > 0) {
    lines.push("", "## Strengths", ...r.strengths.map((s) => `- ${s}`));
  }
  if (r.improvements.length > 0) {
    lines.push("", "## Actionable Improvements", ...r.improvements.map((s) => `- ${s}`));
  }
  if (r.summary) {
    lines.push("", "## Summary", r.summary);
  }
  return lines.join("\n");
}
