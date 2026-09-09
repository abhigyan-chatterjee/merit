"""Generate verified learning path definitions in content/paths/.

DEPRECATED as a source of truth: content/paths/{foundation,targeted,mastery}.json
are now hand-authored (summaries + reading links per step). This script only
re-validates those files through LearningPathSchema so CI catches bad refs.
"""

import json
import sys
from pathlib import Path

# Ensure repo root is on sys.path
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from content.validators.schema import LearningPathSchema


def create_all_paths(target_dir: Path) -> int:
    target_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for f in sorted(target_dir.glob("*.json")):
        with open(f, encoding="utf-8") as fh:
            p_data = json.load(fh)
        # Validate through schema
        LearningPathSchema(**p_data)
        count += 1

    print(f"Validated {count} learning paths.")
    return count


if __name__ == "__main__":
    paths_dir = Path(__file__).resolve().parent.parent / "paths"
    create_all_paths(paths_dir)
