"""Deterministic edge, random, and stress input generation for PAF specs."""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from typing import Any, Sequence

from content.generators.paf.spec import Parameter, ProblemSpec


@dataclass(frozen=True)
class Bounds:
    minimum: int
    maximum: int


_NUMBER = r"-?\d+(?:\^\d+)?"


def _number(value: str) -> int:
    base, marker, exponent = value.replace(" ", "").partition("^")
    return int(base) ** int(exponent) if marker else int(base)


def _find_bounds(statement: str, subject: str, fallback: Bounds) -> Bounds:
    escaped = re.escape(subject)
    match = re.search(
        rf"({_NUMBER})\s*<=\s*{escaped}\s*<=\s*({_NUMBER})", statement, re.IGNORECASE
    )
    if not match:
        return fallback
    lower, upper = _number(match.group(1)), _number(match.group(2))
    return Bounds(lower, upper) if lower <= upper else fallback


def _cap(bounds: Bounds, maximum: int) -> Bounds:
    return Bounds(bounds.minimum, max(bounds.minimum, min(bounds.maximum, maximum)))


def _annotation_kind(annotation: str) -> tuple[str, str | None]:
    clean = annotation.replace("typing.", "").replace(" ", "").lower()
    array_match = re.fullmatch(r"(.+)\[\]", clean)
    if array_match:
        return "list", array_match.group(1)
    list_match = re.fullmatch(r"(?:list|sequence)\[(.+)\]", clean)
    if list_match:
        return "list", list_match.group(1)
    if clean in {"int", "integer", "number", "bigint"}:
        return "int", None
    if clean in {"float"}:
        return "float", None
    if clean in {"bool", "boolean"}:
        return "bool", None
    if clean in {"str", "string"}:
        return "str", None
    if clean in {"any", "object", "json"}:
        return "any", None
    raise ValueError(f"PAF cannot generate JSON inputs for annotation '{annotation}'")


def _scalar(
    kind: str,
    bounds: Bounds,
    profile: str,
    rng: random.Random,
    alphabet: str | None = None,
    length_bounds: Bounds | None = None,
) -> Any:
    if kind == "bool":
        return profile != "edge-min"
    if kind == "str":
        pool = alphabet or "abcxyz012"
        # Strings honour the declared `name.length` bounds like every other
        # collection. Before this they used a hardcoded 128 for the stress
        # profile, so a problem declaring `1 <= s.length <= 100` shipped a
        # 128-character input: valid-looking data that contradicts its own
        # Constraints line. The profile sizes themselves are unchanged (the
        # judge prints every case, and larger corpora push a suite past its
        # 256 KB output ceiling); the declared bound is applied as a clamp.
        if length_bounds is None:
            low, high = 1, 128
        else:
            low = max(1, length_bounds.minimum)
            high = max(low, min(length_bounds.maximum, 128))
        length = {"edge-min": 1, "edge-max": 2, "stress": 128}.get(
            profile, rng.randint(1, 24)
        )
        length = min(max(length, low), high)
        return "".join(rng.choice(pool) for _ in range(length))
    if kind == "any":
        return _scalar("int", bounds, profile, rng, alphabet, length_bounds)
    if profile == "edge-min":
        value = bounds.minimum
    elif profile == "edge-max":
        value = bounds.maximum
    elif profile == "stress":
        # The stress profile deliberately probes the extremes and zero, but a
        # zero outside the declared range is not an extreme, it is an invalid
        # input: it produced `k = 0` for `1 <= k <= num.length` and `n = 0`
        # for `1 <= n <= 8`. Clamp the probe into the declared interval and
        # leave the boundary values (which is all the profile needs) alone.
        candidates = (
            bounds.minimum,
            bounds.maximum,
            min(max(0, bounds.minimum), bounds.maximum),
        )
        value = rng.choice(tuple(dict.fromkeys(candidates)))
    else:
        value = rng.randint(bounds.minimum, bounds.maximum)
    return float(value) if kind == "float" else value


