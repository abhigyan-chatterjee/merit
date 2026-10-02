"""Tests for the type oracle and the signature gate.

These exist because the gate was nearly shipped with two real defects that a
"does it pass on good data?" check would never have caught:

- an int/double mix resolved to whichever type arrived first, so a genuinely
  fractional problem (`pow-x-n`, expects 9.261) could be signed as `int`
- `basic-calculator-ii`, whose floats are all integral, could not be signed as
  `int` even with explicit human sign-off

Both are silent: they reject or accept bad data without complaining. So every
branch below is asserted in both directions.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from content.validators.signature_types import (  # noqa: E402
    BOOLEAN,
    DOUBLE,
    INT,
    INT_LIST,
    LIST_LIST_INT,
    LIST_LIST_LIST_INT,
    LIST_LIST_STRING,
    STRING,
    STRING_LIST,
    UNKNOWN,
    classify,
    infer_problem_types,
)
from content.validators.verify_signatures import verify_signatures  # noqa: E402

PROBLEMS_DIR = _REPO_ROOT / "content" / "problems"


# --- the oracle ------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        (3, INT),
        (3.0, DOUBLE),
        (3.5, DOUBLE),
        # bool must precede int: isinstance(True, int) is True in Python
        (True, BOOLEAN),
        (False, BOOLEAN),
        (None, "null"),
        ("ab", STRING),
        ([1, 2], INT_LIST),
        ([[1, 3], [10, 11]], LIST_LIST_INT),
        ([[3], [9, 20], [15, 7]], LIST_LIST_INT),
        ([[[1]]], LIST_LIST_LIST_INT),
        ([["a"], ["bb"]], LIST_LIST_STRING),
        ([], "List<Object>"),
        ([[1, 2], []], LIST_LIST_INT),
        ([[1, 2], [3, "a"]], UNKNOWN),
    ],
)
def test_classify(value, expected):
    assert classify(value).name == expected


def test_classify_preserves_int_double_distinction():
    assert classify(3.0).saw_integral_float is True
    assert classify(3.0).saw_non_integral_double is False
    assert classify(3.5).saw_integral_float is False
    assert classify(3.5).saw_non_integral_double is True


def _problem(cases):
    return {"testCases": [{"input": list(args), "expected": exp} for args, exp in cases]}


def test_int_double_mix_resolves_to_double():
    """Regression: the merge used to keep whichever type arrived first, so
    `1024` then `9.261` resolved to `int` and a fractional problem could be
    signed as int."""
    inferred = infer_problem_types(_problem([((), 1024), ((), 9.261)]))
    assert inferred["returnType"].name == DOUBLE


def test_int_float_mix_resolves_to_double():
    inferred = infer_problem_types(_problem([((), 7), ((), 7.0)]))
    assert inferred["returnType"].name == DOUBLE
    assert inferred["returnType"].saw_non_integral_double is False
    assert inferred["returnType"].saw_integral_float is True


def test_integer_only_problem_is_int():
    inferred = infer_problem_types(_problem([((), 7), ((), -1)]))
    assert inferred["returnType"].name == INT
    assert inferred["returnType"].is_ambiguous_int_double is False


# --- the gate --------------------------------------------------------------


@pytest.fixture
def gate(tmp_path):
    """Runs the gate over a one-problem sandbox and returns its exit code."""

    def _run(signature, problem=None):
        probs = tmp_path / "problems"
        probs.mkdir(exist_ok=True)
        data = problem or _problem([(([2, 7], 9), [0, 1])])
        (probs / "p.json").write_text(json.dumps({"slug": "p", **data}))

        sig_path = tmp_path / "signatures.json"
        sig_path.write_text(json.dumps({"p": signature}))

        buf = []
        original = sys.stdout.write
        sys.stdout.write = lambda s: buf.append(s) or len(s)
        try:
            return verify_signatures(sig_path, probs), "".join(buf)
        finally:
            sys.stdout.write = original

    return _run


def test_gate_accepts_a_correct_signature(gate):
    code, out = gate({"returnType": "List<Integer>", "params": ["List<Integer>", "int"]})
    assert code == 0, out


@pytest.mark.parametrize(
    "signature,fragment",
    [
        ({"returnType": "boolean", "params": ["List<Integer>", "int"]}, "returnType declared"),
        ({"returnType": "List<Integer>", "params": ["List<Integer>"]}, "pass 2 argument"),
        ({"returnType": "List<Integer>", "params": ["String", "int"]}, "params[0] declared"),
        ({"returnType": "int64_t", "params": ["List<Integer>", "int"]}, "not a known type"),
    ],
)
def test_gate_rejects_wrong_signatures(gate, signature, fragment):
    code, out = gate(signature)
    assert code == 1, out
    assert fragment in out


def test_gate_requires_every_problem_to_have_a_signature(tmp_path):
    probs = tmp_path / "problems"
    probs.mkdir()
    (probs / "a.json").write_text(json.dumps({"slug": "a", **_problem([((), 1)])}))
    (probs / "b.json").write_text(json.dumps({"slug": "b", **_problem([((), 1)])}))
    sig = tmp_path / "signatures.json"
    sig.write_text(json.dumps({"a": {"returnType": "int", "params": []}}))

    code = verify_signatures(sig, probs)
    assert code == 1


def test_gate_flags_ambiguous_int_vs_double_for_review(gate):
    """Data mixing int and double cannot settle the type, so the gate must ask
    for a human rather than pass or fail silently."""
    problem = _problem([((), 7), ((), 7.0)])
    code, out = gate({"returnType": "double", "params": []}, problem)
    assert code == 2, out
    assert "reviewedIntVsDouble" in out


def test_confirmed_int_on_integral_floats_is_accepted(gate):
    """Regression: a human confirming `int` on integral-float data was rejected
    by the compatibility table before sign-off was considered."""
    problem = _problem([((), 7), ((), 7.0)])
    code, out = gate(
        {"returnType": "int", "params": [], "reviewedIntVsDouble": True}, problem
    )
    assert code == 0, out


def test_confirmed_int_is_still_refused_on_fractional_data(gate):
    """Sign-off cannot make a wrong declaration right.

    Two independent checks reject this, so the assertion is not pinned to one
    message — only to the fact that it is refused at all.
    """
    problem = _problem([((), 9.261), ((), 0.25)])
    code, out = gate(
        {"returnType": "int", "params": [], "reviewedIntVsDouble": True}, problem
    )
    assert code == 1, out
    assert "int" in out


def test_unconfirmed_int_on_integral_floats_still_fails(gate):
    """Without explicit sign-off, an `int` declaration over float data must not
    slip through — that is the whole point of the review gate."""
    problem = _problem([((), 7), ((), 7.0)])
    code, out = gate({"returnType": "int", "params": []}, problem)
    assert code == 1, out
