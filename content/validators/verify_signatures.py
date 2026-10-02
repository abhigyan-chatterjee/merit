#!/usr/bin/env python3
"""Validates `content/signatures.json` against ground truth derived from test data.

Why this exists
---------------
Signatures declare the type each problem's solution must return and accept. A
wrong signature is worse than a missing one: a problem declared `int` whose
answers are `double` will reject every correct Java submission with a
compile error, and nothing in the existing suite would notice, because the
existing suite only runs Python and JavaScript — where the declared type is
never consulted.

So this gate derives the truth from the test cases themselves and rejects any
signature that disagrees. It is deliberately an oracle, not a linter: it does
not ask whether a signature looks reasonable, it asks whether it matches the
data the judge will actually run.

Strict typing is intentional. `basic-calculator-ii` expects `7` for integer
division, and a Java student returning `7.0` must fail — teaching the
difference between `int` and `double` is the product's job, not something to
paper over with coercion.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from content.validators.signature_types import (  # noqa: E402
    BOOLEAN,
    DOUBLE,
    INT,
    INT_LIST,
    LIST_LIST_INT,
    LIST_LIST_STRING,
    LIST_LIST_LIST_INT,
    STRING,
    STRING_LIST,
    UNKNOWN,
    ObservedType,
    infer_problem_types,
    load_problems,
)

# Canonical type -> the set of types it is allowed to be, given the data.
# `int` is NOT compatible with `double`: that strictness is the point.
_COMPATIBLE: dict[str, set[str]] = {
    INT: {INT},
    DOUBLE: {DOUBLE},
    BOOLEAN: {BOOLEAN},
    STRING: {STRING},
    INT_LIST: {INT_LIST},
    STRING_LIST: {STRING_LIST},
    LIST_LIST_INT: {LIST_LIST_INT},
    LIST_LIST_STRING: {LIST_LIST_STRING},
    LIST_LIST_LIST_INT: {LIST_LIST_LIST_INT},
    "List<Object>": {"List<Object>"},
}

KNOWN_TYPES = set(_COMPATIBLE) | {UNKNOWN}


def _describe(t: ObservedType) -> str:
    """A short human-readable note about an observed type, for error output."""
    if t.name == UNKNOWN:
        return f"{UNKNOWN} (heterogeneous — no precise type is defensible)"
    if t.is_ambiguous_int_double:
        if t.saw_integral_float:
            return (
                f"{t.name} (every sample is float-valued; "
                f"declaring 'int' would reject a correct Java 'double' solution)"
            )
        return f"{t.name} (data mixes int and double across test cases)"
    return t.name


def _check_one(
    slug: str,
    problem: dict[str, Any],
    sig: Any,
    errors: list[str],
    ambiguous: list[str],
) -> None:
    inferred = infer_problem_types(problem)

    if not isinstance(sig, dict):
        errors.append(f"{slug}: signature must be an object, got {type(sig).__name__}")
        return

    declared_return = sig.get("returnType")
    declared_params = sig.get("params")
    reviewed = bool(sig.get("reviewedIntVsDouble", False))

    observed_return = inferred["returnType"]

    # Data that mixes int and double cannot settle the declared type by itself.
    # Rather than guess, require the author to confirm the decision explicitly.
    if observed_return.is_ambiguous_int_double and observed_return.name != UNKNOWN:
        if not reviewed:
            ambiguous.append(slug)
        elif declared_return == INT and observed_return.name == DOUBLE:
            # Confirming `int` is only defensible when every float in the data is
            # integral (basic-calculator-ii: 7.0 from an int division). If a
            # genuinely fractional value exists (pow-x-n: 9.261), `int` is wrong
            # and no amount of human sign-off makes it right.
            if observed_return.saw_non_integral_double:
                errors.append(
                    f"{slug}: declares int and marked reviewed, but the test cases "
                    "contain genuinely fractional values — int is not defensible here"
                )

    if not isinstance(declared_return, str):
        errors.append(f"{slug}: returnType must be a string, got {declared_return!r}")
    elif declared_return not in KNOWN_TYPES:
        errors.append(
            f"{slug}: returnType {declared_return!r} is not a known type "
            f"(known: {', '.join(sorted(KNOWN_TYPES))})"
        )
    elif inferred["returnType"].name != UNKNOWN:
        # A human-confirmed `int` on data that only ever shows integral floats is
        # a deliberate, correct decision (basic-calculator-ii: integer division).
        # The plain compatibility check would reject it, so the confirmed case
        # is honoured here. Unconfirmed, it still has to fail.
        confirmed_int = (
            reviewed
            and declared_return == INT
            and observed_return.name == DOUBLE
            and not observed_return.saw_non_integral_double
        )
        if not confirmed_int:
            allowed = _COMPATIBLE.get(declared_return, {declared_return})
            if inferred["returnType"].name not in allowed:
                errors.append(
                    f"{slug}: returnType declared {declared_return!r} but the test "
                    f"cases say {_describe(inferred['returnType'])}"
                )

    if not isinstance(declared_params, list):
        errors.append(f"{slug}: params must be a list, got {declared_params!r}")
        return

    if len(declared_params) != inferred["arity"]:
        errors.append(
            f"{slug}: declares {len(declared_params)} param(s) but test cases "
            f"pass {inferred['arity']} argument(s)"
        )
        return

    for idx, declared in enumerate(declared_params):
        observed = inferred["params"][idx]
        if not isinstance(declared, str):
            errors.append(f"{slug}: params[{idx}] must be a string, got {declared!r}")
            continue
        if declared not in KNOWN_TYPES:
            errors.append(
                f"{slug}: params[{idx}] {declared!r} is not a known type "
                f"(known: {', '.join(sorted(KNOWN_TYPES))})"
            )
            continue
        if observed.name == UNKNOWN:
            errors.append(
                f"{slug}: params[{idx}] cannot be validated — the data is "
                f"heterogeneous ({observed.samples}). Author this by hand."
            )
            continue
        allowed = _COMPATIBLE.get(declared, {declared})
        if observed.name not in allowed:
            errors.append(
                f"{slug}: params[{idx}] declared {declared!r} but the test "
                f"cases say {_describe(observed)}"
            )


def verify_signatures(signatures_path: Path, problems_dir: Path) -> int:
    problems = load_problems(problems_dir)

    if not signatures_path.exists():
        print(f"  ! {signatures_path.name} not found")
        return 1

    try:
        signatures = json.loads(signatures_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"  ! could not parse {signatures_path.name}: {exc}")
        return 1

    if not isinstance(signatures, dict):
        print(f"  ! {signatures_path.name} must be a top-level object")
        return 1

    errors: list[str] = []
    # Problems whose data mixes int and double. The gate cannot decide these —
    # `basic-calculator-ii` expects 7 for integer division, but its data also
    # contains 7.0, so `int` and `double` are both defensible readings. Silently
    # accepting either would defeat the point of a type gate, so each one is
    # named and has to be confirmed in writing.
    ambiguous: list[str] = []

    # Coverage: every verified problem needs a signature. A missing signature
    # means that problem silently has no Java/C++ support.
    missing = sorted(set(problems) - set(signatures))
    for slug in missing:
        errors.append(f"{slug}: no signature declared (Java/C++ support would be absent)")

    # Dangling: a signature for a problem that does not exist is dead data.
    extra = sorted(set(signatures) - set(problems))
    for slug in extra:
        errors.append(f"{slug}: signature declared but no such verified problem exists")

    for slug in sorted(set(signatures) & set(problems)):
        _check_one(slug, problems[slug], signatures[slug], errors, ambiguous)

    total = len(problems)
    if errors:
        print(f"\nSignature errors ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"Signatures valid: {total} problems, all matching their test data.")
    if ambiguous:
        print(
            f"\n⚠ {len(ambiguous)} problem(s) mix int and double in their test data, "
            "so the data cannot settle int vs double:\n"
            "  (each needs a deliberate human decision; the value is only a hint)\n"
        )
        for slug in ambiguous:
            declared = signatures[slug].get("returnType")
            print(f"  - {slug}: declares {declared!r}")
        print(
            "\n  Record the decision by adding \"reviewedIntVsDouble\": true to that\n"
            "  problem's signature object. Until then these are unconfirmed."
        )
        return 2
    return 0


def main() -> int:
    content_dir = _REPO_ROOT / "content"
    problems_dir = content_dir / "problems"
    signatures_path = content_dir / "signatures.json"

    print("--- VERIFYING PROBLEM SIGNATURES (Java / C++ return + param types) ---")
    return verify_signatures(signatures_path, problems_dir)


if __name__ == "__main__":
    sys.exit(main())
