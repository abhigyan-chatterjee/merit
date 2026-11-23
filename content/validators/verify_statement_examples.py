"""Verify the worked examples a statement writes out in prose.

A statement often spells out an example: `for nums = [3, 1, 2] ... which sum to
9`, `when haystack is "butterfly" and needle is "fly", the answer is 6`. Those
sentences are written by a model, are read by every learner, and nothing else in
the pipeline checks them: the judge only ever sees `testCases`, so a wrong
worked example ships silently. One did ship (`max-area-of-island` claimed four
cells for a three-cell island).

This finds the sentences that name every parameter with a literal value and
state a numeric or JSON answer, evaluates the problem's own reference solution
on that input, and reports where the prose disagrees with the code.

Precision over recall: it only reports a case when every parameter has a
parseable literal and the claimed answer is a clean literal, so a sentence it
cannot fully parse is skipped rather than guessed at.

Usage:
    python3 content/validators/verify_statement_examples.py            # all
    python3 content/validators/verify_statement_examples.py --new      # untracked
    python3 content/validators/verify_statement_examples.py --slugs a b
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBLEMS_DIR = REPO_ROOT / "content" / "problems"
for _path in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from app.services.judge import execute_code  # noqa: E402

_SIGNATURE = re.compile(r"`(function\s+\w+\s*\([^)]*\))`")
_CLAIM = re.compile(
    r"(?:answer is|answer:|output is|output:|returns?|sum to|equals|gives)\s*"
    r"`?\s*([^`\s,]+)",
    re.IGNORECASE,
)
_SENTENCE_SPLIT = re.compile(r"(?<=[.:])\s+(?=[A-Z0-9`\"\[])")


def _literal_after(sentence: str, name: str):
    """The literal that follows a parameter name, or None.

    Prefers a backticked span, which is how prose writes anything with nested
    brackets (`[[1, 0, 0], [1, 1, 0]]`); falls back to a bare token.
    """
    lead = (
        rf"(?<![A-Za-z_])(?:the\s+)?`?{re.escape(name)}`?\s*"
        rf"(?:=|is|are|holds|contains|:)?\s*"
    )
    match = re.search(lead + r"`([^`]+)`", sentence)
    if match:
        return match.group(1).strip()
    match = re.search(lead + r"(\[[^`]*?\]|-?\d+(?:\.\d+)?|\"[^\"]*\"|true|false)", sentence)
    if match:
        return match.group(1).strip()
    return None


def _parameters(problem: dict) -> list[str]:
    for constraint in problem.get("constraints") or []:
        match = _SIGNATURE.search(constraint)
        if match:
            inner = match.group(1).split("(", 1)[1].rsplit(")", 1)[0]
            return [
                part.strip().split(":")[0].strip()
                for part in inner.split(",")
                if part.strip()
            ]
    return []


def _try_json(raw: str):
    raw = raw.strip()
    if raw.startswith(('"', "[", "{")):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    if raw in {"true", "false"}:
        return raw == "true"
    try:
        return int(raw)
    except ValueError:
        try:
            return float(raw)
        except ValueError:
            return None


def _candidate_examples(problem: dict, parameters: list[str]) -> list[dict]:
    """Sentences that pin every parameter to a literal and state an answer."""
    found: list[dict] = []
    for sentence in _SENTENCE_SPLIT.split(problem.get("statement") or ""):
        if len(sentence) > 400:
            continue
        values: dict[str, object] = {}
        for name in parameters:
            raw = _literal_after(sentence, name)
            if raw is None:
                break
            parsed = _try_json(raw)
            if parsed is None:
                break
            values[name] = parsed
        if len(values) != len(parameters) or not parameters:
            continue
        claimed = _CLAIM.search(sentence)
        if not claimed:
            continue
        claim_text = claimed.group(1).strip().strip("`").rstrip(".")
        claim = _try_json(claim_text)
        if claim is None:
            continue
        # The claim must come after the inputs, otherwise it belongs to another
        # clause of the same sentence.
        if claimed.start() < sentence.rfind(str(values[parameters[-1]])):
            continue
        found.append(
            {
                "sentence": sentence.strip(),
                "input": [values[name] for name in parameters],
                "claimed": claim,
            }
        )
    return found


async def _evaluate(problem: dict, values: list) -> object:
    reference = next(
        (s for s in problem.get("solutions") or [] if s.get("isReference")), None
    )
    if reference is None:
        return "<no reference solution>"
    language = reference["language"]
    result = await execute_code(
        language=language,
        code=reference["code"],
        function_name=problem["functionName"],
        test_cases=[{"label": "prose", "input": values, "expected": None}],
        time_limit_ms=problem.get("timeLimitMs", 2000),
    )
    row = result.test_results[0] if result.test_results else {}
    if row.get("error"):
        return f"<error: {row['error']}>"
    return row.get("actual")


def _compare(claimed, actual) -> bool:
    if isinstance(claimed, bool) or isinstance(actual, bool):
        return claimed is actual or str(claimed).lower() == str(actual).lower()
    if isinstance(claimed, (int, float)) and isinstance(actual, (int, float)):
        return abs(float(claimed) - float(actual)) < 1e-9
    return claimed == actual or json.dumps(claimed) == json.dumps(actual)


async def check_problem(path: Path) -> list[dict]:
    problem = json.loads(path.read_text(encoding="utf-8"))
    parameters = _parameters(problem)
    if not parameters:
        return []
    problems = []
    for candidate in _candidate_examples(problem, parameters):
        actual = await _evaluate(problem, candidate["input"])
        if isinstance(actual, str) and actual.startswith("<"):
            continue
        if not _compare(candidate["claimed"], actual):
            problems.append(
                {
                    "slug": problem["slug"],
                    "input": candidate["input"],
                    "claimed": candidate["claimed"],
                    "actual": actual,
                    "sentence": candidate["sentence"][:200],
                }
            )
    return problems


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slugs", nargs="*", default=[])
    parser.add_argument("--new", action="store_true")
    args = parser.parse_args()

    if args.slugs:
        paths = [PROBLEMS_DIR / f"{s}.json" for s in args.slugs]
    elif args.new:
        out = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "content/problems"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        ).stdout.split()
        paths = [REPO_ROOT / p for p in out]
    else:
        paths = [
            p for p in sorted(PROBLEMS_DIR.glob("*.json")) if not p.stem.startswith("scrap-")
        ]

    checked = 0
    mismatches: list[dict] = []
    for path in paths:
        if not path.exists():
            continue
        checked += 1
        mismatches.extend(await check_problem(path))

    for item in mismatches:
        print(
            f"MISMATCH {item['slug']}: prose claims {item['claimed']!r} for "
            f"{json.dumps(item['input'])[:90]} but the reference returns "
            f"{item['actual']!r}\n    {item['sentence']}"
        )
    print(f"\nchecked prose examples in {checked} problem(s); {len(mismatches)} disagreement(s)")
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