_COLUMN_SUBJECT = re.compile(r"\b([A-Za-z_]\w*)\[i\]\[(\d+)\]")


def _declared_row_width(statement: str, name: str) -> int:
    """Widest literal column a problem constrains (`flights[i][2]` -> 3).

    A list of records declares each field separately, and the highest field
    index it constrains is the width its rows must have. Synthesising a square
    matrix instead produced one- and two-element rows for a problem whose rows
    are triples, which crashed every implementation that reads `row[2]` — a
    crash that only surfaced once the surrounding node-id bounds stopped
    masking it with an early return. Problems that constrain only `name[i][j]`
    (matrices, adjacency lists) declare no width and keep the square shape.
    """
    width = 0
    for base, column in _COLUMN_SUBJECT.findall(statement):
        if base == name:
            width = max(width, int(column) + 1)
    return width


def _value_for(
    parameter: Parameter,
    statement: str,
    profile: str,
    rng: random.Random,
    alphabet: str | None = None,
) -> Any:
    kind, inner = _annotation_kind(parameter.annotation)
    if kind != "list":
        bounds = _find_bounds(statement, parameter.name, Bounds(-100, 100))
        if kind == "str":
            declared = _find_bounds(
                statement, f"{parameter.name}.length", Bounds(1, 100)
            )
            return _scalar(
                kind, _cap(bounds, 10_000), profile, rng, alphabet, declared
            )
        return _scalar(kind, _cap(bounds, 10_000), profile, rng, alphabet)

    length_bounds = _find_bounds(statement, f"{parameter.name}.length", Bounds(1, 12))
    length_bounds = _cap(length_bounds, 128 if profile == "stress" else 24)
    if profile == "edge-min":
        length = length_bounds.minimum
    elif profile == "edge-max" or profile == "stress":
        length = length_bounds.maximum
    else:
        length = rng.randint(length_bounds.minimum, length_bounds.maximum)
    inner_bounds = _find_bounds(
        statement, f"{parameter.name}[i]", Bounds(-100, 100)
    )
    element_kind, nested = _annotation_kind(inner or "any")
    if element_kind == "list":
        # `name[i][j]` is the subject that actually bounds a matrix cell, and
        # it is what problems declare (`0 <= grid[i][j] <= 1`). Reading only
        # `name[i]` never matched it, so declared cell bounds were silently
        # ignored and every matrix element fell back to -100..100.
        element_bounds = _cap(
            _find_bounds(statement, f"{parameter.name}[i][j]", inner_bounds), 10_000
        )
        row_kind, _ = _annotation_kind(nested or "int")
        width = _declared_row_width(statement, parameter.name)
        if width:
            return [
                [
                    _scalar(row_kind, element_bounds, profile, rng)
                    for _ in range(width)
                ]
                for _ in range(length)
            ]
        row_size = min(length, 12)
        if row_kind == "str":
            cell_lengths = _find_bounds(
                statement, f"{parameter.name}[i][j].length", Bounds(1, 100)
            )
            return [
                [
                    _scalar(row_kind, element_bounds, profile, rng, alphabet, cell_lengths)
                    for _ in range(row_size)
                ]
                for _ in range(row_size)
            ]
        return [
            [_scalar(row_kind, element_bounds, profile, rng) for _ in range(row_size)]
            for _ in range(row_size)
        ]
    element_bounds = _cap(inner_bounds, 10_000)
    if element_kind == "str":
        cell_lengths = _find_bounds(
            statement, f"{parameter.name}[i].length", Bounds(1, 100)
        )
        return [
            _scalar(element_kind, element_bounds, profile, rng, alphabet, cell_lengths)
            for _ in range(length)
        ]
    return [
        _scalar(element_kind, element_bounds, profile, rng, alphabet) for _ in range(length)
    ]


_EXPR_ATOM = r"(?:-?\d+(?:\.\d+)?|[A-Za-z_]\w*(?:\.(?:length|size))?)"
_EXPR_RE = rf"{_EXPR_ATOM}(?:\s*[-+*]\s*{_EXPR_ATOM})*"
_SUBJECT_RE = r"[A-Za-z_]\w*(?:\[\w+\]){0,2}(?:\.(?:length|size))?"

