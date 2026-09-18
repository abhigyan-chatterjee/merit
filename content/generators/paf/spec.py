"""Data structures and signature parsing for the Problem Authoring Framework."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Language = Literal["python", "javascript"]
Difficulty = Literal["Easy", "Medium", "Hard"]


@dataclass(frozen=True)
class Algorithm:
    """One author-supplied implementation and its displayed complexity."""

    code: str
    complexity: str = "Complexity profiled by PAF"
    language: Language = "python"

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("Algorithm code cannot be empty")
        if not self.complexity.strip():
            raise ValueError("Algorithm complexity cannot be empty")


@dataclass(frozen=True)
class Parameter:
    """A parsed function argument, retaining its source-language annotation."""

    name: str
    annotation: str


@dataclass(frozen=True)
class ParsedSignature:
    """Normalised information extracted from an author-facing signature."""

    name: str
    parameters: tuple[Parameter, ...]
    language: Language


@dataclass(frozen=True)
class ProblemSpec:
    """The four author inputs plus safe production-artifact defaults.

    ``signature`` accepts either ``def solve(nums: list[int]) -> int`` or
    ``function solve(nums: number[])``. Python and TypeScript-style JavaScript
    annotations drive automatic test-input synthesis.
    Bounds such as ``1 <= nums.length <= 100`` in the Markdown statement are
    recognised automatically.
    """

    signature: str
    statement: str
    brute_force: Algorithm
    optimal: Algorithm
    topic: str = "data-structures"
    difficulty: Difficulty = "Medium"
    pattern: str = "Problem Authoring Framework generated"
    time_limit_ms: int = 2000
    seed: int = 42
    title: str | None = None
    slug: str | None = None
    editorial: dict[str, str] | None = None
    reading_links: list[str] = field(default_factory=list)
    hints: list[str] | None = None

    @classmethod
    def from_author_inputs(
        cls,
        function_signature: str,
        markdown_statement: str,
        brute_force: Algorithm | str,
        optimal: Algorithm | str,
        **metadata: Any,
    ) -> ProblemSpec:
        """Named-argument convenience form matching the authoring vocabulary."""
        return cls(
            signature=function_signature,
            statement=markdown_statement,
            brute_force=brute_force
            if isinstance(brute_force, Algorithm)
            else Algorithm(brute_force),
            optimal=optimal if isinstance(optimal, Algorithm) else Algorithm(optimal),
            **metadata,
        )

    def __post_init__(self) -> None:
        if len(self.statement.strip()) < 10:
            raise ValueError("Problem statement must contain at least 10 characters")
        if self.brute_force.language != self.optimal.language:
            raise ValueError(
                "Brute-force and optimal implementations must use one language"
            )
        parsed = parse_signature(self.signature)
        if parsed.language != self.optimal.language:
            raise ValueError(
                "Signature language must match the supplied algorithm language "
                f"({parsed.language} != {self.optimal.language})"
            )

    @property
    def parsed_signature(self) -> ParsedSignature:
        return parse_signature(self.signature)

    @property
    def function_name(self) -> str:
        return self.parsed_signature.name

    @property
    def resolved_slug(self) -> str:
        if self.slug:
            return self.slug
        words = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", self.function_name)
        return re.sub(r"[^a-z0-9]+", "-", words.lower()).strip("-")

    @property
    def resolved_title(self) -> str:
        if self.title:
            return self.title
        return self.function_name.replace("_", " ").replace("-", " ").title()


@dataclass
class ValidationReport:
    """Execution evidence captured before an artifact may be marked verified."""

    test_cases: list[dict[str, Any]]
    brute_force_runtime_ms: float
    optimal_runtime_ms: float
    brute_force_case_runtimes_ms: list[float]
    optimal_case_runtimes_ms: list[float]

    @property
    def total_cases(self) -> int:
        return len(self.test_cases)


@dataclass
class GeneratedProblem:
    """A schema-ready verified problem and its PAF validation evidence."""

    data: dict[str, Any]
    report: ValidationReport

    def write_to(self, output_dir: Path) -> Path:
        """Write the production JSON file after successful verification only."""
        import json

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{self.data['slug']}.json"
        output_path.write_text(json.dumps(self.data, indent=2) + "\n", encoding="utf-8")
        return output_path


_PYTHON_SIGNATURE = re.compile(
    r"^\s*def\s+(?P<name>[A-Za-z_]\w*)\s*\((?P<params>.*)\)\s*"
    r"(?:->\s*[^:]+)?\s*:?\s*$"
)
_JS_SIGNATURE = re.compile(
    r"^\s*(?:function\s+)?(?P<name>[A-Za-z_$][\w$]*)\s*\((?P<params>.*)\)\s*"
    r"(?:\{)?\s*$"
)


def _split_parameters(raw: str) -> list[str]:
    """Split parameters without breaking generic annotations such as dict[str, int]."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for char in raw:
        if char in "[({<":
            depth += 1
        elif char in "])}>":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if "".join(current).strip():
        parts.append("".join(current).strip())
    return parts


def parse_signature(signature: str) -> ParsedSignature:
    """Parse a Python or JavaScript function signature into JSON-call arguments."""
    match = _PYTHON_SIGNATURE.match(signature)
    language: Language
    if match:
        language = "python"
    else:
        match = _JS_SIGNATURE.match(signature)
        language = "javascript"
    if not match:
        raise ValueError(
            "Signature must be a Python `def name(args) -> result` or JavaScript "
            "`function name(args)` declaration"
        )

    parameters: list[Parameter] = []
    for raw_param in _split_parameters(match.group("params")):
        if raw_param.startswith(("*", "/")):
            raise ValueError(
                "Variadic and positional-only parameters are not supported by PAF"
            )
        name_and_annotation = raw_param.split("=", 1)[0].strip()
        if language == "python":
            name, separator, annotation = name_and_annotation.partition(":")
            if not separator or not annotation.strip():
                raise ValueError(
                    f"Python parameter '{raw_param}' needs a type annotation for test generation"
                )
        else:
            name, separator, annotation = name_and_annotation.partition(":")
            if not separator or not annotation.strip():
                raise ValueError(
                    f"JavaScript parameter '{raw_param}' needs a TypeScript-style "
                    "type annotation for test generation"
                )
        if not re.match(r"^[A-Za-z_$][\w$]*$", name.strip()):
            raise ValueError(f"Invalid parameter name '{name.strip()}'")
        parameters.append(Parameter(name=name.strip(), annotation=annotation.strip()))
    return ParsedSignature(match.group("name"), tuple(parameters), language)
