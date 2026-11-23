"""Master generator runner that builds and saves the verified question corpus."""

import argparse
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
from content.generators.screening_sql_verbal import generate_sql_questions, generate_verbal_questions
from content.generators.sorting_searching import generate_sorting_searching_questions
from content.generators.time_complexity import generate_time_complexity_questions
from content.generators.tree_traversals import generate_tree_questions
from content.generators.trie import generate_trie_questions
from content.generators.two_pointers import generate_two_pointers_questions

SCREENING_TOPICS = ("aptitude", "core-cs", "sql", "verbal")


def _clear_generated(topic_dir: Path) -> None:
    """Remove only generated JSON files in a screening topic dir; keep curated items."""
    if not topic_dir.is_dir():
        return
    for path in topic_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("source") == "generated":
            path.unlink()


def _write_capped(target_dir: Path, questions: list, instance_cap: int, clear_topics=()) -> int:
    by_gk = defaultdict(list)
    seen_hashes = set()
    for q in questions:
        if q.content_hash in seen_hashes:
            continue
        seen_hashes.add(q.content_hash)
        by_gk[q.generator_key].append(q)

    for topic in clear_topics:
        _clear_generated(target_dir / topic)

    written = 0
    for gk in sorted(by_gk.keys()):
        items = sorted(by_gk[gk], key=lambda q: q.content_hash)
        for q in items[:instance_cap]:
            topic_dir = target_dir / q.topic
            topic_dir.mkdir(parents=True, exist_ok=True)
            (topic_dir / f"{q.id}.json").write_text(
                json.dumps(q.to_dict(), indent=2), encoding="utf-8"
            )
            written += 1
    return written


def generate_screening(target_dir: Path, instance_cap: int = 4) -> int:
    """Regenerate only the four screening topics, replacing their stale generated files."""
    target_dir.mkdir(parents=True, exist_ok=True)
    questions = []
    questions.extend(generate_aptitude_questions(count=96, seed=201))
    questions.extend(generate_core_questions(count=104, seed=202))
    questions.extend(generate_sql_questions(count=40, seed=401))
    questions.extend(generate_verbal_questions(count=40, seed=402))
    written = _write_capped(target_dir, questions, instance_cap, clear_topics=SCREENING_TOPICS)
    print(f"Wrote {written} screening questions across topics {', '.join(SCREENING_TOPICS)}.")
    return written


def generate_dsa(target_dir: Path, instance_cap: int = 4) -> int:
    """Regenerate the DSA topic corpus without touching the screening directories."""
    target_dir.mkdir(parents=True, exist_ok=True)
    questions = []
    questions.extend(generate_time_complexity_questions(count=150, seed=101))
    questions.extend(generate_tree_questions(count=500, seed=102))
    questions.extend(generate_ds_questions(count=300, seed=103))
    questions.extend(generate_graph_questions(count=140, seed=104))
    questions.extend(generate_dp_questions(count=140, seed=105))
    questions.extend(generate_sorting_searching_questions(count=300, seed=106))
    questions.extend(generate_cs_fundamentals_questions(count=140, seed=107))
    questions.extend(generate_array_string_questions(count=300))
    questions.extend(generate_bit_manipulation_questions(count=100, seed=109))
    questions.extend(generate_two_pointers_questions(count=12, seed=301))
    questions.extend(generate_trie_questions(count=12, seed=302))
    questions.extend(generate_intervals_questions(count=12, seed=303))
    questions.extend(generate_greedy_questions(count=12, seed=304))
    questions.extend(generate_backtracking_questions(count=12, seed=305))
    questions.extend(generate_math_matrices_questions(count=12, seed=306))
    written = _write_capped(target_dir, questions, instance_cap)
    print(f"Wrote {written} DSA questions.")
    return written


def generate_all(target_dir: Path, instance_cap: int = 4) -> int:
    """Full corpus build: DSA topics plus the four screening topics."""
    dsa_written = generate_dsa(target_dir, instance_cap)
    screening_written = generate_screening(target_dir, instance_cap)
    total = dsa_written + screening_written
    print(f"Successfully generated and wrote {total} verified questions (cap={instance_cap}).")
    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--screening-only",
        action="store_true",
        help="Regenerate only aptitude, core-cs, sql and verbal question files.",
    )
    args = parser.parse_args()
    out_dir = Path(__file__).parent.parent / "questions"
    if args.screening_only:
        generate_screening(out_dir)
    else:
        generate_all(out_dir)
