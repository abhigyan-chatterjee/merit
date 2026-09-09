"""Sync verified content/problems/*.json into the guest-mode static bundle.

Reads every verified content/problems/<slug>.json (excluding any with
reviewStatus != verified), validates through ProblemSchema, and writes
apps/web/src/data/problems.ts (PROBLEMS array + Problem/TestCase types).

This keeps the guest-mode static bank byte-identical to the backend seed
source: one command refreshes both. Run after adding or editing problems:

    python3 content/generators/sync_problems_ts.py

The script never touches content/problems -- it only reads them.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from content.validators.schema import ProblemSchema

PROBLEMS_DIR = REPO_ROOT / "content" / "problems"
OUTPUT_TS = REPO_ROOT / "apps" / "web" / "src" / "data" / "problems.ts"

from content.taxonomy import CATEGORY_SLUGS as TOPIC_ORDER

HEADER = """export interface ProblemExample {
  input: string;
  output: string;
  explanation?: string;
}

export interface ProblemSolution {
  title: string;
  complexity: string;
  code: string;
}

export interface TestCase {
  input: any[];
  expected: any;
  label: string;
}

export interface Problem {
  id: string;
  slug: string;
  title: string;
  topic: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  pattern: string;
  statement: string;
  examples: ProblemExample[];
  constraints: string[];
  hints: string[];
  solutions: ProblemSolution[];
  starterCode: string;
  functionName: string;
  testCases: TestCase[];
  sequence?: number | null;
  prevSlug?: string | null;
  nextSlug?: string | null;
}
"""


def ts_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_problem(data: dict, index: int) -> str:
    starter = data.get("starterCode", "")
    if isinstance(starter, dict):
        starter = starter.get("javascript", "")
    lines = [
        "  {",
        f"    id: {ts_string(data.get('id', f'p-{index}'))},",
        f"    slug: {ts_string(data['slug'])},",
        f"    title: {ts_string(data['title'])},",
        f"    topic: {ts_string(data['topic'])},",
        f"    difficulty: {ts_string(data['difficulty'])},",
        f"    pattern: {ts_string(data['pattern'])},",
        f"    statement: {ts_string(data['statement'])},",
        "    examples: [",
    ]
    for ex in data.get("examples", []):
        parts = [f"input: {ts_string(ex['input'])}", f"output: {ts_string(ex['output'])}"]
        if ex.get("explanation"):
            parts.append(f"explanation: {ts_string(ex['explanation'])}")
        lines.append("      { " + ", ".join(parts) + " },")
    lines.append("    ],")
    lines.append(
        "    constraints: ["
        + ", ".join(ts_string(c) for c in data.get("constraints", []))
        + "],"
    )
    lines.append("    hints: [")
    for h in data.get("hints", []):
        lines.append(f"      {ts_string(h)},")
    lines.append("    ],")
    lines.append("    solutions: [")
    for sol in data.get("solutions", []):
        lines.append("      {")
        lines.append(f"        title: {ts_string(sol.get('title', 'Solution'))},")
        lines.append(f"        complexity: {ts_string(sol.get('complexity', ''))},")
        lines.append(f"        code: {ts_string(sol.get('code', ''))},")
        lines.append("      },")
    lines.append("    ],")
    lines.append(f"    starterCode: {ts_string(starter)},")
    lines.append(f"    functionName: {ts_string(data.get('functionName', 'solve'))},")
    if data.get("sequence") is not None:
        lines.append(f"    sequence: {int(data['sequence'])},")
    if data.get("prevSlug"):
        lines.append(f"    prevSlug: {ts_string(data['prevSlug'])},")
    if data.get("nextSlug"):
        lines.append(f"    nextSlug: {ts_string(data['nextSlug'])},")
    lines.append("    testCases: [")
    for tc in data.get("testCases", []):
        lines.append(
            "      { input: "
            + json.dumps(tc["input"], ensure_ascii=False)
            + ", expected: "
            + json.dumps(tc["expected"], ensure_ascii=False)
            + f", label: {ts_string(tc.get('label', ''))} }},"
        )
    # fix trailing brace: each test case line above has an extra }
    lines[-len(data.get("testCases", [])) :] = [
        l[:-2] + " }," if l.endswith(" }},") else l
        for l in lines[-len(data.get("testCases", [])) :]
    ] if data.get("testCases") else []
    lines.append("    ],")
    lines.append("  },")
    return "\n".join(lines)


def sync() -> int:
    files = sorted(PROBLEMS_DIR.glob("*.json"))
    problems: list[dict] = []
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            raw = json.load(f)
        prob = ProblemSchema(**raw)
        if prob.review_status != "verified":
            continue
        problems.append(raw)

    problems.sort(
        key=lambda d: (
            TOPIC_ORDER.index(d["topic"]) if d["topic"] in TOPIC_ORDER else 99,
            d.get("sequence") or 999,
            d["slug"],
        )
    )

    counts: dict[str, int] = {}
    for d in problems:
        counts[d["topic"]] = counts.get(d["topic"], 0) + 1

    chunks = [HEADER, "\nexport const PROBLEMS: Problem[] = ["]
    prev_topic = None
    for i, d in enumerate(problems):
        if d["topic"] != prev_topic:
            chunks.append(f"\n  // {d['topic'].upper()} ({counts[d['topic']]} problems)")
            prev_topic = d["topic"]
        chunks.append(render_problem(d, i))
    chunks.append("];\n")

    OUTPUT_TS.write_text("\n".join(chunks), encoding="utf-8")
    print(f"Synced {len(problems)} verified problems -> {OUTPUT_TS.relative_to(REPO_ROOT)}")
    print("Per-topic: " + ", ".join(f"{t}={counts.get(t, 0)}" for t in TOPIC_ORDER))
    return len(problems)


if __name__ == "__main__":
    sync()
