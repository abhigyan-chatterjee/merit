"""Sync content/paths/*.json into the guest-mode static bundle.

Reads every content/paths/<slug>.json, validates through LearningPathSchema,
and writes apps/web/src/data/learningPaths.ts (LEARNING_PATHS array + types).

Keeps the guest-mode fallback byte-identical to the backend seed source
(including per-step summary + readingLinks guides): one command refreshes
both. Run after adding or editing paths:

    python3 content/generators/sync_paths_ts.py

The script never touches content/paths -- it only reads them.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from content.validators.schema import LearningPathSchema  # noqa: E402

PATHS_DIR = REPO_ROOT / "content" / "paths"
OUTPUT_TS = REPO_ROOT / "apps" / "web" / "src" / "data" / "learningPaths.ts"

HEADER = """export type StepType = 'visualizer' | 'problem' | 'quiz';

export interface PathStep {
  type: StepType;
  /** Visualizer id, problem slug, or quiz id (topic slug or 'mixed'). */
  id: string;
  /** `title` required only for mixed-quiz steps to be human-readable. */
  title?: string;
  /** One-line beginner summary shown on path detail pages. */
  summary?: string;
  /** Further-reading URLs (Foundation topics). */
  readingLinks?: string[];
}

export interface LearningPath {
  id: string;
  title: string;
  blurb: string;
  icon: 'LayoutGrid' | 'GitCommit' | 'Network' | 'Cpu';
  steps: PathStep[];
}

/**
 * Canonical 3-path structure (mirrors content/paths/*.json).
 * Summaries + reading links live in the JSON; the TS mirror keeps
 * routing/progress working offline. Regenerate with sync_paths_ts.py
 * when JSON changes -- do not hand-edit steps below.
 */
"""


def ts_string(value: str) -> str:
    # Single-quoted TS strings to match repo style (escape embedded quotes).
    escaped = (
        value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")
    )
    return f"'{escaped}'"


def render_step(step: dict) -> str:
    type_map = {"visualizer": "'visualizer'", "problem": "'problem'", "quiz": "'quiz'", "mock": "'quiz'"}
    parts = [
        f"type: {type_map.get(step['step_type'], repr(step['step_type']))}",
        f"id: {ts_string(step['ref_id'])}",
    ]
    if step.get("title"):
        parts.append(f"title: {ts_string(step['title'])}")
    if step.get("summary"):
        parts.append(f"summary: {ts_string(step['summary'])}")
    if step.get("reading_links"):
        links = ", ".join(ts_string(u) for u in step["reading_links"])
        parts.append(f"readingLinks: [{links}]")
    return "{ " + ", ".join(parts) + " }"


def sync() -> int:
    paths: list[dict] = []
    for fp in sorted(PATHS_DIR.glob("*.json")):
        with open(fp, encoding="utf-8") as f:
            raw = json.load(f)
        path = LearningPathSchema(**raw)
        if not path.is_published:
            continue
        paths.append(raw)

    paths.sort(key=lambda d: d.get("ordinal", 99))

    chunks = [HEADER, "\nexport const LEARNING_PATHS: LearningPath[] = ["]
    for d in paths:
        chunks.append("  {")
        chunks.append(f"    id: {ts_string(d['slug'])},")
        chunks.append(f"    title: {ts_string(d['title'])},")
        chunks.append(f"    blurb: {ts_string(d['blurb'])},")
        chunks.append(f"    icon: {ts_string(d['icon'])},")
        chunks.append("    steps: [")
        for step in sorted(d["steps"], key=lambda s: s["ordinal"]):
            chunks.append(f"      {render_step(step)},")
        chunks.append("    ]")
        chunks.append("  },")
    chunks.append("];\n")

    OUTPUT_TS.write_text("\n".join(chunks), encoding="utf-8")
    total_steps = sum(len(d["steps"]) for d in paths)
    print(f"Synced {len(paths)} paths ({total_steps} steps) -> {OUTPUT_TS.relative_to(REPO_ROOT)}")
    return len(paths)


if __name__ == "__main__":
    sync()
