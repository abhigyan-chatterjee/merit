"""Focused PAF tests; run with ``python -m unittest content.generators.paf.test_paf``."""

import asyncio
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))
sys.path.insert(0, str(REPO_ROOT))

from content.generators.paf import Algorithm, ProblemSpec, build_verified_problem
from content.generators.paf.inputs import generate_inputs
from content.validators.schema import ProblemSchema

BRUTE_FORCE = """def max_profit(prices):
    best = 0
    for left in range(len(prices)):
        for right in range(left + 1, len(prices)):
            best = max(best, prices[right] - prices[left])
    return best
"""

OPTIMAL = """def max_profit(prices):
    lowest = prices[0]
    best = 0
    for price in prices:
        lowest = min(lowest, price)
        best = max(best, price - lowest)
    return best
"""


def make_spec() -> ProblemSpec:
    return ProblemSpec(
        signature="def max_profit(prices: list[int]) -> int",
        statement=(
            "# Maximum Profit\n\nReturn the maximum later-minus-earlier price, or zero.\n\n"
            "Constraints: 1 <= prices.length <= 100 and 0 <= prices[i] <= 1000."
        ),
        brute_force=Algorithm(BRUTE_FORCE, "Time: O(n²) | Space: O(1)"),
        optimal=Algorithm(OPTIMAL, "Time: O(n) | Space: O(1)"),
        topic="arrays-hashing",
        difficulty="Easy",
    )


class PafTests(unittest.TestCase):
    def test_input_generation_uses_markdown_bounds_and_is_deterministic(self) -> None:
        first = generate_inputs(make_spec(), random_cases=3, stress_cases=1)
        second = generate_inputs(make_spec(), random_cases=3, stress_cases=1)
        self.assertEqual(first, second)
        self.assertTrue(all(len(case["input"][0]) >= 1 for case in first))
        self.assertTrue(
            all(0 <= value <= 1000 for case in first for value in case["input"][0])
        )

    def test_builds_schema_valid_verified_problem_with_profiles(self) -> None:
        result = asyncio.run(
            build_verified_problem(make_spec(), random_cases=3, stress_cases=1)
        )
        problem = ProblemSchema(**result.data)
        self.assertEqual(problem.review_status, "verified")
        self.assertGreaterEqual(result.report.total_cases, 3)
        self.assertEqual(
            len(result.report.brute_force_case_runtimes_ms), result.report.total_cases
        )
        self.assertEqual(
            len(result.report.optimal_case_runtimes_ms), result.report.total_cases
        )
        self.assertEqual(
            result.data["pafVerification"]["generatedCaseCount"],
            result.report.total_cases,
        )

    def test_builds_javascript_problem_from_a_typed_signature(self) -> None:
        spec = ProblemSpec(
            signature="function array_sum(values: number[])",
            statement=(
                "Return the sum of all values. Constraints: 1 <= values.length <= 20 "
                "and 0 <= values[i] <= 9."
            ),
            brute_force=Algorithm(
                "function array_sum(values) { let total = 0; for (let i = 0; i < values.length; i++) total += values[i]; return total; }",
                language="javascript",
            ),
            optimal=Algorithm(
                "function array_sum(values) { return values.reduce((total, value) => total + value, 0); }",
                language="javascript",
            ),
        )
        result = asyncio.run(
            build_verified_problem(spec, random_cases=2, stress_cases=1)
        )
        self.assertEqual(result.data["functionName"], "array_sum")
        self.assertEqual(result.data["solutions"][1]["language"], "javascript")

    def test_rejects_disagreeing_algorithms(self) -> None:
        source = make_spec()
        broken = ProblemSpec(
            signature=source.signature,
            statement=source.statement,
            brute_force=Algorithm(
                "def max_profit(prices):\n    return -1\n", "Time: O(1) | Space: O(1)"
            ),
            optimal=source.optimal,
        )
        with self.assertRaisesRegex(ValueError, "Brute-force implementation failed"):
            asyncio.run(build_verified_problem(broken, random_cases=2, stress_cases=1))


if __name__ == "__main__":
    unittest.main()
