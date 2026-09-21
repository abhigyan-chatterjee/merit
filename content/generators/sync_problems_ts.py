"""Sync verified content/problems/*.json into the guest-mode static bundle.

Reads every verified content/problems/<slug>.json (excluding scrap-*.json),
validates through ProblemSchema, and writes apps/web/src/data/problems.ts
(PROBLEMS array + Problem/TestCase/ProblemSolution/ProblemEditorial types).

Usage:
    python3 content/generators/sync_problems_ts.py
    python3 content/generators/sync_problems_ts.py --wire-sequences
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from content.taxonomy import CATEGORY_SLUGS as TOPIC_ORDER
from content.validators.schema import ProblemSchema

PROBLEMS_DIR = REPO_ROOT / "content" / "problems"
OUTPUT_TS = REPO_ROOT / "apps" / "web" / "src" / "data" / "problems.ts"

DIFF_RANK = {"Easy": 0, "Medium": 1, "Hard": 2}

TOPIC_PREFIXES: dict[str, str] = {
    "arrays-hashing": "arr",
    "two-pointers": "tp",
    "sliding-windows": "sw",
    "stack": "stack",
    "linked-lists": "ll",
    "binary-search": "bs",
    "trees": "tree",
    "heap": "heap",
    "backtracking": "bt",
    "graphs": "graph",
    "dynamic-programming": "dp",
    "greedy": "greedy",
    "trie": "trie",
    "intervals": "intervals",
    "math-matrices": "math",
    "bit-manipulation": "bit",
    "sorting": "sort",
    "data-structures": "ds",
}

HEADER = """export interface ProblemExample {
  input: string;
  output: string;
  explanation?: string;
}

export interface ProblemSolution {
  title: string;
  complexity: string;
  language: 'javascript' | 'python';
  code: string;
}

export interface TestCase {
  input: any[];
  expected: any;
  label: string;
}

