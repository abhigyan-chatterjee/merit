"""PAF verification and production JSON assembly."""

from __future__ import annotations

import asyncio
import copy
import json
from typing import Any

from content.generators.paf.inputs import generate_inputs
from content.generators.paf.spec import GeneratedProblem, ProblemSpec, ValidationReport


def _starter_code(spec: ProblemSpec, language: str) -> str:
    names = ", ".join(parameter.name for parameter in spec.parsed_signature.parameters)
    if language == "python":
        return (
            f"def {spec.function_name}({names}):\n"
            "    # Write your solution here\n"
            "    raise NotImplementedError\n"
        )
    return (
        f"function {spec.function_name}({names}) {{\n"
        "  // Write your solution here\n"
        "  throw new Error('Not implemented');\n"
        "}\n"
    )


def _display_input(spec: ProblemSpec, values: list[Any]) -> str:
    return ", ".join(
        f"{parameter.name} = {json.dumps(value, ensure_ascii=False)}"
        for parameter, value in zip(
            spec.parsed_signature.parameters, values, strict=True
        )
    )


def _examples(spec: ProblemSpec, cases: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "input": _display_input(spec, case["input"]),
            "output": json.dumps(case["expected"], ensure_ascii=False),
            "explanation": "Generated from the verified optimal implementation.",
        }
        for case in cases[:2]
    ]


def _constraints(spec: ProblemSpec) -> list[str]:
    signature = spec.signature.strip().rstrip(":{").strip()
    return [
        f"Function signature: `{signature}`.",
        "Inputs are JSON-serializable values satisfying the bounds stated above.",
    ]


_DEFAULT_HINTS = [
    "First express the direct brute-force search over the input.",
    "Then identify the repeated work that the optimal implementation eliminates.",
]


def _hints(spec: ProblemSpec) -> list[str]:
    return list(spec.hints) if spec.hints is not None else list(_DEFAULT_HINTS)


def _failure_message(role: str, result: Any) -> str:
    details = result.compile_output.strip()
    failures = [
        f"{row.get('label')}: {row.get('error') or 'output did not match expected'}"
        for row in result.test_results
        if not row.get("passed")
    ]
    suffix = "; ".join(failures)
    return f"{role} implementation failed ({result.verdict})" + (
        f": {details or suffix}" if details or suffix else ""
    )


async def _execute(code: str, spec: ProblemSpec, cases: list[dict[str, Any]]) -> Any:
    """Run author code with the same judge used by content verification."""
    from app.services.judge import execute_code

    return await execute_code(
        language=spec.optimal.language,
        code=code,
        function_name=spec.function_name,
        test_cases=cases,
        time_limit_ms=spec.time_limit_ms,
    )


async def verify_problem_spec(
    spec: ProblemSpec,
    random_cases: int = 16,
    stress_cases: int = 4,
) -> ValidationReport:
    """Compare both solutions and profile them against generated test inputs."""
    cases = generate_inputs(spec, random_cases=random_cases, stress_cases=stress_cases)
    optimal_probe = await _execute(spec.optimal.code, spec, cases)
    if optimal_probe.compile_output or len(optimal_probe.test_results) != len(cases):
        raise ValueError(_failure_message("Optimal", optimal_probe))
    expected_values: list[Any] = []
    for result in optimal_probe.test_results:
        if result.get("error") is not None or "actual" not in result:
            raise ValueError(_failure_message("Optimal", optimal_probe))
        expected_values.append(result["actual"])
    for case, expected in zip(cases, expected_values, strict=True):
        case["expected"] = expected

    brute_result, optimal_result = await asyncio.gather(
        _execute(spec.brute_force.code, spec, copy.deepcopy(cases)),
        _execute(spec.optimal.code, spec, copy.deepcopy(cases)),
    )
    if brute_result.verdict != "AC":
        raise ValueError(_failure_message("Brute-force", brute_result))
    if optimal_result.verdict != "AC":
        raise ValueError(_failure_message("Optimal", optimal_result))

    return ValidationReport(
        test_cases=cases,
        brute_force_runtime_ms=brute_result.runtime_ms,
        optimal_runtime_ms=optimal_result.runtime_ms,
        brute_force_case_runtimes_ms=[
            row["runtime_ms"] for row in brute_result.test_results
        ],
        optimal_case_runtimes_ms=[
            row["runtime_ms"] for row in optimal_result.test_results
        ],
    )


async def build_verified_problem(
    spec: ProblemSpec,
    random_cases: int = 16,
    stress_cases: int = 4,
) -> GeneratedProblem:
    """Return a production-ready JSON problem only after full PAF verification."""
    report = await verify_problem_spec(
        spec, random_cases=random_cases, stress_cases=stress_cases
    )
    language = spec.optimal.language
    data: dict[str, Any] = {
        "slug": spec.resolved_slug,
        "title": spec.resolved_title,
        "topic": spec.topic,
        "difficulty": spec.difficulty,
        "pattern": spec.pattern,
        "statement": spec.statement,
        "examples": _examples(spec, report.test_cases),
        "constraints": _constraints(spec),
        "hints": _hints(spec),
        "editorial": dict(spec.editorial) if spec.editorial is not None else None,
        "reading_links": list(spec.reading_links),
        "starterCode": {
            "javascript": _starter_code(spec, "javascript"),
            "python": _starter_code(spec, "python"),
        },
        "functionName": spec.function_name,
        "timeLimitMs": spec.time_limit_ms,
        "reviewStatus": "verified",
        "pafVerification": {
            "seed": spec.seed,
            "generatedCaseCount": report.total_cases,
            "bruteForceRuntimeMs": report.brute_force_runtime_ms,
            "optimalRuntimeMs": report.optimal_runtime_ms,
        },
        "testCases": report.test_cases,
        "solutions": [
            {
                "title": "Brute Force",
                "complexity": spec.brute_force.complexity,
                "language": language,
                "code": spec.brute_force.code,
                "isReference": False,
            },
            {
                "title": "Optimal",
                "complexity": spec.optimal.complexity,
                "language": language,
                "code": spec.optimal.code,
                "isReference": True,
            },
        ],
    }
    return GeneratedProblem(data=data, report=report)


def build_problem(
    spec: ProblemSpec,
    random_cases: int = 16,
    stress_cases: int = 4,
) -> GeneratedProblem:
    """Synchronous convenience wrapper for scripts and one-off authoring tools."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(build_verified_problem(spec, random_cases, stress_cases))
    raise RuntimeError("Use 'await build_verified_problem(...)' from an async context")


# Verb aliases make the framework discoverable alongside QAF's generate_* API.
generate_problem = build_problem
generate_verified_problem = build_verified_problem
