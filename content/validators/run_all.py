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

from content.validators.coverage_report import generate_coverage_report
from content.validators.schema import LearningPathSchema
from content.validators.verify_problems import verify_all_problems
from content.validators.verify_questions import verify_all_questions


def _collect_problem_slugs(problems_dir: Path) -> set[str]:
    """Collect verified (non-scrap) problem slugs from content/problems/."""
    return {p.stem for p in problems_dir.glob("*.json") if not p.stem.startswith("scrap-")}


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


def main() -> int:
    print("=" * 65)
    print(" RUNNING ALGOVISTA CONTENT VERIFICATION SUITE")
    print("=" * 65)

    content_dir = Path(__file__).resolve().parent.parent
    problems_dir = content_dir / "problems"
    questions_dir = content_dir / "questions"
    paths_dir = content_dir / "paths"

    # 1. Verify Problems through real judge
    print("\n--- [1/4] VERIFYING PROBLEMS & REFERENCE SOLUTIONS ---")
    prob_code = asyncio.run(verify_all_problems(problems_dir))
    if prob_code != 0:
        print("\n❌ Problems verification FAILED.")
        return prob_code

    # 2. Verify Question Bank Schemas & Hashes
    print("\n--- [2/4] VERIFYING QUESTION BANK INTEGRITY ---")
    q_code = verify_all_questions(questions_dir)
    if q_code != 0:
        print("\n❌ Questions verification FAILED.")
        return q_code

    # 3. Coverage Matrix & Staged Target Report
    print("\n--- [3/4] CHECKING PLACEMENT CORPUS COVERAGE ---")
    cov_code = generate_coverage_report(questions_dir, target_designs=130)
    if cov_code != 0:
        print("\n❌ Coverage threshold NOT MET.")
        return cov_code

    # 4. Learning path ref integrity (dangling-ref gate)
    print("\n--- [4/4] VERIFYING PATH REF INTEGRITY ---")
    ref_code = verify_path_refs(paths_dir, problems_dir, _repo_root)
    if ref_code != 0:
        print("\n❌ Path ref integrity FAILED.")
        return ref_code

    print("\n" + "=" * 65)
    print(" ✅ ALL CONTENT VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
