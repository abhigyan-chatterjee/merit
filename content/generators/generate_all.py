"""Master generator runner that builds and saves the verified question corpus."""

import json
import sys
from collections import defaultdict
from pathlib import Path

# Ensure repo root is on sys.path so modules resolve cleanly without PYTHONPATH env var
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from content.generators.aptitude import generate_aptitude_questions
from content.generators.arrays_strings import generate_array_string_questions
from content.generators.backtracking import generate_backtracking_questions
from content.generators.bit_manipulation import generate_bit_manipulation_questions
from content.generators.core_cs import generate_core_questions
from content.generators.cs_fundamentals import generate_cs_fundamentals_questions
from content.generators.ds_operations import generate_ds_questions
from content.generators.dynamic_programming import generate_dp_questions
from content.generators.graph_algorithms import generate_graph_questions
from content.generators.greedy import generate_greedy_questions
from content.generators.intervals import generate_intervals_questions
from content.generators.math_matrices import generate_math_matrices_questions
from content.generators.sorting_searching import generate_sorting_searching_questions
from content.generators.time_complexity import generate_time_complexity_questions
from content.generators.tree_traversals import generate_tree_questions
from content.generators.trie import generate_trie_questions
from content.generators.two_pointers import generate_two_pointers_questions


def generate_all(target_dir: Path, instance_cap: int = 4) -> int:
    target_dir.mkdir(parents=True, exist_ok=True)

    all_questions = []

    print("Generating Time Complexity questions...")
    all_questions.extend(generate_time_complexity_questions(count=150, seed=101))

    print("Generating Tree Traversals questions...")
    all_questions.extend(generate_tree_questions(count=500, seed=102))

    print("Generating Data Structure Operations questions...")
    all_questions.extend(generate_ds_questions(count=300, seed=103))

    print("Generating Graph Algorithms questions...")
    all_questions.extend(generate_graph_questions(count=140, seed=104))

    print("Generating Dynamic Programming questions...")
    all_questions.extend(generate_dp_questions(count=140, seed=105))

    print("Generating Sorting & Searching questions...")
    all_questions.extend(generate_sorting_searching_questions(count=300, seed=106))

    print("Generating CS Fundamentals & Networks questions...")
    all_questions.extend(generate_cs_fundamentals_questions(count=140, seed=107))

    print("Generating Arrays & Strings questions...")
    all_questions.extend(generate_array_string_questions(count=300, seed=108))

    print("Generating Bit Manipulation questions...")
    all_questions.extend(generate_bit_manipulation_questions(count=100, seed=109))

    print("Generating Aptitude questions...")
    all_questions.extend(generate_aptitude_questions(count=100, seed=201))

    print("Generating Core CS questions...")
    all_questions.extend(generate_core_questions(count=100, seed=202))

    print("Generating Two Pointers questions...")
    all_questions.extend(generate_two_pointers_questions(count=12, seed=301))

    print("Generating Trie questions...")
    all_questions.extend(generate_trie_questions(count=12, seed=302))

    print("Generating Intervals questions...")
    all_questions.extend(generate_intervals_questions(count=12, seed=303))

    print("Generating Greedy questions...")
    all_questions.extend(generate_greedy_questions(count=12, seed=304))

    print("Generating Backtracking questions...")
    all_questions.extend(generate_backtracking_questions(count=12, seed=305))

    print("Generating Math & Matrices questions...")
    all_questions.extend(generate_math_matrices_questions(count=12, seed=306))

    # Group by generator_key and enforce instance_cap per design sorted by content_hash
    by_gk = defaultdict(list)
    seen_hashes = set()
    for q in all_questions:
        if q.content_hash in seen_hashes:
            continue
        seen_hashes.add(q.content_hash)
        by_gk[q.generator_key].append(q)

    capped_questions = []
    for gk in sorted(by_gk.keys()):
        items = by_gk[gk]
        items.sort(key=lambda q: q.content_hash)
        capped_questions.extend(items[:instance_cap])

    written_count = 0
    for q in capped_questions:
        topic_dir = target_dir / q.topic
        topic_dir.mkdir(parents=True, exist_ok=True)

        q_path = topic_dir / f"{q.id}.json"
        with open(q_path, "w", encoding="utf-8") as f:
            json.dump(q.to_dict(), f, indent=2)
        written_count += 1

    print(
        f"Successfully generated and wrote {written_count} verified questions "
        f"across {len(by_gk)} distinct generator templates (cap={instance_cap})."
    )
    return written_count


if __name__ == "__main__":
    out_dir = Path(__file__).parent.parent / "questions"
    generate_all(out_dir)
