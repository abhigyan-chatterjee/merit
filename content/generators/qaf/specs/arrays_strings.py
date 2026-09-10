"""Declarative design specs for Arrays & Strings topic ported to QAF."""

import random
from typing import Any

from content.generators.qaf.distractors import (
    FixedDistractorStrategy,
    NumericOffsetStrategy,
)
from content.generators.qaf.spec import DesignSpec, register_spec

# --- 1. Kadane's Algorithm Maximum Subarray Sum ---

KADANE_CASES: list[dict[str, Any]] = [
    {"arr": [-2, 1, -3, 4, -1, 2, 1, -5, 4], "id": "gen-arr-kadane-1"},
    {"arr": [5, 4, -1, 7, 8], "id": "gen-arr-kadane-3"},
    {"arr": [-1, -2, -3, -4], "id": "gen-arr-kadane-4"},
    {"arr": [3, -1, 2, -1, -2, 4], "id": "gen-arr-kadane-7"},
]


def sample_kadane(rng: random.Random) -> dict[str, Any]:
    """Sample one parameter set for Kadane's algorithm."""
    return rng.choice(KADANE_CASES)


kadane_spec = register_spec(
    DesignSpec(
        key="arrays_strings.kadane",
        topic="arrays-hashing",
        subtopic="kadane",
        oracle="kadane",
        sample=sample_kadane,
        prompt="Using Kadane's algorithm, what is the maximum subarray sum in the integer array:\n`{arr}`?",
        explanation="Kadane's algorithm maintains `currMax = max(x, currMax + x)`. The maximum contiguous subarray sum is {answer}.",
        difficulty=lambda p: "Medium" if len(p["arr"]) > 4 else "Easy",
        distractors=NumericOffsetStrategy(offsets=[2, 4, 6, -2, -4]),
        id_prefix="gen-arr-kadane",
        seed=49,
    )
)


# --- 2. Prefix Sum Range Query ---

PREFIX_SUM_CASES: list[dict[str, Any]] = [
    {"arr": [3, 1, 4, 1, 5, 9, 2], "L": 2, "R": 5, "id": "gen-arr-prefix-17"},
    {"arr": [2, 4, 6, 8, 10, 12], "L": 2, "R": 4, "id": "gen-arr-prefix-22"},
    {"arr": [15, 25, 35, 45], "L": 0, "R": 2, "id": "gen-arr-prefix-23"},
    {"arr": [8, 16, 24, 32, 40], "L": 2, "R": 4, "id": "gen-arr-prefix-26"},
]


def sample_prefix_sum(rng: random.Random) -> dict[str, Any]:
    """Sample one parameter set for Prefix Sum range query."""
    return rng.choice(PREFIX_SUM_CASES)


prefix_sum_spec = register_spec(
    DesignSpec(
        key="arrays_strings.prefix_sum",
        topic="arrays-hashing",
        subtopic="prefix-sums",
        oracle="prefix_sum",
        sample=sample_prefix_sum,
        prompt="Given array `{arr}`, what is the range sum of elements from index {L} to {R} inclusive (`nums[{L}..{R}]`) computed in O(1) time using a precomputed prefix sum array?",
        explanation="Using prefix sums P[i], RangeSum(L, R) = P[R] - (P[L-1] if L > 0 else 0) = {answer}.",
        difficulty="Easy",
        distractors=NumericOffsetStrategy(offsets=[5, 10, -3, 3, -5]),
        id_prefix="gen-arr-prefix",
        seed=44,
    )
)


# --- 3. Sliding Window Maximum Sum of Size K ---

SLIDING_WINDOW_CASES: list[dict[str, Any]] = [
    {"arr": [2, 1, 5, 1, 3, 2], "k": 3, "id": "gen-arr-win-28"},
    {"arr": [100, 200, 300, 400], "k": 2, "id": "gen-arr-win-31"},
    {"arr": [10, 5, 2, 7, 8, 7], "k": 3, "id": "gen-arr-win-35"},
    {"arr": [1, 9, 3, 5, 6, 2], "k": 2, "id": "gen-arr-win-36"},
]


