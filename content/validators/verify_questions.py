"""Question bank verification validator that checks schemas, hashes, option validity, and uniqueness."""

import json
import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

from content.validators.schema import QuestionSchema, compute_content_hash


def verify_all_questions(questions_dir: Path) -> int:
    question_files = sorted(questions_dir.glob("*/*.json"))
    if not question_files:
        print(f"No question files found in {questions_dir}")
        return 1

    print(f"Verifying {len(question_files)} questions across all topic directories...")
    errors: list[str] = []
    seen_hashes: dict[str, str] = {}  # hash -> file_path

    for q_path in question_files:
        try:
            with open(q_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            q = QuestionSchema(**data)
        except Exception as err:
            errors.append(f"{q_path.relative_to(questions_dir)}: Schema error: {err}")
            continue

        # Check hash uniqueness
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

    if errors:
        print(f"\nFAILED: {len(errors)} question verification errors:")
        for err in errors[:30]:
            print(f"  - {err}")
        if len(errors) > 30:
            print(f"  ... and {len(errors) - 30} more errors.")
        return 1

    print(f"\nSUCCESS: All {len(question_files)} questions verified with valid schemas, unique hashes, and correct options.")
    return 0


def main() -> int:
    q_dir = Path(__file__).parent.parent / "questions"
    return verify_all_questions(q_dir)


if __name__ == "__main__":
    sys.exit(main())
