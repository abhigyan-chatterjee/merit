"""Dynamic programming question generator with exact DP state & recurrence oracles."""

import random
from content.generators.base import GeneratedQuestion, make_question


def lis_oracle(nums: list[int]) -> int:
    if not nums:
        return 0
    dp = [1] * len(nums)
    for i in range(len(nums)):
        for j in range(i):
            if nums[i] > nums[j]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp)


def knapsack_oracle(weights: list[int], values: list[int], capacity: int) -> int:
    dp = [0] * (capacity + 1)
    for w, v in zip(weights, values):
        for c in range(capacity, w - 1, -1):
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[capacity]


def lcs_oracle(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]


def generate_dp_questions(count: int = 120, seed: int = 46) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    q_idx = 1

    # 1. Longest Increasing Subsequence Length calculations
    lis_inputs = [
        [10, 9, 2, 5, 3, 7, 101, 18],
        [0, 1, 0, 3, 2, 3],
        [7, 7, 7, 7, 7],
        [4, 10, 4, 3, 8, 9],
        [1, 3, 6, 7, 9, 4, 10, 5, 6],
        [3, 1, 4, 1, 5, 9, 2, 6],
        [10, 22, 9, 33, 21, 50, 41, 60],
        [5, 2, 8, 6, 3, 6, 9, 7],
        [3, 10, 2, 1, 20],
        [50, 3, 10, 7, 40, 80],
        [16, 3, 5, 19, 10, 14, 12, 0, 15],
        [2, 4, 3, 5, 1, 7, 6, 9, 8],
        [10, 15, 20, 25, 30],
        [9, 8, 7, 6, 5, 4],
        [1, 2, 3, 4, 5, 6, 7],
        [18, 55, 23, 98, 56, 76, 82, 93],
        [100, 22, 9, 33, 21, 50, 41, 60, 80],
        [3, 5, 6, 2, 5, 4, 19, 5, 6, 7, 12],
    ]

    for nums in lis_inputs:
        ans_len = lis_oracle(nums)
        ans = str(ans_len)
        cand_lis = [ans_len + 1, ans_len + 2, ans_len + 3]
        if ans_len > 1:
            cand_lis.append(ans_len - 1)
        distractors = [str(d) for d in cand_lis if d != ans_len]
        prompt = (
            f"Given the integer sequence `{nums}`, what is the length of the Longest Strictly Increasing Subsequence (LIS)?"
        )
        q = make_question(
            id_str=f"gen-dp-lis-{q_idx}",
            topic="dynamic-programming",
            subtopic="lis",
            difficulty="Medium",
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=f"By dynamic programming or patience sorting, the longest strictly increasing subsequence in `{nums}` has length {ans_len}.",
            generator_key="dp.lis",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 2. 0/1 Knapsack Value calculations
    knapsack_instances = [
        ([2, 3, 4, 5], [3, 4, 5, 6], 5),
        ([1, 2, 3], [10, 15, 40], 4),
        ([3, 4, 6, 5], [2, 3, 1, 4], 8),
        ([1, 3, 4, 5], [1, 4, 5, 7], 7),
        ([2, 1, 3, 2], [12, 10, 20, 15], 5),
        ([5, 4, 6, 3], [10, 40, 30, 50], 10),
        ([2, 3, 5], [1, 2, 6], 8),
        ([4, 5, 1], [1, 2, 3], 4),
        ([1, 1, 1], [10, 20, 30], 2),
        ([3, 2, 5, 4], [25, 20, 40, 30], 7),
        ([2, 3, 4, 5, 9], [3, 4, 8, 8, 10], 11),
        ([1, 2, 5, 6], [1, 6, 18, 22], 7),
    ]

    for weights, values, cap in knapsack_instances:
        max_val = knapsack_oracle(weights, values, cap)
        ans = str(max_val)
        cand_knap = [max_val + 3, max_val + 5, max_val + 8]
        if max_val > 3:
            cand_knap.append(max_val - 2)
        distractors = [str(d) for d in cand_knap if d != max_val]
        prompt = (
            f"In a 0/1 Knapsack problem with knapsack capacity {cap}, items with weights `{weights}` "
            f"and corresponding values `{values}` are available. "
            f"What is the maximum total value that can fit within the capacity?"
        )
        q = make_question(
            id_str=f"gen-dp-knap-{q_idx}",
            topic="dynamic-programming",
            subtopic="knapsack",
            difficulty="Medium",
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=f"The optimal subset yields total value {max_val} without exceeding capacity {cap}.",
            generator_key="dp.knapsack",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 3. LCS calculations
    lcs_pairs = [
        ("abcde", "ace"),
        ("abc", "abc"),
        ("abc", "def"),
        ("AGGTAB", "GXTXAYB"),
        ("BDCAB", "ABCBDAB"),
        ("ALGORITHM", "LOGARITHM"),
        ("DYNAMIC", "PROGRAMMING"),
        ("INTENTION", "EXECUTION"),
        ("SUNDAY", "SATURDAY"),
        ("HORSE", "ROS"),
        ("DISTANCE", "EDITING"),
        ("BANANA", "ATANA"),
        ("OXFORD", "CAMBRIDGE"),
        ("HELLO", "WORLD"),
    ]

    for s1, s2 in lcs_pairs:
        lcs_len = lcs_oracle(s1, s2)
        ans = str(lcs_len)
        cand_lcs = [lcs_len + 1, lcs_len + 2, lcs_len + 3]
        if lcs_len > 0:
            cand_lcs.append(lcs_len - 1)
        distractors = [str(d) for d in cand_lcs if d != lcs_len]
        prompt = (
            f"What is the length of the Longest Common Subsequence (LCS) between strings `\"{s1}\"` and `\"{s2}\"`?"
        )
        q = make_question(
            id_str=f"gen-dp-lcs-{q_idx}",
            topic="dynamic-programming",
            subtopic="lcs",
            difficulty="Easy",
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=f"Standard 2D DP matrix comparison between '{s1}' and '{s2}' yields an LCS length of {lcs_len}.",
            generator_key="dp.lcs",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 4. DP Conceptual & Invariant questions
    dp_concepts = [
        ("What two core mathematical properties must a problem satisfy to be solvable via Dynamic Programming?", "Optimal substructure and overlapping subproblems", ["Greedy choice property and independence", "Divide and conquer and sparsity", "Polynomial time and monotonicity"], "Dynamic programming applies when the problem exhibits overlapping subproblems (recomputing identical states) and optimal substructure (optimal solution composed of optimal solutions to subproblems).", "Easy"),
        ("What is the difference between Top-Down Memoization and Bottom-Up Tabulation in Dynamic Programming?", "Top-Down uses recursion with caching; Bottom-Up iteratively fills a table in topological dependency order", ["Top-Down uses less time complexity than Bottom-Up", "Bottom-Up cannot handle 2D state spaces", "Memoization never uses extra memory"], "Top-Down executes recursively on demand and saves computed subproblems in a cache. Bottom-Up starts from base cases and fills an array/table iteratively without recursion overhead.", "Easy"),
        ("How can the space complexity of the standard Fibonacci calculation or 1D DP `dp[i] = dp[i-1] + dp[i-2]` be optimized from O(n) to O(1)?", "By maintaining only two previous state variables instead of a full array", ["By using binary search memoization", "By storing values in a min-heap", "By hashing every fourth index"], "Because each state only depends on the immediately preceding two states, two scalar variables can be updated in a rolling loop, reducing auxiliary space from O(n) to O(1).", "Easy"),
        ("What is the time complexity of solving the 0/1 Knapsack problem with N items and integer capacity W using dynamic programming?", "O(N * W) pseudo-polynomial time", ["O(N log W) strictly polynomial", "O(2^N) exponential time", "O(N² + W) linear time"], "The DP table requires filling N * W cells, with O(1) work per cell. Because runtime is proportional to the numeric value of W rather than the input bit-length log(W), it is classified as pseudo-polynomial.", "Hard"),
    ]

    for prompt, ans, distractors, exp, diff in dp_concepts:
        q = make_question(
            id_str=f"gen-dp-concept-{q_idx}",
            topic="dynamic-programming",
            subtopic="dp-theory",
            difficulty=diff,
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=exp,
            generator_key="dp.concepts",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    return questions[:count]
