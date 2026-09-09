"""Master generator runner that builds and saves the verified question corpus."""

import json
import sys
from pathlib import Path

# Ensure repo root is on sys.path so modules resolve cleanly without PYTHONPATH env var
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from content.generators.arrays_strings import generate_array_string_questions
from content.generators.bit_manipulation import generate_bit_manipulation_questions
from content.generators.cs_fundamentals import generate_cs_fundamentals_questions
from content.generators.ds_operations import generate_ds_questions
from content.generators.dynamic_programming import generate_dp_questions
from content.generators.graph_algorithms import generate_graph_questions
from content.generators.sorting_searching import generate_sorting_searching_questions
from content.generators.time_complexity import generate_time_complexity_questions
from content.generators.tree_traversals import generate_tree_questions


def generate_all(target_dir: Path) -> int:
    target_dir.mkdir(parents=True, exist_ok=True)
    # Clean up any previously generated question files to prevent stale ID duplicates
    for old_file in target_dir.glob("*/*.json"):
        if old_file.name.startswith("gen-"):
            old_file.unlink()

    all_questions = []

    print("Generating Time Complexity questions...")
    all_questions.extend(generate_time_complexity_questions(count=150, seed=101))

    print("Generating Tree Traversals questions...")
    all_questions.extend(generate_tree_questions(count=500, seed=102))

    print("Generating Data Structure Operations questions...")
    all_questions.extend(generate_ds_questions(count=160, seed=103))

    print("Generating Graph Algorithms questions...")
    all_questions.extend(generate_graph_questions(count=140, seed=104))

    print("Generating Dynamic Programming questions...")
    all_questions.extend(generate_dp_questions(count=140, seed=105))

    print("Generating Sorting & Searching questions...")
    all_questions.extend(generate_sorting_searching_questions(count=140, seed=106))

    print("Generating CS Fundamentals & Networks questions...")
    all_questions.extend(generate_cs_fundamentals_questions(count=140, seed=107))

    print("Generating Arrays & Strings questions...")
    all_questions.extend(generate_array_string_questions(count=150, seed=108))

    print("Generating Bit Manipulation questions...")
    all_questions.extend(generate_bit_manipulation_questions(count=100, seed=109))

    seen_hashes = set()
    written_count = 0

    for q in all_questions:
        if q.content_hash in seen_hashes:
            continue
        seen_hashes.add(q.content_hash)

        topic_dir = target_dir / q.topic
        topic_dir.mkdir(parents=True, exist_ok=True)

        q_path = topic_dir / f"{q.id}.json"
        with open(q_path, "w", encoding="utf-8") as f:
            json.dump(q.to_dict(), f, indent=2)
        written_count += 1

    print(f"Successfully generated and wrote {written_count} unique verified questions.")
    return written_count


if __name__ == "__main__":
    out_dir = Path(__file__).parent.parent / "questions"
    generate_all(out_dir)
