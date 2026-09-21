"""Deterministic edge, random, and stress input generation for PAF specs."""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from typing import Any

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
    if clean in {"float", "number"}:
        return "float", None
    if clean in {"bool", "boolean"}:
        return "bool", None
    if clean in {"str", "string"}:
        return "str", None
    if clean in {"any", "object", "json"}:
        return "any", None
    raise ValueError(f"PAF cannot generate JSON inputs for annotation '{annotation}'")


def _scalar(kind: str, bounds: Bounds, profile: str, rng: random.Random) -> Any:
    if kind == "bool":
        return profile != "edge-min"
    if kind == "str":
        length = {"edge-min": 1, "edge-max": 2, "stress": 128}.get(
            profile, rng.randint(1, 24)
        )
        return "".join(rng.choice("abcxyz012") for _ in range(length))
    if kind == "any":
        return _scalar("int", bounds, profile, rng)
    if profile == "edge-min":
        value = bounds.minimum
    elif profile == "edge-max":
        value = bounds.maximum
    elif profile == "stress":
        value = rng.choice((bounds.minimum, bounds.maximum, 0))
    else:
        value = rng.randint(bounds.minimum, bounds.maximum)
    return float(value) if kind == "float" else value


def _value_for(
    parameter: Parameter, statement: str, profile: str, rng: random.Random
) -> Any:
    kind, inner = _annotation_kind(parameter.annotation)
    if kind != "list":
        bounds = _find_bounds(statement, parameter.name, Bounds(-100, 100))
        return _scalar(kind, _cap(bounds, 10_000), profile, rng)

    length_bounds = _find_bounds(statement, f"{parameter.name}.length", Bounds(1, 12))
    length_bounds = _cap(length_bounds, 128 if profile == "stress" else 24)
    if profile == "edge-min":
        length = length_bounds.minimum
    elif profile == "edge-max" or profile == "stress":
        length = length_bounds.maximum
    else:
        length = rng.randint(length_bounds.minimum, length_bounds.maximum)
    element_bounds = _cap(
        _find_bounds(statement, f"{parameter.name}[i]", Bounds(-100, 100)), 10_000
    )
    element_kind, nested = _annotation_kind(inner or "any")
    if element_kind == "list":
        row_kind, _ = _annotation_kind(nested or "int")
        row_size = min(length, 12)
        return [
            [_scalar(row_kind, element_bounds, profile, rng) for _ in range(row_size)]
            for _ in range(row_size)
        ]
    return [_scalar(element_kind, element_bounds, profile, rng) for _ in range(length)]


def _apply_cross_parameter_constraints(values: dict[str, Any], statement: str) -> None:
    """Honor simple relations such as ``1 <= k <= nums.length`` when present."""
    relation = re.compile(
        rf"({_NUMBER})\s*<=\s*([A-Za-z_]\w*)\s*<=\s*([A-Za-z_]\w*)\.length",
        re.IGNORECASE,
    )
    for minimum, scalar_name, collection_name in relation.findall(statement):
        collection = values.get(collection_name)
        scalar = values.get(scalar_name)
        if isinstance(collection, list) and isinstance(scalar, int):
            values[scalar_name] = max(_number(minimum), min(scalar, len(collection)))


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
            parameter.name: _value_for(parameter, spec.statement, profile, rng)
            for parameter in spec.parsed_signature.parameters
        }
        _apply_cross_parameter_constraints(values, spec.statement)
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
