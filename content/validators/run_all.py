#!/usr/bin/env python3
"""Master verification suite runner for Algovista content (problems, questions, coverage)."""

import asyncio
import sys
from pathlib import Path

# Ensure repo root and apps/api are in sys.path
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_repo_root / "apps" / "api") not in sys.path:
    sys.path.insert(0, str(_repo_root / "apps" / "api"))

from content.validators.coverage_report import generate_coverage_report
from content.validators.verify_problems import verify_all_problems
from content.validators.verify_questions import verify_all_questions


def main() -> int:
    print("=" * 65)
    print(" RUNNING ALGOVISTA CONTENT VERIFICATION SUITE")
    print("=" * 65)

    content_dir = Path(__file__).resolve().parent.parent
    problems_dir = content_dir / "problems"
    questions_dir = content_dir / "questions"

    # 1. Verify Problems through real judge
    print("\n--- [1/3] VERIFYING PROBLEMS & REFERENCE SOLUTIONS ---")
    prob_code = asyncio.run(verify_all_problems(problems_dir))
    if prob_code != 0:
        print("\n❌ Problems verification FAILED.")
        return prob_code

    # 2. Verify Question Bank Schemas & Hashes
    print("\n--- [2/3] VERIFYING QUESTION BANK INTEGRITY ---")
    q_code = verify_all_questions(questions_dir)
    if q_code != 0:
        print("\n❌ Questions verification FAILED.")
        return q_code

    # 3. Coverage Matrix & Staged Target Report
    print("\n--- [3/3] CHECKING PLACEMENT CORPUS COVERAGE ---")
    cov_code = generate_coverage_report(questions_dir, target_designs=130)
    if cov_code != 0:
        print("\n❌ Coverage threshold NOT MET.")
        return cov_code

    print("\n" + "=" * 65)
    print(" ✅ ALL CONTENT VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
