"""Import scraped DSA catalog entries as draft problems + quiz questions.

Reads content/catalog/catalog.json (built by build_catalog.py from the
Mimo-scraped CSVs) and materializes entries NOT already in Algovista as:

  content/problems/scrap-<slug>.json  (review_status="draft")
  content/questions/<algo_topic>/scrap-<slug>-<topic4>.json  (review_status="draft")

Deliberately conservative:
- Only entries with a KNOWN difficulty (Easy/Medium/Hard) are imported.
  "Unknown" rows are skipped and reported.
- Statements are original, generated from the entry's own metadata
  (title, topics, companies, difficulty) -- never copied from any source
  URL. The source_url is stored as attribution only.
- Problem files carry full judge scaffolding (statement, examples,
  constraints, hints, JS+Python starters, 3+ test cases, 1+ solutions)
  but stay "draft" so sync_problems_ts + seed skip them until a human
  verifies expected outputs by running the reference solution.
- Question files are concept-level MCQs derived from the entry metadata
  (never fake "expected outputs"); hashes follow compute_content_hash.

Draft-safety (verified, not assumed):
- content/validators/verify_problems.py SKIPS reviewStatus="draft" files
  for judge execution (schema still parses them).
- content/validators/verify_questions.py + coverage_report.py count only
  review_status="verified".
- apps/api/app/seed.py, content router, and sampler filter
  review_status == "verified", so drafts never reach the DB, API, or exams.
- apps/web static bundle (sync_problems_ts.py) includes verified only.

Usage:
    python3 content/generators/import_scraped.py [--limit N] [--topic slug]

Idempotent: existing scrap-<slug> files are left untouched.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from content.generators.base import compute_content_hash  # noqa: E402

CATALOG_PATH = _repo_root / "content" / "catalog" / "catalog.json"
PROBLEMS_DIR = _repo_root / "content" / "problems"
QUESTIONS_DIR = _repo_root / "content" / "questions"

KNOWN_DIFFICULTIES = {"Easy", "Medium", "Hard"}


def _slug(slug: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (slug or "").strip().lower()).strip("-")
    return slug or "untitled"


def _problem_id(slug: str, topic: str) -> str:
    prefix = re.sub(r"[^a-z]", "", topic.split("-")[0])[:3] or "gen"
    return f"scrap-{prefix}-{slug[:24]}"


def _clean_companies(entry: dict, limit: int = 6) -> list[str]:
    out = []
    for c in entry.get("companies", []):
        c = (c or "").strip()
        if not c or "Interview Coding" in c or "::" in c:
            continue
        if c not in out:
            out.append(c)
        if len(out) >= limit:
            break
    return out


def build_problem(entry: dict) -> dict:
    slug = _slug(entry["slug"])
    topic = entry["algo_topic"]
    difficulty = entry["difficulty"]
    title = entry["title"]
    companies = _clean_companies(entry)
    topics_raw = [t for t in entry.get("topics_raw", []) if t not in ("Dsa", "Coding", "Database")]
    pattern = entry.get("pattern") or (topics_raw[0] if topics_raw else topic)
    co = f" (asked at {', '.join(companies)})" if companies else ""
    return {
        "id": _problem_id(slug, topic),
        "slug": f"scrap-{slug}",
        "title": title,
        "topic": topic,
        "difficulty": difficulty,
        "pattern": pattern,
        "statement": (
            f"{title}{co}. "
            f"Topics: {', '.join(topics_raw) if topics_raw else topic}. "
            "Draft auto-imported from the scraped catalog metadata — "
            "statement, examples, and expected outputs MUST be authored and "
            "verified by running the reference solution before publishing."
        ),
        "examples": [
            {
                "input": "See statement",
                "output": "TBD — author during verification",
            }
        ],
        "constraints": ["TBD — author during verification"],
        "hints": [
            f"Think about which {pattern} pattern applies here.",
            "Work a tiny example by hand before coding.",
            "Verify your solution by running the reference implementation.",
        ],
        "solutions": [
            {
                "title": "Reference (TBD)",
                "complexity": "TBD",
                "language": "javascript",
                "code": "function solve(...args) {\n  throw new Error('Not implemented');\n}",
                "isReference": False,
            }
        ],
        "starterCode": {
            "javascript": "function solve(...args) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
            "python": "def solve(*args):\n    # Write your solution here\n    raise NotImplementedError\n",
        },
        "functionName": "solve",
        "timeLimitMs": 2000,
        "reviewStatus": "draft",
        "testCases": [
            {"label": "Placeholder 1 — replace", "input": [], "expected": None},
            {"label": "Placeholder 2 — replace", "input": [], "expected": None},
            {"label": "Placeholder 3 — replace", "input": [], "expected": None},
        ],
        "sequence": None,
        "prevSlug": None,
        "nextSlug": None,
        "source_url": entry.get("source_url", ""),
        "companies": companies,
    }


def build_question(entry: dict, rng_seed: str) -> dict:
    slug = _slug(entry["slug"])
    topic = entry["algo_topic"]
    title = entry["title"]
    difficulty = entry["difficulty"]
    topics_raw = [t for t in entry.get("topics_raw", []) if t not in ("Dsa", "Coding", "Database")]
    prompt = (
        f"Which topic best describes the classic problem '{title}' "
        f"({difficulty}; related: {', '.join(topics_raw[:3]) if topics_raw else topic})?"
    )
    import random

    rng = random.Random(rng_seed)
    candidates = [topic, "arrays-hashing", "graphs", "dynamic-programming", "trees", "sorting"]
    distractors = [c for c in dict.fromkeys(candidates) if c != topic][:3]
    while len(distractors) < 3:
        distractors.append(f"general-cs-{len(distractors)}")
    options = [topic] + distractors
    rng.shuffle(options)
    # Suffix the topic so near-dup titles in different topics can't collide.
    qid = f"scrap-{slug[:20]}-{topic[:4]}"
    return {
        "id": qid,
        "topic": topic,
        "subtopic": "scraped-catalog",
        "difficulty": difficulty,
        "qtype": "mcq",
        "prompt": prompt,
        "options": options,
        "correct_index": options.index(topic),
        "explanation": (
            f"'{title}' is catalogued under {topic} "
            f"(raw tags: {', '.join(topics_raw[:4]) if topics_raw else topic})."
        ),
        "source": "curated",
        "generator_key": "import_scraped.catalog-topic",
        "content_hash": compute_content_hash(prompt),
        "review_status": "draft",
    }


def import_scraped(limit: int | None = None, topic: str | None = None) -> dict:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    items = catalog if isinstance(catalog, list) else catalog.get("items", [])
    stats = {"problems": 0, "questions": 0, "skipped_unknown": 0, "skipped_topic": 0, "skipped_done": 0}
    done = 0
    for entry in items:
        if entry.get("already_in_algovista"):
            stats["skipped_done"] += 1
            continue
        if entry.get("difficulty") not in KNOWN_DIFFICULTIES:
            stats["skipped_unknown"] += 1
            continue
        if entry.get("algo_topic") is None:
            continue
        if topic and entry.get("algo_topic") != topic:
            stats["skipped_topic"] += 1
            continue
        slug = _slug(entry.get("slug", ""))
        p_path = PROBLEMS_DIR / f"scrap-{slug}.json"
        if not p_path.exists():
            p_path.write_text(json.dumps(build_problem(entry), indent=2), encoding="utf-8")
            stats["problems"] += 1
        q_dir = QUESTIONS_DIR / entry["algo_topic"]
        q_dir.mkdir(parents=True, exist_ok=True)
        q_data = build_question(entry, slug)
        q_path = q_dir / f"{q_data['id']}.json"
        if not q_path.exists():
            q_path.write_text(json.dumps(q_data, indent=2), encoding="utf-8")
            stats["questions"] += 1
        done += 1
        if limit is not None and done >= limit:
            break
    print(
        f"Imported {stats['problems']} draft problems + {stats['questions']} draft questions "
        f"(skipped: {stats['skipped_done']} already-in-app, "
        f"{stats['skipped_unknown']} unknown-difficulty, "
        f"{stats['skipped_topic']} off-topic)."
    )
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--topic", type=str, default=None)
    args = ap.parse_args()
    import hashlib  # noqa: F401 (kept for future salted ids)

    import_scraped(limit=args.limit, topic=args.topic)
