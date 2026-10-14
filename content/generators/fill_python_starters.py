"""Give every problem a real Python starter derived from its own JavaScript starter.

The editor offers Python on every problem, and a learner reads the starter to see
the signature they must implement. Problems written before the generated starters
existed carry a bare `def solve(*args)` placeholder, so the Python tab showed no
parameter names while Java and C++ showed theirs.

Parameter *names* are the whole content of a starter here: the bank's Python
starters name their parameters and carry no annotations (the types live in
`content/signatures.json` and are enforced by the judge harness instead). The
JavaScript starter is the reliable source of those names, because it is the one
starter every problem has always had.

Problems that already name their parameters are left byte-for-byte alone.

Usage:
    python3 content/generators/fill_python_starters.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBLEMS_DIR = REPO_ROOT / "content" / "problems"

JS_PARAMS = re.compile(r"function\s+\w+\s*\(([^)]*)\)")
PLACEHOLDER = "(*args)"
BODY = "    # Write your solution here\n    raise NotImplementedError\n"


def js_param_names(js_starter: str) -> list[str] | None:
    """Parameter names from a JS starter, ignoring a trailing comma."""
    match = JS_PARAMS.search(js_starter or "")
    if not match:
        return None
    return [part.strip() for part in match.group(1).split(",") if part.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    filled, skipped, untouched = [], [], 0

    for path in sorted(PROBLEMS_DIR.glob("*.json")):
        if path.name.startswith("scrap-"):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        starters = data.get("starterCode")
        if not isinstance(starters, dict):
            continue
        if PLACEHOLDER not in starters.get("python", ""):
            untouched += 1
            continue

        slug = data["slug"]
        names = js_param_names(starters.get("javascript", ""))
        if not names:
            skipped.append((slug, "JavaScript starter has no parameter list"))
            continue

        rendered = f"def solve({', '.join(names)}):\n{BODY}"
        filled.append((slug, rendered.splitlines()[0]))
        if args.dry_run:
            continue

        starters["python"] = rendered
        data["starterCode"] = starters
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    for slug, line in filled:
        print(f"  {slug:52} {line}")
    for slug, why in skipped:
        print(f"  SKIP {slug:47} {why}")

    verb = "would fill" if args.dry_run else "filled"
    print(f"{verb} {len(filled)}; skipped {len(skipped)}; already named {untouched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
