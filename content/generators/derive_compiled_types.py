"""Derive Java/C++ starters and the signatures.json entry from a built problem.

The compiled-language harnesses are generated from `content/signatures.json`, and
the editor offers Java/C++ on every problem, so a published problem must carry
both a typed starter pair and a signature entry. Types are *derived from the test
data*, never from the prose signature: this mirrors the repo rule that the
signature oracle is the data, not the author's intent.

Parameter and return spellings come from the judge's own `_TYPES` table rather
than a copy of it. The signature vocabulary and the Java spelling differ —
`List<Integer>` is `int[]` in the Java harness — so a starter written from the
vocabulary alone disagrees with the harness and fails to compile. Importing the
table makes that class of drift impossible; a type the harness cannot emit is
rejected here instead of shipping a starter nobody can compile.

`verify_signatures.py` is the gate that then checks the derived entry against
that data.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "apps" / "api"))

from app.services.judge import _TYPES  # noqa: E402
from content.validators.signature_types import (  # noqa: E402
    DOUBLE,
    INT,
    infer_problem_types,
)


def _resolve(observed) -> tuple[str | None, str | None]:
    """Map one observed type to the harness vocabulary, or explain why not."""
    name = observed.name
    if name == DOUBLE:
        # A JSON-encoded expected value of `7` classifies as int, so an observed
        # double that is never fractional arrived only because the value was
        # written as a float. Integer arithmetic is the intent, matching the
        # bank's own ruling on division problems.
        if observed.saw_non_integral_double:
            return DOUBLE, None
        return INT, None
    if name in _TYPES:
        return name, None
    return None, f"type '{name}' has no compiled equivalent"


def derive_compiled(problem: dict, param_names: list[str]) -> tuple[dict, dict | None, list[str]]:
    """Derive (starters, signature_entry, warnings) for a built problem.

    ``starters`` is ``{"java": str, "cpp": str}`` (empty when the data cannot be
    mapped). ``signature_entry`` is ``{"params": [...], "returnType": "..."}`` or
    None. ``warnings`` names every shape that could not be mapped.
    """
    warnings: list[str] = []
    inferred = infer_problem_types(problem)
    observed_params = inferred["params"]
    observed_return = inferred["returnType"]

    if len(observed_params) != len(param_names):
        return {}, None, [
            f"arity mismatch: signature has {len(param_names)} params, data has {len(observed_params)}"
        ]

    param_types: list[str] = []
    for idx, observed in enumerate(observed_params):
        sig_type, warn = _resolve(observed)
        if warn or sig_type is None:
            warnings.append(f"param '{param_names[idx]}': {warn}")
            return {}, None, warnings
        param_types.append(sig_type)

    return_type, warn = _resolve(observed_return)
    if warn or return_type is None:
        warnings.append(warn or "return type could not be mapped")
        return {}, None, warnings

    fn = problem["functionName"]
    java_params = ", ".join(
        f"{_TYPES[t]['java']} {n}" for t, n in zip(param_types, param_names, strict=True)
    )
    cpp_params = ", ".join(
        f"{_TYPES[t]['cpp']} {n}" for t, n in zip(param_types, param_names, strict=True)
    )

    java = (
        "class Solution {\n"
        f"    public {_TYPES[return_type]['java']} {fn}({java_params}) {{\n"
        "        // Write your solution here\n"
        '        throw new UnsupportedOperationException("Not implemented");\n'
        "    }\n"
        "}\n"
    )
    cpp = (
        "class Solution {\n"
        "public:\n"
        f"    {_TYPES[return_type]['cpp']} {fn}({cpp_params}) {{\n"
        "        // Write your solution here\n"
        '        throw std::logic_error("Not implemented");\n'
        "    }\n"
        "};\n"
    )
    return (
        {"java": java, "cpp": cpp},
        {"params": param_types, "returnType": return_type},
        warnings,
    )
