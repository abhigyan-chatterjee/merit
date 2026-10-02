"""Runs the gate over model-authored signatures and reports per-problem verdicts.

The gate is the mechanical half of the two-model review. It catches anything
that contradicts the test data outright. What it cannot catch is a signature
that is *technically* consistent with the data but wrong about intent — which
is what the independent validation pass is for.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from content.validators.signature_types import load_problems  # noqa: E402
from content.validators.verify_signatures import _check_one  # noqa: E402

BATCH_DIR = _REPO_ROOT / ".signature-batches"
PROBLEMS_DIR = _REPO_ROOT / "content" / "problems"


def main() -> int:
    authored: dict[str, dict] = {}
    for path in sorted(BATCH_DIR.glob("authored_*.json")):
        data = json.loads(path.read_text())
        for batch in data.get("batches", []):
            for entry in batch.get("problems", []):
                slug = entry.get("slug")
                if slug:
                    authored[slug] = entry

    problems = load_problems(PROBLEMS_DIR)

    print(f"authored: {len(authored)}   problems: {len(problems)}")

    missing = sorted(set(problems) - set(authored))
    if missing:
        print(f"\n!! not authored: {missing}")

    gate_errors: dict[str, list[str]] = {}
    for slug in sorted(set(problems) & set(authored)):
        errors: list[str] = []
        ambiguous: list[str] = []
        _check_one(slug, problems[slug], authored[slug], errors, ambiguous)
        if errors:
            gate_errors[slug] = errors

    notes = {s: e["note"] for s, e in authored.items() if e.get("note")}
    review_flagged = sorted(
        s for s, e in authored.items()
        if e.get("note")
    )

    out = {
        "authored": authored,
        "gate_errors": gate_errors,
        "needs_human_note": review_flagged,
    }
    (BATCH_DIR / "validation_input.json").write_text(json.dumps(out, indent=2))

    print(f"\ngate errors: {len(gate_errors)}")
    for slug, errs in list(gate_errors.items())[:20]:
        for e in errs:
            print(f"  - {slug}: {e}")
    print(f"author flags a note: {len(notes)} -> {review_flagged}")
    print(f"\nwrote {BATCH_DIR / 'validation_input.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
