#!/usr/bin/env python3
"""Master verification suite runner for Algovista content (problems, questions, coverage, paths)."""

import asyncio
import json
import re
import sys
from pathlib import Path

from pydantic import ValidationError

# Ensure repo root and apps/api are in sys.path
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_repo_root / "apps" / "api") not in sys.path:
    sys.path.insert(0, str(_repo_root / "apps" / "api"))

from content.validators.check_relative_bounds import KNOWN_UNSUPPORTED
from content.validators.check_relative_bounds import check as check_declared_bounds
from content.validators.coverage_report import generate_coverage_report
from content.validators.schema import LearningPathSchema
from content.validators.verify_problems import verify_all_problems
from content.validators.verify_questions import verify_all_questions
from content.validators.verify_signatures import verify_signatures


def _collect_problem_slugs(problems_dir: Path) -> set[str]:
    """Collect verified (non-scrap) problem slugs from content/problems/."""
    return {p.stem for p in problems_dir.glob("*.json") if not p.stem.startswith("scrap-")}


def verify_problem_reading_links(problems_dir: Path) -> int:
    """Require every problem artifact, including drafts, to expose 1-3 HTTPS links."""
    errors: list[str] = []
    for path in sorted(problems_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: could not read JSON ({exc})")
            continue
        links = data.get("reading_links")
        if not isinstance(links, list) or not 1 <= len(links) <= 3:
            errors.append(f"{path.name}: reading_links must contain 1-3 entries")
        elif any(not isinstance(link, str) or not link.startswith("https://") for link in links):
            errors.append(f"{path.name}: reading_links entries must be HTTPS URLs")
    if errors:
        print("\nReading link errors:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"Reading links present for all {len(list(problems_dir.glob('*.json')))} problem files.")
    return 0


def _collect_visualizer_ids(repo_root: Path) -> set[str]:
    """Collect visualizer IDs from the frontend registry and backend catalog.

    Both apps/web/src/data/curriculum.ts (VISUALIZERS array) and
    apps/api/app/routers/content.py (VISUALIZERS_CATALOG, served at
    /api/v1/visualizers) define the canonical set of visualizer ids.
    A step ref_id is valid if it appears in either source.
    """
    ids: set[str] = set()
    curriculum_ts = repo_root / "apps" / "web" / "src" / "data" / "curriculum.ts"
    if curriculum_ts.exists():
        text = curriculum_ts.read_text(encoding="utf-8")
        ids.update(re.findall(r"id:\s*'([^']+)'", text))
    content_py = repo_root / "apps" / "api" / "app" / "routers" / "content.py"
    if content_py.exists():
        text = content_py.read_text(encoding="utf-8")
        ids.update(re.findall(r'"id":\s*"([^"]+)"', text))
    return ids


def verify_path_refs(paths_dir: Path, problems_dir: Path, repo_root: Path) -> int:
    """Verify every problem/visualizer step ref_id resolves to a real artifact.

    Problem-type steps must match a non-scrap-*.json slug in content/problems/.
    Visualizer-type steps must exist in the visualizer registry.
    Fails (returns 1) with every offending ref_id printed.
    """
    problem_slugs = _collect_problem_slugs(problems_dir)
    viz_ids = _collect_visualizer_ids(repo_root)

    print("\n" + "=" * 65)
    print(" LEARNING PATH REF INTEGRITY CHECK")
    print("=" * 65)
    print(f"Verified problem slugs: {len(problem_slugs)}")
    print(f"Visualizer IDs: {sorted(viz_ids)}")

    errors: list[str] = []
    for path_file in sorted(paths_dir.glob("*.json")):
        with open(path_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data.get("is_published"):
            continue
        try:
            LearningPathSchema(**data)
        except ValidationError as exc:
            errors.append(f"{path_file.stem}: path schema validation failed: {exc}")
            continue
        for step in data["steps"]:
            rt = step["step_type"]
            ref = step["ref_id"]
            if rt == "problem":
                if ref not in problem_slugs:
                    errors.append(
                        f"{path_file.stem} step {step['ordinal']}: "
                        f"dangling problem ref_id '{ref}' "
                        f"(no non-scrap file in content/problems/)"
                    )
            elif rt == "visualizer":
                if ref not in viz_ids:
                    errors.append(
                        f"{path_file.stem} step {step['ordinal']}: "
                        f"dangling visualizer ref_id '{ref}' "
                        f"(not in visualizer registry)"
                    )

    if errors:
        print("\nDangling ref_id(s) detected:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\nPASSED: All path ref_ids resolve to verified problems/visualizers.")
    return 0


def verify_declared_bounds(problems_dir: Path) -> int:
    """Fail when shipped test data contradicts a problem's own Constraints line.

    The test generator reads `<number> <= subject <= <number>` directly and
    resolves bounds that reference another parameter (`1 <= k <= num.length`)
    in a second pass. Where it cannot resolve a bound it falls back to
    -100..100, and the resulting cases still pass the judge if all four
    implementations merely tolerate them. The learner who writes a correct
    solution against the stated bounds is the one who fails. So every problem's
    generated data is checked against the bounds printed on its own page.
    """
    errors: list[str] = []
    known = {slug: reason for slug, reason in KNOWN_UNSUPPORTED.items()}
    seen_known: list[str] = []
    checked = 0
    for path in sorted(problems_dir.glob("*.json")):
        if path.stem.startswith("scrap-"):
            continue
        checked += 1
        result = check_declared_bounds(path)
        if not result["violations"]:
            continue
        if result["slug"] in known:
            seen_known.append(result["slug"])
            continue
        for violation in result["violations"][:1]:
            errors.append(
                f"{result['slug']}: {violation['case']} has "
                f"`{violation['clause']}` = {violation['value']}, "
                f"outside the declared [{violation['range'][0]}, {violation['range'][1]}]"
            )
    if seen_known:
        print(
            f"\n{len(seen_known)} problem(s) rely on an input premise the generator "
            "cannot synthesise (tracked in KNOWN_UNSUPPORTED, not a pass):"
        )
        for slug in seen_known:
            print(f"  ! {slug}: {known[slug]}")
    if errors:
        print("\nTest data outside its declared bounds:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"Test data conforms to declared bounds for {checked - len(seen_known)} problems.")
    return 0


async def verify_prose_examples(problems_dir: Path) -> int:
    """Fail when a statement's own worked example disagrees with the code.

    The judge only ever sees `testCases`, so a statement that spells out an
    example in prose ("for `nums = [3, 1, 2]` ... which sum to `9`") is checked
    by nothing. One shipped: `max-area-of-island` claimed four cells for a
    three-cell island. This evaluates each fully-specified prose example with
    the problem's own reference solution and compares.
    """
    from content.validators.verify_statement_examples import check_problem

    mismatches: list[dict] = []
    checked = 0
    for path in sorted(problems_dir.glob("*.json")):
        if path.stem.startswith("scrap-"):
            continue
        checked += 1
        mismatches.extend(await check_problem(path))
    if mismatches:
        print("\nProse examples that disagree with the reference solution:")
        for item in mismatches:
            print(
                f"  - {item['slug']}: prose says {item['claimed']!r}, "
                f"reference returns {item['actual']!r} for {item['input']}"
            )
        return 1
    print(f"Prose examples agree with the reference solution in {checked} problems.")
    return 0


def main() -> int:
    print("=" * 65)
    print(" RUNNING ALGOVISTA CONTENT VERIFICATION SUITE")
    print("=" * 65)

    content_dir = Path(__file__).resolve().parent.parent
    problems_dir = content_dir / "problems"
    questions_dir = content_dir / "questions"
    paths_dir = content_dir / "paths"

    # Reading links are metadata and must also be present on quarantined drafts.
    links_code = verify_problem_reading_links(problems_dir)
    if links_code != 0:
        print("\n❌ Problem reading-link verification FAILED.")
        return links_code

    # 1. Verify Problems through real judge
    print("\n--- [1/7] VERIFYING PROBLEMS & REFERENCE SOLUTIONS ---")
    prob_code = asyncio.run(verify_all_problems(problems_dir))
    if prob_code != 0:
        print("\n❌ Problems verification FAILED.")
        return prob_code

    # 2. Problem signatures (Java/C++ return + param types)
    #    Exit 2 means every signature matches the data but some int-vs-double
    #    decisions still need a human. That is reported, not silently passed.
    print("\n--- [2/7] VERIFYING PROBLEM SIGNATURES ---")
    sig_code = verify_signatures(content_dir / "signatures.json", problems_dir)
    if sig_code == 1:
        print("\n❌ Signature verification FAILED.")
        return sig_code

    # 3. Question Bank Schemas & Hashes
    print("\n--- [3/7] VERIFYING QUESTION BANK INTEGRITY ---")
    q_code = verify_all_questions(questions_dir)
    if q_code != 0:
        print("\n❌ Questions verification FAILED.")
        return q_code

    # 4. Coverage Matrix & Staged Target Report
    print("\n--- [4/7] CHECKING PLACEMENT CORPUS COVERAGE ---")
    cov_code = generate_coverage_report(questions_dir, target_designs=130)
    if cov_code != 0:
        print("\n❌ Coverage threshold NOT MET.")
        return cov_code

    # 5. Learning path ref integrity (dangling-ref gate)
    print("\n--- [5/7] VERIFYING PATH REF INTEGRITY ---")
    ref_code = verify_path_refs(paths_dir, problems_dir, _repo_root)
    if ref_code != 0:
        print("\n❌ Path ref integrity FAILED.")
        return ref_code

    # 6. Shipped test data against the bounds the page declares
    print("\n--- [6/7] VERIFYING TEST DATA AGAINST DECLARED BOUNDS ---")
    bounds_code = verify_declared_bounds(problems_dir)
    if bounds_code != 0:
        print("\n❌ Declared-bound conformance FAILED.")
        return bounds_code

    # 7. Worked examples written in prose
    print("\n--- [7/7] VERIFYING STATEMENT WORKED EXAMPLES ---")
    prose_code = asyncio.run(verify_prose_examples(problems_dir))
    if prose_code != 0:
        print("\n❌ Statement worked examples disagree with the code.")
        return prose_code

    if sig_code == 2:
        print(
            "\n⚠ Signatures are consistent with the test data, but int-vs-double "
            "decisions above are still unconfirmed."
        )

    print("\n" + "=" * 65)
    print(" ✅ ALL CONTENT VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
