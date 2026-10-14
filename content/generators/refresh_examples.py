"""Choose learner-facing examples from a problem's own verified test data.

The build takes `testCases[:2]` as the examples shown on the problem page, and
the first two generated cases are the edge-min and edge-max profiles. For a
problem bounded by `-10000 <= nums[i] <= 10000` that means the learner is shown
a one-element array and then a wall of twenty-four identical `10000`s — legally
correct, and about as unhelpful as an example can be.

This re-picks the two most readable cases from the cases the problem already
ships (the shortest random cases), re-derives their display strings, and
rewrites `examples` only. Nothing about the judge's data changes, so there is
nothing to re-verify.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBLEMS_DIR = REPO_ROOT / "content" / "problems"

_SIGNATURE = re.compile(r"`(function\s+\w+\s*\([^)]*\))`")

EXPLANATION = "Produced by the reference solution, verified against all four implementations."


def _parameters(problem: dict) -> list[str]:
    for constraint in problem.get("constraints") or []:
        match = _SIGNATURE.search(constraint)
        if match:
            inner = match.group(1).split("(", 1)[1].rsplit(")", 1)[0]
            return [part.strip().split(":")[0].strip() for part in inner.split(",") if part.strip()]
    return []


def _is_readable(case: dict) -> bool:
    return len(json.dumps(case.get("input"))) <= 220


def refresh(slug: str, dry_run: bool) -> tuple[bool, str]:
    path = PROBLEMS_DIR / f"{slug}.json"
    problem = json.loads(path.read_text(encoding="utf-8"))
    cases = problem.get("testCases") or []
    if len(cases) < 2:
        return False, "fewer than two cases"
    parameters = _parameters(problem)
    if not parameters:
        return False, "no parameters parsed from the signature"

    readable = [c for c in cases if _is_readable(c)]
    if len(readable) < 2:
        # Top the pool up with the remaining cases, smallest first, so there
        # are always two examples even when the suite is dominated by big ones.
        rest = sorted(
            (c for c in cases if c not in readable),
            key=lambda c: len(json.dumps(c["input"])),
        )
        readable = readable + rest
    ordered = sorted(readable, key=lambda c: len(json.dumps(c["input"])))
    chosen = ordered[:2]

    examples = [
        {
            "input": ", ".join(
                f"{name} = {json.dumps(value, ensure_ascii=False)}"
                for name, value in zip(parameters, case["input"], strict=True)
            ),
            "output": json.dumps(case.get("expected"), ensure_ascii=False),
            "explanation": EXPLANATION,
        }
        for case in chosen
    ]
    if examples == problem.get("examples"):
        return True, "already readable"
    if not dry_run:
        problem["examples"] = examples
        path.write_text(json.dumps(problem, indent=2) + "\n", encoding="utf-8")
    return True, f"{chosen[0]['label']} + {chosen[1]['label']}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slugs", nargs="*", default=[])
    parser.add_argument("--new", action="store_true", help="untracked problems only")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.slugs:
        slugs = args.slugs
    elif args.new:
        import subprocess

        out = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "content/problems"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        ).stdout.split()
        slugs = [Path(p).stem for p in out]
    else:
        slugs = [p.stem for p in sorted(PROBLEMS_DIR.glob("*.json")) if not p.stem.startswith("scrap-")]

    changed = 0
    for slug in slugs:
        ok, note = refresh(slug, args.dry_run)
        if ok and note != "already readable":
            changed += 1
            print(f"  {slug}: {note}")
        elif not ok:
            print(f"  SKIP {slug}: {note}")
    print(f"\nexamples refreshed for {changed} of {len(slugs)} problem(s)"
          f"{' (dry run)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
