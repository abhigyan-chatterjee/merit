"""Problem verification validator that runs all reference solutions through the real judge."""

import asyncio
import json
import sys
from pathlib import Path

# Add apps/api to sys.path so app.services.judge can be imported
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "apps" / "api"))
sys.path.insert(0, str(repo_root))

from app.services.judge import execute_code
from content.validators.schema import ProblemSchema

EDITORIAL_KEYS = ("approach", "why_optimal", "pitfalls")


def check_paf_gates(data: dict, name: str) -> list[str]:
    """Enforce editorial/reading_links/hints gates on PAF-authored problems.

    Problems carrying a ``pafVerification`` key are PAF-authored (new) and must
    carry a 3-key editorial, 1-3 https reading links, and >=3 distinct hints.
    Legacy problems without that key are grandfathered: they pass with a
    printed warning only. PAF emissions predating the editorial schema carry
    ``pafVerification`` but neither ``editorial`` nor ``reading_links`` keys;
    those are grandfathered too so the existing bank stays green, while every
    problem emitted by the current engine always carries both keys and is gated.
    """
    if "pafVerification" not in data:
        slug = data.get("slug", "")
        status = data.get("reviewStatus") or data.get("review_status") or "verified"
        if status == "draft" or slug.startswith("scrap-"):
            return []
        print(f"  ! {name}: legacy problem, editorial gates skipped")
        return []
    if "editorial" not in data and "reading_links" not in data:
        print(f"  ! {name}: legacy PAF emission, editorial gates skipped")
        return []
    errors: list[str] = []
    editorial = data.get("editorial")
    if not isinstance(editorial, dict):
        errors.append(f"{name}: PAF problem missing 'editorial' with keys {list(EDITORIAL_KEYS)}")
    else:
        for key in EDITORIAL_KEYS:
            value = editorial.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(
                    f"{name}: PAF problem 'editorial.{key}' must be a non-empty string"
                )
    links = data.get("reading_links")
    if not isinstance(links, list) or not 1 <= len(links) <= 3:
        errors.append(
            f"{name}: PAF problem 'reading_links' must have 1-3 entries"
        )
    elif any(not isinstance(link, str) or not link.startswith("https://") for link in links):
        errors.append(
            f"{name}: PAF problem 'reading_links' entries must be https URLs"
        )
    hints = data.get("hints")
    if not isinstance(hints, list):
        errors.append(f"{name}: PAF problem 'hints' must be a list with >=3 entries")
    else:
        cleaned = [hint.strip() for hint in hints if isinstance(hint, str) and hint.strip()]
        if len(cleaned) < 3 or len(set(cleaned)) < 3:
            errors.append(
                f"{name}: PAF problem 'hints' must have >=3 distinct non-empty entries"
            )
    return errors


async def verify_single_problem(path: Path) -> list[str]:
    errors: list[str] = []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    errors.extend(check_paf_gates(data, path.name))

    try:
        problem = ProblemSchema(**data)
    except Exception as err:
        return errors + [f"Schema validation error in {path.name}: {err}"]

    # Find reference solution
    ref_solutions = [s for s in problem.solutions if s.is_reference]
    if not ref_solutions:
        ref_solutions = [problem.solutions[-1]]

    test_case_dicts = [
        {
            "label": tc.label,
            "input": tc.input,
            "expected": tc.expected,
            "is_sample": tc.is_sample,
        }
        for tc in problem.test_cases
    ]

    for sol in ref_solutions:
        result = await execute_code(
            language=sol.language,
            code=sol.code,
            function_name=problem.function_name,
            test_cases=test_case_dicts,
            time_limit_ms=problem.time_limit_ms,
        )

        if result.verdict != "AC":
            errors.append(
                f"Problem {problem.slug} reference solution '{sol.title}' FAILED with verdict {result.verdict}. Output: {result.compile_output}"
            )
            for tr in result.test_results:
                if not tr.get("passed"):
                    errors.append(
                        f"  Test Case '{tr.get('label')}' Failed: Expected {tr.get('expected')}, Got {tr.get('actual')}. Error: {tr.get('error')}"
                    )

    return errors


async def verify_all_problems(problems_dir: Path) -> int:
    problem_files = sorted(problems_dir.glob("*.json"))
    if not problem_files:
        print(f"No problem files found in {problems_dir}")
        return 1

    # Drafts (e.g. scraped-catalog imports awaiting human verification) are
    # schema-checked but never judge-executed: their expected outputs are
    # placeholders by construction.
    verified_files: list[Path] = []
    skipped_drafts = 0
    for p_path in problem_files:
        try:
            with open(p_path, encoding="utf-8") as f:
                status = json.load(f).get("reviewStatus", "verified")
        except Exception:
            status = "verified"
        if status == "draft":
            skipped_drafts += 1
        else:
            verified_files.append(p_path)

    print(
        f"Verifying {len(verified_files)} problems with reference solutions through judge..."
        + (f" ({skipped_drafts} drafts skipped)" if skipped_drafts else "")
    )
    all_errors: list[str] = []

    for p_path in verified_files:
        errs = await verify_single_problem(p_path)
        if errs:
            all_errors.extend(errs)
            print(f"  ✘ {p_path.name}")
        else:
            print(f"  ✓ {p_path.name}")

    if all_errors:
        print(f"\nFAILED: {len(all_errors)} problem verification errors found:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print(f"\nSUCCESS: All {len(verified_files)} problems verified 100% AC against reference solutions.")
    return 0


def main() -> int:
    p_dir = Path(__file__).parent.parent / "problems"
    return asyncio.run(verify_all_problems(p_dir))


if __name__ == "__main__":
    sys.exit(main())
