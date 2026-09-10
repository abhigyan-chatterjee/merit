"""Question bank verification validator that checks schemas, hashes, option validity, and QAF quality gates."""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from content.generators.qaf.spec import get_all_specs
from content.validators.schema import QuestionSchema

JOKE_OR_PLACEHOLDER_OPTIONS = {
    "none",
    "none of the above",
    "all of the above",
    "n/a",
    "null",
    "todo",
    "magic",
    "placeholder",
    "test",
}


def verify_all_questions(questions_dir: Path) -> int:
    """Verify all questions for schema correctness, hash uniqueness, and QAF quality gates."""
    question_files = sorted(questions_dir.glob("*/*.json"))
    if not question_files:
        print(f"No question files found in {questions_dir}")
        return 1

    print(f"Verifying {len(question_files)} questions across all topic directories...")
    errors: list[str] = []
    seen_hashes: dict[str, str] = {}  # hash -> file_path
    by_gk: dict[str, list[QuestionSchema]] = defaultdict(list)
    verified_questions: list[QuestionSchema] = []

    for q_path in question_files:
        try:
            with open(q_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            q = QuestionSchema(**data)
        except (json.JSONDecodeError, TypeError, ValueError) as err:
            errors.append(f"{q_path.relative_to(questions_dir)}: Schema error: {err}")
            continue

        # Gate 6: Content hash uniqueness bank-wide
        if q.content_hash in seen_hashes:
            orig = seen_hashes[q.content_hash]
            errors.append(f"{q_path.name}: Duplicate content hash with {orig}")
        else:
            seen_hashes[q.content_hash] = str(q_path.relative_to(questions_dir))

        # Check correct_index points to valid option
        if q.correct_index < 0 or q.correct_index >= len(q.options):
            errors.append(f"{q_path.name}: correct_index {q.correct_index} out of range (0..{len(q.options)-1})")

        # Check distinct non-empty options
        cleaned_options = [opt.strip() for opt in q.options if opt.strip()]
        if len(cleaned_options) != 4 or len(set(cleaned_options)) != 4:
            errors.append(f"{q_path.name}: Options must have 4 non-empty distinct choices. Got: {q.options}")

        # Check non-empty explanation
        if not q.explanation or len(q.explanation.strip()) < 5:
            errors.append(f"{q_path.name}: Explanation too short or empty.")

        if q.review_status == "verified":
            verified_questions.append(q)
            if q.generator_key:
                by_gk[q.generator_key].append(q)

    # --- Gate 2 (Bank-wide): Option-index spread histogram ---
    print("\n" + "=" * 70)
    print(" BANK-WIDE CORRECT OPTION INDEX HISTOGRAM")
    print("=" * 70)
    index_counts = Counter(q.correct_index for q in verified_questions)
    total_verified = len(verified_questions)
    labels = ["A (index 0)", "B (index 1)", "C (index 2)", "D (index 3)"]
    for idx, label in enumerate(labels):
        cnt = index_counts[idx]
        pct = (cnt / total_verified * 100) if total_verified > 0 else 0
        print(f"  {label:<15}: {cnt:>4} questions ({pct:5.1f}%)")
    print("-" * 70)
    print(f"  Total Verified Questions: {total_verified}")
    print("=" * 70)

    # Check for excessive bank-wide skew
    if total_verified > 50:
        for idx in range(4):
            pct = index_counts[idx] / total_verified
            if pct < 0.10 or pct > 0.45:
                errors.append(
                    f"Bank-wide correct_index distribution skewed: option {labels[idx]} has {pct*100:.1f}% "
                    f"(expected roughly uniform 15% - 40%)"
                )

    # --- QAF Specific Quality Gates ---
    qaf_specs = {s.key: s for s in get_all_specs()}
    print("\n" + "=" * 80)
    print(" QAF DESIGN QUALITY GATES REPORT")
    print("=" * 80)
    hdr = f"{'Design Key':<38} | {'Instances':<9} | {'Distinct Ans':<12} | {'Indices':<10} | {'Status'}"
    print(hdr)
    print("-" * len(hdr))

    for gk in sorted(qaf_specs.keys()):
        instances = by_gk.get(gk, [])
        if not instances:
            errors.append(f"QAF Design '{gk}' has 0 verified instances in questions directory.")
            print(f"{gk:<38} | {0:<9} | {0:<12} | {'None':<10} | FAILED (no instances)")
            continue

        design_errors: list[str] = []

        # 1. Answer variance: across a design's instances, answer must take at least 3 distinct values
        answers = {str(q.options[q.correct_index]).strip() for q in instances}
        min_required_answers = min(3, len(instances))
        if len(answers) < min_required_answers:
            err = (
                f"Design '{gk}' failed Quality Gate 1 (Answer Variance): "
                f"expected at least {min_required_answers} distinct answers across {len(instances)} instances, "
                f"got {len(answers)} ({sorted(answers)})"
            )
            design_errors.append(err)
            errors.append(err)

        # 2. Option-index spread (per design): no design may have every instance with same correct_index
        indices = {q.correct_index for q in instances}
        if len(instances) > 1 and len(indices) == 1:
            err = (
                f"Design '{gk}' failed Quality Gate 2 (Option-Index Spread): "
                f"all {len(instances)} instances have the identical correct_index ({next(iter(indices))})"
            )
            design_errors.append(err)
            errors.append(err)

        # 3. Distractor sanity: non-empty, distinct, not trivially distinguishable, no joke options
        for q in instances:
            ans_str = str(q.options[q.correct_index]).strip()
            distractors = [str(opt).strip() for i, opt in enumerate(q.options) if i != q.correct_index]
            for d in distractors:
                if not d:
                    err = f"Design '{gk}' ({q.id}) failed Quality Gate 3 (Distractor Sanity): empty distractor"
                    design_errors.append(err)
                    errors.append(err)
                if d.lower() == ans_str.lower():
                    err = f"Design '{gk}' ({q.id}) failed Quality Gate 3 (Distractor Sanity): distractor matches answer '{d}'"
                    design_errors.append(err)
                    errors.append(err)
                if d.lower() in JOKE_OR_PLACEHOLDER_OPTIONS:
                    err = f"Design '{gk}' ({q.id}) failed Quality Gate 3 (Distractor Sanity): placeholder distractor '{d}'"
                    design_errors.append(err)
                    errors.append(err)

            # Check numeric distractors outlier magnitude if answer is integer/float
            try:
                ans_num = float(ans_str)
                for d in distractors:
                    try:
                        d_num = float(d)
                        threshold = max(1000.0, 100.0 * abs(ans_num) + 20.0)
                        if abs(d_num - ans_num) > threshold:
                            err = (
                                f"Design '{gk}' ({q.id}) failed Quality Gate 3 (Distractor Sanity): "
                                f"numeric outlier distractor '{d}' vs answer '{ans_str}'"
                            )
                            design_errors.append(err)
                            errors.append(err)
                    except ValueError:
                        pass
            except ValueError:
                pass

        # 4. Prompt variance: rendered prompt must differ across instances
        prompts = [q.prompt.strip() for q in instances]
        if len(prompts) != len(set(prompts)):
            err = f"Design '{gk}' failed Quality Gate 4 (Prompt Variance): duplicate prompt detected across instances"
            design_errors.append(err)
            errors.append(err)

        # 5. Answer in explanation: explanation must reference computed answer
        for q in instances:
            ans_str = str(q.options[q.correct_index]).strip()
            exp_str = q.explanation.strip()
            if ans_str.lower() not in exp_str.lower():
                err = (
                    f"Design '{gk}' ({q.id}) failed Quality Gate 5 (Answer in Explanation): "
                    f"answer '{ans_str}' not found in explanation: '{exp_str}'"
                )
                design_errors.append(err)
                errors.append(err)

        status = "PASS" if not design_errors else f"FAIL ({len(design_errors)} errors)"
        indices_str = str(sorted(indices))
        print(f"{gk:<38} | {len(instances):<9} | {len(answers):<12} | {indices_str:<10} | {status}")

    print("=" * 80)

    if errors:
        print(f"\nFAILED: {len(errors)} question verification errors:")
        for err in errors[:30]:
            print(f"  - {err}")
        if len(errors) > 30:
            print(f"  ... and {len(errors) - 30} more errors.")
        return 1

    print(
        f"\nSUCCESS: All {len(question_files)} questions verified with valid schemas, unique hashes, "
        f"and all QAF quality gates fulfilled."
    )
    return 0


def main() -> int:
    q_dir = Path(__file__).resolve().parent.parent / "questions"
    return verify_all_questions(q_dir)


if __name__ == "__main__":
    sys.exit(main())