export interface ProblemEditorial {
  approach: string;
  why_optimal: string;
  pitfalls: string;
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
  editorial?: ProblemEditorial;
  readingLinks?: string[];
}
"""


def ts_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def load_existing_ids() -> dict[str, str]:
    if not OUTPUT_TS.exists():
        return {}
    content = OUTPUT_TS.read_text(encoding="utf-8")
    matches = re.findall(
        r'id:\s*["\']([^"\']+)["\'],\s*slug:\s*["\']([^"\']+)["\']', content
    )
    return {slug: pid for pid, slug in matches}


def get_topic_prefix(topic: str) -> str:
    return TOPIC_PREFIXES.get(topic, topic.split("-")[0])


def wire_sequences() -> int:
    """Wire clean sequence chains for every verified problem topic."""
    files = sorted(PROBLEMS_DIR.glob("*.json"))
    by_topic: dict[str, list[tuple[Path, dict]]] = {}

    for fp in files:
        if fp.name.startswith("scrap-"):
            continue
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)
        status = data.get("reviewStatus") or data.get("review_status") or "verified"
        if status != "verified":
            continue
        by_topic.setdefault(data["topic"], []).append((fp, data))

    total_wired = 0
    for topic, items in by_topic.items():
        items.sort(
            key=lambda x: (
                DIFF_RANK.get(x[1].get("difficulty"), 99),
                x[1]["title"],
                x[1]["slug"],
            )
        )
        n = len(items)
        for i, (fp, data) in enumerate(items):
            seq = i + 1
            prev_slug = items[i - 1][1]["slug"] if i > 0 else None
            next_slug = items[i + 1][1]["slug"] if i < n - 1 else None
            data["sequence"] = seq
            data["prevSlug"] = prev_slug
            data["nextSlug"] = next_slug
            fp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            total_wired += 1

    print(f"Wired sequences for {total_wired} problems across {len(by_topic)} topics")
    return total_wired


def render_problem(data: dict) -> str:
    starter = data.get("starterCode", "")
    if isinstance(starter, dict):
        starter = starter.get("javascript", "")

    lines = [
        "  {",
        f"    id: {ts_string(data['id'])},",
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
        lang = sol.get("language") or "javascript"
        lines.append(f"        language: {ts_string(lang)},")
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
            f"      {{ input: {json.dumps(tc['input'], ensure_ascii=False)}, "
            f"expected: {json.dumps(tc['expected'], ensure_ascii=False)}, "
            f"label: {ts_string(tc.get('label', ''))} }},"
        )
    lines.append("    ],")
    if data.get("editorial"):
        ed = data["editorial"]
        lines.append("    editorial: {")
        lines.append(f"      approach: {ts_string(ed.get('approach', ''))},")
        lines.append(f"      why_optimal: {ts_string(ed.get('why_optimal', ''))},")
        lines.append(f"      pitfalls: {ts_string(ed.get('pitfalls', ''))},")
        lines.append("    },")
    if data.get("reading_links"):
        lines.append("    readingLinks: [")
        for link in data["reading_links"]:
            lines.append(f"      {ts_string(link)},")
        lines.append("    ],")
    lines.append("  },")
    return "\n".join(lines)


def sync() -> int:
    existing_ids = load_existing_ids()
    # Compute max counter per prefix from existing IDs
    prefix_counters: dict[str, int] = {}
    for pid in existing_ids.values():
        m = re.match(r"^([a-z0-9]+)-(\d+)$", pid)
        if m:
            pfx, num = m.group(1), int(m.group(2))
            prefix_counters[pfx] = max(prefix_counters.get(pfx, 0), num)

    files = sorted(PROBLEMS_DIR.glob("*.json"))
    problems: list[dict] = []
    for fp in files:
        if fp.name.startswith("scrap-"):
            continue
        with open(fp, encoding="utf-8") as f:
            raw = json.load(f)
        prob = ProblemSchema(**raw)
        if prob.review_status != "verified":
            continue
        problems.append(raw)

    # Order deterministically by (topic, difficulty-rank Easy<Medium<Hard, slug)
    problems.sort(
        key=lambda d: (
            TOPIC_ORDER.index(d["topic"]) if d["topic"] in TOPIC_ORDER else 99,
            DIFF_RANK.get(d.get("difficulty"), 99),
            d["slug"],
        )
    )

    # Assign IDs: keep existing IDs, assign continuing counters for new
    for d in problems:
        slug = d["slug"]
        if slug in existing_ids:
            d["id"] = existing_ids[slug]
        else:
            pfx = get_topic_prefix(d["topic"])
            counter = prefix_counters.get(pfx, 0) + 1
            prefix_counters[pfx] = counter
            d["id"] = f"{pfx}-{counter}"
            existing_ids[slug] = d["id"]

    counts: dict[str, int] = {}
    for d in problems:
        counts[d["topic"]] = counts.get(d["topic"], 0) + 1

    chunks = [HEADER, "\nexport const PROBLEMS: Problem[] = ["]
    prev_topic = None
    for d in problems:
        if d["topic"] != prev_topic:
            chunks.append(f"\n  // {d['topic'].upper()} ({counts[d['topic']]} problems)")
            prev_topic = d["topic"]
        chunks.append(render_problem(d))
    chunks.append("];\n")

    OUTPUT_TS.write_text("\n".join(chunks), encoding="utf-8")
    print(f"Synced {len(problems)} verified problems -> {OUTPUT_TS.relative_to(REPO_ROOT)}")
    print("Per-topic: " + ", ".join(f"{t}={counts.get(t, 0)}" for t in TOPIC_ORDER if t in counts))
    return len(problems)


def main():
    parser = argparse.ArgumentParser(description="Sync problems to TypeScript bundle")
    parser.add_argument(
        "--wire-sequences",
        action="store_true",
        help="Wire sequence numbers and prevSlug/nextSlug in every verified problem JSON",
    )
    args = parser.parse_args()

    if args.wire_sequences:
        wire_sequences()
    sync()


if __name__ == "__main__":
    main()
