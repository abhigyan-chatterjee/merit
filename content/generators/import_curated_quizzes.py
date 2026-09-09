"""Extract curated questions from apps/web/src/data/quizzes.ts into content/questions/."""

import json
import re
import sys
from pathlib import Path

# Ensure repo root is on sys.path so modules resolve cleanly without PYTHONPATH env var
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from content.generators.base import compute_content_hash


def import_curated_quizzes(source_file: Path, target_dir: Path) -> int:
    with open(source_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Find each topic block: arrays, trees, graphs, dp, mixed
    blocks = re.findall(r"(\w+):\s*\[(.*?)\]\n\s*(\}|[a-z]+:)", content, re.DOTALL)
    imported = 0

    topic_mapping = {
        "arrays": "arrays",
        "trees": "trees",
        "graphs": "graphs",
        "dp": "dp",
        "mixed": "mixed",
    }

    # Match objects: id, question, options, correctIndex, explanation
    obj_pattern = re.compile(
        r"\{\s*id:\s*['\"]([^'\"]+)['\"],\s*question:\s*['\"](.*?)['\"],\s*options:\s*\[(.*?)\]\s*,\s*correctIndex:\s*(\d+),\s*explanation:\s*['\"](.*?)['\"]\s*\}",
        re.DOTALL,
    )

    for match in obj_pattern.finditer(content):
        qid = match.group(1).strip()
        prompt = match.group(2).strip().replace("\\'", "'").replace('\\"', '"')
        raw_opts = match.group(3).strip()
        # Parse options
        options = [
            opt.strip().strip("'\"").replace("\\'", "'").replace('\\"', '"')
            for opt in re.findall(r"['\"](.*?)['\"]", raw_opts)
        ]
        correct_idx = int(match.group(4))
        explanation = match.group(5).strip().replace("\\'", "'").replace('\\"', '"')

        if len(options) != 4:
            continue

        # Determine topic by qid prefix
        if qid.startswith("arr"):
            topic = "arrays"
        elif qid.startswith("tree"):
            topic = "trees"
        elif qid.startswith("graph"):
            topic = "graphs"
        elif qid.startswith("dp"):
            topic = "dp"
        else:
            topic = "mixed"

        c_hash = compute_content_hash(prompt)
        q_dict = {
            "id": f"curated-{qid}",
            "topic": topic,
            "subtopic": "curated",
            "difficulty": "Medium",
            "qtype": "mcq",
            "prompt": prompt,
            "options": options,
            "correct_index": correct_idx,
            "explanation": explanation,
            "source": "curated",
            "generator_key": None,
            "content_hash": c_hash,
            "review_status": "verified",
        }

        topic_dir = target_dir / topic
        topic_dir.mkdir(parents=True, exist_ok=True)
        q_path = topic_dir / f"curated-{qid}.json"
        with open(q_path, "w", encoding="utf-8") as out:
            json.dump(q_dict, out, indent=2)
        imported += 1

    print(f"Imported {imported} curated quiz questions.")
    return imported


if __name__ == "__main__":
    src = Path(__file__).parent.parent.parent / "apps" / "web" / "src" / "data" / "quizzes.ts"
    dest = Path(__file__).parent.parent / "questions"
    import_curated_quizzes(src, dest)
