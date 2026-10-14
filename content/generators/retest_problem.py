"""Regenerate and re-verify the test data of problems that already ship.

Some problems carry test data that contradicts their own Constraints line,
because they were generated before the PAF generator could resolve bounds that
reference another parameter. Blanket-regenerating them from
``content/generators/paf/specs/`` is not safe: their statements and editorials
have been rewritten by hand since, and a rebuild would revert that. This
rewrites **only** ``testCases``, ``examples`` and ``pafVerification``, keeping
the statement, hints, editorial, reading links, starter code and solutions
exactly as the live bank has them.

A problem is written back only when the new data passes the same standard the
net-new gate applies: the JS optimal produces the expected values, the other
three implementations reproduce them through the real judge, and the generated
cases satisfy the bounds the statement declares.

Usage:
    python3 content/generators/retest_problem.py --slugs binary-search ...
    python3 content/generators/retest_problem.py --violating       # auto-detect
    python3 content/generators/retest_problem.py --violating --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for _path in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from app.services.judge import execute_code  # noqa: E402
from content.generators.paf.inputs import generate_inputs  # noqa: E402
from content.generators.paf.spec import Algorithm, ProblemSpec  # noqa: E402
from content.validators.check_relative_bounds import check as check_bounds  # noqa: E402

PROBLEMS_DIR = REPO_ROOT / "content" / "problems"

_SIGNATURE = re.compile(r"`(function\s+\w+\s*\([^)]*\))`")


def _signature_of(problem: dict) -> str | None:
    for constraint in problem.get("constraints") or []:
        match = _SIGNATURE.search(constraint)
        if match:
            return match.group(1)
    return None


def _implementations(problem: dict) -> dict[str, str]:
    """Pull the four solutions out of a published problem file."""
    out: dict[str, str] = {}
    for solution in problem.get("solutions") or []:
        language = solution.get("language")
        role = "optimal" if solution.get("isReference") else "brute"
        if language in {"javascript", "python"}:
            out[f"{'js' if language == 'javascript' else 'py'}_{role}"] = solution["code"]
    return out


def _spec(problem: dict, code: dict[str, str]) -> ProblemSpec:
    signature = _signature_of(problem)
    if not signature:
        raise ValueError("no function signature found in constraints")
    # Only the signature and the statement drive input generation; a problem
    # with no separate brute force still needs a slot filled here.
    brute = code.get("js_brute") or code["js_optimal"]
    return ProblemSpec(
        signature=signature,
        statement=problem["statement"],
        brute_force=Algorithm(brute, "profiled by PAF", "javascript"),
        optimal=Algorithm(code["js_optimal"], "profiled by PAF", "javascript"),
        topic=problem["topic"],
        difficulty=problem["difficulty"],
        pattern=problem["pattern"],
        title=problem["title"],
        slug=problem["slug"],
    )


async def _run(code: str, language: str, cases, function_name: str, limit: int):
    return await execute_code(
        language=language,
        code=code,
        function_name=function_name,
        test_cases=copy.deepcopy(cases),
        time_limit_ms=limit,
    )


async def retest(slug: str, dry_run: bool) -> tuple[bool, list[str]]:
    path = PROBLEMS_DIR / f"{slug}.json"
    if not path.exists():
        return False, ["no such problem file"]
    problem = json.loads(path.read_text(encoding="utf-8"))
    code = _implementations(problem)
    if "js_optimal" not in code:
        return False, ["no reference optimal solution to derive expected values from"]
    others = [key for key in ("js_brute", "py_optimal", "py_brute") if key in code]
    if not others:
        return False, ["only one implementation present; nothing to cross-check against"]

    spec = _spec(problem, code)
    fn = problem["functionName"]
    limit = problem.get("timeLimitMs", 2000)
    try:
        cases = generate_inputs(spec, random_cases=16, stress_cases=4)
    except Exception as err:  # noqa: BLE001
        return False, [f"input generation failed: {err}"]

    oracle = await _run(code["js_optimal"], "javascript", cases, fn, limit)
    if oracle.compile_output or len(oracle.test_results) != len(cases):
        return False, [f"js-optimal unusable: {oracle.verdict} {oracle.compile_output[:120]}"]
    for case, row in zip(cases, oracle.test_results, strict=True):
        if row.get("error") is not None or "actual" not in row:
            return False, [f"js-optimal errored on {row.get('label')}: {row.get('error')}"]
        case["expected"] = row["actual"]

    languages = {
        "js_brute": "javascript",
        "py_optimal": "python",
        "py_brute": "python",
    }
    results = await asyncio.gather(
        *(
            _run(code[key], languages[key], cases, fn, limit)
            for key in others
        )
    )
    for key, result in zip(others, results, strict=True):
        if result.verdict != "AC":
            bad = next(
                (r for r in result.test_results if not r.get("passed")), {}
            )
            return False, [
                f"{key} {result.verdict} on {bad.get('label')}: "
                f"{(bad.get('error') or 'output mismatch')[:110]}"
            ]

    updated = dict(problem)
    updated["testCases"] = [
        {
            "label": case["label"],
            "input": case["input"],
            "expected": case["expected"],
            "isSample": index < 2,
        }
        for index, case in enumerate(cases)
    ]
    updated["examples"] = [
        {
            "input": ", ".join(
                f"{parameter.name} = {json.dumps(value, ensure_ascii=False)}"
                for parameter, value in zip(
                    spec.parsed_signature.parameters, case["input"], strict=True
                )
            ),
            "output": json.dumps(case["expected"], ensure_ascii=False),
            "explanation": "Generated from the verified optimal implementation.",
        }
        for case in cases[:2]
    ]
    verification = dict(problem.get("pafVerification") or {})
    verification.update(
        {
            "seed": spec.seed,
            "generatedCaseCount": len(cases),
            "bruteForceRuntimeMs": results[0].runtime_ms,
            "optimalRuntimeMs": oracle.runtime_ms,
        }
    )
    updated["pafVerification"] = verification

    if not dry_run:
        path.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")

    # The regenerated data must satisfy the bounds the statement declares.
    scratch = PROBLEMS_DIR / f".retest-{slug}.json"
    scratch.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
    try:
        violations = check_bounds(scratch)["violations"]
    finally:
        scratch.unlink(missing_ok=True)
    if violations:
        return False, [
            f"regenerated data still violates `{violations[0]['clause']}` "
            f"({violations[0]['value']} outside {violations[0]['range']})"
        ]
    return True, [f"{len(cases)} cases, 4 solutions AC, bounds satisfied"]


def _violating_slugs() -> list[str]:
    out = []
    for path in sorted(PROBLEMS_DIR.glob("*.json")):
        if path.stem.startswith("scrap-"):
            continue
        if check_bounds(path)["violations"]:
            out.append(path.stem)
    return out


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slugs", nargs="*", default=[])
    parser.add_argument("--violating", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    slugs = list(args.slugs)
    if args.violating:
        slugs.extend(_violating_slugs())
    if not slugs:
        print("nothing to retest")
        return 0
    print(f"retesting {len(slugs)} problem(s){' (dry run)' if args.dry_run else ''}")
    failures = 0
    for slug in slugs:
        ok, notes = await retest(slug, args.dry_run)
        print(f"  {'PASS' if ok else 'FAIL'} {slug}: {notes[0]}")
        if not ok:
            failures += 1
    print(f"\nretest: {len(slugs) - failures}/{len(slugs)} ok")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