def sample_sliding_window(rng: random.Random) -> dict[str, Any]:
    """Sample one parameter set for fixed sliding window maximum sum."""
    return rng.choice(SLIDING_WINDOW_CASES)


sliding_window_spec = register_spec(
    DesignSpec(
        key="arrays_strings.sliding_window",
        topic="arrays-hashing",
        subtopic="sliding-window",
        oracle="max_sum_fixed",
        sample=sample_sliding_window,
        prompt="Using a sliding window of fixed size `k = {k}`, what is the **maximum subarray sum** over all contiguous subarrays of size {k} in array `{arr}`?",
        explanation="By maintaining a sliding window of size {k} and updating sum in O(1) time per shift, the maximum window sum is {answer}.",
        difficulty="Easy",
        distractors=NumericOffsetStrategy(offsets=[3, 6, -2, -5, 2]),
        id_prefix="gen-arr-win",
        seed=49,
    )
)


# --- 4. String Algorithms & Pattern Matching Concepts ---

CONCEPTS_CASES: list[dict[str, Any]] = [
    {
        "prompt_text": "What is the worst-case time complexity of the Knuth-Morris-Pratt (KMP) string matching algorithm for text of length N and pattern of length M?",
        "answer": "O(N + M)",
        "distractors": ["O(N * M)", "O(N log M)", "O(N²)"],
        "exp": "KMP precomputes the Longest Prefix Suffix (LPS) table in O(M) time and scans the text in O(N) time without backtracking, achieving O(N + M) total worst-case time.",
        "diff": "Medium",
        "id": "gen-str-concept-40",
    },
    {
        "prompt_text": "In the Rabin-Karp string matching algorithm, what technique enables O(1) computation of the hash of the next substring window?",
        "answer": "Rolling hash (Rabin fingerprint)",
        "distractors": ["Cryptographic SHA-256", "Huffman frequency tree", "Suffix automaton"],
        "exp": "A rolling hash (Rabin fingerprint) removes the leading character's contribution and adds the trailing character's contribution in O(1) arithmetic operations.",
        "diff": "Medium",
        "id": "gen-str-concept-41",
    },
    {
        "prompt_text": "What data structure allows querying the Longest Common Prefix (LCP) and finding all occurrences of any substring in a text of length N in O(M) time after O(N) construction?",
        "answer": "Suffix Tree or Suffix Automaton",
        "distractors": ["Binary Search Tree", "Disjoint Set Union", "Adjacency Matrix"],
        "exp": "A Suffix Tree or Suffix Automaton exposes all substrings as root-to-node paths, enabling linear-time pattern search and LCP queries.",
        "diff": "Hard",
        "id": "gen-str-concept-42",
    },
    {
        "prompt_text": "How does the Boyer-Moore string matching algorithm achieve sublinear average-case time complexity?",
        "answer": "By scanning the pattern from right-to-left and applying the Bad Character and Good Suffix skip heuristics",
        "distractors": [
            "By sorting all characters in the text first",
            "By compressing the text using Huffman encoding",
            "By hashing every character to 32 bits",
        ],
        "exp": "By scanning the pattern from right-to-left and applying the Bad Character and Good Suffix skip heuristics, Boyer-Moore matches characters backwards from the end of the pattern, allowing it to skip up to M characters at a time when a mismatch occurs.",
        "diff": "Medium",
        "id": "gen-str-concept-43",
    },
]


def sample_concepts(rng: random.Random) -> dict[str, Any]:
    """Sample one conceptual string algorithm question."""
    return rng.choice(CONCEPTS_CASES)