# A whole relational clause: `LOW <= subject <= HIGH`, either comparison may be
# strict. LOW and HIGH may be numbers, other parameters, `.length`, or small
# arithmetic over them (`n - 1`, `adj.length - 1`).
_RELATION = re.compile(
    rf"(?P<low>{_EXPR_RE})\s*(?P<op_low><=|<)\s*"
    rf"(?P<subject>{_SUBJECT_RE})\s*"
    rf"(?P<op_high><=|<)\s*(?P<high>{_EXPR_RE})"
)


def _evaluate(expression: str, values: dict[str, Any]) -> float | None:
    """Evaluate a bound expression against the generated values, or None."""
    total: float | None = None
    operator = "+"
    for token in re.split(r"(\s*[-+*]\s*)", expression.strip()):
        if not token.strip():
            continue
        if token.strip() in {"+", "-", "*"} and total is not None:
            operator = token.strip()
            continue
        token = token.strip()
        if re.fullmatch(r"-?\d+(?:\.\d+)?", token):
            operand: float = float(token)
        else:
            base, dot, attr = token.partition(".")
            if base not in values:
                return None
            raw = values[base]
            if dot:
                if not isinstance(raw, (list, str, dict)):
                    return None
                operand = float(len(raw))
            elif isinstance(raw, bool) or not isinstance(raw, (int, float)):
                return None
            else:
                operand = float(raw)
        if total is None:
            total = -operand if operator == "-" else operand
            continue
        if operator == "+":
            total += operand
        elif operator == "-":
            total -= operand
        else:
            total *= operand
    return total


def _clamp(value: Any, low: float | None, high: float | None, strict_low: bool, strict_high: bool) -> Any:
    """Clamp an integer (or float) into a resolved bound, or leave it alone."""
    if low is None or high is None:
        return value
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return value
    if isinstance(value, int):
        if strict_low:
            low += 1
        if strict_high:
            high -= 1
    if low > high:
        return value
    clamped = min(max(float(value), low), high)
    return int(clamped) if isinstance(value, int) and clamped == int(clamped) else clamped


def _apply_to_subject(
    subject: str,
    low: float | None,
    high: float | None,
    strict_low: bool,
    strict_high: bool,
    values: dict[str, Any],
) -> None:
    """Enforce one relational clause on the generated value it constrains."""
    if subject.endswith(".length") or subject.endswith(".size"):
        # A length bound is enforced by trimming the longer collection, which
        # is what keeps one corpus from overrunning a sibling it must fit in
        # (`1 <= needle.length <= haystack.length`). Only truncation is safe:
        # padding would invent elements the solutions never agreed on. A row
        # length (`flights[i].length`) is not this case: trimming the outer
        # list would delete rows rather than shorten them, so it is left to the
        # implementations to tolerate a short row.
        head = re.match(r"([A-Za-z_]\w*)\s*(?:\.(?:length|size))?\Z", subject)
        if head is not None:
            container = values.get(head.group(1))
            if isinstance(container, (list, str)) and high is not None:
                limit = int(high) - 1 if strict_high else int(high)
                if limit >= 1 and len(container) > limit:
                    values[head.group(1)] = container[:limit]
        return
    head = re.match(r"([A-Za-z_]\w*)", subject)
    if head is None:
        return
    name = head.group(1)
    if name not in values:
        return
    indices = re.findall(r"\[(\w+)\]", subject)
    container = values[name]
    if not indices:
        values[name] = _clamp(container, low, high, strict_low, strict_high)
        return
    if not isinstance(container, list):
        return
    if len(indices) == 1:
        for position, item in enumerate(container):
            container[position] = _clamp(item, low, high, strict_low, strict_high)
        return
    column = indices[1]
    for row in container:
        if not isinstance(row, list):
            continue
        if column.isdigit():
            # `flights[i][0]`: a literal column index bounds one field of every
            # row, so only that column is constrained.
            index = int(column)
            if 0 <= index < len(row):
                row[index] = _clamp(row[index], low, high, strict_low, strict_high)
            continue
        for position, cell in enumerate(row):
            row[position] = _clamp(cell, low, high, strict_low, strict_high)


