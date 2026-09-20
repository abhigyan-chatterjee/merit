"""Coverage report validator that outputs topic x difficulty matrix and checks target thresholds."""

import json
import sys
from collections import defaultdict
from pathlib import Path

# Ensure repo root is on sys.path
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))


def generate_coverage_report(questions_dir: Path, target_designs: int = 130) -> int:
    question_files = list(questions_dir.glob("*/*.json"))
    if not question_files:
        print(f"Error: No question files found in {questions_dir}")
        return 1

    # Topic metrics: raw difficulties, generator keys, curated count
    matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    topic_gen_keys: dict[str, set[str]] = defaultdict(set)
    topic_curated: dict[str, int] = defaultdict(int)

    # Bank-wide metrics
    bank_gen_keys: set[str] = set()
    total_curated = 0
    total_verified = 0

    # Instance counts per generator_key: key -> (topic, count)
    gen_key_counts: dict[str, int] = defaultdict(int)
    gen_key_topic: dict[str, str] = {}

    for q_path in question_files:
        with open(q_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        topic = data.get("topic", "unknown")
        diff = data.get("difficulty", "Medium")
        status = data.get("review_status", "draft")
        gk = data.get("generator_key")
        src = data.get("source", "generated")

        if status == "verified":
            matrix[topic][diff] += 1
            matrix[topic]["Total"] += 1
            total_verified += 1

            if src == "curated" or not gk:
                topic_curated[topic] += 1
                total_curated += 1
            else:
                topic_gen_keys[topic].add(gk)
                bank_gen_keys.add(gk)
                gen_key_counts[gk] += 1
                gen_key_topic[gk] = topic

    print("\n" + "=" * 90)
    print(" ALGOVISTA VERIFIED QUESTION BANK COVERAGE & DESIGN MATRIX")
    print("=" * 90)
    header = (
        f"{'Topic':<20} | {'Easy':<6} | {'Med':<6} | {'Hard':<6} | {'RawTot':<7} | "
        f"{'GenKeys':<8} | {'Curated':<8} | {'Designs':<8}"
    )
    print(header)
    print("-" * len(header))

    diff_totals = {"Easy": 0, "Medium": 0, "Hard": 0}
    tot_gen_keys_sum = 0
    tot_designs_sum = 0

    for topic in sorted(matrix.keys()):
        easy = matrix[topic]["Easy"]
        med = matrix[topic]["Medium"]
        hard = matrix[topic]["Hard"]
        tot = matrix[topic]["Total"]
        gks = len(topic_gen_keys[topic])
        cur = topic_curated[topic]
        designs = gks + cur

        diff_totals["Easy"] += easy
        diff_totals["Medium"] += med
        diff_totals["Hard"] += hard
        tot_gen_keys_sum += gks
        tot_designs_sum += designs

        print(
            f"{topic:<20} | {easy:<6} | {med:<6} | {hard:<6} | {tot:<7} | "
            f"{gks:<8} | {cur:<8} | {designs:<8}"
        )

    print("-" * len(header))
    total_distinct_designs = len(bank_gen_keys) + total_curated
    summary_row = (
        f"{'TOTAL (bank-wide)':<20} | {diff_totals['Easy']:<6} | {diff_totals['Medium']:<6} | "
        f"{diff_totals['Hard']:<6} | {total_verified:<7} | {len(bank_gen_keys):<8} | "
        f"{total_curated:<8} | {total_distinct_designs:<8}"
    )
    print(summary_row)
    print("=" * 90)

    # Over-repetition section: generator keys with > 4 instances
    print("\n" + "=" * 90)
    print(" OVER-REPETITION REPORT (Generator keys exceeding cap of 4 instances)")
    print("=" * 90)
    over_repeated = [
        (gk, gen_key_topic[gk], count)
        for gk, count in gen_key_counts.items()
        if count > 4
    ]
    over_repeated.sort(key=lambda item: (-item[2], item[0]))

    if over_repeated:
        rep_header = f"{'Generator Key':<36} | {'Topic':<20} | {'Instances':<10} | {'Excess (>4)':<10}"
        print(rep_header)
        print("-" * len(rep_header))
        for gk, top, cnt in over_repeated:
            print(f"{gk:<36} | {top:<20} | {cnt:<10} | {f'+{cnt - 4}':<10}")
        print("\nFAILED: Generator keys exceed the hard cap of 4 verified instances.")
        return 1
    else:
        print("None: all generator keys are within the cap of 4 instances.")
    print("=" * 90)

    # Gating on distinct designs, not raw counts
    gap_250 = max(0, 250 - total_distinct_designs)
    gap_500 = max(0, 500 - total_distinct_designs)

    print("\n" + "=" * 90)
    print(" BANK INTEGRITY & STAGED TARGET REPORT")
    print("=" * 90)
    print(f"Raw Verified Count (inflated by repetition): {total_verified}")
    print(f"Distinct Generator Templates:                {len(bank_gen_keys)}")
    print(f"Curated Unique Questions:                    {total_curated}")
    print(f"Distinct Designs (Templates + Curated):      {total_distinct_designs}")
    print(f"Gate Threshold:                              distinct_designs >= {target_designs}")
    print(f"Gap to Staged Aspirational Target (250):     {gap_250} designs")
    print(f"Gap to Staged Aspirational Target (500):     {gap_500} designs")
    print("=" * 90)

    if total_distinct_designs < target_designs:
        print(
            f"\nFAILED: Bank has {total_distinct_designs} distinct designs, "
            f"which is below the gate threshold of {target_designs}."
        )
        return 1

    print(f"\nPASSED: Distinct designs gate fulfilled ({total_distinct_designs} >= {target_designs})!")
    return 0


def main() -> int:
    q_dir = Path(__file__).parent.parent / "questions"
    return generate_coverage_report(q_dir, target_designs=130)


if __name__ == "__main__":
    sys.exit(main())
