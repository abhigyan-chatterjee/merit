"""Coverage report validator that outputs topic x difficulty matrix and checks target thresholds."""

import json
import sys
from collections import defaultdict
from pathlib import Path

# Ensure repo root is on sys.path
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))


def generate_coverage_report(questions_dir: Path, target_count: int = 750) -> int:
    question_files = list(questions_dir.glob("*/*.json"))
    if not question_files:
        print(f"Error: No question files found in {questions_dir}")
        return 1

    matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    total_verified = 0

    for q_path in question_files:
        with open(q_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        topic = data.get("topic", "unknown")
        diff = data.get("difficulty", "Medium")
        status = data.get("review_status", "draft")

        if status == "verified":
            matrix[topic][diff] += 1
            matrix[topic]["Total"] += 1
            total_verified += 1

    print("\n" + "=" * 65)
    print(" ALGOVISTA VERIFIED QUESTION BANK COVERAGE MATRIX (Phase 5 MVP)")
    print("=" * 65)
    header = f"{'Topic':<22} | {'Easy':<8} | {'Medium':<8} | {'Hard':<8} | {'Total':<8}"
    print(header)
    print("-" * len(header))

    diffs = ["Easy", "Medium", "Hard"]
    diff_totals = {"Easy": 0, "Medium": 0, "Hard": 0}

    for topic in sorted(matrix.keys()):
        easy = matrix[topic]["Easy"]
        med = matrix[topic]["Medium"]
        hard = matrix[topic]["Hard"]
        tot = matrix[topic]["Total"]
        diff_totals["Easy"] += easy
        diff_totals["Medium"] += med
        diff_totals["Hard"] += hard
        print(f"{topic:<22} | {easy:<8} | {med:<8} | {hard:<8} | {tot:<8}")

    print("-" * len(header))
    summary_row = f"{'TOTAL':<22} | {diff_totals['Easy']:<8} | {diff_totals['Medium']:<8} | {diff_totals['Hard']:<8} | {total_verified:<8}"
    print(summary_row)
    print("=" * 65)

    print(f"\nTarget Threshold: >= {target_count} verified questions.")
    print(f"Current Corpus:   {total_verified} verified questions.")

    if total_verified < target_count:
        print(f"\nFAILED: Corpus of {total_verified} questions is below staged target of {target_count}.")
        return 1

    print("\nPASSED: Staged coverage target fulfilled!")
    return 0


def main() -> int:
    q_dir = Path(__file__).parent.parent / "questions"
    return generate_coverage_report(q_dir, target_count=750)


if __name__ == "__main__":
    sys.exit(main())
