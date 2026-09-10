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


async def verify_single_problem(path: Path) -> list[str]:
    errors: list[str] = []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        problem = ProblemSchema(**data)
    except Exception as err:
        return [f"Schema validation error in {path.name}: {err}"]

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
