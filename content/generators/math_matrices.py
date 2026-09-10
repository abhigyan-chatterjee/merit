"""Math & Matrices algorithmic question generator with exact programmatic oracles."""

import math
import random

from content.generators.base import GeneratedQuestion, make_question


def lcm_oracle(a: int, b: int) -> int:
    """Least Common Multiple using Euclidean GCD."""
    return (a * b) // math.gcd(a, b)


def matrix_spiral_order_oracle(matrix: list[list[int]], k: int) -> int:
    """Element at 0-indexed position k in clockwise spiral traversal."""
    res: list[int] = []
    top = 0
    bottom = len(matrix) - 1
    left = 0
    right = len(matrix[0]) - 1
    while top <= bottom and left <= right:
        for c in range(left, right + 1):
            res.append(matrix[top][c])
        top += 1
        for r in range(top, bottom + 1):
            res.append(matrix[r][right])
        right -= 1
        if top <= bottom:
            for c in range(right, left - 1, -1):
                res.append(matrix[bottom][c])
            bottom -= 1
        if left <= right:
            for r in range(bottom, top - 1, -1):
                res.append(matrix[r][left])
            left += 1
    return res[k]


def matrix_determinant_3x3_oracle(m: list[list[int]]) -> int:
    """Determinant of a 3x3 square matrix."""
    a, b, c = m[0]
    d, e, f = m[1]
    g, h, i = m[2]
    return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)


def generate_math_matrices_questions(count: int = 12, seed: int = 306) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    q_idx = 1

    # Design 1: math_matrices.gcd_lcm (Easy, 4 instances)
    lcm_cases = [
        (12, 18),
        (15, 25),
        (14, 35),
        (24, 36),
    ]
    for a, b in lcm_cases:
        ans_val = lcm_oracle(a, b)
        ans = str(ans_val)
        cand = [ans_val * 2, math.gcd(a, b), a * b, max(1, ans_val - 12), ans_val + 12]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans and d > 0]
        prompt = (
            f"Using the Euclidean algorithm for greatest common divisor `gcd(a, b)` and the relation "
            f"`lcm(a, b) = (a * b) // gcd(a, b)`, what is the Least Common Multiple (LCM) of `{a}` and `{b}`?"
        )
        exp = (
            f"gcd({a}, {b}) = {math.gcd(a, b)}. Applying the identity "
            f"lcm({a}, {b}) = ({a} * {b}) // {math.gcd(a, b)} = {ans_val}."
        )
        questions.append(
            make_question(
                id_str=f"gen-math-lcm-{q_idx}",
                topic="math-matrices",
                subtopic="number-theory",
                difficulty="Easy",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="math_matrices.gcd_lcm",
                rng=rng,
            )
        )
        q_idx += 1

    # Design 2: math_matrices.matrix_spiral_order (Medium, 4 instances)
    spiral_cases = [
        ([[1, 2, 3], [4, 5, 6], [7, 8, 9]], 4),
        ([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]], 11),
        ([[2, 5, 8], [4, 0, -1]], 3),
        ([[1, 2], [3, 4], [5, 6]], 5),
    ]
    for matrix, k in spiral_cases:
        ans_val = matrix_spiral_order_oracle(matrix, k)
        ans = str(ans_val)
        flat = [item for row in matrix for item in row]
        cand = [ans_val + 1, ans_val - 1, flat[min(k, len(flat) - 1)], ans_val + 2, ans_val - 2]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans]
        prompt = (
            f"Given the matrix `matrix = {matrix}`, elements are traversed in clockwise spiral order "
            f"starting from the top-left cell `(0, 0)`. "
            f"What is the value of the 0-indexed element at position `{k}` in this spiral sequence?"
        )
        exp = (
            f"Traversing matrix boundaries in top -> right -> bottom -> left sequence reaches "
            f"value {ans_val} at 0-indexed step {k}."
        )
        questions.append(
            make_question(
                id_str=f"gen-mat-spiral-{q_idx}",
                topic="math-matrices",
                subtopic="spiral-matrix",
                difficulty="Medium",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="math_matrices.matrix_spiral_order",
                rng=rng,
            )
        )
        q_idx += 1

    # Design 3: math_matrices.matrix_determinant_3x3 (Hard, 4 instances)
    det_cases = [
        [[1, 2, 3], [0, 1, 4], [5, 6, 0]],
        [[2, -3, 1], [2, 0, -1], [1, 4, 5]],
        [[3, 1, 2], [1, 4, 5], [2, 3, 1]],
        [[2, 1, 3], [1, 0, 2], [4, 1, 5]],
    ]
    for mat in det_cases:
        ans_val = matrix_determinant_3x3_oracle(mat)
        ans = str(ans_val)
        cand = [ans_val + 4, ans_val - 4, ans_val + 2, ans_val - 2, 0 if ans_val != 0 else 1]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans]
        prompt = (
            f"What is the determinant `det(A)` of the following 3x3 square matrix `A`?\n"
            f"`{mat[0]}`\n"
            f"`{mat[1]}`\n"
            f"`{mat[2]}`\n"
        )
        exp = (
            f"Using Laplace expansion along the first row: "
            f"det(A) = a(ei - fh) - b(di - fg) + c(dh - eg), which evaluates to exactly {ans_val}."
        )
        questions.append(
            make_question(
                id_str=f"gen-mat-det-{q_idx}",
                topic="math-matrices",
                subtopic="matrix-determinant",
                difficulty="Hard",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="math_matrices.matrix_determinant_3x3",
                rng=rng,
            )
        )
        q_idx += 1

    return questions[:count]
