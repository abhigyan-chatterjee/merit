"""Prepares per-problem signature authoring batches.

Splits the 140 verified problems into chunks small enough for a model to reason
about properly, and emits exactly the evidence an author needs — the test-case
shapes, not the statement prose, since the gate judges against the data.

The author must not read the existing signatures.json. If it did, it would
anchor on them and reproduce whatever they already say, which would make the
validation stage meaningless.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from content.validators.signature_types import (  # noqa: E402
    classify,
    infer_problem_types,
    load_problems,
)

PROBLEMS_DIR = _REPO_ROOT / "content" / "problems"
KNOWN_TYPES = [
    "int",
    "double",
    "boolean",
    "String",
    "List<Integer>",
    "List<String>",
    "List<List<Integer>>",
    "List<List<String>>",
    "List<List<List<Integer>>>",
    "List<Object>",
    "unknown",
]


def evidence(problem: dict) -> dict:
    """Just enough about a problem to declare its types, drawn from the data."""
    inferred = infer_problem_types(problem)
    tcs = problem.get("testCases") or []

    def shape(v):
        return classify(v).name

    return {
        "slug": problem.get("slug"),
        "functionName": problem.get("functionName", "solve"),
        "title": problem.get("title"),
        "arity": inferred["arity"],
        "observed_return": inferred["returnType"].name,
        "observed_return_integral_float_only": (
            inferred["returnType"].saw_integral_float
            and not inferred["returnType"].saw_non_integral_double
        ),
        "observed_params": [t.name for t in inferred["params"]],
        # A few concrete samples so the author can see the real shape rather
        # than infer it from a type name.
        "sample_input_shapes": [shape(a) for a in (tcs[0].get("input") or [])],
        "sample_expected": (tcs[0].get("expected")
                            if isinstance(tcs[0].get("expected"), (int, float, str, bool))
                            else str(tcs[0].get("expected"))[:60]),
        "has_ambiguous_int_double": inferred["returnType"].is_ambiguous_int_double,
    }


def main() -> int:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else _REPO_ROOT / ".signature-batches"
    out_dir.mkdir(parents=True, exist_ok=True)

    problems = load_problems(PROBLEMS_DIR)
    slugs = sorted(problems)

    batch_size = 20
    written = []
    for i in range(0, len(slugs), batch_size):
        chunk = slugs[i : i + batch_size]
        payload = {
            "known_types": KNOWN_TYPES,
            "problems": [evidence(problems[s]) for s in chunk],
        }
        path = out_dir / f"batch_{i // batch_size + 1:02d}.json"
        path.write_text(json.dumps(payload, indent=2))
        written.append(path)
        print(f"  {path.name}: {len(chunk)} problems")

    (out_dir / "all_slugs.json").write_text(json.dumps(slugs, indent=2))
    print(f"\n{len(slugs)} problems across {len(written)} batches -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
