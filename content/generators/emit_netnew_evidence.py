"""Emit per-candidate evidence for the net-new problem authoring pipeline.

Evidence only — never a statement. The author model reasons from metadata
(title, topic, difficulty, pattern, companies, source) and writes original
prose, so no scraped statement text can leak in and nothing anchors on an
existing answer.

Reads the quarantined scrap drafts (content/problems/scrap-*.json) and drops
every one whose title already exists as a verified problem, leaving the
genuinely net-new candidates.

Usage:
    python3 content/generators/emit_netnew_evidence.py [--batch-size N]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from content.taxonomy import CATEGORIES  # noqa: E402

PROBLEMS_DIR = REPO_ROOT / "content" / "problems"
CATALOG_PATH = REPO_ROOT / "content" / "catalog" / "catalog.json"
OUT_DIR = REPO_ROOT / ".netnew"


def normalize(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", title.lower())


def load_catalog_index() -> dict[str, dict]:
    """Map normalized title -> catalog row (companies, raw topics, source)."""
    if not CATALOG_PATH.exists():
        return {}
    rows = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    index: dict[str, dict] = {}
    for row in rows:
        title = row.get("title")
        if title:
            index.setdefault(normalize(title), row)
    return index


def verified_titles() -> tuple[dict[str, str], set[str]]:
    titles: dict[str, str] = {}
    slugs: set[str] = set()
    for path in sorted(PROBLEMS_DIR.glob("*.json")):
        if path.name.startswith("scrap-"):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        titles[normalize(data["title"])] = data["slug"]
        slugs.add(data["slug"])
    return titles, slugs


def build_evidence() -> list[dict]:
    catalog = load_catalog_index()
    verified, verified_slugs = verified_titles()
    seen: set[str] = set()
    records: list[dict] = []

    for path in sorted(PROBLEMS_DIR.glob("scrap-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        title = data.get("title", "").strip()
        key = normalize(title)
        if not title or key in verified or key in seen:
            continue
        # Some verified problems were renamed for original-content reasons
        # (e.g. "Asteroid Collision" -> "Colliding Asteroids"), so a title
        # mismatch alone is not proof of novelty. A slug collision is: the
        # scrap slug is derived from the same source question.
        slug = path.stem.replace("scrap-", "")
        if slug in verified_slugs:
            continue
        seen.add(key)

        row = catalog.get(key, {})
        companies = data.get("companies") or row.get("companies") or []
        raw_topics = row.get("topics_raw") or []

        records.append(
            {
                "slug": slug,
                "title": title,
                "difficulty": data.get("difficulty", "Medium"),
                "scrap_topic": data.get("topic"),
                "pattern_hint": data.get("pattern"),
                "raw_topics": raw_topics,
                "companies": list(companies)[:10],
                "source_url": data.get("source_url", ""),
            }
        )

    # Stable difficulty-then-title order so batches are reproducible.
    rank = {"Easy": 0, "Medium": 1, "Hard": 2}
    records.sort(key=lambda r: (rank.get(r["difficulty"], 9), r["title"], r["slug"]))
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=5)
    args = parser.parse_args()

    records = build_evidence()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    topics = [
        {"slug": c["slug"], "title": c["title"], "description": c["description"]}
        for c in CATEGORIES
    ]
    (OUT_DIR / "candidates.json").write_text(
        json.dumps(records, indent=2) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "taxonomy.json").write_text(
        json.dumps(topics, indent=2) + "\n", encoding="utf-8"
    )

    batches = [
        records[i : i + args.batch_size]
        for i in range(0, len(records), args.batch_size)
    ]
    for idx, chunk in enumerate(batches, 1):
        payload = {"taxonomy": topics, "candidates": chunk}
        (OUT_DIR / f"batch_{idx:02d}.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )

    counts: dict[str, int] = {}
    for r in records:
        counts[r["difficulty"]] = counts.get(r["difficulty"], 0) + 1

    print(f"net-new candidates: {len(records)}")
    print("difficulty: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    print(f"batches: {len(batches)} of up to {args.batch_size} -> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
