"""Re-check the reviewer's verdicts against the data that is shipping now.

The review verdicts were produced before the generator was fixed, so a large
part of them complain about things that no longer exist: the leading `# Title`
heading is stripped at publish time, and the bound and premise defects they
found have been repaired. What remains is the genuinely editorial residue,
which no validator can settle.

This does not change any content. It sorts each MISMATCH into:

  stale-heading    the only complaint was the leading heading, which never
                   reaches a learner
  resolved-bounds  the complaint was about test data outside the declared
                   bounds, and the current data is conformant
  resolved-example the complaint was a wrong worked example, and the current
                   statement agrees with the reference solution
  open-editorial   a claim about prose or editorial accuracy that still needs a
                   human decision

Usage:
    python3 content/generators/triage_reviews.py [--json PATH]
"""

from __future__ import annotations

import argparse
import asyncio
import glob
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for _path in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from content.validators.check_relative_bounds import check as check_bounds  # noqa: E402
from content.validators.verify_statement_examples import check_problem  # noqa: E402

NETNEW = REPO_ROOT / ".netnew"
PROBLEMS = REPO_ROOT / "content" / "problems"

HEADING = re.compile(
    r"(opens with|leading|duplicat\w+|forbid\w*|redundant with|page already (shows|renders))"
    r"[^.]{0,80}?(#|H1|heading|title)",
    re.IGNORECASE,
)
# Reviewer boilerplate that says "and nothing else is wrong". Stripped before
# deciding whether a verdict has any substance beyond the heading.
REASSURANCE = re.compile(
    r"(no logic defects? found|no semantic defect|content otherwise sound|"
    r"code unaffected|implementations? (verified|agreed)[^.]*|logic itself is clean|"
    r"verified clean|cannot produce a wrong answer|no wrong-answer (risk|trigger)|"
    r"concern only|concern, no wrong|triggers? on every render|"
    r"does not (change|affect) any (output|answer)|no input changes any output|"
    r"same defect prior review rounds flagged[^.]*)",
    re.IGNORECASE,
)
BOUNDS = re.compile(
    r"(out of range|absolute|instead of relative|constraint line|"
    r"256 KB|output limit|exceeds|falls? back to -100)",
    re.IGNORECASE,
)
EXAMPLE = re.compile(
    r"(worked example|the example is (factually )?wrong|example is wrong|"
    r"answer is wrong|contradicts the code|statement says .* but)",
    re.IGNORECASE,
)
PREMISE = re.compile(
    r"(premise|must be sorted|sorted by snap|distinct|unique|rotated|non-decreasing)",
    re.IGNORECASE,
)
# Claims that a learner would notice and be misled by.
EDITORIAL = re.compile(
    r"(pitfall|editorial|why_optimal|approach section|misdescribes|"
    r"is wrong|are wrong|false|backwards|misleading|overclaims|undercounts?|"
    r"does not implement|contradict)",
    re.IGNORECASE,
)


def load_verdicts() -> dict[str, dict]:
    out: dict[str, dict] = {}
    # Only real batch outputs: `review_<digits>.json`. A looser glob also picks
    # up this script's own output file, which is a list of triage rows, not
    # verdicts, and would silently inflate every count.
    for path in sorted(NETNEW.glob("review_*.json")):
        if not re.fullmatch(r"review_\d+\.json", path.name):
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        # A batch is normally {"reviews": [...]}, but a model that answers with
        # a bare array is passed through, so both shapes have to be read.
        entries = payload.get("reviews", []) if isinstance(payload, dict) else payload
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict) and entry.get("slug"):
                out[entry["slug"]] = entry
    return out


async def classify(slug: str, entry: dict) -> dict:
    issue = entry.get("issue") or ""
    heading = bool(HEADING.search(issue))
    # What remains once the heading complaint and the reviewer's "and nothing
    # else is wrong" boilerplate are removed.
    residue = REASSURANCE.sub("", HEADING.sub("", issue))
    residue = re.sub(r"[\s\W]*(also|additionally|separately)[\s\W]*", " ", residue, flags=re.IGNORECASE)
    residue = residue.strip(" .,;:-()")

    result = {"slug": slug, "verdict": entry.get("verdict"), "category": None, "note": ""}
    path = PROBLEMS / f"{slug}.json"
    if not path.exists():
        result["category"] = "missing-file"
        return result
    if heading and len(residue) < 25:
        result["category"] = "stale-heading"
        result["note"] = "the publish step strips the leading heading"
        return result
    if not issue.strip():
        result["category"] = "no-detail"
        result["note"] = "verdict recorded without an issue description"
        return result
    if BOUNDS.search(issue):
        violations = check_bounds(path)["violations"]
        if not violations:
            result["category"] = "resolved-bounds"
            result["note"] = "current test data satisfies every declared bound"
            return result
        result["category"] = "open-bounds"
        result["note"] = f"{len(violations)} bound violation(s) remain"
        return result
    if EXAMPLE.search(issue):
        mismatches = await check_problem(path)
        if not mismatches:
            result["category"] = "resolved-example"
            result["note"] = "statement agrees with the reference solution now"
            return result
        result["category"] = "open-example"
        result["note"] = f"{len(mismatches)} prose example(s) still disagree"
        return result
    if PREMISE.search(residue) and len(residue) < 25:
        result["category"] = "stale-heading"
        result["note"] = "only the heading was reported, plus a premise note"
        return result
    if EDITORIAL.search(residue):
        result["category"] = "open-editorial"
        result["note"] = (residue or issue)[:180]
        return result
    result["category"] = "advisory"
    result["note"] = (residue or issue)[:180]
    return result


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="")
    args = parser.parse_args()

    verdicts = load_verdicts()
    print(f"review verdicts on record: {len(verdicts)}")
    rows = []
    for slug, entry in sorted(verdicts.items()):
        rows.append(await classify(slug, entry))

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["category"]] = counts.get(row["category"], 0) + 1
    print("\nby category:")
    for category, count in sorted(counts.items(), key=lambda item: -item[1]):
        print(f"  {count:4d}  {category}")

    for category in ("open-bounds", "open-example", "open-editorial", "missing-file"):
        items = [row for row in rows if row["category"] == category]
        if not items:
            continue
        print(f"\n{category}:")
        for row in items:
            print(f"  - {row['slug']}: {row['note']}")

    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