concepts_spec = register_spec(
    DesignSpec(
        key="arrays_strings.concepts",
        topic="sliding-windows",
        subtopic="string-algorithms",
        oracle="identity",
        sample=sample_concepts,
        prompt=lambda p: p["prompt_text"],
        explanation=lambda p: p["exp"],
        difficulty=lambda p: p["diff"],
        distractors=FixedDistractorStrategy(),
        id_prefix="gen-str-concept",
        seed=43,
    )
)


# --- 5. Fixed Sliding Window Maximum Subarray Sum ---

FIXED_CASES: list[dict[str, Any]] = [
    {"nums": [2, 1, 5, 1, 3, 2], "k": 3, "id": "gen-sw-maxsum-44"},
    {"nums": [2, 3, 4, 1, 5], "k": 2, "id": "gen-sw-maxsum-45"},
    {"nums": [1, 4, 2, 10, 23, 3, 1, 0, 20], "k": 4, "id": "gen-sw-maxsum-46"},
    {"nums": [100, 200, 300, 400], "k": 2, "id": "gen-sw-maxsum-47"},
]


def sample_max_sum_fixed(rng: random.Random) -> dict[str, Any]:
    """Sample one parameter set for fixed sliding window max sum."""
    return rng.choice(FIXED_CASES)


max_sum_fixed_spec = register_spec(
    DesignSpec(
        key="sliding_windows.max_sum_fixed",
        topic="sliding-windows",
        subtopic="fixed-window-max-sum",
        oracle="max_sum_fixed",
        sample=sample_max_sum_fixed,
        prompt="Given array `nums = {nums}` and window size `k = {k}`, what is the maximum sum of any contiguous subarray of length {k} computed using a fixed-size sliding window?",
        explanation="Maintaining a sliding window of size {k} and updating the sum in O(1) time per step finds the maximum subarray sum of {answer}.",
        difficulty="Easy",
        distractors=NumericOffsetStrategy(offsets=[2, -2, 4, -4, 7], min_val=1),
        id_prefix="gen-sw-maxsum",
        seed=53,
    )
)


# --- 6. Variable Sliding Window Minimum Window Substring ---

MIN_WIN_CASES: list[dict[str, Any]] = [
    {"s": "ADOBECODEBANC", "t": "ABC", "id": "gen-sw-minwin-48"},
    {"s": "a", "t": "a", "id": "gen-sw-minwin-49"},
    {"s": "a", "t": "aa", "id": "gen-sw-minwin-50"},
    {"s": "ABAACBAB", "t": "ABC", "id": "gen-sw-minwin-51"},
]


def sample_min_window_substring(rng: random.Random) -> dict[str, Any]:
    """Sample one parameter set for minimum window substring length."""
    return rng.choice(MIN_WIN_CASES)


def min_window_explanation(params: dict[str, Any]) -> str:
    ans_val = params["answer"]
    if ans_val == "0":
        return "String `s` does not contain the required character frequencies of `t`, so no valid window exists (length is 0)."
    return f"Expanding the right pointer to satisfy all characters and shrinking the left pointer to minimize window width achieves a minimum window length of {ans_val}."


min_window_substring_spec = register_spec(
    DesignSpec(
        key="sliding_windows.min_window_substring",
        topic="sliding-windows",
        subtopic="minimum-window-substring",
        oracle="min_window_substring",
        sample=sample_min_window_substring,
        prompt="Given strings `s = \"{s}\"` and `t = \"{t}\"`, a variable sliding window with two pointers finds the minimum window substring of `s` containing all characters in `t`. What is the length of this minimum window substring (or 0 if no valid window exists)?",
        explanation=min_window_explanation,
        difficulty="Hard",
        distractors=NumericOffsetStrategy(offsets=[1, -1, 2, -2, 3], min_val=0),
        id_prefix="gen-sw-minwin",
        seed=55,
    )
)

ARRAY_STRING_SPECS: list[DesignSpec] = [
    kadane_spec,
    prefix_sum_spec,
    sliding_window_spec,
    concepts_spec,
    max_sum_fixed_spec,
    min_window_substring_spec,
]
