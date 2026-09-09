"""Generator for Time and Space Complexity Analysis questions with exact mathematical oracles."""

import random
from content.generators.base import GeneratedQuestion, make_question


def generate_time_complexity_questions(count: int = 120, seed: int = 42) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []

    # 1. Master Theorem Recurrences
    recurrence_cases = [
        ("T(n) = 2T(n/2) + O(n)", "O(n log n)", ["O(n)", "O(n²)", "O(log n)", "O(n log² n)"], "Case 2 of Master Theorem: a=2, b=2, log_b(a)=1, f(n)=Θ(n^1). Hence T(n) = Θ(n log n).", "Medium"),
        ("T(n) = 4T(n/2) + O(n)", "O(n²)", ["O(n log n)", "O(n³)", "O(n)", "O(2^n)"], "Case 1 of Master Theorem: a=4, b=2, log_b(a)=2. Since f(n)=O(n^1) where 1 < 2, T(n) = Θ(n²).", "Medium"),
        ("T(n) = 2T(n/2) + O(n²)", "O(n²)", ["O(n log n)", "O(n³)", "O(n)", "O(n log² n)"], "Case 3 of Master Theorem: a=2, b=2, log_b(a)=1. Since f(n)=Ω(n²), regularity condition holds, T(n) = Θ(n²).", "Medium"),
        ("T(n) = 8T(n/2) + O(n²)", "O(n³)", ["O(n²)", "O(n log n)", "O(n⁴)", "O(2^n)"], "Case 1 of Master Theorem: a=8, b=2, log_2(8)=3. Since f(n)=O(n²), T(n) = Θ(n³).", "Hard"),
        ("T(n) = 3T(n/3) + O(1)", "O(n)", ["O(log n)", "O(n log n)", "O(1)", "O(n²)"], "Case 1 of Master Theorem: a=3, b=3, log_3(3)=1. Since f(n)=O(1)=O(n^0), T(n) = Θ(n).", "Easy"),
        ("T(n) = T(n-1) + O(1)", "O(n)", ["O(log n)", "O(n²)", "O(1)", "O(2^n)"], "Unrolling the recurrence yields 1 + 1 + ... + 1 (n times) = Θ(n).", "Easy"),
        ("T(n) = T(n-1) + O(n)", "O(n²)", ["O(n)", "O(n log n)", "O(n³)", "O(2^n)"], "Unrolling gives the arithmetic series n + (n-1) + ... + 1 = n(n+1)/2 = Θ(n²).", "Easy"),
        ("T(n) = 2T(n-1) + O(1)", "O(2^n)", ["O(n²)", "O(n log n)", "O(n!)", "O(n)"], "A full binary recursion tree of depth n with constant work per node gives 2^0 + 2^1 + ... + 2^n = 2^(n+1) - 1 = Θ(2^n).", "Medium"),
    ]

    q_idx = 1
    for rec, ans, distractors, explanation, diff in recurrence_cases:
        prompt = f"What is the asymptotic time complexity of an algorithm whose execution satisfies the recurrence relation: {rec} with base case T(1) = O(1)?"
        q = make_question(
            id_str=f"gen-tc-rec-{q_idx}",
            topic="sorting",
            subtopic="recurrence-relations",
            difficulty=diff,
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=explanation,
            generator_key="time_complexity.recurrence",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 2. Nested Loops with Parameter Variations
    loop_templates = [
        (
            "for i from 1 to n:\n    for j from 1 to n with j *= 2:\n        sum += 1",
            "O(n log n)",
            ["O(n²)", "O(n)", "O(log n)", "O(n² log n)"],
            "The outer loop executes n times. The inner loop doubles j until reaching n, which executes ⌊log₂ n⌋ + 1 times. Multiplying gives Θ(n log n).",
            "Easy",
        ),
        (
            "for i from 1 to n:\n    for j from 1 to i:\n        for k from 1 to j:\n            counter++",
            "O(n³)",
            ["O(n²)", "O(n log n)", "O(n⁴)", "O(n² log n)"],
            "The number of iterations is Σ_{i=1}^n Σ_{j=1}^i j = Σ_{i=1}^n i(i+1)/2 ≈ n³/6 = Θ(n³).",
            "Medium",
        ),
        (
            "i = 1\nwhile i * i <= n:\n    i += 1",
            "O(√n)",
            ["O(n)", "O(log n)", "O(n²)", "O(n log n)"],
            "The loop terminates when i > √n. With unit increment per step, exactly ⌊√n⌋ iterations occur, giving Θ(√n) time complexity.",
            "Easy",
        ),
        (
            "for i from 1 to n:\n    j = 1\n    while j <= i:\n        j *= 2",
            "O(n log n)",
            ["O(n²)", "O(n)", "O(log n)", "O(2^n)"],
            "The inner loop runs log₂(i) times for each i. Sum_{i=1}^n log(i) = log(n!) = Θ(n log n) by Stirling's approximation.",
            "Medium",
        ),
        (
            "for i from 1 to n:\n    for j from i to n:\n        sum += 1",
            "O(n²)",
            ["O(n)", "O(n log n)", "O(n³)", "O(log n)"],
            "When i=1, inner loop runs n times; when i=2, n-1 times; ... when i=n, 1 time. Total operations = n + (n-1) + ... + 1 = n(n+1)/2 = Θ(n²).",
            "Easy",
        ),
        (
            "for i from 1 to n with i *= 2:\n    for j from 1 to i:\n        sum += 1",
            "O(n)",
            ["O(n log n)", "O(n²)", "O(log n)", "O(n²)"],
            "The outer loop variable i takes values 1, 2, 4, 8, ..., 2^k where 2^k <= n. Total operations = 1 + 2 + 4 + ... + 2^k = 2^(k+1) - 1 <= 2n - 1 = Θ(n).",
            "Hard",
        ),
        (
            "for i from 1 to n:\n    for j from 1 to n with step j += i:\n        count++",
            "O(n log n)",
            ["O(n²)", "O(n)", "O(log n)", "O(n√n)"],
            "For a given i, the inner loop executes ⌊n/i⌋ times. Summing over all i from 1 to n yields n * (1 + 1/2 + 1/3 + ... + 1/n) = n * H_n = Θ(n log n), known as the Harmonic Series sum.",
            "Hard",
        ),
        (
            "i = n\nwhile i > 0:\n    i = i // 2",
            "O(log n)",
            ["O(n)", "O(√n)", "O(1)", "O(n log n)"],
            "Dividing n by 2 iteratively reaches 0 in exactly ⌊log₂ n⌋ + 1 iterations, yielding Θ(log n).",
            "Easy",
        ),
    ]

    for code, ans, distractors, explanation, diff in loop_templates:
        prompt = f"Determine the worst-case asymptotic time complexity of the following code snippet with respect to input n:\n\n```text\n{code}\n```"
        q = make_question(
            id_str=f"gen-tc-loop-{q_idx}",
            topic="sorting",
            subtopic="loop-analysis",
            difficulty=diff,
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=explanation,
            generator_key="time_complexity.loops",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 3. Dynamic Array & Amortized Complexity Variations
    amortized_cases = [
        ("Inserting n elements sequentially into an initially empty dynamic array with capacity doubling strategy", "O(1) amortized per insert, O(n) total", ["O(n) amortized per insert, O(n²) total", "O(log n) amortized per insert", "O(n log n) total"], "Doubling capacity when full causes reallocations at powers of 2 (1, 2, 4, ..., n). Total copy cost <= 2n, so average cost per insertion is (n + 2n)/n = O(1) amortized.", "Medium"),
        ("Finding the connected component of a node in Disjoint Set Union (DSU) with both Path Compression and Union by Rank", "O(α(n)) amortized, where α is the inverse Ackermann function", ["O(1) strictly", "O(log n) amortized", "O(log* n) strictly"], "Path compression flattens the tree while union by rank keeps depth shallow. Tarjan proved this achieves O(α(n)) amortized per operation, practically constant (< 5 for any realistic universe size).", "Hard"),
        ("Populating a binary heap of n elements using Floyd's bottom-up buildHeap algorithm versus n sequential heap insertions", "buildHeap is O(n), sequential insertion is O(n log n)", ["Both are O(n log n)", "Both are O(n)", "buildHeap is O(n log n), sequential is O(n)"], "Floyd's algorithm computes sum_{h=0}^{log n} (n / 2^{h+1}) * O(h) which converges to O(n). In contrast, inserting n elements one-by-one into a heap can take up to sum log(i) = O(n log n).", "Medium"),
        ("What is the auxiliary space complexity of Breadth-First Search on a balanced binary tree of n nodes?", "O(n)", ["O(log n)", "O(1)", "O(n log n)"], "In a balanced binary tree, the last level contains approximately n/2 nodes. BFS queues an entire level before processing, requiring O(n/2) = O(n) maximum queue space.", "Medium"),
        ("What is the maximum auxiliary stack space consumed by Depth-First Search on a balanced binary tree of n nodes?", "O(log n)", ["O(n)", "O(1)", "O(√n)"], "On a balanced binary tree of n nodes, the maximum depth from root to leaf is ⌊log₂ n⌋. The recursion call stack at any moment contains at most O(log n) frames.", "Easy"),
    ]

    for scenario, ans, distractors, explanation, diff in amortized_cases:
        prompt = f"Regarding computational complexity analysis: {scenario}. Which of the following correctly characterizes the complexity?"
        q = make_question(
            id_str=f"gen-tc-amort-{q_idx}",
            topic="sorting",
            subtopic="amortized-analysis",
            difficulty=diff,
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=explanation,
            generator_key="time_complexity.amortized",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 4. Programmatic parameterized loop generator to scale verified questions
    # We parameterize bases, increments, nested depths, and multipliers
    # 4. Programmatic parameterized loop generator to scale verified questions
    # We parameterize bases, increments, nested depths, and multipliers
    for step_factor in [2, 3, 4, 5, 6, 8, 10]:
        for power in [1, 2, 3]:
            if power == 1:
                prompt = (
                    f"Analyze the worst-case time complexity of the following algorithm on input n:\n\n"
                    f"```text\ni = 1\nwhile i <= n:\n    i *= {step_factor}\n```"
                )
                ans = "O(log n)"
                distractors = ["O(n)", f"O(n / {step_factor})", "O(1)", "O(√n)"]
                exp = f"Variable i starts at 1 and multiplies by {step_factor} in each step, reaching n in ⌊log_{step_factor} n⌋ steps = Θ(log n)."
                diff = "Easy"
            elif power == 2:
                prompt = (
                    f"Analyze the time complexity of the following algorithm on input n:\n\n"
                    f"```text\nfor i from 1 to n:\n    j = 1\n    while j <= n:\n        j *= {step_factor}\n```"
                )
                ans = "O(n log n)"
                distractors = ["O(n²)", f"O(n * {step_factor})", "O(log n)", "O(n² log n)"]
                exp = f"Outer loop runs n times. Inner loop multiplies j by {step_factor} each step, running log_{step_factor}(n) times. Asymptotic time is Θ(n log n)."
                diff = "Medium"
            else:
                prompt = (
                    f"Analyze the time complexity of the following algorithm on input n:\n\n"
                    f"```text\nfor i from 1 to n:\n    for k from 1 to n:\n        j = 1\n        while j <= n:\n            j *= {step_factor}\n```"
                )
                ans = "O(n² log n)"
                distractors = ["O(n³)", "O(n²)", "O(n log n)", "O(n³ log n)"]
                exp = f"Two outer loops each run n times (total n² combinations). The innermost loop runs log_{step_factor}(n) times. Asymptotic time is Θ(n² log n)."
                diff = "Hard"

            q = make_question(
                id_str=f"gen-tc-param-{q_idx}",
                topic="sorting",
                subtopic="nested-loops",
                difficulty=diff,
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="time_complexity.param_loop",
                rng=rng,
            )
            questions.append(q)
            q_idx += 1

    # 5. Additional Master Theorem Recurrences
    more_recurrences = [
        (3, 2, 1, "T(n) = 3T(n/2) + O(n)", "O(n^log₂ 3)", ["O(n log n)", "O(n²)", "O(n)"], "Case 1: a=3, b=2, log₂ 3 ≈ 1.58 > 1. Hence Θ(n^log₂ 3).", "Hard"),
        (9, 3, 1, "T(n) = 9T(n/3) + O(n)", "O(n²)", ["O(n log n)", "O(n³)", "O(n)"], "Case 1: a=9, b=3, log₃ 9 = 2. f(n) = O(n¹), so Θ(n²).", "Medium"),
        (2, 4, 0.5, "T(n) = 2T(n/4) + O(√n)", "O(√n log n)", ["O(√n)", "O(n)", "O(n log n)"], "Case 2: a=2, b=4, log₄ 2 = 0.5. f(n) = Θ(n^0.5) = Θ(√n). Hence Θ(√n log n).", "Hard"),
        (7, 2, 2, "T(n) = 7T(n/2) + O(n²)", "O(n^log₂ 7)", ["O(n²)", "O(n³)", "O(n² log n)"], "Case 1: a=7, b=2, log₂ 7 ≈ 2.81 > 2. Hence Θ(n^log₂ 7).", "Hard"),
        (1, 2, 0, "T(n) = T(n/2) + O(1)", "O(log n)", ["O(n)", "O(1)", "O(n log n)"], "Case 2: a=1, b=2, log₂ 1 = 0. f(n) = O(1) = O(n^0). Hence Θ(log n). This represents standard Binary Search.", "Easy"),
        (2, 2, 0, "T(n) = 2T(n/2) + O(1)", "O(n)", ["O(log n)", "O(n log n)", "O(1)"], "Case 1: a=2, b=2, log₂ 2 = 1 > 0. Hence Θ(n).", "Easy"),
        (4, 2, 2, "T(n) = 4T(n/2) + O(n²)", "O(n² log n)", ["O(n²)", "O(n³)", "O(n log n)"], "Case 2: a=4, b=2, log₂ 4 = 2. f(n) = Θ(n²). Hence Θ(n² log n).", "Medium"),
        (16, 4, 2, "T(n) = 16T(n/4) + O(n²)", "O(n² log n)", ["O(n²)", "O(n⁴)", "O(n³ log n)"], "Case 2: a=16, b=4, log₄ 16 = 2. f(n) = Θ(n²). Hence Θ(n² log n).", "Medium"),
        (2, 2, 2, "T(n) = 2T(n/2) + O(n²)", "O(n²)", ["O(n log n)", "O(n³)", "O(n² log n)"], "Case 3: a=2, b=2, log₂ 2 = 1. f(n) = Ω(n²), so Θ(n²).", "Medium"),
    ]

    for a, b, c, rec_str, ans, distractors, exp, diff in more_recurrences:
        prompt = f"Solve the asymptotic recurrence relation for an algorithm with base case T(1) = O(1):\n`{rec_str}`"
        q = make_question(
            id_str=f"gen-tc-mrec-{q_idx}",
            topic="sorting",
            subtopic="master-theorem",
            difficulty=diff,
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=exp,
            generator_key="time_complexity.master_theorem",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    return questions[:count]
