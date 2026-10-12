"""Derives the true type of each test-case value from the JSON itself.

This is the ground truth the signature validator checks hand-authored data
against. It is deliberately derived purely from data rather than from problem
text: a signature that disagrees with the test bank is wrong regardless of how
the prose reads.

The one piece of real judgement is `int` versus `double`. Python's `json` parses
`3` and `3.0` into `int` and `float`, so the distinction survives, but only if
we treat an integral float as genuinely ambiguous rather than silently
normalising it. `basic-calculator-ii` is exactly this case: it expects `7` for
integer division, and a Java student returning `7.0` must fail to compile. So
`3.0` is reported as `double` with a flag saying the value is integral, and
callers decide what to do about it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Canonical type names. These are the strings that appear in signatures.json,
# chosen to be readable in both Java and C++ contexts.
INT = "int"
LONG = "long"
DOUBLE = "double"
BOOLEAN = "boolean"
STRING = "String"
NULL = "null"
INT_LIST = "List<Integer>"
DOUBLE_LIST = "List<Double>"
STRING_LIST = "List<String>"
LIST_LIST_INT = "List<List<Integer>>"
LIST_LIST_STRING = "List<List<String>>"
LIST_LIST_LIST_INT = "List<List<List<Integer>>>"
EMPTY_LIST = "List<Object>"
MAP = "Map<String, Object>"
TREE_NODE = "TreeNode"
UNKNOWN = "unknown"

# Types that carry a definite shape, as opposed to EMPTY_LIST (nothing observed
# at all) and UNKNOWN (observed and contradictory). Two different members of
# this set across test cases means the data supports neither alone.
_CONCRETE_CONTAINERS = frozenset(
    {
        INT_LIST,
        DOUBLE_LIST,
        STRING_LIST,
        LIST_LIST_INT,
        LIST_LIST_STRING,
        LIST_LIST_LIST_INT,
        TREE_NODE,
    }
)


@dataclass
class ObservedType:
    """A type observed in the data, plus what we know about its confidence.

    `saw_non_integral_double` is the field that matters most. It is what
    distinguishes two cases that look identical from the type alone:

    - `pow-x-n` expects 9.261 and 0.25. Those are genuinely fractional, so the
      problem is a `double` problem and declaring `int` is simply wrong.
    - `basic-calculator-ii` expects 7, and a handful of values like 1.2e43 that
      happen to be integral floats. Integer division is still the intent, so
      `int` is defensible — but only a human can confirm that.

    Getting this distinction wrong in either direction is how a type gate
    becomes worse than no gate at all.
    """

    name: str
    saw_double: bool = False
    saw_int: bool = False
    saw_integral_float: bool = False
    saw_non_integral_double: bool = False
    samples: list[Any] = field(default_factory=list)

    @property
    def is_ambiguous_int_double(self) -> bool:
        """True when the data mixes int and double, or is float-but-integral.

        Either way, declaring one type will reject correct answers in the other,
        so this must be surfaced rather than silently collapsed.
        """
        return self.saw_integral_float or (self.saw_int and self.saw_double)


def _list_depth(value: Any) -> int:
    """Maximum nesting depth of lists, counting the outermost as 1."""
    if not isinstance(value, list):
        return 0
    if not value:
        return 1
    return 1 + max(_list_depth(v) for v in value)


def _has_non_integral_float(value: Any) -> bool:
    """True if any float anywhere inside is genuinely fractional (3.5, not 3.0)."""
    if isinstance(value, float):
        return not float(value).is_integer()
    if isinstance(value, list):
        return any(_has_non_integral_float(v) for v in value)
    return False


def classify(value: Any) -> ObservedType:
    """Classifies one JSON value into a canonical type, preserving int/float."""
    if value is None:
        return ObservedType(NULL)

    # bool must be checked before int: in Python True is an instance of int,
    # and `isinstance(True, int)` is True. Getting this backwards would make
    # every boolean problem look like an integer problem.
    if isinstance(value, bool):
        return ObservedType(BOOLEAN)

    if isinstance(value, int):
        # A value outside signed 32-bit cannot be held by a Java int, so the
        # declared type has to be wider. The data settles this; there is no
        # authoring judgement to make. Unsigned 32-bit results (reverse-bits,
        # number-of-1-bits) are exactly this case.
        if value < -(2**31) or value > 2**31 - 1:
            return ObservedType(LONG, samples=[value])
        return ObservedType(INT, saw_int=True, samples=[value])

    if isinstance(value, float):
        integral = float(value).is_integer()
        return ObservedType(
            DOUBLE,
            saw_double=True,
            saw_integral_float=integral,
            saw_non_integral_double=not integral,
            samples=[value],
        )

    if isinstance(value, str):
        return ObservedType(STRING, samples=[value])

    if isinstance(value, list):
        if not value:
            return ObservedType(EMPTY_LIST)

        # Collapse the tree once and look at every distinct element type found
        # anywhere inside it, rather than only the top level. A 2-D board like
        # [[1,3,5],[10,11,16]] is List<List<Integer>>, and a level-order tree
        # like [[3],[9,20],[15,7]] is List<List<Integer>> too — checking only
        # the immediate children cannot tell those apart from a genuinely mixed
        # list such as [[1,2],[3,"a"]], which is what the previous version got
        # wrong on 32 problems.
        distinct: set[str] = set()
        saw_int = False
        saw_double = False
        saw_integral_float = False
        saw_null = False

        def walk(node: Any) -> None:
            nonlocal saw_int, saw_double, saw_integral_float, saw_null
            if isinstance(node, bool):
                return
            if node is None:
                saw_null = True
                return
            if isinstance(node, int):
                saw_int = True
                return
            if isinstance(node, float):
                saw_double = True
                if float(node).is_integer():
                    saw_integral_float = True
                return
            if isinstance(node, str):
                distinct.add(STRING)
                return
            if isinstance(node, list):
                for child in node:
                    walk(child)

        walk(value)

        depth = _list_depth(value)
        scalars = distinct | {
            INT if saw_int else None,
            DOUBLE if saw_double else None,
        }
        scalars = {s for s in scalars if s}

        if not scalars:
            # Every element was an empty container: nothing about the element
            # type was observed. Falling through to the depth-appropriate int
            # type would be a guess, and a guess here is what pins a String
            # board to List<List<Integer>> — a signature no compiled language
            # can emit and the data cannot justify. Report no evidence and let a
            # case that has some decide.
            return ObservedType(EMPTY_LIST, samples=value[:2])

        if saw_null and scalars <= {INT}:
            # An integer list holding nulls is a node encoding: the level-order
            # form of a binary tree marks an absent child with null, and no plain
            # int array can express that. It is the only reading under which the
            # data has a type a compiled language can declare a parameter of.
            return ObservedType(TREE_NODE, saw_int=True, samples=value[:2])

        if scalars <= {INT}:
            base = {1: INT_LIST, 2: LIST_LIST_INT, 3: LIST_LIST_LIST_INT}.get(depth)
            if base:
                return ObservedType(base, saw_int=True, samples=value[:2])
            return ObservedType(INT_LIST if depth <= 1 else LIST_LIST_INT, saw_int=True, samples=value[:2])
        if scalars <= {DOUBLE}:
            integral = saw_integral_float and not _has_non_integral_float(value)
            return ObservedType(
                DOUBLE_LIST,
                saw_double=True,
                saw_integral_float=integral,
                samples=value[:2],
            )
        if scalars <= {STRING}:
            base = {1: STRING_LIST, 2: LIST_LIST_STRING}.get(depth)
            return ObservedType(base or STRING_LIST, samples=value[:2])
        if scalars <= {INT, NULL}:
            return ObservedType(INT_LIST, saw_int=True, samples=value[:2])
        if scalars <= {DOUBLE, NULL}:
            return ObservedType(DOUBLE_LIST, saw_double=True, samples=value[:2])

        # Mixed int and String (e.g. subsets/permutations of a mixed alphabet):
        # genuinely heterogeneous, so no precise element type is defensible.
        return ObservedType(UNKNOWN, samples=value[:2])

    if isinstance(value, dict):
        return ObservedType(MAP, samples=list(value.items())[:2])

    return ObservedType(UNKNOWN, samples=[repr(value)])


def _merge(target: ObservedType, other: ObservedType) -> ObservedType:
    """Combines observations of the same type across many test cases.

    If one test case yields `1024` (int) and the next `9.261` (double), the
    merged observation must be `double`, not whichever type happened to arrive
    first. Keeping the first name would let a genuinely-float problem be signed
    as `int`, which would reject every correct Java `double` solution.

    The same reasoning applies to containers. An empty list carries no element
    type at all, so it must never outrank a case that does supply one: `[]` on
    the first case and `[[0]]` on the third is a List<List<Integer>> problem.
    Letting the empty case win would pin the signature to List<Object>, which
    no compiled language can emit a parameter type for.
    """
    target.saw_int |= other.saw_int
    target.saw_double |= other.saw_double
    target.saw_integral_float |= other.saw_integral_float
    target.saw_non_integral_double |= other.saw_non_integral_double

    # double wins over int: a float is strictly wider, so any int in the data
    # is representable as one, but not the reverse.
    if target.saw_double:
        target.name = DOUBLE
    elif LONG in (target.name, other.name) and {target.name, other.name} <= {INT, LONG}:
        # Wider wins, exactly as double wins over int: an int literal is always
        # representable as a long, and one case needing the wider type settles it.
        target.name = LONG
    elif {target.name, other.name} == {TREE_NODE, INT_LIST}:
        # A tree whose nodes all have both children serialises with no nulls at
        # all, so the same parameter legitimately arrives as a plain int list in
        # some cases and a null-bearing one in others. Both are the tree.
        target.name = TREE_NODE
    elif target.name == EMPTY_LIST and other.name not in (EMPTY_LIST, UNKNOWN):
        # Nothing observed yet versus something observed: the observation wins.
        target.name = other.name
    elif (
        other.name != EMPTY_LIST
        and target.name != other.name
        and target.name in _CONCRETE_CONTAINERS
        and other.name in _CONCRETE_CONTAINERS
    ):
        # Two different concrete container shapes across cases: the data does
        # not support either one alone, so say so rather than over-claim.
        target.name = UNKNOWN

    for s in other.samples[:2]:
        if s not in target.samples and len(target.samples) < 3:
            target.samples.append(s)
    return target


def infer_problem_types(problem: dict[str, Any]) -> dict[str, Any]:
    """Infers the declared shape of a problem from its test cases alone.

    Returns the observed param types and return type, each annotated with the
    ambiguity flags the validator needs in order to reject a signature that
    over-claims precision the data does not support.
    """
    test_cases = problem.get("testCases") or problem.get("testcases") or []

    param_counts: dict[int, ObservedType] = {}
    ret: ObservedType | None = None

    for tc in test_cases:
        args = tc.get("input") or []
        for idx, arg in enumerate(args):
            observed = classify(arg)
            if idx in param_counts:
                _merge(param_counts[idx], observed)
            else:
                param_counts[idx] = observed

        expected = tc.get("expected")
        observed_ret = classify(expected)
        if ret is None:
            ret = observed_ret
        else:
            _merge(ret, observed_ret)

    params = [param_counts[i] for i in sorted(param_counts)]
    return {
        "params": params,
        "returnType": ret or ObservedType(UNKNOWN),
        "arity": len(params),
    }


def load_problems(problems_dir: Path) -> dict[str, dict[str, Any]]:
    """Loads verified (non-scrap) problems keyed by slug."""
    out: dict[str, dict[str, Any]] = {}
    for path in sorted(problems_dir.glob("*.json")):
        if path.stem.startswith("scrap-"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        slug = data.get("slug") or path.stem
        out[slug] = data
    return out
