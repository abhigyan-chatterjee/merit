# Problem Authoring Framework (PAF)

PAF makes a verified problem from four author inputs: a typed function
signature, its Markdown statement (including constraints), a brute-force
implementation, and an optimal implementation. It derives boundary, random,
and stress inputs from signature types and Markdown bounds; verifies both
solutions using the production judge; captures runtime profiles; and writes a
`reviewStatus: "verified"` JSON artifact only if every case agrees.

```python
from pathlib import Path

from content.generators.paf import Algorithm, ProblemSpec, build_problem

spec = ProblemSpec(
    signature="def max_profit(prices: list[int]) -> int",
    statement="""# Maximum Profit

Return the greatest later-minus-earlier value in `prices`, or `0`.

Constraints: `1 <= prices.length <= 100` and `0 <= prices[i] <= 1000`.
""",
    brute_force=Algorithm(
        """def max_profit(prices):
    return max([0] + [prices[j] - prices[i] for i in range(len(prices)) for j in range(i + 1, len(prices))])
""",
        "Time: O(n²) | Space: O(1)",
    ),
    optimal=Algorithm(
        """def max_profit(prices):
    lowest, best = prices[0], 0
    for price in prices:
        lowest = min(lowest, price)
        best = max(best, price - lowest)
    return best
""",
        "Time: O(n) | Space: O(1)",
    ),
    topic="arrays-hashing",
    difficulty="Easy",
)

problem = build_problem(spec)
problem.write_to(Path("content/problems"))
print(problem.report.optimal_runtime_ms)
```

Python signatures must annotate every argument with a supported JSON type:
`int`, `float`, `bool`, `str`, `list[T]`, or `list[list[T]]`. JavaScript
signatures use equivalent TypeScript-style types, such as
`function solve(values: number[])`; the implementation itself remains plain
JavaScript. Write numeric, `.length`, and `values[i]` bounds in the Markdown
statement when an algorithm requires them.