def _apply_relative_bounds(
    values: dict[str, Any], statement: str, passes: int = 2
) -> None:
    """Enforce every stated relational bound on the generated values.

    Bounds that reference another parameter (`1 <= k <= num.length`,
    `0 <= src <= n - 1`, `0 <= adj[i][j] <= adj.length - 1`) cannot be resolved
    while a value is being generated, because the parameter they reference may
    not exist yet. They are resolved here instead, once the whole call has been
    produced. Clamping is what keeps the shipped test data consistent with the
    Constraints line; without it the value silently falls back to -100..100.

    Two passes because a clause may reference a parameter that a later clause
    narrows (n is bounded before the flights that depend on it).
    """
    for _ in range(max(1, passes)):
        for match in _RELATION.finditer(statement):
            low = _evaluate(match.group("low"), values)
            high = _evaluate(match.group("high"), values)
            _apply_to_subject(
                match.group("subject"),
                low,
                high,
                match.group("op_low") == "<",
                match.group("op_high") == "<",
                values,
            )


_SENTENCE = re.compile(r"[^.\n]+")
# Problems whose values must not be re-drawn even though their prose declares a
# premise, because the values are not independent of each other or of a layout
# convention. Redrawing each parameter separately satisfies the words and
# breaks the problem.
_PREMISE_EXEMPT: dict[str, str] = {
    "merge-sorted-array": (
        "`nums1` is a buffer: only its first `m` entries are the sorted input and "
        "the tail is scratch space the merge writes into, so sorting the whole "
        "array destroys the input the solution reads"
    ),
    "construct-from-preorder-inorder": (
        "`preorder` and `inorder` are two traversals of the SAME tree, so they "
        "must share one value set; drawing distinct values for each separately "
        "makes them describe different trees and the solution recurses without "
        "terminating"
    ),
    "combination-sum": (
        "with `candidates` made distinct the Python reference solution exhausts "
        "its limits on the larger search space (target 40 over 20 candidates), so "
        "the premises cannot be honoured until that solution is fixed"
    ),
}
_ROTATED_PHRASE = re.compile(r"\brotated\b", re.IGNORECASE)
_ROWWISE_PHRASE = re.compile(
    r"first integer of each row is greater than the last integer", re.IGNORECASE
)
# Sentences that are about the answer or an example rather than the input.
# Deliberately narrow: "return" and "output" appear in ordinary premise
# sentences ("Given an array of integers `nums` arranged in non-decreasing
# order, return a new array..."), so excluding on those words discards real
# premises. "the answer is" and an explicit assignment are the reliable tells.
_CLAIM_SENTENCE = re.compile(r"\bthe answer is\b|\bfor example\b|\be\.g\.", re.IGNORECASE)
# A premise is a *statement about the input*, not an instruction to the solver.
# "`nums` is sorted in ascending order" declares one; "Sort `nums` in ascending
# order" is the task, and sorting its input for it would leave nothing to test.
# Only copular and reduced-relative forms count, and the parameter must come
# first in the clause, so an imperative cannot match.
_NAME = "{name}"
_SORTED_PREMISE = (
    # "nums is sorted in ascending order", "nums which is sorted",
    # "nums sorted in non-decreasing order" -- but never "non-increasing",
    # which is the opposite claim.
    rf"\b{_NAME}\b[^.]{{0,40}}?\b(?:which\s+|that\s+)?(?:is\s+|are\s+)?sorted\b"
    rf"(?!\s+in\s+non-?increasing)"
    # "nums are non-decreasing", "the values are strictly increasing"
    rf"|\b{_NAME}\b[^.]{{0,30}}?\b(?:is|are)\b[^.]{{0,20}}?\b(?:strictly increasing|non-?decreasing)\b"
    # "an array nums arranged in non-decreasing numerical order"
    rf"|\b{_NAME}\b[^.]{{0,30}}?\barranged\s+in\s+(?:non-?decreasing|ascending)\b"
)
_UNIQUE_PREMISE = (
    # "All elements of nums are unique", "candidates are distinct",
    # "nums contains distinct values". The lookbehinds keep the sentence
    # "subarrays of nums that contain exactly k distinct values" out: there the
    # distinctness belongs to k, and nums is only the object of "of".
    rf"(?<!of )(?<!in )\b{_NAME}\b[^.]{{0,40}}?"
    rf"\b(?:is|are|has|have|contains?)\b[^.]{{0,30}}?\b(?:unique|distinct)\b"
    # "an array nums of distinct integers"
    rf"|\b{_NAME}\b\s+of\s+(?:unique|distinct)\b"
    # "All integers of nums are unique", "the values in nums are distinct"
    rf"|\b(?:elements|integers|values|numbers)\s+(?:of|in)\s+{_NAME}\b"
    rf"[^.]{{0,20}}?\b(?:unique|distinct)\b"
    # "nums sorted in ascending order with distinct values"
    rf"|\b{_NAME}\b[^.]{{0,40}}?\bwith\s+(?:unique|distinct)\b"
    # "a sorted array of distinct integers nums" -- the qualifier comes first
    # and the name follows, so long as it is not an element reference like
    # nums[i] in "find all unique triplets [nums[i], ...]".
    rf"|\b(?:unique|distinct)\b[^.]{{0,40}}?\b{_NAME}\b(?!\s*\[)"
)


