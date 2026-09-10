"""Backtracking algorithmic question generator with programmatic search oracles."""

import random

from content.generators.base import GeneratedQuestion, make_question


def combination_sum_count_oracle(candidates: list[int], target: int) -> int:
    """Number of distinct combinations summing to target."""
    res = []

    def backtrack(remain: int, combo: list[int], start: int) -> None:
        if remain == 0:
            res.append(list(combo))
            return
        if remain < 0:
            return
        for i in range(start, len(candidates)):
            combo.append(candidates[i])
            backtrack(remain - candidates[i], combo, i)
            combo.pop()

    backtrack(target, [], 0)
    return len(res)


def n_queens_count_oracle(n: int) -> int:
    """Count valid distinct N-Queens placements on N x N board."""
    count = 0
    cols: set[int] = set()
    diag1: set[int] = set()
    diag2: set[int] = set()

    def backtrack(r: int) -> None:
        nonlocal count
        if r == n:
            count += 1
            return
        for c in range(n):
            if c in cols or (r - c) in diag1 or (r + c) in diag2:
                continue
            cols.add(c)
            diag1.add(r - c)
            diag2.add(r + c)
            backtrack(r + 1)
            cols.remove(c)
            diag1.remove(r - c)
            diag2.remove(r + c)

    backtrack(0)
    return count


def max_gold_oracle(grid: list[list[int]]) -> int:
    """Maximum gold path in grid without visiting any cell twice."""
    m, n = len(grid), len(grid[0])
    max_gold = 0
    grid_copy = [row[:] for row in grid]

    def dfs(r: int, c: int) -> int:
        gold = grid_copy[r][c]
        grid_copy[r][c] = 0
        best_child = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and grid_copy[nr][nc] > 0:
                best_child = max(best_child, dfs(nr, nc))
        grid_copy[r][c] = gold
        return gold + best_child

    for r in range(m):
        for c in range(n):
            if grid_copy[r][c] > 0:
                max_gold = max(max_gold, dfs(r, c))
    return max_gold


def generate_backtracking_questions(count: int = 12, seed: int = 305) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    q_idx = 1

    # Design 1: backtracking.combination_sum (Easy, 4 instances)
    combo_cases = [
        ([2, 3, 6, 7], 7),
        ([2, 3, 5], 8),
        ([2], 1),
        ([3, 5], 9),
    ]
    for candidates, target in combo_cases:
        ans_val = combination_sum_count_oracle(candidates, target)
        ans = str(ans_val)
        cand = [ans_val + 1, ans_val + 2, ans_val + 3, max(0, ans_val - 1), max(0, ans_val - 2)]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans]
        prompt = (
            f"Given distinct positive integers `candidates = {candidates}` and `target = {target}`, "
            f"backtracking searches for all unique combinations where numbers sum to `target` "
            f"(each candidate may be chosen unlimited times). "
            f"How many distinct combinations exist?"
        )
        exp = (
            f"Exploring combinations recursively with DFS and candidate pruning yields exactly "
            f"{ans_val} unique valid combination(s) that sum to {target}."
        )
        questions.append(
            make_question(
                id_str=f"gen-back-combo-{q_idx}",
                topic="backtracking",
                subtopic="combination-sum",
                difficulty="Easy",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="backtracking.combination_sum",
                rng=rng,
            )
        )
        q_idx += 1

    # Design 2: backtracking.n_queens_count (Medium, 4 instances)
    queens_cases = [4, 5, 6, 7]
    for n in queens_cases:
        ans_val = n_queens_count_oracle(n)
        ans = str(ans_val)
        cand = [ans_val + 2, max(1, ans_val - 2), ans_val * 2, ans_val // 2 if ans_val > 2 else ans_val + 4]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans and d > 0]
        prompt = (
            f"The N-Queens puzzle requires placing {n} non-attacking queens on a {n} x {n} chessboard. "
            f"Using backtracking with column and diagonal constraint sets, how many distinct valid "
            f"queen configurations exist for N = {n}?"
        )
        exp = (
            f"For an {n} x {n} board, row-by-row backtracking with pruning across columns and diagonals "
            f"(row-col and row+col) finds exactly {ans_val} distinct solution(s)."
        )
        questions.append(
            make_question(
                id_str=f"gen-back-queens-{q_idx}",
                topic="backtracking",
                subtopic="n-queens",
                difficulty="Medium",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="backtracking.n_queens_count",
                rng=rng,
            )
        )
        q_idx += 1

    # Design 3: backtracking.path_with_max_gold (Hard, 4 instances)
    gold_cases = [
        [[0, 6, 0], [5, 8, 7], [0, 9, 0]],
        [[1, 0, 7], [2, 0, 6], [3, 4, 5], [0, 3, 0], [9, 0, 20]],
        [[1, 2, 3], [0, 0, 4], [7, 6, 5]],
        [[0, 0, 1], [2, 4, 3], [0, 5, 0]],
    ]
    for grid in gold_cases:
        ans_val = max_gold_oracle(grid)
        ans = str(ans_val)
        cand = [ans_val + 3, ans_val - 3, ans_val + 4, ans_val - 4, ans_val + 6]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans and d > 0]
        prompt = (
            f"In a gold mine represented by grid `grid = {grid}`, each cell has gold (0 is empty/wall). "
            f"From any gold-containing cell, a miner moves up, down, left, or right, collecting gold "
            f"without ever visiting the same cell twice. What is the maximum amount of gold the miner can collect?"
        )
        exp = (
            f"Using DFS backtracking starting from every non-zero cell and unmarking visited cells on return, "
            f"the optimal path yields {ans_val} total gold."
        )
        questions.append(
            make_question(
                id_str=f"gen-back-gold-{q_idx}",
                topic="backtracking",
                subtopic="path-with-max-gold",
                difficulty="Hard",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="backtracking.path_with_max_gold",
                rng=rng,
            )
        )
        q_idx += 1

    return questions[:count]
