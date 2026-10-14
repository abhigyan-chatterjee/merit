"""Validate generated test data against the relation bounds stated in a problem.

The PAF generator reads bounds of the form `<number> <= <subject> <= <number>`.
Bounds written against another parameter (`1 <= k <= num.length`,
`0 <= src <= n - 1`, `0 <= adj[i][j] <= adj.length - 1`) are only partly
supported, so shipped test data can contradict the problem's own Constraints
line while still passing the judge gate (all four authored implementations may
tolerate the out-of-range values).

This validator evaluates each relational clause against every shipped test case
using that case's own values, so the check is independent of the generator.

Usage:
    python3 content/validators/check_relative_bounds.py            # all problems
    python3 content/validators/check_relative_bounds.py SLUG ...   # named problems
    python3 content/validators/check_relative_bounds.py --new      # untracked problems
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBLEMS = ROOT / "content" / "problems"

# Problems whose shipped test data cannot yet satisfy their own Constraints
# line, with the reason. Empty: the three problems that used to be listed here
# (`binary-search`, `search-in-rotated-sorted-array`, `search-a-2d-matrix`)
# needed input premises the generator could not synthesise, and those premises
# are now generated (`_apply_premises` in paf/inputs.py). The mechanism stays so
# a future problem that genuinely cannot be generated is listed rather than
# silently passed.
KNOWN_UNSUPPORTED: dict[str, str] = {}

# `MIN <= EXPR <(=) MAX` where either end may be a number or an expression
# built from parameter names / `.length` / `+ - *` / digits.
_ATOM = r"(?:-?\d+(?:\.\d+)?|[A-Za-z_]\w*(?:\.(?:length|size))?)"
_EXPR = rf"{_ATOM}(?:\s*[-+*]\s*{_ATOM})*"
_CLAUSE = re.compile(
    rf"({_EXPR})\s*(<=|<)\s*({_EXPR})\s*(<=|<)\s*({_EXPR})"
)


def _params(problem: dict) -> list[str]:
    js = (problem.get("starterCode") or {}).get("javascript") or ""
    match = re.search(r"function\s+\w+\s*\(([^)]*)\)", js)
    if not match:
        return []
    return [p.strip() for p in match.group(1).split(",") if p.strip()]


def _eval(node: str, env: dict) -> float | None:
    node = node.strip()
    if node.isdigit():
        return float(node)
    base, dot, attr = node.partition(".")
    if base not in env:
        return None
    value = env[base]
    if dot:  # only `.length` / `.size` are meaningful
        if not isinstance(value, (list, str, dict)):
            return None
        return float(len(value))
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _atom_values(expr: str, env: dict) -> float | None:
    """Evaluate a small arithmetic expression of atoms and + - * operators."""
    tokens = re.split(r"(\s*[-+*]\s*)", expr)
    total: float | None = None
    op = "+"
    for token in tokens:
        if not token.strip():
            continue
        if token.strip() in {"+", "-", "*"}:
            op = token.strip()
            continue
        value = _eval(token, env)
        if value is None:
            return None
        if total is None:
            total = value if op == "+" else -value
            continue
        total = total + value if op == "+" else total - value if op == "-" else total * value
    return total


def clauses(statement: str) -> list[re.Match]:
    line = ""
    for ln in statement.split("\n"):
        if ln.strip().lower().startswith("constraints"):
            line = ln.strip()
            break
    if not line:
        return []
    return list(_CLAUSE.finditer(line))


def check(path: Path) -> dict:
    problem = json.loads(path.read_text(encoding="utf-8"))
    params = _params(problem)
    statement = problem.get("statement") or ""
    found = clauses(statement)
    violations: list[dict] = []
    checked_clauses = 0
    for match in found:
        low_s, op_a, mid, op_b, high_s = match.groups()
        checked = False
        for case in problem.get("testCases") or []:
            raw = case.get("input")
            if not isinstance(raw, list) or len(raw) != len(params):
                continue
            env = dict(zip(params, raw))
            mid_val = _eval(mid, env)
            if mid_val is None:
                # vector/nested subjects (e.g. adj[i][j]) are covered by the
                # dedicated nested check below; skip scalar evaluation here
                continue
            low = _atom_values(low_s, env)
            high = _atom_values(high_s, env)
            if low is None or high is None:
                continue
            checked = True
            if op_a == "<=":
                ok_low = low <= mid_val
            else:
                ok_low = low < mid_val
            if op_b == "<=":
                ok_high = mid_val <= high
            else:
                ok_high = mid_val < high
            if not (ok_low and ok_high):
                violations.append(
                    {
                        "case": case.get("label"),
                        "clause": match.group(0).strip(),
                        "value": mid_val,
                        "range": [low, high],
                    }
                )
        if checked:
            checked_clauses += 1

    # nested subjects: `MIN <= name[i][j] <= MAX` against nested lists
    nested = re.compile(
        rf"({_EXPR})\s*<=\s*([A-Za-z_]\w*)\[i\]\[j\]\s*<=\s*({_EXPR})"
    )
    for match in nested.finditer(statement):
        low_s, name, high_s = match.groups()
        for case in problem.get("testCases") or []:
            raw = case.get("input")
            if not isinstance(raw, list) or len(raw) != len(params):
                continue
            env = dict(zip(params, raw))
            rows = env.get(name)
            if not isinstance(rows, list):
                continue
            low = _atom_values(low_s, env)
            high = _atom_values(high_s, env)
            if low is None or high is None:
                continue
            for row in rows:
                if not isinstance(row, list):
                    continue
                for value in row:
                    if isinstance(value, (int, float)) and not (
                        low <= value <= high
                    ):
                        violations.append(
                            {
                                "case": case.get("label"),
                                "clause": match.group(0).strip(),
                                "value": value,
                                "range": [low, high],
                            }
                        )
                        break

    return {
        "slug": problem.get("slug"),
        "clauses": len(found),
        "evaluated": checked_clauses,
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("slugs", nargs="*")
    parser.add_argument("--new", action="store_true", help="untracked problems only")
    args = parser.parse_args()

    if args.slugs:
        paths = [PROBLEMS / f"{s}.json" for s in args.slugs]
    elif args.new:
        out = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "content/problems"],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        ).stdout.split()
        paths = [ROOT / p for p in out]
    else:
        paths = sorted(PROBLEMS.glob("*.json"))

    bad = 0
    for path in paths:
        if not path.exists():
            print(f"MISSING {path.name}")
            continue
        result = check(path)
        if result["violations"]:
            bad += 1
            shown = result["violations"][:3]
            print(
                f"FAIL {result['slug']}: {len(result['violations'])} violating case(s) "
                f"over {result['clauses']} relational clause(s)"
            )
            for item in shown:
                print(
                    f"      {item['case']}: {item['clause']} -> value {item['value']} "
                    f"outside [{item['range'][0]}, {item['range'][1]}]"
                )
    print(f"\nchecked {len(paths)} problem(s); {bad} with constraint-violating test data")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