def _declares(template: str, name: str, sentences: list[str]) -> bool:
    """True when a sentence states a premise of this form about `name`."""
    # str.replace, not str.format: the templates carry regex quantifiers like
    # `{0,60}`, which format() would try to read as its own fields.
    pattern = re.compile(template.replace("{name}", re.escape(name)), re.IGNORECASE)
    return any(pattern.search(sentence) for sentence in sentences)


def _distinct_sorted_values(bounds: Bounds, count: int) -> list[int]:
    """`count` distinct integers inside `bounds`, ascending.

    Used where a statement declares its array sorted *and* unique: re-sampling
    is the only way to satisfy both, because the boundary profiles would
    otherwise fill the array with one repeated value.
    """
    low, high = int(bounds.minimum), int(bounds.maximum)
    span = high - low
    if count < 1:
        return []
    if span + 1 < count:
        return [low + offset for offset in range(span + 1)]
    step = max(1, span // count)
    return [low + index * step for index in range(count)]


def _apply_premises(
    values: dict[str, Any],
    parameters: Sequence[Parameter],
    statement: str,
    rng: random.Random,
    slug: str | None = None,
) -> None:
    """Reshape generated values to satisfy premises the statement declares.

    Some problems are only well-posed on a restricted input space: a binary
    search needs the array sorted with distinct values, a rotated-array search
    needs an actual rotation, and a row-major matrix search needs every row to
    continue where the previous one ended. The generator used to sample those
    parameters freely, and the failure is subtle rather than loud: a linear
    scan and a binary search agree on almost every array and disagree only on
    the duplicates the edge profile produces, so the problem was "verified"
    while its stated premise was false.

    Only premises stated in prose are honoured, and only for the parameter the
    sentence names, so a problem that says nothing keeps exactly the values it
    gets today.
    """
    if slug in _PREMISE_EXEMPT:
        return
    kinds = {parameter.name: _annotation_kind(parameter.annotation) for parameter in parameters}
    # A worked example is not a premise. "For `nums1 = [3, 1]` and `nums2 = [2]`
    # the answer is 2, from the sorted order 1, 2, 3" mentions both an
    # assignment and the derived order, and reading it as a premise would sort
    # an array the statement explicitly says may arrive in any order.
    sentences = [
        sentence
        for sentence in _SENTENCE.findall(statement.replace("`", ""))
        if not _CLAIM_SENTENCE.search(sentence)
        and not any(
            re.search(
                rf"(?<![A-Za-z_]){re.escape(parameter.name)}(?![A-Za-z_])\s*=",
                sentence,
            )
            for parameter in parameters
        )
    ]

    for parameter in parameters:
        name = parameter.name
        if name not in values:
            continue
        kind, inner = kinds[name]
        if kind != "list":
            continue
        container = values[name]
        if not isinstance(container, list) or not container:
            continue
        element_kind, _nested = _annotation_kind(inner or "any")
        if element_kind != "int":
            continue

        wants_sorted = _declares(_SORTED_PREMISE, name, sentences)
        wants_unique = _declares(_UNIQUE_PREMISE, name, sentences)
        wants_rotated = wants_sorted and any(
            _ROTATED_PHRASE.search(sentence) and re.search(
                rf"(?<![A-Za-z_]){re.escape(name)}(?![A-Za-z_])", sentence
            )
            for sentence in sentences
        )
        if not (wants_sorted or wants_unique or wants_rotated):
            continue

        bounds = _cap(_find_bounds(statement, f"{name}[i]", Bounds(-100, 100)), 10_000)
        if wants_unique:
            # Distinct values cannot be conjured from a list the boundary
            # profile filled with one repeated value, so the list is re-drawn
            # from its declared range.
            container = _distinct_sorted_values(bounds, len(container))
        elif wants_sorted:
            container = sorted(container)
        if wants_rotated and len(container) > 1:
            pivot = rng.randrange(len(container))
            container = container[pivot:] + container[:pivot]
        values[name] = container

    if not any(_ROWWISE_PHRASE.search(sentence) for sentence in sentences):
        return

    for parameter in parameters:
        name = parameter.name
        container = values.get(name)
        kind, inner = kinds[name]
        if kind != "list" or not isinstance(container, list) or not container:
            continue
        if _annotation_kind(inner or "any")[0] != "list":
            continue
        rows = len(container)
        width = len(container[0]) if isinstance(container[0], list) else 0
        if rows < 1 or width < 1:
            continue
        cell_bounds = _cap(
            _find_bounds(statement, f"{name}[i][j]", Bounds(-100, 100)), 10_000
        )
        flat = _distinct_sorted_values(cell_bounds, rows * width)
        if len(flat) < rows * width:
            continue
        values[name] = [
            flat[row * width : (row + 1) * width] for row in range(rows)
        ]


def generate_inputs(
    spec: ProblemSpec, random_cases: int = 16, stress_cases: int = 4
) -> list[dict[str, Any]]:
    """Build deduplicated edge, randomized, and stress calls from an authored spec."""
    if random_cases < 1 or stress_cases < 1:
        raise ValueError("PAF needs at least one random case and one stress case")
    rng = random.Random(spec.seed)
    profiles = (
        ["edge-min", "edge-max"] + ["random"] * random_cases + ["stress"] * stress_cases
    )
    seen: set[str] = set()
    generated: list[dict[str, Any]] = []
    for profile in profiles:
        values = {
            parameter.name: _value_for(
                parameter,
                spec.statement,
                profile,
                rng,
                spec.string_alphabets.get(parameter.name),
            )
            for parameter in spec.parsed_signature.parameters
        }
        _apply_relative_bounds(values, spec.statement)
        _apply_premises(
            values,
            spec.parsed_signature.parameters,
            spec.statement,
            rng,
            slug=spec.resolved_slug,
        )
        input_values = [
            values[parameter.name] for parameter in spec.parsed_signature.parameters
        ]
        fingerprint = json.dumps(input_values, sort_keys=True, separators=(",", ":"))
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        generated.append(
            {
                "label": f"{profile}-{len(generated) + 1}",
                "input": input_values,
                "expected": None,
                "isSample": len(generated) < 2,
            }
        )
    if len(generated) < 3:
        raise ValueError(
            "Signature and constraints produced fewer than three distinct test inputs"
        )
    return generated
