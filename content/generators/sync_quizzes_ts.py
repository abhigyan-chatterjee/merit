"""Generate the guest quiz bundle from verified question-bank entries.

Usage:
    python3 content/generators/sync_quizzes_ts.py
"""

import json
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QUESTIONS_DIR = REPO_ROOT / "content" / "questions"
OUTPUT_TS = REPO_ROOT / "apps" / "web" / "src" / "data" / "quizzes.ts"

SEED = 20260920
QUESTION_COUNT = 10
TOPICS = [
    ("arrays-hashing", "Arrays & Hashing", "Indexing, frequency maps, and subarray bounds."),
    ("trees", "Trees & BST", "Traversals, binary search trees, and heap invariants."),
    ("graphs", "Graphs & Traversals", "BFS, DFS, Dijkstra, topological sort, and connectivity."),
    (
        "dynamic-programming",
        "Dynamic Programming",
        "Optimal substructure, memoization, and tabulation recurrence.",
    ),
    ("sorting", "Sorting & Searching", "Binary search invariants, in-place sorts, and comparison bounds."),
    (
        "data-structures",
        "Stacks, Queues & Heaps",
        "Amortized structures, circular queues, and priority queues.",
    ),
    ("bit-manipulation", "Bit Manipulation", "Bitwise masks, popcounts, and bit tricks."),
    ("cs-fundamentals", "CS Fundamentals", "Operating systems, memory management, networks, and DBMS."),
    ("mixed", "Mixed Mastery", "Adaptive placement assessment drawn across all verified items."),
]

SOURCE_TOPICS = {
    "arrays-hashing": "arrays-hashing",
    "trees": "trees",
    "graphs": "graphs",
    "dynamic-programming": "dynamic-programming",
    "sorting": "sorting",
    "data-structures": "data-structures",
    "bit-manipulation": "bit-manipulation",
    "cs-fundamentals": "core-cs",
}

DIFFICULTIES = ("Easy", "Medium", "Hard")


def load_questions() -> list[dict]:
    questions = []
    for path in sorted(QUESTIONS_DIR.glob("*/*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("review_status") != "verified":
            continue
        if data.get("qtype") != "mcq":
            continue
        questions.append(data)
    return questions


def pick_questions(pool: list[dict], topic: str) -> list[dict]:
    if len(pool) < QUESTION_COUNT:
        raise ValueError(f"{topic} has only {len(pool)} verified MCQs; need {QUESTION_COUNT}")

    rng = random.Random(f"{SEED}:{topic}")
    buckets = {difficulty: [] for difficulty in DIFFICULTIES}
    for question in pool:
        buckets.setdefault(question.get("difficulty"), []).append(question)
    for bucket in buckets.values():
        rng.shuffle(bucket)

    selected = []
    # Start with an Easy/Medium mix, then fill from any remaining difficulty.
    for difficulty in ("Easy", "Medium"):
        selected.extend(buckets[difficulty][:QUESTION_COUNT // 2])
    if len(selected) < QUESTION_COUNT:
        selected_ids = {question["id"] for question in selected}
        remaining = [
            question
            for difficulty in DIFFICULTIES
            for question in buckets[difficulty]
            if question["id"] not in selected_ids
        ]
        rng.shuffle(remaining)
        selected.extend(remaining[: QUESTION_COUNT - len(selected)])
    rng.shuffle(selected)
    return selected


def ts_string(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_question(question: dict, index: int) -> str:
    return "\n".join(
        [
            "    {",
            f"      id: {ts_string(question['id'])},",
            f"      question: {ts_string(question['prompt'])},",
            f"      options: {ts_string(question['options'])},",
            f"      correctIndex: {question['correct_index']},",
            f"      explanation: {ts_string(question['explanation'])},",
            "    },",
        ]
    )


def render(topic_questions: dict[str, list[dict]]) -> str:
    lines = [
        "export interface QuizQuestion {",
        "  id: string;",
        "  question: string;",
        "  options: string[];",
        "  correctIndex: number;",
        "  explanation: string;",
        "}",
        "",
        "export const QUIZZES: Record<string, QuizQuestion[]> = {",
    ]
    for topic_id, _, _ in TOPICS:
        lines.append(f"  {json.dumps(topic_id)}: [")
        for index, question in enumerate(topic_questions[topic_id]):
            lines.append(render_question(question, index))
        lines.append("  ],")
    lines.extend(
        [
            "};",
            "",
            "export interface QuizTopicMeta {",
            "  id: string;",
            "  title: string;",
            "  description: string;",
            "}",
            "",
            "export const QUIZ_TOPICS: QuizTopicMeta[] = [",
        ]
    )
    for topic_id, title, description in TOPICS:
        lines.append(
            f"  {{ id: {ts_string(topic_id)}, title: {ts_string(title)}, "
            f"description: {ts_string(description)} }},"
        )
    lines.extend(["];", ""])
    return "\n".join(lines)


def sync() -> None:
    all_questions = load_questions()
    by_source: dict[str, list[dict]] = {}
    for question in all_questions:
        by_source.setdefault(question["topic"], []).append(question)

    topic_questions = {}
    for topic_id, _, _ in TOPICS:
        if topic_id == "mixed":
            pool = [
                question
                for source_topic in SOURCE_TOPICS.values()
                for question in by_source.get(source_topic, [])
            ]
        else:
            pool = by_source.get(SOURCE_TOPICS[topic_id], [])
        topic_questions[topic_id] = pick_questions(pool, topic_id)

    OUTPUT_TS.write_text(render(topic_questions), encoding="utf-8")
    counts = ", ".join(f"{topic_id}={len(topic_questions[topic_id])}" for topic_id, _, _ in TOPICS)
    print(f"Synced {len(TOPICS)} quiz topics ({counts}) -> {OUTPUT_TS.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    sync()
