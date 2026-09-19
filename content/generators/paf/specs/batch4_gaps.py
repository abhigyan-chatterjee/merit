"""Authoring and verification script for Batch 4: Backtracking, Bit Manipulation, Sorting, and Top-Ups."""

from __future__ import annotations

import asyncio
import copy
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
api_path = str(REPO_ROOT / "apps" / "api")
if api_path not in sys.path:
    sys.path.insert(0, api_path)

from app.services.judge import execute_code
from content.generators.paf.spec import Algorithm, ProblemSpec
from content.validators.schema import ProblemSchema
from content.validators.verify_problems import check_paf_gates


@dataclass
class ProblemBundle:
    spec: ProblemSpec
    py_brute_code: str
    py_brute_complexity: str
    py_optimal_code: str
    py_optimal_complexity: str
    input_generator: Callable[[random.Random], list[list[Any]]]
    examples: list[dict[str, str]]
    approach: str
    why_optimal_template: str
    pitfalls: str
    reading_links: list[str]
    hints: list[str]


# ===========================================================================
# 1. subsets
# ===========================================================================
spec_subsets = ProblemSpec(
    signature="function subsets(nums: number[])",
    statement="""# Subsets

Given an integer array `nums` of unique elements, return all possible subsets (the power set).

The solution set must not contain duplicate subsets. Each individual subset must be sorted in ascending numerical order, and the outer list of subsets must be sorted in lexicographical order.

Constraints: `0 <= nums.length <= 10` and `-10 <= nums[i] <= 10`. All elements of `nums` are unique.
""",
    brute_force=Algorithm(
        """function subsets(nums) {
  const n = nums.length;
  const total = 1 << n;
  const res = [];
  for (let mask = 0; mask < total; mask++) {
    const subset = [];
    for (let i = 0; i < n; i++) {
      if ((mask >> i) & 1) {
        subset.push(nums[i]);
      }
    }
    subset.sort((a, b) => a - b);
    res.push(subset);
  }
  res.sort((a, b) => {
    for (let i = 0; i < Math.min(a.length, b.length); i++) {
      if (a[i] !== b[i]) return a[i] - b[i];
    }
    return a.length - b.length;
  });
  return res;
}""",
        complexity="Time: O(n · 2ⁿ) | Space: O(n · 2ⁿ)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function subsets(nums) {
  const sortedNums = nums.slice().sort((a, b) => a - b);
  const res = [];
  const current = [];
  function backtrack(idx) {
    if (idx === sortedNums.length) {
      res.push(current.slice());
      return;
    }
    // Skip
    backtrack(idx + 1);
    // Choose
    current.push(sortedNums[idx]);
    backtrack(idx + 1);
    current.pop();
  }
  backtrack(0);
  res.sort((a, b) => {
    for (let i = 0; i < Math.min(a.length, b.length); i++) {
      if (a[i] !== b[i]) return a[i] - b[i];
    }
    return a.length - b.length;
  });
  return res;
}""",
        complexity="Time: O(n · 2ⁿ) | Space: O(n)",
        language="javascript",
    ),
    topic="backtracking",
    difficulty="Medium",
    pattern="backtracking / Choose-skip",
    time_limit_ms=2000,
    seed=42,
    title="Subsets",
    slug="subsets",
)

py_brute_subsets = """def subsets(nums: list[int]) -> list[list[int]]:
    n = len(nums)
    res = []
    for mask in range(1 << n):
        sub = [nums[i] for i in range(n) if (mask >> i) & 1]
        res.append(sorted(sub))
    res.sort()
    return res
"""

py_optimal_subsets = """def subsets(nums: list[int]) -> list[list[int]]:
    arr = sorted(nums)
    res = []
    current: list[int] = []

    def backtrack(idx: int) -> None:
        if idx == len(arr):
            res.append(list(current))
            return
        backtrack(idx + 1)
        current.append(arr[idx])
        backtrack(idx + 1)
        current.pop()

    backtrack(0)
    res.sort()
    return res
"""


def _gen_subsets_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[]],
        [[0]],
        [[1]],
        [[1, 2]],
        [[3, 1]],
        [[1, 2, 3]],
        [[-1, 0, 1]],
        [[4, 1, 0]],
        [[9, -2, 5]],
        [[-5, -4, -3]],
    ]
    for _ in range(12):
        length = rng.randint(4, 7)
        vals = rng.sample(range(-10, 11), length)
        cases.append([vals])
    cases.append([[-10, -8, -6, -4, -2, 0, 2, 4]])
    cases.append([[-10, -7, -4, -1, 2, 5, 8, 9, 10]])
    cases.append([[-5, -4, -3, -2, -1, 0, 1, 2, 3, 4]])
    return cases


# ===========================================================================
# 2. permutations
# ===========================================================================
spec_permutations = ProblemSpec(
    signature="function permute(nums: number[])",
    statement="""# Permutations

Given an array `nums` of distinct integers, return all the possible permutations.

The returned list of permutations must be sorted in lexicographical order.

Constraints: `1 <= nums.length <= 6` and `-10 <= nums[i] <= 10`. All integers of `nums` are unique.
""",
    brute_force=Algorithm(
        """function permute(nums) {
  const res = [];
  function generate(used, path) {
    if (path.length === nums.length) {
      res.push(path.slice());
      return;
    }
    for (let i = 0; i < nums.length; i++) {
      if (!used[i]) {
        used[i] = true;
        path.push(nums[i]);
        generate(used, path);
        path.pop();
        used[i] = false;
      }
    }
  }
  generate(new Array(nums.length).fill(false), []);
  res.sort((a, b) => {
    for (let i = 0; i < Math.min(a.length, b.length); i++) {
      if (a[i] !== b[i]) return a[i] - b[i];
    }
    return a.length - b.length;
  });
  return res;
}""",
        complexity="Time: O(n · n!) | Space: O(n · n!)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function permute(nums) {
  const arr = nums.slice();
  const res = [];
  function backtrack(start) {
    if (start === arr.length) {
      res.push(arr.slice());
      return;
    }
    for (let i = start; i < arr.length; i++) {
      const temp = arr[start];
      arr[start] = arr[i];
      arr[i] = temp;
      backtrack(start + 1);
      const temp2 = arr[start];
      arr[start] = arr[i];
      arr[i] = temp2;
    }
  }
  backtrack(0);
  res.sort((a, b) => {
    for (let i = 0; i < Math.min(a.length, b.length); i++) {
      if (a[i] !== b[i]) return a[i] - b[i];
    }
    return a.length - b.length;
  });
  return res;
}""",
        complexity="Time: O(n · n!) | Space: O(n)",
        language="javascript",
    ),
    topic="backtracking",
    difficulty="Medium",
    pattern="backtracking / Swap-build",
    time_limit_ms=2000,
    seed=42,
    title="Permutations",
    slug="permutations",
)

py_brute_permutations = """def permute(nums: list[int]) -> list[list[int]]:
    res = []
    used = [False] * len(nums)

    def generate(path: list[int]) -> None:
        if len(path) == len(nums):
            res.append(list(path))
            return
        for i in range(len(nums)):
            if not used[i]:
                used[i] = True
                path.append(nums[i])
                generate(path)
                path.pop()
                used[i] = False

    generate([])
    res.sort()
    return res
"""

py_optimal_permutations = """def permute(nums: list[int]) -> list[list[int]]:
    arr = list(nums)
    res = []

    def backtrack(start: int) -> None:
        if start == len(arr):
            res.append(list(arr))
            return
        for i in range(start, len(arr)):
            arr[start], arr[i] = arr[i], arr[start]
            backtrack(start + 1)
            arr[start], arr[i] = arr[i], arr[start]

    backtrack(0)
    res.sort()
    return res
"""


def _gen_permutations_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[1]],
        [[0]],
        [[-1]],
        [[1, 2]],
        [[2, 1]],
        [[0, 1]],
        [[1, 2, 3]],
        [[3, 2, 1]],
        [[-1, 0, 1]],
        [[5, -3, 2]],
    ]
    for _ in range(11):
        length = rng.randint(3, 5)
        vals = rng.sample(range(-10, 11), length)
        cases.append([vals])
    cases.append([[1, 2, 3, 4, 5, 6]])
    cases.append([[-3, -2, -1, 0, 1, 2]])
    cases.append([[6, 5, 4, 3, 2, 1]])
    cases.append([[-10, 10, -5, 5, 0, 1]])
    return cases


# ===========================================================================
# 3. combination-sum
# ===========================================================================
spec_combination_sum = ProblemSpec(
    signature="function combinationSum(candidates: number[], target: number)",
    statement="""# Combination Sum

Given an array of distinct integers `candidates` and a target integer `target`, return a list of all unique combinations of `candidates` where the chosen numbers sum to `target`.

The same candidate number may be chosen from `candidates` an unlimited number of times. Two combinations are unique if the frequency of at least one of the chosen numbers is different.

To ensure determinism, sort each individual combination in ascending numerical order, and sort the outer list of combinations in lexicographical order.

Constraints: `1 <= candidates.length <= 20`, `2 <= candidates[i] <= 40`, and `1 <= target <= 40`. All elements of `candidates` are distinct.
""",
    brute_force=Algorithm(
        """function combinationSum(candidates, target) {
  const res = [];
  function search(idx, current, sum) {
    if (sum === target) {
      const sorted = current.slice().sort((a, b) => a - b);
      res.push(sorted);
      return;
    }
    if (sum > target || idx >= candidates.length) return;
    for (let i = idx; i < candidates.length; i++) {
      current.push(candidates[i]);
      search(i, current, sum + candidates[i]);
      current.pop();
    }
  }
  search(0, [], 0);
  res.sort((a, b) => {
    for (let i = 0; i < Math.min(a.length, b.length); i++) {
      if (a[i] !== b[i]) return a[i] - b[i];
    }
    return a.length - b.length;
  });
  return res;
}""",
        complexity="Time: O(2^target) | Space: O(target)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function combinationSum(candidates, target) {
  const sorted = candidates.slice().sort((a, b) => a - b);
  const res = [];
  const current = [];
  function backtrack(idx, remain) {
    if (remain === 0) {
      res.push(current.slice());
      return;
    }
    for (let i = idx; i < sorted.length; i++) {
      if (sorted[i] > remain) break;
      current.push(sorted[i]);
      backtrack(i, remain - sorted[i]);
      current.pop();
    }
  }
  backtrack(0, target);
  res.sort((a, b) => {
    for (let i = 0; i < Math.min(a.length, b.length); i++) {
      if (a[i] !== b[i]) return a[i] - b[i];
    }
    return a.length - b.length;
  });
  return res;
}""",
        complexity="Time: O(N^(T/M)) | Space: O(T/M)",
        language="javascript",
    ),
    topic="backtracking",
    difficulty="Medium",
    pattern="backtracking / Unbounded pick",
    time_limit_ms=2000,
    seed=42,
    title="Combination Sum",
    slug="combination-sum",
)

py_brute_combination_sum = """def combinationSum(candidates: list[int], target: int) -> list[list[int]]:
    res = []

    def search(idx: int, current: list[int], cur_sum: int) -> None:
        if cur_sum == target:
            res.append(sorted(current))
            return
        if cur_sum > target or idx >= len(candidates):
            return
        for i in range(idx, len(candidates)):
            current.append(candidates[i])
            search(i, current, cur_sum + candidates[i])
            current.pop()

    search(0, [], 0)
    res.sort()
    return res
"""

py_optimal_combination_sum = """def combinationSum(candidates: list[int], target: int) -> list[list[int]]:
    arr = sorted(candidates)
    res = []
    current: list[int] = []

    def backtrack(idx: int, remain: int) -> None:
        if remain == 0:
            res.append(list(current))
            return
        for i in range(idx, len(arr)):
            if arr[i] > remain:
                break
            current.append(arr[i])
            backtrack(i, remain - arr[i])
            current.pop()

    backtrack(0, target)
    res.sort()
    return res
"""


def _gen_combination_sum_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[2], 1],
        [[2], 2],
        [[2], 4],
        [[2, 3, 6, 7], 7],
        [[2, 3, 5], 8],
        [[2], 3],
        [[3, 5], 11],
        [[8, 7, 4, 3], 11],
        [[2, 4, 6, 8], 10],
        [[7, 3, 2], 18],
    ]
    for _ in range(12):
        k = rng.randint(3, 6)
        cands = sorted(rng.sample(range(2, 25), k))
        t = rng.randint(8, 24)
        cases.append([cands, t])
    cases.append([[2, 3, 5, 7], 20])
    cases.append([[3, 5, 7, 11], 25])
    cases.append([[5, 10, 15, 20], 35])
    return cases


# ===========================================================================
# 4. letter-combinations-of-a-phone-number
# ===========================================================================
spec_letter_combinations = ProblemSpec(
    signature="function letterCombinations(digits: string)",
    statement="""# Letter Combinations of a Phone Number

Given a string containing digits from `2-9` inclusive, return all possible letter combinations that the number could represent according to standard telephone keypad mappings:
- `2`: `a, b, c`
- `3`: `d, e, f`
- `4`: `g, h, i`
- `5`: `j, k, l`
- `6`: `m, n, o`
- `7`: `p, q, r, s`
- `8`: `t, u, v`
- `9`: `w, x, y, z`

If the input string is empty, return an empty array `[]`. Return the combinations in lexicographical order.

Constraints: `0 <= digits.length <= 4`. `digits[i]` is a digit in the range `['2', '9']`.
""",
    brute_force=Algorithm(
        """function letterCombinations(digits) {
  if (!digits || digits.length === 0) return [];
  const map = {
    "2": ["a", "b", "c"], "3": ["d", "e", "f"], "4": ["g", "h", "i"],
    "5": ["j", "k", "l"], "6": ["m", "n", "o"], "7": ["p", "q", "r", "s"],
    "8": ["t", "u", "v"], "9": ["w", "x", "y", "z"]
  };
  let queue = [""];
  for (let i = 0; i < digits.length; i++) {
    const letters = map[digits[i]] || [];
    const nextQueue = [];
    for (let j = 0; j < queue.length; j++) {
      for (let k = 0; k < letters.length; k++) {
        nextQueue.push(queue[j] + letters[k]);
      }
    }
    queue = nextQueue;
  }
  queue.sort();
  return queue;
}""",
        complexity="Time: O(4ⁿ) | Space: O(4ⁿ)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function letterCombinations(digits) {
  if (!digits || digits.length === 0) return [];
  const map = {
    "2": ["a", "b", "c"], "3": ["d", "e", "f"], "4": ["g", "h", "i"],
    "5": ["j", "k", "l"], "6": ["m", "n", "o"], "7": ["p", "q", "r", "s"],
    "8": ["t", "u", "v"], "9": ["w", "x", "y", "z"]
  };
  const res = [];
  const path = [];
  function backtrack(idx) {
    if (idx === digits.length) {
      res.push(path.join(""));
      return;
    }
    const letters = map[digits[idx]] || [];
    for (let i = 0; i < letters.length; i++) {
      path.push(letters[i]);
      backtrack(idx + 1);
      path.pop();
    }
  }
  backtrack(0);
  res.sort();
  return res;
}""",
        complexity="Time: O(4ⁿ) | Space: O(n)",
        language="javascript",
    ),
    topic="backtracking",
    difficulty="Medium",
    pattern="backtracking / Digit map",
    time_limit_ms=2000,
    seed=42,
    title="Letter Combinations of a Phone Number",
    slug="letter-combinations-of-a-phone-number",
)

py_brute_letter_combinations = """def letterCombinations(digits: str) -> list[str]:
    if not digits:
        return []
    phone = {
        "2": ["a", "b", "c"], "3": ["d", "e", "f"], "4": ["g", "h", "i"],
        "5": ["j", "k", "l"], "6": ["m", "n", "o"], "7": ["p", "q", "r", "s"],
        "8": ["t", "u", "v"], "9": ["w", "x", "y", "z"]
    }
    queue = [""]
    for d in digits:
        queue = [prev + ch for prev in queue for ch in phone.get(d, [])]
    queue.sort()
    return queue
"""

py_optimal_letter_combinations = """def letterCombinations(digits: str) -> list[str]:
    if not digits:
        return []
    phone = {
        "2": "abc", "3": "def", "4": "ghi", "5": "jkl",
        "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz"
    }
    res = []
    path: list[str] = []

    def backtrack(idx: int) -> None:
        if idx == len(digits):
            res.append("".join(path))
            return
        for ch in phone.get(digits[idx], ""):
            path.append(ch)
            backtrack(idx + 1)
            path.pop()

    backtrack(0)
    res.sort()
    return res
"""


def _gen_letter_combinations_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [""],
        ["2"],
        ["3"],
        ["7"],
        ["9"],
        ["23"],
        ["27"],
        ["79"],
        ["45"],
        ["89"],
        ["234"],
        ["567"],
        ["789"],
        ["999"],
        ["222"],
        ["2345"],
        ["6789"],
        ["7777"],
        ["9876"],
        ["2468"],
    ]
    for _ in range(5):
        length = rng.randint(1, 4)
        digs = "".join(str(rng.randint(2, 9)) for _ in range(length))
        cases.append([digs])
    return cases


# ===========================================================================
# 5. palindrome-partitioning
# ===========================================================================
spec_palindrome_partitioning = ProblemSpec(
    signature="function partition(s: string)",
    statement="""# Palindrome Partitioning

Given a string `s`, partition `s` such that every substring of the partition is a palindrome.

Return all possible palindrome partitionings of `s`. The partitions must be returned sorted in lexicographical order.

Constraints: `1 <= s.length <= 16`. `s` contains only lowercase English letters.
""",
    brute_force=Algorithm(
        """function partition(s) {
  const res = [];
  const current = [];
  function isPal(str) {
    let l = 0, r = str.length - 1;
    while (l < r) {
      if (str[l++] !== str[r--]) return false;
    }
    return true;
  }
  function backtrack(start) {
    if (start === s.length) {
      res.push(current.slice());
      return;
    }
    for (let end = start + 1; end <= s.length; end++) {
      const sub = s.slice(start, end);
      if (isPal(sub)) {
        current.push(sub);
        backtrack(end);
        current.pop();
      }
    }
  }
  backtrack(0);
  res.sort((a, b) => {
    for (let i = 0; i < Math.min(a.length, b.length); i++) {
      const cmp = a[i].localeCompare(b[i]);
      if (cmp !== 0) return cmp;
    }
    return a.length - b.length;
  });
  return res;
}""",
        complexity="Time: O(n · 2ⁿ) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function partition(s) {
  const n = s.length;
  const isPal = Array.from({ length: n }, () => new Array(n).fill(false));
  for (let i = 0; i < n; i++) isPal[i][i] = true;
  for (let len = 2; len <= n; len++) {
    for (let i = 0; i <= n - len; i++) {
      const j = i + len - 1;
      if (s[i] === s[j]) {
        isPal[i][j] = len === 2 ? true : isPal[i + 1][j - 1];
      }
    }
  }
  const res = [];
  const current = [];
  function backtrack(start) {
    if (start === n) {
      res.push(current.slice());
      return;
    }
    for (let end = start; end < n; end++) {
      if (isPal[start][end]) {
        current.push(s.slice(start, end + 1));
        backtrack(end + 1);
        current.pop();
      }
    }
  }
  backtrack(0);
  res.sort((a, b) => {
    for (let i = 0; i < Math.min(a.length, b.length); i++) {
      const cmp = a[i].localeCompare(b[i]);
      if (cmp !== 0) return cmp;
    }
    return a.length - b.length;
  });
  return res;
}""",
        complexity="Time: O(n² + 2ⁿ) | Space: O(n²)",
        language="javascript",
    ),
    topic="backtracking",
    difficulty="Medium",
    pattern="backtracking / Cut positions",
    time_limit_ms=2000,
    seed=42,
    title="Palindrome Partitioning",
    slug="palindrome-partitioning",
)

py_brute_palindrome_partitioning = """def partition(s: str) -> list[list[str]]:
    res = []
    current = []

    def backtrack(start: int) -> None:
        if start == len(s):
            res.append(list(current))
            return
        for end in range(start + 1, len(s) + 1):
            sub = s[start:end]
            if sub == sub[::-1]:
                current.append(sub)
                backtrack(end)
                current.pop()

    backtrack(0)
    res.sort()
    return res
"""

py_optimal_palindrome_partitioning = """def partition(s: str) -> list[list[str]]:
    n = len(s)
    is_pal = [[False] * n for _ in range(n)]
    for i in range(n):
        is_pal[i][i] = True
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                is_pal[i][j] = True if length == 2 else is_pal[i + 1][j - 1]

    res = []
    current: list[str] = []

    def backtrack(start: int) -> None:
        if start == n:
            res.append(list(current))
            return
        for end in range(start, n):
            if is_pal[start][end]:
                current.append(s[start : end + 1])
                backtrack(end + 1)
                current.pop()

    backtrack(0)
    res.sort()
    return res
"""


def _gen_palindrome_partitioning_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        ["a"],
        ["aa"],
        ["ab"],
        ["aab"],
        ["aba"],
        ["racecar"],
        ["noon"],
        ["civic"],
        ["bb"],
        ["efe"],
        ["abcba"],
        ["cddc"],
        ["abacaba"],
        ["aaaa"],
        ["aaaaa"],
        ["aaaaaa"],
        ["abcde"],
        ["radar"],
        ["madam"],
        ["level"],
    ]
    for _ in range(5):
        s = "".join(rng.choice(["a", "b", "c"]) for _ in range(rng.randint(3, 7)))
        cases.append([s])
    return cases


# ===========================================================================
# 6. word-search
# ===========================================================================
spec_word_search = ProblemSpec(
    signature="function exist(board: string[][], word: string)",
    statement="""# Word Search

Given an `m x n` grid of characters `board` and a string `word`, return `true` if `word` exists in the grid, or `false` otherwise.

The word can be constructed from letters of sequentially adjacent cells, where adjacent cells are horizontally or vertically neighboring. The same letter cell may not be used more than once in a single word path.

Constraints: `1 <= board.length, board[i].length <= 6`, `1 <= word.length <= 15`. `board` and `word` consist only of lowercase English letters.
""",
    brute_force=Algorithm(
        """function exist(board, word) {
  const m = board.length, n = board[0].length;
  const visited = Array.from({ length: m }, () => new Array(n).fill(false));
  function dfs(r, c, k) {
    if (k === word.length) return true;
    if (r < 0 || r >= m || c < 0 || c >= n || visited[r][c] || board[r][c] !== word[k]) {
      return false;
    }
    visited[r][c] = true;
    const found = dfs(r + 1, c, k + 1) || dfs(r - 1, c, k + 1) || dfs(r, c + 1, k + 1) || dfs(r, c - 1, k + 1);
    visited[r][c] = false;
    return found;
  }
  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      if (dfs(i, j, 0)) return true;
    }
  }
  return false;
}""",
        complexity="Time: O(m · n · 4ᴸ) | Space: O(m · n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function exist(board, word) {
  const m = board.length, n = board[0].length;
  if (word.length > m * n) return false;
  const boardCount = {};
  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      boardCount[board[i][j]] = (boardCount[board[i][j]] || 0) + 1;
    }
  }
  const wordCount = {};
  for (let i = 0; i < word.length; i++) {
    wordCount[word[i]] = (wordCount[word[i]] || 0) + 1;
    if ((boardCount[word[i]] || 0) < wordCount[word[i]]) return false;
  }
  let targetWord = word;
  if ((boardCount[word[0]] || 0) > (boardCount[word[word.length - 1]] || 0)) {
    targetWord = word.split("").reverse().join("");
  }
  function dfs(r, c, k) {
    if (k === targetWord.length) return true;
    if (r < 0 || r >= m || c < 0 || c >= n || board[r][c] !== targetWord[k]) return false;
    const saved = board[r][c];
    board[r][c] = "#";
    const found = dfs(r + 1, c, k + 1) || dfs(r - 1, c, k + 1) || dfs(r, c + 1, k + 1) || dfs(r, c - 1, k + 1);
    board[r][c] = saved;
    return found;
  }
  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      if (board[i][j] === targetWord[0] && dfs(i, j, 0)) return true;
    }
  }
  return false;
}""",
        complexity="Time: O(m · n · 4ᴸ) | Space: O(L)",
        language="javascript",
    ),
    topic="backtracking",
    difficulty="Medium",
    pattern="backtracking / DFS grid",
    time_limit_ms=2000,
    seed=42,
    title="Word Search",
    slug="word-search",
)

py_brute_word_search = """def exist(board: list[list[str]], word: str) -> bool:
    m, n = len(board), len(board[0])
    visited = [[False] * n for _ in range(m)]

    def dfs(r: int, c: int, k: int) -> bool:
        if k == len(word):
            return True
        if r < 0 or r >= m or c < 0 or c >= n or visited[r][c] or board[r][c] != word[k]:
            return False
        visited[r][c] = True
        found = (
            dfs(r + 1, c, k + 1)
            or dfs(r - 1, c, k + 1)
            or dfs(r, c + 1, k + 1)
            or dfs(r, c - 1, k + 1)
        )
        visited[r][c] = False
        return found

    for i in range(m):
        for j in range(n):
            if dfs(i, j, 0):
                return True
    return False
"""

py_optimal_word_search = """def exist(board: list[list[str]], word: str) -> bool:
    m, n = len(board), len(board[0])
    if len(word) > m * n:
        return False
    from collections import Counter
    board_cnt = Counter(ch for row in board for ch in row)
    word_cnt = Counter(word)
    for ch, count in word_cnt.items():
        if board_cnt[ch] < count:
            return False
    target = word
    if board_cnt[word[0]] > board_cnt[word[-1]]:
        target = word[::-1]

    def dfs(r: int, c: int, k: int) -> bool:
        if k == len(target):
            return True
        if r < 0 or r >= m or c < 0 or c >= n or board[r][c] != target[k]:
            return False
        saved = board[r][c]
        board[r][c] = "#"
        found = (
            dfs(r + 1, c, k + 1)
            or dfs(r - 1, c, k + 1)
            or dfs(r, c + 1, k + 1)
            or dfs(r, c - 1, k + 1)
        )
        board[r][c] = saved
        return found

    for i in range(m):
        for j in range(n):
            if board[i][j] == target[0] and dfs(i, j, 0):
                return True
    return False
"""


def _gen_word_search_inputs(rng: random.Random) -> list[list[Any]]:
    board1 = [["a", "b", "c", "e"], ["s", "f", "c", "s"], ["a", "d", "e", "e"]]
    cases: list[list[Any]] = [
        [[["a"]], "a"],
        [[["a"]], "b"],
        [[["a", "b"], ["c", "d"]], "abcd"],
        [[["a", "b"], ["c", "d"]], "abdc"],
        [board1, "abcced"],
        [board1, "see"],
        [board1, "abcb"],
        [board1, "asadeee"],
        [[["a", "a", "a"], ["a", "b", "a"], ["a", "a", "a"]], "aba"],
        [[["a", "a", "a"], ["a", "b", "a"], ["a", "a", "a"]], "abac"],
        [[["c", "a", "a"], ["a", "a", "a"], ["b", "c", "d"]], "aab"],
        [[["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i"]], "beh"],
        [[["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i"]], "cfi"],
        [[["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i"]], "adg"],
        [[["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i"]], "ihgfedcba"],
        [[["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i"]], "xyz"],
        [[["a", "a"], ["a", "a"]], "aaaa"],
        [[["a", "a"], ["a", "a"]], "aaaaa"],
        [[["z"]], "z"],
        [[["z"]], "a"],
    ]
    return cases


# ===========================================================================
# 7. n-queens-count
# ===========================================================================
spec_n_queens_count = ProblemSpec(
    signature="function totalNQueens(n: number)",
    statement="""# N-Queens Count

The n-queens puzzle is the problem of placing `n` chess queens on an `n x n` chessboard so that no two queens attack each other.

Given an integer `n`, return the number of distinct solutions to the n-queens puzzle.

Constraints: `1 <= n <= 9`.
""",
    brute_force=Algorithm(
        """function totalNQueens(n) {
  let count = 0;
  const cols = new Array(n).fill(-1);
  function isValid(row, col) {
    for (let r = 0; r < row; r++) {
      const c = cols[r];
      if (c === col || Math.abs(r - row) === Math.abs(c - col)) {
        return false;
      }
    }
    return true;
  }
  function solve(row) {
    if (row === n) {
      count++;
      return;
    }
    for (let col = 0; col < n; col++) {
      if (isValid(row, col)) {
        cols[row] = col;
        solve(row + 1);
        cols[row] = -1;
      }
    }
  }
  solve(0);
  return count;
}""",
        complexity="Time: O(n!) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function totalNQueens(n) {
  let count = 0;
  function solve(row, cols, diag1, diag2) {
    if (row === n) {
      count++;
      return;
    }
    let available = ((1 << n) - 1) & ~(cols | diag1 | diag2);
    while (available !== 0) {
      const bit = available & -available;
      available ^= bit;
      solve(row + 1, cols | bit, (diag1 | bit) << 1, (diag2 | bit) >> 1);
    }
  }
  solve(0, 0, 0, 0);
  return count;
}""",
        complexity="Time: O(n!) | Space: O(n)",
        language="javascript",
    ),
    topic="backtracking",
    difficulty="Hard",
    pattern="backtracking / Constraint place",
    time_limit_ms=2000,
    seed=42,
    title="N-Queens Count",
    slug="n-queens-count",
)

py_brute_n_queens_count = """def totalNQueens(n: int) -> int:
    cols = [-1] * n
    count = 0

    def is_valid(row: int, col: int) -> bool:
        for r in range(row):
            c = cols[r]
            if c == col or abs(r - row) == abs(c - col):
                return False
        return True

    def solve(row: int) -> None:
        nonlocal count
        if row == n:
            count += 1
            return
        for col in range(n):
            if is_valid(row, col):
                cols[row] = col
                solve(row + 1)
                cols[row] = -1

    solve(0)
    return count
"""

py_optimal_n_queens_count = """def totalNQueens(n: int) -> int:
    count = 0
    all_mask = (1 << n) - 1

    def solve(row: int, cols: int, diag1: int, diag2: int) -> None:
        nonlocal count
        if row == n:
            count += 1
            return
        available = all_mask & ~(cols | diag1 | diag2)
        while available:
            bit = available & -available
            available ^= bit
            solve(row + 1, cols | bit, (diag1 | bit) << 1, (diag2 | bit) >> 1)

    solve(0, 0, 0, 0)
    return count
"""


def _gen_n_queens_count_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [1],
        [2],
        [3],
        [4],
        [5],
        [6],
        [7],
        [8],
        [9],
        [1],
        [2],
        [3],
        [4],
        [5],
        [6],
        [7],
        [8],
        [9],
        [4],
        [8],
    ]
    return cases


# ===========================================================================
# 8. single-number
# ===========================================================================
spec_single_number = ProblemSpec(
    signature="function singleNumber(nums: number[])",
    statement="""# Single Number

Given a non-empty array of integers `nums`, every element appears twice except for one. Find that single element.

You must implement a solution with linear runtime complexity and use only constant extra space.

Constraints: `1 <= nums.length <= 101` (`nums.length` is odd) and `-30000 <= nums[i] <= 30000`. Each element appears twice except one which appears once.
""",
    brute_force=Algorithm(
        """function singleNumber(nums) {
  const counts = {};
  for (let i = 0; i < nums.length; i++) {
    counts[nums[i]] = (counts[nums[i]] || 0) + 1;
  }
  for (const k in counts) {
    if (counts[k] === 1) return Number(k);
  }
  return nums[0];
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function singleNumber(nums) {
  let res = 0;
  for (let i = 0; i < nums.length; i++) {
    res ^= nums[i];
  }
  return res;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    topic="bit-manipulation",
    difficulty="Easy",
    pattern="bit-manipulation / XOR cancel",
    time_limit_ms=2000,
    seed=42,
    title="Single Number",
    slug="single-number",
)

py_brute_single_number = """def singleNumber(nums: list[int]) -> int:
    from collections import Counter
    counts = Counter(nums)
    for num, count in counts.items():
        if count == 1:
            return num
    return nums[0]
"""

py_optimal_single_number = """def singleNumber(nums: list[int]) -> int:
    res = 0
    for num in nums:
        res ^= num
    return res
"""


def _gen_single_number_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[1]],
        [[2, 2, 1]],
        [[4, 1, 2, 1, 2]],
        [[-1]],
        [[-1, -1, -2]],
        [[0, 1, 0]],
        [[100, 200, 100]],
        [[-50, -50, 25]],
        [[999, 888, 999]],
        [[0]],
    ]
    for _ in range(12):
        pair_count = rng.randint(2, 10)
        singles = rng.sample(range(-1000, 1001), pair_count + 1)
        lone = singles[0]
        pairs = singles[1:]
        arr = [lone]
        for p in pairs:
            arr.extend([p, p])
        rng.shuffle(arr)
        cases.append([arr])
    # Stress case
    lone = 12345
    pairs = rng.sample(range(-30000, 30000), 50)
    arr = [lone]
    for p in pairs:
        arr.extend([p, p])
    rng.shuffle(arr)
    cases.append([arr])
    return cases


# ===========================================================================
# 9. number-of-1-bits
# ===========================================================================
spec_number_of_1_bits = ProblemSpec(
    signature="function hammingWeight(n: number)",
    statement="""# Number of 1 Bits

Given a 32-bit unsigned integer `n`, return the number of `1` bits it has (also known as the Hamming weight).

Constraints: `0 <= n <= 4294967295` (32-bit unsigned integer).
""",
    brute_force=Algorithm(
        """function hammingWeight(n) {
  let count = 0;
  for (let i = 0; i < 32; i++) {
    count += (n >>> i) & 1;
  }
  return count;
}""",
        complexity="Time: O(32) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function hammingWeight(n) {
  let count = 0;
  let val = n >>> 0;
  while (val !== 0) {
    val = (val & (val - 1)) >>> 0;
    count++;
  }
  return count;
}""",
        complexity="Time: O(k) | Space: O(1)",
        language="javascript",
    ),
    topic="bit-manipulation",
    difficulty="Easy",
    pattern="bit-manipulation / n&(n-1)",
    time_limit_ms=2000,
    seed=42,
    title="Number of 1 Bits",
    slug="number-of-1-bits",
)

py_brute_number_of_1_bits = """def hammingWeight(n: int) -> int:
    count = 0
    for i in range(32):
        count += (n >> i) & 1
    return count
"""

py_optimal_number_of_1_bits = """def hammingWeight(n: int) -> int:
    count = 0
    val = n & 0xFFFFFFFF
    while val > 0:
        val &= val - 1
        count += 1
    return count
"""


def _gen_number_of_1_bits_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [0],
        [1],
        [2],
        [3],
        [4],
        [7],
        [11],
        [128],
        [255],
        [2147483648],
        [4294967295],
        [4294967294],
        [1431655765],  # alternating 0101...
        [2863311530],  # alternating 1010...
    ]
    for _ in range(10):
        cases.append([rng.randint(0, 0xFFFFFFFF)])
    return cases


# ===========================================================================
# 10. reverse-bits
# ===========================================================================
spec_reverse_bits = ProblemSpec(
    signature="function reverseBits(n: number)",
    statement="""# Reverse Bits

Reverse the bits of a given 32-bit unsigned integer and return the resulting 32-bit unsigned integer.

Constraints: `0 <= n <= 4294967295` (32-bit unsigned integer).
""",
    brute_force=Algorithm(
        """function reverseBits(n) {
  let res = 0;
  for (let i = 0; i < 32; i++) {
    res = (res * 2) + ((n >>> i) & 1);
  }
  return res >>> 0;
}""",
        complexity="Time: O(32) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function reverseBits(n) {
  n = ((n >>> 16) | (n << 16)) >>> 0;
  n = (((n & 0xff00ff00) >>> 8) | ((n & 0x00ff00ff) << 8)) >>> 0;
  n = (((n & 0xf0f0f0f0) >>> 4) | ((n & 0x0f0f0f0f) << 4)) >>> 0;
  n = (((n & 0xcccccccc) >>> 2) | ((n & 0x33333333) << 2)) >>> 0;
  n = (((n & 0xaaaaaaaa) >>> 1) | ((n & 0x55555555) << 1)) >>> 0;
  return n >>> 0;
}""",
        complexity="Time: O(1) | Space: O(1)",
        language="javascript",
    ),
    topic="bit-manipulation",
    difficulty="Easy",
    pattern="bit-manipulation / Mirror",
    time_limit_ms=2000,
    seed=42,
    title="Reverse Bits",
    slug="reverse-bits",
)

py_brute_reverse_bits = """def reverseBits(n: int) -> int:
    res = 0
    for i in range(32):
        res = (res << 1) | ((n >> i) & 1)
    return res
"""

py_optimal_reverse_bits = """def reverseBits(n: int) -> int:
    n = ((n >> 16) | ((n << 16) & 0xFFFFFFFF))
    n = (((n & 0xFF00FF00) >> 8) | ((n & 0x00FF00FF) << 8))
    n = (((n & 0xF0F0F0F0) >> 4) | ((n & 0x0F0F0F0F) << 4))
    n = (((n & 0xCCCCCCCC) >> 2) | ((n & 0x33333333) << 2))
    n = (((n & 0xAAAAAAAA) >> 1) | ((n & 0x55555555) << 1))
    return n & 0xFFFFFFFF
"""


def _gen_reverse_bits_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [0],
        [1],
        [2],
        [43261596],
        [4294967295],
        [2147483648],
        [1073741824],
        [3],
        [255],
        [65535],
        [16777215],
        [1431655765],
    ]
    for _ in range(12):
        cases.append([rng.randint(0, 0xFFFFFFFF)])
    return cases


# ===========================================================================
# 11. sum-of-two-integers
# ===========================================================================
spec_sum_of_two_integers = ProblemSpec(
    signature="function getSum(a: number, b: number)",
    statement="""# Sum of Two Integers

Given two integers `a` and `b`, return the sum of the two integers without using the operators `+` and `-`.

Calculations must follow standard 32-bit signed two's complement integer arithmetic.

Constraints: `-1000 <= a, b <= 1000`.
""",
    brute_force=Algorithm(
        """function getSum(a, b) {
  let res = 0;
  let carry = 0;
  for (let i = 0; i < 32; i++) {
    const bitA = (a >> i) & 1;
    const bitB = (b >> i) & 1;
    const sum = bitA ^ bitB ^ carry;
    carry = (bitA & bitB) | (bitA & carry) | (bitB & carry);
    res |= (sum << i);
  }
  return res;
}""",
        complexity="Time: O(32) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function getSum(a, b) {
  while (b !== 0) {
    const carry = (a & b) << 1;
    a = a ^ b;
    b = carry;
  }
  return a;
}""",
        complexity="Time: O(1) | Space: O(1)",
        language="javascript",
    ),
    topic="bit-manipulation",
    difficulty="Medium",
    pattern="bit-manipulation / Carry loop",
    time_limit_ms=2000,
    seed=42,
    title="Sum of Two Integers",
    slug="sum-of-two-integers",
)

py_brute_sum_of_two_integers = """def getSum(a: int, b: int) -> int:
    res = 0
    carry = 0
    for i in range(32):
        bit_a = (a >> i) & 1
        bit_b = (b >> i) & 1
        sum_bit = bit_a ^ bit_b ^ carry
        carry = (bit_a & bit_b) | (bit_a & carry) | (bit_b & carry)
        res |= (sum_bit << i)
    mask = 0xFFFFFFFF
    res &= mask
    return res if res <= 0x7FFFFFFF else ~(res ^ mask)
"""

py_optimal_sum_of_two_integers = """def getSum(a: int, b: int) -> int:
    mask = 0xFFFFFFFF
    while (b & mask) != 0:
        carry = (a & b) << 1
        a = (a ^ b) & mask
        b = carry & mask
    return a if a <= 0x7FFFFFFF else ~(a ^ mask)
"""


def _gen_sum_of_two_integers_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [1, 2],
        [2, 3],
        [0, 0],
        [-1, 1],
        [-2, 3],
        [-5, -7],
        [100, -100],
        [500, 500],
        [-1000, 1000],
        [-1000, -1000],
        [0, 15],
        [-15, 0],
        [12, -4],
        [-4, 12],
    ]
    for _ in range(12):
        cases.append([rng.randint(-1000, 1000), rng.randint(-1000, 1000)])
    return cases


# ===========================================================================
# 12. power-of-two
# ===========================================================================
spec_power_of_two = ProblemSpec(
    signature="function isPowerOfTwo(n: number)",
    statement="""# Power of Two

Given an integer `n`, return `true` if it is a power of two. Otherwise, return `false`.

An integer `n` is a power of two if there exists an integer `x` such that `n == 2ˣ`.

Constraints: `-2³¹ <= n <= 2³¹ - 1`.
""",
    brute_force=Algorithm(
        """function isPowerOfTwo(n) {
  if (n <= 0) return false;
  while (n % 2 === 0) {
    n = Math.floor(n / 2);
  }
  return n === 1;
}""",
        complexity="Time: O(log n) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function isPowerOfTwo(n) {
  return n > 0 && (n & (n - 1)) === 0;
}""",
        complexity="Time: O(1) | Space: O(1)",
        language="javascript",
    ),
    topic="bit-manipulation",
    difficulty="Easy",
    pattern="bit-manipulation / n&(n-1)",
    time_limit_ms=2000,
    seed=42,
    title="Power of Two",
    slug="power-of-two",
)

py_brute_power_of_two = """def isPowerOfTwo(n: int) -> bool:
    if n <= 0:
        return False
    while n % 2 == 0:
        n //= 2
    return n == 1
"""

py_optimal_power_of_two = """def isPowerOfTwo(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0
"""


def _gen_power_of_two_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [1],
        [16],
        [3],
        [0],
        [-16],
        [-1],
        [2],
        [4],
        [8],
        [1024],
        [1073741824],
        [6],
        [5],
        [2147483647],
        [-2147483648],
    ]
    for _ in range(10):
        if rng.random() < 0.5:
            shift = rng.randint(0, 30)
            cases.append([1 << shift])
        else:
            val = rng.randint(2, 10000)
            if (val & (val - 1)) == 0:
                val += 1
            cases.append([val])
    return cases


# ===========================================================================
# 13. sort-an-array
# ===========================================================================
spec_sort_an_array = ProblemSpec(
    signature="function sortArray(nums: number[])",
    statement="""# Sort an Array

Given an array of integers `nums`, sort the array in ascending numerical order and return it.

You must solve the problem with an efficient divide-and-conquer comparison sorting algorithm (such as merge sort) with `O(n log n)` time complexity.

Constraints: `0 <= nums.length <= 1000` and `-50000 <= nums[i] <= 50000`.
""",
    brute_force=Algorithm(
        """function sortArray(nums) {
  const arr = nums.slice();
  for (let i = 1; i < arr.length; i++) {
    const key = arr[i];
    let j = i - 1;
    while (j >= 0 && arr[j] > key) {
      arr[j + 1] = arr[j];
      j--;
    }
    arr[j + 1] = key;
  }
  return arr;
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function sortArray(nums) {
  const arr = nums.slice();
  const temp = new Array(arr.length);
  function mergeSort(left, right) {
    if (left >= right) return;
    const mid = Math.floor((left + right) / 2);
    mergeSort(left, mid);
    mergeSort(mid + 1, right);
    let i = left, j = mid + 1, k = left;
    while (i <= mid && j <= right) {
      if (arr[i] <= arr[j]) temp[k++] = arr[i++];
      else temp[k++] = arr[j++];
    }
    while (i <= mid) temp[k++] = arr[i++];
    while (j <= right) temp[k++] = arr[j++];
    for (let p = left; p <= right; p++) arr[p] = temp[p];
  }
  mergeSort(0, arr.length - 1);
  return arr;
}""",
        complexity="Time: O(n log n) | Space: O(n)",
        language="javascript",
    ),
    topic="sorting",
    difficulty="Medium",
    pattern="sorting / Merge sort",
    time_limit_ms=2000,
    seed=42,
    title="Sort an Array",
    slug="sort-an-array",
)

py_brute_sort_an_array = """def sortArray(nums: list[int]) -> list[int]:
    arr = list(nums)
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr
"""

py_optimal_sort_an_array = """def sortArray(nums: list[int]) -> list[int]:
    arr = list(nums)
    temp = [0] * len(arr)

    def merge_sort(left: int, right: int) -> None:
        if left >= right:
            return
        mid = (left + right) // 2
        merge_sort(left, mid)
        merge_sort(mid + 1, right)
        i, j, k = left, mid + 1, left
        while i <= mid and j <= right:
            if arr[i] <= arr[j]:
                temp[k] = arr[i]
                i += 1
            else:
                temp[k] = arr[j]
                j += 1
            k += 1
        while i <= mid:
            temp[k] = arr[i]
            i += 1
            k += 1
        while j <= right:
            temp[k] = arr[j]
            j += 1
            k += 1
        for p in range(left, right + 1):
            arr[p] = temp[p]

    merge_sort(0, len(arr) - 1)
    return arr
"""


def _gen_sort_an_array_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[]],
        [[1]],
        [[2, 1]],
        [[5, 2, 3, 1]],
        [[5, 1, 1, 2, 0, 0]],
        [[-4, 0, 7, 4, 9, -5, -1, 0, -7, -1]],
        [[1, 2, 3, 4, 5]],
        [[5, 4, 3, 2, 1]],
        [[3, 3, 3, 3, 3]],
        [[0, -1, -2, -3]],
    ]
    for _ in range(12):
        n = rng.randint(10, 50)
        cases.append([[rng.randint(-1000, 1000) for _ in range(n)]])
    cases.append([[rng.randint(-50000, 50000) for _ in range(100)]])
    cases.append([[rng.randint(-50000, 50000) for _ in range(200)]])
    return cases


# ===========================================================================
# 14. largest-number
# ===========================================================================
spec_largest_number = ProblemSpec(
    signature="function largestNumber(nums: number[])",
    statement="""# Largest Number

Given a list of non-negative integers `nums`, arrange them such that they form the largest possible number and return it as a string.

Since the result may be very large, return a string instead of an integer. If the highest value is `"0"`, return `"0"`.

Constraints: `1 <= nums.length <= 100` and `0 <= nums[i] <= 10⁹`.
""",
    brute_force=Algorithm(
        """function largestNumber(nums) {
  const strs = nums.map(String);
  for (let i = 0; i < strs.length; i++) {
    for (let j = 0; j < strs.length - 1; j++) {
      if ((strs[j + 1] + strs[j]).localeCompare(strs[j] + strs[j + 1]) > 0) {
        const temp = strs[j];
        strs[j] = strs[j + 1];
        strs[j + 1] = temp;
      }
    }
  }
  if (strs[0] === "0") return "0";
  return strs.join("");
}""",
        complexity="Time: O(n² · k) | Space: O(n · k)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function largestNumber(nums) {
  const strs = nums.map(String);
  strs.sort((a, b) => (b + a).localeCompare(a + b));
  if (strs[0] === "0") return "0";
  return strs.join("");
}""",
        complexity="Time: O(n log n · k) | Space: O(n · k)",
        language="javascript",
    ),
    topic="sorting",
    difficulty="Medium",
    pattern="sorting / Custom comparator",
    time_limit_ms=2000,
    seed=42,
    title="Largest Number",
    slug="largest-number",
)

py_brute_largest_number = """def largestNumber(nums: list[int]) -> str:
    strs = [str(x) for x in nums]
    for i in range(len(strs)):
        for j in range(len(strs) - 1):
            if strs[j + 1] + strs[j] > strs[j] + strs[j + 1]:
                strs[j], strs[j + 1] = strs[j + 1], strs[j]
    if strs[0] == "0":
        return "0"
    return "".join(strs)
"""

py_optimal_largest_number = """def largestNumber(nums: list[int]) -> str:
    from functools import cmp_to_key

    strs = [str(x) for x in nums]

    def cmp(a: str, b: str) -> int:
        if a + b > b + a:
            return -1
        elif a + b < b + a:
            return 1
        return 0

    strs.sort(key=cmp_to_key(cmp))
    if strs[0] == "0":
        return "0"
    return "".join(strs)
"""


def _gen_largest_number_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[10, 2]],
        [[3, 30, 34, 5, 9]],
        [[0, 0]],
        [[1]],
        [[0]],
        [[111311, 1113]],
        [[12, 121]],
        [[8308, 8308, 830]],
        [[0, 0, 0, 0]],
        [[9, 98, 97, 99]],
        [[4, 40, 44, 45, 43]],
        [[100, 10, 1]],
    ]
    for _ in range(10):
        n = rng.randint(3, 10)
        cases.append([[rng.randint(0, 1000) for _ in range(n)]])
    cases.append([[rng.randint(0, 1000000) for _ in range(30)]])
    return cases


# ===========================================================================
# 15. wiggle-sort-ii-lite
# ===========================================================================
spec_wiggle_sort_ii_lite = ProblemSpec(
    signature="function wiggleSort(nums: number[])",
    statement="""# Wiggle Sort II Lite

Given an integer array `nums`, reorder it such that `nums[0] < nums[1] > nums[2] < nums[3]...`.

Duplicate values may be present. To guarantee a unique and deterministic output across implementations, your solution must sort the elements in ascending order, partition them into a smaller half of length `⌈n/2⌉` and a larger half of length `⌊n/2⌋`, and interleave them in reverse order:
- Even indices `0, 2, 4, ...` receive elements backwards from the end of the smaller half.
- Odd indices `1, 3, 5, ...` receive elements backwards from the end of the larger half.

Return the rearranged array.

Constraints: `0 <= nums.length <= 100` and `0 <= nums[i] <= 1000`. You may assume a valid wiggle arrangement always exists for the given inputs.
""",
    brute_force=Algorithm(
        """function wiggleSort(nums) {
  const n = nums.length;
  if (n <= 1) return nums.slice();
  const sorted = nums.slice();
  for (let i = 0; i < n; i++) {
    let minIdx = i;
    for (let j = i + 1; j < n; j++) {
      if (sorted[j] < sorted[minIdx]) minIdx = j;
    }
    const temp = sorted[i];
    sorted[i] = sorted[minIdx];
    sorted[minIdx] = temp;
  }
  const mid = Math.floor((n + 1) / 2);
  const left = sorted.slice(0, mid);
  const right = sorted.slice(mid);
  const res = new Array(n);
  let l = left.length - 1;
  let r = right.length - 1;
  for (let i = 0; i < n; i++) {
    if (i % 2 === 0) res[i] = left[l--];
    else res[i] = right[r--];
  }
  return res;
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function wiggleSort(nums) {
  const n = nums.length;
  if (n <= 1) return nums.slice();
  const sorted = nums.slice().sort((a, b) => a - b);
  const mid = Math.floor((n + 1) / 2);
  const left = sorted.slice(0, mid);
  const right = sorted.slice(mid);
  const res = new Array(n);
  let l = left.length - 1;
  let r = right.length - 1;
  for (let i = 0; i < n; i++) {
    if (i % 2 === 0) res[i] = left[l--];
    else res[i] = right[r--];
  }
  return res;
}""",
        complexity="Time: O(n log n) | Space: O(n)",
        language="javascript",
    ),
    topic="sorting",
    difficulty="Medium",
    pattern="sorting / Interleave halves",
    time_limit_ms=2000,
    seed=42,
    title="Wiggle Sort II Lite",
    slug="wiggle-sort-ii-lite",
)

py_brute_wiggle_sort_ii_lite = """def wiggleSort(nums: list[int]) -> list[int]:
    n = len(nums)
    if n <= 1:
        return list(nums)
    sorted_nums = list(nums)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if sorted_nums[j] < sorted_nums[min_idx]:
                min_idx = j
        sorted_nums[i], sorted_nums[min_idx] = sorted_nums[min_idx], sorted_nums[i]
    mid = (n + 1) // 2
    left = sorted_nums[:mid]
    right = sorted_nums[mid:]
    res = [0] * n
    l, r = len(left) - 1, len(right) - 1
    for i in range(n):
        if i % 2 == 0:
            res[i] = left[l]
            l -= 1
        else:
            res[i] = right[r]
            r -= 1
    return res
"""

py_optimal_wiggle_sort_ii_lite = """def wiggleSort(nums: list[int]) -> list[int]:
    n = len(nums)
    if n <= 1:
        return list(nums)
    sorted_nums = sorted(nums)
    mid = (n + 1) // 2
    left = sorted_nums[:mid]
    right = sorted_nums[mid:]
    res = [0] * n
    l, r = len(left) - 1, len(right) - 1
    for i in range(n):
        if i % 2 == 0:
            res[i] = left[l]
            l -= 1
        else:
            res[i] = right[r]
            r -= 1
    return res
"""


def _gen_wiggle_sort_ii_lite_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[]],
        [[1]],
        [[1, 2]],
        [[1, 5, 1, 1, 6, 4]],
        [[1, 3, 2, 2, 3, 1]],
        [[4, 5, 5, 6]],
        [[1, 1, 2, 1, 2, 2, 1]],
        [[3, 2, 1, 4, 5]],
        [[1, 2, 3, 4, 5, 6]],
        [[6, 5, 4, 3, 2, 1]],
        [[1, 2, 2, 3]],
    ]
    for _ in range(10):
        n = rng.randint(4, 15)
        vals = [rng.randint(1, 20) for _ in range(n)]
        cases.append([vals])
    cases.append([[rng.randint(1, 100) for _ in range(40)]])
    cases.append([[rng.randint(1, 100) for _ in range(60)]])
    return cases


# ===========================================================================
# 16. merge-sorted-array
# ===========================================================================
spec_merge_sorted_array = ProblemSpec(
    signature="function merge(nums1: number[], m: number, nums2: number[], n: number)",
    statement="""# Merge Sorted Array

You are given two integer arrays `nums1` and `nums2`, sorted in non-decreasing order, and two integers `m` and `n`, representing the number of initial elements in `nums1` and `nums2` respectively.

`nums1` has a total length of `m + n`, where the first `m` elements denote the values to be merged, and the last `n` elements are set to `0` and should be ignored. `nums2` has a length of `n`.

Merge `nums2` into `nums1` as one sorted array in non-decreasing order and return `nums1`.

Constraints: `nums1.length == m + n`, `nums2.length == n`, `0 <= m, n <= 100`, `1 <= m + n <= 200`, and `-1000 <= nums1[i], nums2[j] <= 1000`.
""",
    brute_force=Algorithm(
        """function merge(nums1, m, nums2, n) {
  for (let i = 0; i < n; i++) {
    nums1[m + i] = nums2[i];
  }
  nums1.sort((a, b) => a - b);
  return nums1;
}""",
        complexity="Time: O((m + n) log(m + n)) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function merge(nums1, m, nums2, n) {
  let p1 = m - 1;
  let p2 = n - 1;
  let p = m + n - 1;
  while (p2 >= 0) {
    if (p1 >= 0 && nums1[p1] > nums2[p2]) {
      nums1[p] = nums1[p1--];
    } else {
      nums1[p] = nums2[p2--];
    }
    p--;
  }
  return nums1;
}""",
        complexity="Time: O(m + n) | Space: O(1)",
        language="javascript",
    ),
    topic="sorting",
    difficulty="Easy",
    pattern="sorting / Back-fill",
    time_limit_ms=2000,
    seed=42,
    title="Merge Sorted Array",
    slug="merge-sorted-array",
)

py_brute_merge_sorted_array = """def merge(nums1: list[int], m: int, nums2: list[int], n: int) -> list[int]:
    for i in range(n):
        nums1[m + i] = nums2[i]
    nums1.sort()
    return nums1
"""

py_optimal_merge_sorted_array = """def merge(nums1: list[int], m: int, nums2: list[int], n: int) -> list[int]:
    p1 = m - 1
    p2 = n - 1
    p = m + n - 1
    while p2 >= 0:
        if p1 >= 0 and nums1[p1] > nums2[p2]:
            nums1[p] = nums1[p1]
            p1 -= 1
        else:
            nums1[p] = nums2[p2]
            p2 -= 1
        p -= 1
    return nums1
"""


def _gen_merge_sorted_array_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[1, 2, 3, 0, 0, 0], 3, [2, 5, 6], 3],
        [[1], 1, [], 0],
        [[0], 0, [1], 1],
        [[2, 0], 1, [1], 1],
        [[4, 5, 6, 0, 0, 0], 3, [1, 2, 3], 3],
        [[1, 1, 1, 0, 0, 0], 3, [1, 1, 1], 3],
        [[0, 0, 0], 0, [2, 4, 6], 3],
        [[-3, -1, 0, 0], 2, [-2, 1], 2],
    ]
    for _ in range(12):
        m = rng.randint(1, 15)
        n = rng.randint(1, 15)
        vals1 = sorted(rng.randint(-100, 100) for _ in range(m))
        vals2 = sorted(rng.randint(-100, 100) for _ in range(n))
        nums1 = vals1 + [0] * n
        cases.append([nums1, m, vals2, n])
    m = 50
    n = 50
    v1 = sorted(rng.randint(-1000, 1000) for _ in range(m))
    v2 = sorted(rng.randint(-1000, 1000) for _ in range(n))
    cases.append([v1 + [0] * n, m, v2, n])
    return cases


# ===========================================================================
# 17. jump-game-ii
# ===========================================================================
spec_jump_game_ii = ProblemSpec(
    signature="function jump(nums: number[])",
    statement="""# Jump Game II

You are given a 0-indexed array of integers `nums` of length `n`. You are initially positioned at `nums[0]`.

Each element `nums[i]` represents the maximum length of a forward jump from index `i`.

Return the minimum number of jumps to reach index `n - 1`. It is guaranteed that you can always reach the last index.

Constraints: `1 <= nums.length <= 1000` and `0 <= nums[i] <= 1000`.
""",
    brute_force=Algorithm(
        """function jump(nums) {
  const n = nums.length;
  if (n <= 1) return 0;
  const dp = new Array(n).fill(Infinity);
  dp[0] = 0;
  for (let i = 0; i < n; i++) {
    if (dp[i] === Infinity) continue;
    const maxReach = Math.min(n - 1, i + nums[i]);
    for (let j = i + 1; j <= maxReach; j++) {
      if (dp[i] + 1 < dp[j]) {
        dp[j] = dp[i] + 1;
      }
    }
  }
  return dp[n - 1];
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function jump(nums) {
  const n = nums.length;
  if (n <= 1) return 0;
  let jumps = 0, currentEnd = 0, farthest = 0;
  for (let i = 0; i < n - 1; i++) {
    if (i + nums[i] > farthest) farthest = i + nums[i];
    if (i === currentEnd) {
      jumps++;
      currentEnd = farthest;
      if (currentEnd >= n - 1) break;
    }
  }
  return jumps;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    topic="greedy",
    difficulty="Medium",
    pattern="greedy / Window expand",
    time_limit_ms=2000,
    seed=42,
    title="Jump Game II",
    slug="jump-game-ii",
)

py_brute_jump_game_ii = """def jump(nums: list[int]) -> int:
    n = len(nums)
    if n <= 1:
        return 0
    dp = [float("inf")] * n
    dp[0] = 0
    for i in range(n):
        if dp[i] == float("inf"):
            continue
        max_reach = min(n - 1, i + nums[i])
        for j in range(i + 1, max_reach + 1):
            if dp[i] + 1 < dp[j]:
                dp[j] = dp[i] + 1
    return int(dp[-1])
"""

py_optimal_jump_game_ii = """def jump(nums: list[int]) -> int:
    n = len(nums)
    if n <= 1:
        return 0
    jumps = 0
    current_end = 0
    farthest = 0
    for i in range(n - 1):
        farthest = max(farthest, i + nums[i])
        if i == current_end:
            jumps += 1
            current_end = farthest
            if current_end >= n - 1:
                break
    return jumps
"""


def _gen_jump_game_ii_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[0]],
        [[1]],
        [[2, 3, 1, 1, 4]],
        [[2, 3, 0, 1, 4]],
        [[1, 2, 3]],
        [[1, 1, 1, 1]],
        [[5, 9, 3, 2, 1, 0, 2, 3, 3, 1, 0, 0]],
        [[3, 4, 3, 2, 5, 4, 3]],
        [[10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 1, 0]],
        [[1, 3, 2]],
    ]
    for _ in range(12):
        n = rng.randint(5, 30)
        # Guarantee reachable: each element >= 1
        arr = [rng.randint(1, 4) for _ in range(n - 1)] + [0]
        cases.append([arr])
    cases.append([[rng.randint(1, 5) for _ in range(150)] + [0]])
    cases.append([[rng.randint(1, 10) for _ in range(300)] + [0]])
    return cases


# ===========================================================================
# 18. pow-x-n
# ===========================================================================
spec_pow_x_n = ProblemSpec(
    signature="function myPow(x: number, n: number)",
    statement="""# Pow(x, n)

Implement `myPow(x, n)`, which calculates `x` raised to the power `n` (i.e., `xⁿ`).

The exponent `n` may be positive, negative, or zero. Return the result rounded to 5 decimal places. If the result is an exact integer, an integer value is returned.

Constraints: `-100.0 < x < 100.0`, `-1000 <= n <= 1000`. `x` will not be `0` when `n <= 0`.
""",
    brute_force=Algorithm(
        """function myPow(x, n) {
  if (n === 0) return 1;
  let exp = n;
  let base = x;
  if (exp < 0) {
    base = 1 / base;
    exp = -exp;
  }
  let res = 1.0;
  for (let i = 0; i < exp; i++) {
    res *= base;
  }
  res = Math.round(res * 1e5) / 1e5;
  return Number.isInteger(res) ? Math.trunc(res) : res;
}""",
        complexity="Time: O(|n|) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function myPow(x, n) {
  if (n === 0) return 1;
  let exp = n;
  let base = x;
  if (exp < 0) {
    base = 1 / base;
    exp = -exp;
  }
  let res = 1.0;
  while (exp > 0) {
    if (exp % 2 === 1) res *= base;
    base *= base;
    exp = Math.floor(exp / 2);
  }
  res = Math.round(res * 1e5) / 1e5;
  return Number.isInteger(res) ? Math.trunc(res) : res;
}""",
        complexity="Time: O(log |n|) | Space: O(1)",
        language="javascript",
    ),
    topic="math-matrices",
    difficulty="Medium",
    pattern="math-matrices / Fast pow",
    time_limit_ms=2000,
    seed=42,
    title="Pow(x, n)",
    slug="pow-x-n",
)

py_brute_pow_x_n = """def myPow(x: float, n: int) -> float | int:
    if n == 0:
        return 1
    exp = n
    base = x
    if exp < 0:
        base = 1.0 / base
        exp = -exp
    res = 1.0
    for _ in range(exp):
        res *= base
    res = round(res, 5)
    return int(res) if res.is_integer() else res
"""

py_optimal_pow_x_n = """def myPow(x: float, n: int) -> float | int:
    if n == 0:
        return 1
    exp = n
    base = x
    if exp < 0:
        base = 1.0 / base
        exp = -exp
    res = 1.0
    while exp > 0:
        if exp % 2 == 1:
            res *= base
        base *= base
        exp //= 2
    res = round(res, 5)
    return int(res) if res.is_integer() else res
"""


def _gen_pow_x_n_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [2.0, 10],
        [2.1, 3],
        [2.0, -2],
        [1.0, 100],
        [-1.0, 3],
        [-1.0, 4],
        [2.0, 0],
        [0.5, 2],
        [3.0, 5],
        [5.0, -3],
        [0.0, 5],
        [7.0, 2],
        [-2.0, 3],
        [-2.0, 4],
        [0.25, 2],
    ]
    for _ in range(10):
        x = round(rng.uniform(0.5, 3.0), 1)
        n = rng.randint(-10, 15)
        cases.append([x, n])
    cases.append([2.0, 30])
    cases.append([1.0001, 500])
    return cases


# ===========================================================================
# 19. meeting-rooms-ii
# ===========================================================================
spec_meeting_rooms_ii = ProblemSpec(
    signature="function minMeetingRooms(intervals: number[][])",
    statement="""# Meeting Rooms II

Given an array of meeting time intervals `intervals` where `intervals[i] = [start_i, end_i]`, return the minimum number of conference rooms required to hold all meetings without overlaps.

An interval `[start, end]` reserves the room from time `start` up to (but not including) time `end`. A meeting ending at time `t` does not conflict with a meeting starting at time `t`.

Constraints: `0 <= intervals.length <= 1000` and `0 <= start_i < end_i <= 10⁶`.
""",
    brute_force=Algorithm(
        """function minMeetingRooms(intervals) {
  if (!intervals || intervals.length === 0) return 0;
  let maxRooms = 0;
  for (let i = 0; i < intervals.length; i++) {
    const time = intervals[i][0];
    let count = 0;
    for (let j = 0; j < intervals.length; j++) {
      if (intervals[j][0] <= time && time < intervals[j][1]) {
        count++;
      }
    }
    if (count > maxRooms) maxRooms = count;
  }
  return maxRooms;
}""",
        complexity="Time: O(n²) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function minMeetingRooms(intervals) {
  if (!intervals || intervals.length === 0) return 0;
  const starts = intervals.map(iv => iv[0]).sort((a, b) => a - b);
  const ends = intervals.map(iv => iv[1]).sort((a, b) => a - b);
  let s = 0, e = 0, rooms = 0, maxRooms = 0;
  while (s < starts.length) {
    if (starts[s] < ends[e]) {
      rooms++;
      if (rooms > maxRooms) maxRooms = rooms;
      s++;
    } else {
      rooms--;
      e++;
    }
  }
  return maxRooms;
}""",
        complexity="Time: O(n log n) | Space: O(n)",
        language="javascript",
    ),
    topic="intervals",
    difficulty="Medium",
    pattern="intervals / Heap sweep",
    time_limit_ms=2000,
    seed=42,
    title="Meeting Rooms II",
    slug="meeting-rooms-ii",
)

py_brute_meeting_rooms_ii = """def minMeetingRooms(intervals: list[list[int]]) -> int:
    if not intervals:
        return 0
    max_rooms = 0
    for i in range(len(intervals)):
        time = intervals[i][0]
        count = sum(1 for iv in intervals if iv[0] <= time < iv[1])
        if count > max_rooms:
            max_rooms = count
    return max_rooms
"""

py_optimal_meeting_rooms_ii = """def minMeetingRooms(intervals: list[list[int]]) -> int:
    if not intervals:
        return 0
    starts = sorted(iv[0] for iv in intervals)
    ends = sorted(iv[1] for iv in intervals)
    s = e = rooms = max_rooms = 0
    while s < len(starts):
        if starts[s] < ends[e]:
            rooms += 1
            max_rooms = max(max_rooms, rooms)
            s += 1
        else:
            rooms -= 1
            e += 1
    return max_rooms
"""


def _gen_meeting_rooms_ii_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[]],
        [[[0, 30], [5, 10], [15, 20]]],
        [[[7, 10], [2, 4]]],
        [[[1, 5], [2, 6], [3, 7], [4, 8]]],
        [[[1, 2], [2, 3], [3, 4]]],
        [[[1, 10], [2, 3], [4, 5], [6, 7], [8, 9]]],
        [[[9, 10], [4, 9], [4, 17]]],
        [[[5, 8], [6, 8]]],
        [[[1, 100]]],
        [[[1, 4], [2, 5], [7, 9]]],
    ]
    for _ in range(12):
        n = rng.randint(3, 15)
        ivs = []
        for _ in range(n):
            start = rng.randint(0, 100)
            end = start + rng.randint(1, 50)
            ivs.append([start, end])
        cases.append([ivs])
    cases.append([[[i, i + 10] for i in range(50)]])
    cases.append([[[i * 2, (i * 2) + 1] for i in range(50)]])
    return cases


# ===========================================================================
# 20. find-words-on-board
# ===========================================================================
spec_find_words_on_board = ProblemSpec(
    signature="function findWords(board: string[][], words: string[])",
    statement="""# Find Words on Board

Given an `m x n` board of characters and a list of strings `words`, return all words found on the board.

Each word must be constructed from letters of sequentially adjacent cells, where adjacent cells are horizontally or vertically neighboring. The same letter cell may not be used more than once in a single word path.

The returned list of words must be sorted in lexicographical order.

Constraints: `1 <= board.length, board[i].length <= 6`, `1 <= words.length <= 20`, and `1 <= words[i].length <= 10`. `board` and `words[i]` consist only of lowercase English letters. All strings in `words` are unique.
""",
    brute_force=Algorithm(
        """function findWords(board, words) {
  const m = board.length, n = board[0].length;
  const found = new Set();
  function checkWord(word) {
    function dfs(r, c, k) {
      if (k === word.length) return true;
      if (r < 0 || r >= m || c < 0 || c >= n || board[r][c] !== word[k]) return false;
      const saved = board[r][c];
      board[r][c] = "#";
      const res = dfs(r + 1, c, k + 1) || dfs(r - 1, c, k + 1) || dfs(r, c + 1, k + 1) || dfs(r, c - 1, k + 1);
      board[r][c] = saved;
      return res;
    }
    for (let i = 0; i < m; i++) {
      for (let j = 0; j < n; j++) {
        if (dfs(i, j, 0)) return true;
      }
    }
    return false;
  }
  for (let w = 0; w < words.length; w++) {
    if (checkWord(words[w])) {
      found.add(words[w]);
    }
  }
  return Array.from(found).sort();
}""",
        complexity="Time: O(W · m · n · 4ᴸ) | Space: O(m · n + W)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function findWords(board, words) {
  const root = {};
  for (let i = 0; i < words.length; i++) {
    const word = words[i];
    let node = root;
    for (let j = 0; j < word.length; j++) {
      const ch = word[j];
      if (!node[ch]) node[ch] = {};
      node = node[ch];
    }
    node.word = word;
  }
  const m = board.length, n = board[0].length;
  const result = [];
  function dfs(r, c, parent) {
    const ch = board[r][c];
    const currNode = parent[ch];
    if (!currNode) return;
    if (currNode.word) {
      result.push(currNode.word);
      currNode.word = null;
    }
    board[r][c] = "#";
    if (r + 1 < m && board[r + 1][c] !== "#") dfs(r + 1, c, currNode);
    if (r - 1 >= 0 && board[r - 1][c] !== "#") dfs(r - 1, c, currNode);
    if (c + 1 < n && board[r][c + 1] !== "#") dfs(r, c + 1, currNode);
    if (c - 1 >= 0 && board[r][c - 1] !== "#") dfs(r, c - 1, currNode);
    board[r][c] = ch;
  }
  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      if (root[board[i][j]]) {
        dfs(i, j, root);
      }
    }
  }
  return result.sort();
}""",
        complexity="Time: O(m · n · 4ᴸ) | Space: O(Σ|word|)",
        language="javascript",
    ),
    topic="trie",
    difficulty="Hard",
    pattern="trie / Prefix prune",
    time_limit_ms=2000,
    seed=42,
    title="Find Words on Board",
    slug="find-words-on-board",
)

py_brute_find_words_on_board = """def findWords(board: list[list[str]], words: list[str]) -> list[str]:
    m, n = len(board), len(board[0])
    found = set()

    def check_word(word: str) -> bool:
        def dfs(r: int, c: int, k: int) -> bool:
            if k == len(word):
                return True
            if r < 0 or r >= m or c < 0 or c >= n or board[r][c] != word[k]:
                return False
            saved = board[r][c]
            board[r][c] = "#"
            ok = (
                dfs(r + 1, c, k + 1)
                or dfs(r - 1, c, k + 1)
                or dfs(r, c + 1, k + 1)
                or dfs(r, c - 1, k + 1)
            )
            board[r][c] = saved
            return ok

        for i in range(m):
            for j in range(n):
                if dfs(i, j, 0):
                    return True
        return False

    for word in words:
        if check_word(word):
            found.add(word)
    return sorted(found)
"""

py_optimal_find_words_on_board = """def findWords(board: list[list[str]], words: list[str]) -> list[str]:
    root = {}
    for word in words:
        node = root
        for ch in word:
            node = node.setdefault(ch, {})
        node["$"] = word

    m, n = len(board), len(board[0])
    result = []

    def dfs(r: int, c: int, parent: dict) -> None:
        ch = board[r][c]
        curr_node = parent.get(ch)
        if not curr_node:
            return
        if "$" in curr_node:
            result.append(curr_node.pop("$"))
        board[r][c] = "#"
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and board[nr][nc] != "#":
                dfs(nr, nc, curr_node)
        board[r][c] = ch

    for i in range(m):
        for j in range(n):
            if board[i][j] in root:
                dfs(i, j, root)

    result.sort()
    return result
"""


def _gen_find_words_on_board_inputs(rng: random.Random) -> list[list[Any]]:
    board1 = [["o", "a", "a", "n"], ["e", "t", "a", "e"], ["i", "h", "k", "r"], ["i", "f", "l", "v"]]
    cases: list[list[Any]] = [
        [[["a"]], ["a", "b"]],
        [[["a"]], ["b"]],
        [board1, ["oath", "pea", "eat", "rain"]],
        [[["a", "b"], ["c", "d"]], ["abcb"]],
        [[["a", "b"], ["c", "d"]], ["ab", "cd", "ac", "bd"]],
        [[["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i"]], ["abc", "cfi", "ihg", "adg", "beh"]],
        [[["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i"]], ["xyz", "uvw"]],
        [[["a", "a"], ["a", "a"]], ["a", "aa", "aaa", "aaaa", "aaaaa"]],
        [[["c", "a", "t"], ["o", "d", "s"], ["w", "o", "g"]], ["cat", "dog", "cow", "sow", "god"]],
        [[["m", "e", "r"], ["i", "t", "s"], ["a", "p", "p"]], ["merit", "merits", "tap", "sip", "rip"]],
        [[["b", "a"], ["a", "b"]], ["ba", "ab", "baa", "bab"]],
        [[["x", "y"], ["z", "w"]], ["xw", "xyw", "yzw"]],
        [[["l", "e", "e", "t"], ["c", "o", "d", "e"]], ["leet", "code", "led", "cot"]],
        [[["z"]], ["z"]],
        [[["a", "b", "c"]], ["abc", "cba", "bca"]],
    ]
    return cases


# ===========================================================================
# Problem Bundles Assembly
# ===========================================================================
BUNDLES: list[ProblemBundle] = [
    # 1. subsets
    ProblemBundle(
        spec=spec_subsets,
        py_brute_code=py_brute_subsets,
        py_brute_complexity="Time: O(n · 2ⁿ) | Space: O(n · 2ⁿ)",
        py_optimal_code=py_optimal_subsets,
        py_optimal_complexity="Time: O(n · 2ⁿ) | Space: O(n)",
        input_generator=_gen_subsets_inputs,
        examples=[
            {
                "input": "nums = [1, 2, 3]",
                "output": "[[], [1], [1, 2], [1, 2, 3], [1, 3], [2], [2, 3], [3]]",
                "explanation": "All 2³ = 8 possible subsets are generated, with each subset sorted ascending and the full collection sorted lexicographically.",
            },
            {
                "input": "nums = [0]",
                "output": "[[], [0]]",
                "explanation": "A single element array produces the empty set and the singleton set.",
            },
            {
                "input": "nums = []",
                "output": "[[]]",
                "explanation": "An empty array yields only the empty subset [].",
            },
        ],
        approach="""### Backtracking: Decision Tree over Choose vs. Skip

To construct the power set of an array of $n$ distinct elements, every element presents a binary choice: either include it in the current subset or skip it.

#### 1. State Definition and Decision Tree
Let $nums$ be pre-sorted in ascending order. At depth $idx$ in the recursion:
- State is represented by the tuple $(idx, \\text{current})$, where $\\text{current}$ holds the elements chosen so far from $nums[0 \\dots idx - 1]$.
- From state $(idx, \\text{current})$, we have two branches:
  1. **Skip $nums[idx]$**: Recurse to $(idx + 1, \\text{current})$.
  2. **Choose $nums[idx]$**: Append $nums[idx]$ to $\\text{current}$, recurse to $(idx + 1, \\text{current} \\cup \\{nums[idx]\\})$, and backtrack by popping $nums[idx]$.

#### 2. Base Case and Invariant
When $idx == n$, the decision path is complete. Append a snapshot of $\\text{current}$ to the result list. Because $nums$ is sorted, every produced subset is inherently sorted. Finally, sort the outer collection to satisfy the canonical lexicographical ordering requirement.

#### 3. Recurrence
$$S(idx) = S(idx + 1) \\cup \\{ \\{nums[idx]\\} \\cup s \\mid s \\in S(idx + 1) \\}$$
Base case: $S(n) = \\{\\emptyset\\}$.""",
        why_optimal_template="Bitmask iteration requires O(n · 2ⁿ) time with continuous mask shifting and array allocations, while backtracking builds subsets along a recursion tree reusing a single mutable path array with O(n) auxiliary stack space. On {case_count} verified test cases, backtracking executed in {optimal_ms:.2f} ms versus {brute_ms:.2f} ms for bitmask enumeration.",
        pitfalls="Forgetting to pop from the path array after the recursive step corrupts subsequent branches. Neglecting to copy the current path when saving it will result in an array of empty subsets.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Power_set",
            "https://en.wikipedia.org/wiki/Backtracking",
        ],
        hints=[
            "Each element can either be included or excluded from a subset, yielding 2ⁿ total subsets.",
            "Sort the initial array first so that generated subsets are automatically in ascending order.",
            "Use a recursive helper that takes the current index and maintains a path snapshot.",
        ],
    ),

    # 2. permutations
    ProblemBundle(
        spec=spec_permutations,
        py_brute_code=py_brute_permutations,
        py_brute_complexity="Time: O(n · n!) | Space: O(n · n!)",
        py_optimal_code=py_optimal_permutations,
        py_optimal_complexity="Time: O(n · n!) | Space: O(n)",
        input_generator=_gen_permutations_inputs,
        examples=[
            {
                "input": "nums = [1, 2, 3]",
                "output": "[[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]",
                "explanation": "All 3! = 6 permutations are generated and returned in lexicographical order.",
            },
            {
                "input": "nums = [0, 1]",
                "output": "[[0, 1], [1, 0]]",
                "explanation": "The 2! = 2 permutations of two elements.",
            },
            {
                "input": "nums = [1]",
                "output": "[[1]]",
                "explanation": "A single element has exactly one permutation.",
            },
        ],
        approach="""### Backtracking: In-Place Swap Exploration

Generating all permutations of an array of $n$ distinct elements corresponds to choosing each available element for the current position and permuting the remaining elements.

#### 1. In-Place Swap Formulation
Instead of allocating auxiliary boolean arrays or sets to track used elements, we partition the array into:
- Left prefix $nums[0 \\dots start - 1]$: Elements whose positions are fixed for the current branch.
- Suffix $nums[start \\dots n - 1]$: Candidates available to be placed at position $start$.

#### 2. Recursive Transition
For each index $i$ from $start$ to $n - 1$:
1. Swap $nums[start]$ with $nums[i]$ to place candidate $nums[i]$ at position $start$.
2. Recurse on $start + 1$.
3. Backtrack by swapping $nums[start]$ with $nums[i]$ again to restore the original array order.

#### 3. Base Case & Recurrence
When $start == n$, record a copy of $nums$.
$$P(start) = \\bigcup_{i = start}^{n - 1} \\text{swap}(start, i) \\circ P(start + 1)$$
Base case: $P(n) = \\{nums\\}$.
Sorting the final collection guarantees lexicographical ordering.""",
        why_optimal_template="Standard permutation algorithms allocate boolean tracking tables or slice arrays at each step, consuming O(n · n!) space. In-place swapping mutates the array directly, using only O(n) call stack space. Across {case_count} verified test cases, in-place swap backtracking ran in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for boolean table tracking.",
        pitfalls="Failing to swap back after the recursive call destroys array state for sibling iterations. Slicing or copying the array on every step incurs severe memory allocation overhead.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Permutation",
            "https://en.wikipedia.org/wiki/Heap%27s_algorithm",
        ],
        hints=[
            "There are n! total permutations for an array of n distinct elements.",
            "Swap elements into the current pivot index, recurse on index + 1, and swap back.",
            "Sort the final list of permutations lexicographically to ensure canonical output.",
        ],
    ),

    # 3. combination-sum
    ProblemBundle(
        spec=spec_combination_sum,
        py_brute_code=py_brute_combination_sum,
        py_brute_complexity="Time: O(2^target) | Space: O(target)",
        py_optimal_code=py_optimal_combination_sum,
        py_optimal_complexity="Time: O(N^(T/M)) | Space: O(T/M)",
        input_generator=_gen_combination_sum_inputs,
        examples=[
            {
                "input": "candidates = [2, 3, 6, 7], target = 7",
                "output": "[[2, 2, 3], [7]]",
                "explanation": "2 + 2 + 3 = 7 and 7 = 7. 2 can be chosen multiple times.",
            },
            {
                "input": "candidates = [2, 3, 5], target = 8",
                "output": "[[2, 2, 2, 2], [2, 3, 3], [3, 5]]",
                "explanation": "All three combinations sum to 8.",
            },
            {
                "input": "candidates = [2], target = 1",
                "output": "[]",
                "explanation": "No combination of 2 can sum to 1.",
            },
        ],
        approach="""### Backtracking with Unbounded Element Selection & Pruning

We must find all unique multisets of numbers from `candidates` that sum to `target`. Elements may be reused an unlimited number of times.

#### 1. Sorting and Pruning
Sort `candidates` ascending. If at any step the current candidate exceeds the remaining target (`candidates[i] > remain`), all subsequent candidates in the sorted array will also exceed `remain`, allowing an immediate `break` from the loop.

#### 2. Decision Formulation
At state $(idx, remain)$:
- If $remain == 0$, record the current combination.
- Iterate $i$ from $idx$ to $len(candidates) - 1$:
  - If $candidates[i] > remain$, terminate loop (prune).
  - Push $candidates[i]$ into path.
  - Recurse to $(i, remain - candidates[i])$. Passing $i$ (rather than $i + 1$) enables unbounded reuse of the current candidate while preventing duplicate combinations in different orderings.
  - Pop $candidates[i]$ to backtrack.

#### 3. Recurrence
$$C(idx, remain) = \\bigcup_{i = idx}^{len - 1} [candidates[i]] \\oplus C(i, remain - candidates[i])$$
Base case: $C(idx, 0) = \\{[]\\}$.""",
        why_optimal_template="Unsorted candidate searching explores dead branches where remaining sums go negative, resulting in exponential overhead. Pre-sorting candidates allows immediate loop termination when candidate > remain. Across {case_count} verified test cases, sorted pruned backtracking executed in {optimal_ms:.2f} ms versus {brute_ms:.2f} ms for unpruned exploration.",
        pitfalls="Starting the inner loop at index 0 instead of idx generates duplicate permutations of the same combination. Not breaking when candidate > remain wastes significant recursion depth.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Subset_sum_problem",
            "https://en.wikipedia.org/wiki/Backtracking",
        ],
        hints=[
            "Sort the candidates array first to enable early break pruning.",
            "Pass the current index i to the recursive call so the same number can be reused.",
            "When the remaining sum reaches 0, save a copy of the current combination.",
        ],
    ),

    # 4. letter-combinations-of-a-phone-number
    ProblemBundle(
        spec=spec_letter_combinations,
        py_brute_code=py_brute_letter_combinations,
        py_brute_complexity="Time: O(4ⁿ) | Space: O(4ⁿ)",
        py_optimal_code=py_optimal_letter_combinations,
        py_optimal_complexity="Time: O(4ⁿ) | Space: O(n)",
        input_generator=_gen_letter_combinations_inputs,
        examples=[
            {
                "input": "digits = '23'",
                "output": "['ad', 'ae', 'af', 'bd', 'be', 'bf', 'cd', 'ce', 'cf']",
                "explanation": "Digit 2 maps to 'abc' and 3 maps to 'def', yielding 3 × 3 = 9 combinations.",
            },
            {
                "input": "digits = ''",
                "output": "[]",
                "explanation": "An empty input produces an empty output array.",
            },
            {
                "input": "digits = '2'",
                "output": "['a', 'b', 'c']",
                "explanation": "Single digit yields its mapped letters.",
            },
        ],
        approach="""### Backtracking: N-Ary Cartesian Product Tree

Each digit in the input string represents an independent dimension in the Cartesian product of letter sets.

#### 1. Mapping Definition
Construct a lookup table mapping digits `'2'` through `'9'` to their respective letter strings. For instance, `'2'` $\\to$ `"abc"`, `'7'` $\\to$ `"pqrs"`, `'9'` $\\to$ `"wxyz"`.

#### 2. Depth-First Search Path Generation
Define a recursive function `backtrack(idx)`:
- State: `idx` is the index of the digit currently being expanded, and `path` is an array of characters selected so far.
- When `idx === digits.length`: Concatenate `path` into a string and push into results.
- For each character `ch` in `map[digits[idx]]`:
  1. `path.push(ch)`
  2. `backtrack(idx + 1)`
  3. `path.pop()`

#### 3. Recurrence
$$L(idx) = \\{ c + s \\mid c \\in \\text{map}[digits[idx]], s \\in L(idx + 1) \\}$$
Base case: $L(n) = \\{\\\"\\\"\\}$. If $digits$ is empty, return $[]$ immediately.""",
        why_optimal_template="Iterative queue generation continuously reallocates and copies intermediate partial strings at every stage. Backtracking uses a single mutable character stack of depth at most 4, building strings only upon reaching terminal leaves. On {case_count} verified test cases, depth-first backtracking executed in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for iterative BFS queueing.",
        pitfalls="Returning [''] for empty string input instead of []. Be sure to check digits.length === 0 at the start. Note digits 7 and 9 have 4 letters while others have 3.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Cartesian_product",
            "https://en.wikipedia.org/wiki/Telephone_keypad",
        ],
        hints=[
            "Use a hash map or array of strings to store the telephone keypad digit-to-letter mappings.",
            "If the input string is empty, immediately return an empty array.",
            "Depth-first search avoids intermediate string allocations until a complete combination is assembled.",
        ],
    ),

    # 5. palindrome-partitioning
    ProblemBundle(
        spec=spec_palindrome_partitioning,
        py_brute_code=py_brute_palindrome_partitioning,
        py_brute_complexity="Time: O(n · 2ⁿ) | Space: O(n)",
        py_optimal_code=py_optimal_palindrome_partitioning,
        py_optimal_complexity="Time: O(n² + 2ⁿ) | Space: O(n²)",
        input_generator=_gen_palindrome_partitioning_inputs,
        examples=[
            {
                "input": "s = 'aab'",
                "output": "[['a', 'a', 'b'], ['aa', 'b']]",
                "explanation": "'aab' can be partitioned into ['a', 'a', 'b'] and ['aa', 'b'] where all components are palindromes.",
            },
            {
                "input": "s = 'a'",
                "output": "[['a']]",
                "explanation": "A single character string is a palindrome itself.",
            },
            {
                "input": "s = 'racecar'",
                "output": "[['r', 'a', 'c', 'e', 'c', 'a', 'r'], ['r', 'a', 'cec', 'a', 'r'], ['r', 'aceca', 'r'], ['racecar']]",
                "explanation": "Multiple valid palindrome decompositions exist for 'racecar'.",
            },
        ],
        approach="""### Dynamic Programming Precomputation + Backtracking

We must split string $s$ of length $n$ at a subset of cut positions such that every segmented substring is a palindrome.

#### 1. DP Palindrome Table Precomputation
Instead of evaluating whether substring $s[i \\dots j]$ is a palindrome using a two-pointer scan in $O(j - i)$ time repeatedly, precalculate an $n \\times n$ boolean matrix $isPal$:
- Base cases: $isPal[i][i] = true$ for all $i$.
- For length 2: $isPal[i][i+1] = (s[i] == s[i+1])$.
- For lengths $L \\ge 3$: $isPal[i][j] = (s[i] == s[j]) \\land isPal[i+1][j-1]$.
This precomputation takes $O(n^2)$ time and allows $O(1)$ palindrome checks during backtracking.

#### 2. Backtracking Decision Process
At state $start$:
- If $start == n$, append a copy of current partition to result.
- For $end$ from $start$ to $n - 1$:
  - If $isPal[start][end]$ is true:
    - Add $s[start \\dots end]$ to current partition.
    - Recurse on $end + 1$.
    - Pop substring to backtrack.""",
        why_optimal_template="Checking palindromes on-the-fly with two pointers takes O(n) per substring verification across all 2ⁿ possible cuts. Precomputing an O(n²) boolean table reduces palindrome validation to O(1) time. Across {case_count} verified test cases, DP-accelerated partitioning executed in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for naive verification.",
        pitfalls="In 0-indexed substring slicing, s.slice(start, end + 1) includes character end, so the next recursion must begin at end + 1.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Palindrome",
            "https://en.wikipedia.org/wiki/Dynamic_programming",
        ],
        hints=[
            "Precompute a 2D boolean table isPal[i][j] where isPal[i][j] is true if s[i..j] is a palindrome.",
            "From each start index, iterate over all possible end indices and cut only if s[start..end] is a palindrome.",
            "Sort the final partitions lexicographically to ensure consistent ordering.",
        ],
    ),

    # 6. word-search
    ProblemBundle(
        spec=spec_word_search,
        py_brute_code=py_brute_word_search,
        py_brute_complexity="Time: O(m · n · 4ᴸ) | Space: O(m · n)",
        py_optimal_code=py_optimal_word_search,
        py_optimal_complexity="Time: O(m · n · 4ᴸ) | Space: O(L)",
        input_generator=_gen_word_search_inputs,
        examples=[
            {
                "input": "board = [['a', 'b', 'c', 'e'], ['s', 'f', 'c', 's'], ['a', 'd', 'e', 'e']], word = 'abcced'",
                "output": "true",
                "explanation": "The word 'abcced' can be traced along cells (0,0)->(0,1)->(0,2)->(1,2)->(2,2)->(2,1).",
            },
            {
                "input": "board = [['a', 'b', 'c', 'e'], ['s', 'f', 'c', 's'], ['a', 'd', 'e', 'e']], word = 'see'",
                "output": "true",
                "explanation": "'see' is found at (1,3)->(2,3)->(2,2).",
            },
            {
                "input": "board = [['a', 'b', 'c', 'e'], ['s', 'f', 'c', 's'], ['a', 'd', 'e', 'e']], word = 'abcb'",
                "output": "false",
                "explanation": "Cell reuse is prohibited, so 'abcb' cannot be formed.",
            },
        ],
        approach="""### In-Place DFS Grid Search with Frequency Pruning

We determine whether a given word can be formed by a contiguous 4-directional path on an $m \\times n$ grid without reusing cells.

#### 1. Pruning Optimizations
Before launching grid searches:
1. Length check: If $len(word) > m \\times n$, return `false`.
2. Character count check: Count frequencies of every character in `board`. If `board` lacks sufficient occurrences of any letter in `word`, return `false` immediately.
3. Frequency inversion: If the starting character of `word` occurs more frequently on `board` than the trailing character, reverse `word`. Starting the search from the rarer letter dramatically prunes the initial branching factor.

#### 2. In-Place Backtracking
Rather than allocating a visited matrix:
- When visiting $(r, c)$, save $board[r][c]$ and overwrite it with `'#'`.
- Explore all 4 adjacent cells: $(r+1, c), (r-1, c), (r, c+1), (r, c-1)$.
- Upon returning, restore $board[r][c]$ to its original character.""",
        why_optimal_template="Allocating auxiliary visited matrices creates substantial memory churn on grid traversals. In-place character masking with '#' reduces auxiliary space to O(L) recursion depth, and letter frequency reversal cuts initial DFS branches. On {case_count} verified test cases, optimized in-place DFS finished in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for visited-matrix DFS.",
        pitfalls="Forgetting to restore board[r][c] after backtracking permanently corrupts the grid for subsequent search roots.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Depth-first_search",
            "https://en.wikipedia.org/wiki/Backtracking",
        ],
        hints=[
            "Check board character counts against word character counts before starting any search.",
            "If the first letter of word is more frequent than the last letter, reverse the search direction.",
            "Mark visited cells in-place by temporarily modifying board[r][c] = '#' and restoring it upon return.",
        ],
    ),

    # 7. n-queens-count
    ProblemBundle(
        spec=spec_n_queens_count,
        py_brute_code=py_brute_n_queens_count,
        py_brute_complexity="Time: O(n!) | Space: O(n)",
        py_optimal_code=py_optimal_n_queens_count,
        py_optimal_complexity="Time: O(n!) | Space: O(n)",
        input_generator=_gen_n_queens_count_inputs,
        examples=[
            {
                "input": "n = 4",
                "output": "2",
                "explanation": "There are 2 distinct configurations to place 4 non-attacking queens on a 4x4 board.",
            },
            {
                "input": "n = 1",
                "output": "1",
                "explanation": "A 1x1 board has trivially 1 valid queen placement.",
            },
            {
                "input": "n = 2",
                "output": "0",
                "explanation": "No valid non-attacking configuration exists for n = 2.",
            },
        ],
        approach="""### Bitmask Backtracking for N-Queens

Placing $n$ non-attacking queens requires placing exactly one queen per row such that no two queens share the same column, main diagonal, or anti-diagonal.

#### 1. Bitmask Representation
For row $r$:
- Bitmask `cols` tracks occupied columns (bit $c$ set means column $c$ is taken).
- Bitmask `diag1` tracks occupied main diagonals (drifting left as we move down: `(diag1 | bit) << 1`).
- Bitmask `diag2` tracks occupied anti-diagonals (drifting right as we move down: `(diag2 | bit) >> 1`).

#### 2. Bitwise Position Extraction
At row $r$:
$$\\text{available} = ((1 \\ll n) - 1) \\land \\sim(cols \\mid diag1 \\mid diag2)$$
While $\\text{available} \\ne 0$:
- Extract least significant bit: $bit = \\text{available} \\land (-\\text{available})$.
- Clear this bit: $\\text{available} \\oplus= bit$.
- Recurse: `solve(row + 1, cols | bit, (diag1 | bit) << 1, (diag2 | bit) >> 1)`.

When $row == n$, increment total count.""",
        why_optimal_template="Checking column and diagonal validity using array iterations takes O(n) time per candidate placement. Bitwise operations compute all available positions simultaneously with bit shifts and mask extractions in O(1) time. Across {case_count} verified test cases, bitmask backtracking completed in {optimal_ms:.2f} ms versus {brute_ms:.2f} ms for array-based conflict checks.",
        pitfalls="When shifting diagonals in JavaScript, ensure 32-bit integer boundaries and mask by (1 << n) - 1 so bits do not leak past column bounds.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Eight_queens_puzzle",
            "https://en.wikipedia.org/wiki/Backtracking",
        ],
        hints=[
            "Represent occupied columns and diagonals as bitmasks to test availability in O(1).",
            "Left shifts model main diagonals shifting leftward for each advancing row; right shifts model anti-diagonals.",
            "Use available & -available to extract the lowest available candidate bit.",
        ],
    ),

    # 8. single-number
    ProblemBundle(
        spec=spec_single_number,
        py_brute_code=py_brute_single_number,
        py_brute_complexity="Time: O(n) | Space: O(n)",
        py_optimal_code=py_optimal_single_number,
        py_optimal_complexity="Time: O(n) | Space: O(1)",
        input_generator=_gen_single_number_inputs,
        examples=[
            {
                "input": "nums = [2, 2, 1]",
                "output": "1",
                "explanation": "2 appears twice; 1 appears once.",
            },
            {
                "input": "nums = [4, 1, 2, 1, 2]",
                "output": "4",
                "explanation": "1 and 2 appear twice; 4 appears once.",
            },
            {
                "input": "nums = [1]",
                "output": "1",
                "explanation": "The array has a single element which is trivially unique.",
            },
        ],
        approach="""### Bitwise XOR Invariant: Self-Cancellation

The problem states that every element appears exactly twice except for a single element that appears once.

#### 1. Mathematical Invariants of XOR
XOR ($\\oplus$) possesses three algebraic properties:
1. **Identity**: $x \\oplus 0 = x$
2. **Self-Inverse**: $x \\oplus x = 0$
3. **Commutativity and Associativity**: Order of evaluation does not alter the result.

#### 2. Reduction
Let the unique element be $u$ and the pairs of duplicates be $p_1, p_1, p_2, p_2, \\dots, p_k, p_k$.
$$\\bigoplus_{x \\in nums} x = u \\oplus (p_1 \\oplus p_1) \\oplus (p_2 \\oplus p_2) \\dots = u \\oplus 0 \\oplus 0 = u$$
Iterating through `nums` once and accumulating XOR values yields $u$ in $O(n)$ time and $O(1)$ auxiliary space.""",
        why_optimal_template="Using a hash map or frequency table requires O(n) auxiliary memory to count occurrences. Bitwise XOR cancellation isolates the single element in a single pass using strictly O(1) auxiliary memory. On {case_count} verified test cases, XOR cancellation completed in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for hash map counting.",
        pitfalls="Initializing the accumulator to anything other than 0 corrupts the XOR sum.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Exclusive_or",
            "https://en.wikipedia.org/wiki/Bit_manipulation",
        ],
        hints=[
            "Recall that x XOR x = 0 and x XOR 0 = x.",
            "Because XOR is commutative, all paired duplicates cancel out regardless of their positions.",
            "Initialize an accumulator to 0 and XOR each element in the array.",
        ],
    ),

    # 9. number-of-1-bits
    ProblemBundle(
        spec=spec_number_of_1_bits,
        py_brute_code=py_brute_number_of_1_bits,
        py_brute_complexity="Time: O(32) | Space: O(1)",
        py_optimal_code=py_optimal_number_of_1_bits,
        py_optimal_complexity="Time: O(k) | Space: O(1)",
        input_generator=_gen_number_of_1_bits_inputs,
        examples=[
            {
                "input": "n = 11",
                "output": "3",
                "explanation": "11 in binary is 1011, which has three '1' bits.",
            },
            {
                "input": "n = 128",
                "output": "1",
                "explanation": "128 in binary is 10000000, which has one '1' bit.",
            },
            {
                "input": "n = 4294967295",
                "output": "32",
                "explanation": "All 32 bits are 1 in 0xFFFFFFFF.",
            },
        ],
        approach="""### Brian Kernighan's Bit-Clearing Algorithm

To count the number of set bits (Hamming weight) of a 32-bit unsigned integer $n$:

#### 1. Invariant of n & (n - 1)
Subtracting 1 from a binary number $n$ flips all bits after the rightmost set bit, including that rightmost set bit itself.
Performing a bitwise AND between $n$ and $n - 1$ ($n \\land (n - 1)$) clears the lowest set bit while keeping all higher bits unchanged.

#### 2. Algorithm
1. Initialize `count = 0`.
2. While $n \\ne 0$:
   - $n = (n \\land (n - 1)) \\ggg 0$
   - `count++`
3. Return `count`.

This loop executes exactly $k$ times, where $k$ is the number of set bits, rather than iterating through all 32 bits.""",
        why_optimal_template="A fixed 32-iteration loop inspects every bit position regardless of sparsity. Brian Kernighan's algorithm loops only once per set bit, terminating in at most k steps where k <= 32. On {case_count} verified test cases, Kernighan's algorithm completed in {optimal_ms:.2f} ms versus {brute_ms:.2f} ms for fixed 32-bit scanning.",
        pitfalls="In JavaScript, bitwise operations convert numbers to 32-bit signed integers. Use the unsigned right shift >>> 0 to ensure non-negative integer representation.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Hamming_weight",
            "https://en.wikipedia.org/wiki/Bit_manipulation",
        ],
        hints=[
            "Subtracting 1 from n turns the lowest 1-bit into a 0 and turns trailing 0s into 1s.",
            "Thus, n & (n - 1) always clears the lowest set bit of n.",
            "Count how many times you can clear the lowest set bit until n becomes 0.",
        ],
    ),

    # 10. reverse-bits
    ProblemBundle(
        spec=spec_reverse_bits,
        py_brute_code=py_brute_reverse_bits,
        py_brute_complexity="Time: O(32) | Space: O(1)",
        py_optimal_code=py_optimal_reverse_bits,
        py_optimal_complexity="Time: O(1) | Space: O(1)",
        input_generator=_gen_reverse_bits_inputs,
        examples=[
            {
                "input": "n = 43261596",
                "output": "964176192",
                "explanation": "43261596 represented in binary is 00000010100101000001111010011100; reversed it is 00111001011110000010100101000000 = 964176192.",
            },
            {
                "input": "n = 1",
                "output": "2147483648",
                "explanation": "1 with bit 0 set becomes bit 31 set, which is 2³¹ = 2147483648.",
            },
            {
                "input": "n = 4294967295",
                "output": "4294967295",
                "explanation": "All 32 bits are 1; reversing yields the identical integer.",
            },
        ],
        approach="""### Divide-and-Conquer Bit Reversal

Reversing 32 bits can be achieved without iterative shifting by hierarchically swapping bit blocks using bitmasks:

#### 1. Swap Blocks of Decreasing Powers of 2
1. Swap the top 16 bits with the bottom 16 bits:
   $$n = ((n \\ggg 16) \\mid (n \\ll 16)) \\ggg 0$$
2. Swap adjacent 8-bit bytes using mask `0x00FF00FF`:
   $$n = (((n \\& \\text{0xFF00FF00}) \\ggg 8) \\mid ((n \\& \\text{0x00FF00FF}) \\ll 8)) \\ggg 0$$
3. Swap adjacent 4-bit nibbles using mask `0x0F0F0F0F`:
   $$n = (((n \\& \\text{0xF0F0F0F0}) \\ggg 4) \\mid ((n \\& \\text{0x0F0F0F0F}) \\ll 4)) \\ggg 0$$
4. Swap adjacent 2-bit pairs using mask `0x33333333`:
   $$n = (((n \\& \\text{0xCCCCCCCC}) \\ggg 2) \\mid ((n \\& \\text{0x33333333}) \\ll 2)) \\ggg 0$$
5. Swap adjacent single bits using mask `0x55555555`:
   $$n = (((n \\& \\text{0xAAAAAAAA}) \\ggg 1) \\mid ((n \\& \\text{0x55555555}) \\ll 1)) \\ggg 0$$

All 32 bits are completely reversed in exactly 5 constant-time parallel operations.""",
        why_optimal_template="Iterative bit reversal requires 32 loop iterations with branch and shift evaluations. Divide-and-conquer bit swaps reverse blocks in 5 parallel bitwise operations in O(1) time. Across {case_count} verified test cases, divide-and-conquer reversal executed in {optimal_ms:.2f} ms versus {brute_ms:.2f} ms for loop-based reversal.",
        pitfalls="JavaScript bitwise shifts produce signed 32-bit integers. Applying >>> 0 at each step guarantees non-negative unsigned representation.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Bit-reversal_permutation",
            "https://en.wikipedia.org/wiki/Bitwise_operation",
        ],
        hints=[
            "Think of reversing 32 bits like merge sort in reverse: swap halves, then quarters, then eighths.",
            "Mask 0xFF00FF00 and 0x00FF00FF to swap 8-bit bytes.",
            "Use >>> 0 in JavaScript to keep numbers in unsigned 32-bit integer range.",
        ],
    ),

    # 11. sum-of-two-integers
    ProblemBundle(
        spec=spec_sum_of_two_integers,
        py_brute_code=py_brute_sum_of_two_integers,
        py_brute_complexity="Time: O(32) | Space: O(1)",
        py_optimal_code=py_optimal_sum_of_two_integers,
        py_optimal_complexity="Time: O(1) | Space: O(1)",
        input_generator=_gen_sum_of_two_integers_inputs,
        examples=[
            {
                "input": "a = 1, b = 2",
                "output": "3",
                "explanation": "1 + 2 = 3 calculated with bitwise operators.",
            },
            {
                "input": "a = 2, b = 3",
                "output": "5",
                "explanation": "2 + 3 = 5 without using + or -.",
            },
            {
                "input": "a = -1, b = 1",
                "output": "0",
                "explanation": "Two's complement cancellation yields 0.",
            },
        ],
        approach="""### Digital Logic: Full-Adder Carry-Lookahead Loop

Addition of two numbers in digital electronics can be decomposed into XOR addition (sum without carry) and AND addition (carry propagation).

#### 1. Arithmetic Decomposition
For two binary integers $a$ and $b$:
- **Sum without carry**: $a \\oplus b$ computes the sum bit at each position.
- **Carry**: $(a \\land b) \\ll 1$ computes where both bits were 1, shifting left by 1 because the carry adds into the next higher bit position.

#### 2. Iterative Carry Propagation
Set $a = a \\oplus b$ and $b = (a \\land b) \\ll 1$. Repeat this process until $b == 0$. Since carry bits propagate upward, the loop terminates within at most 32 iterations for any 32-bit signed integers.

In Python, arbitrary precision integers must be masked by `0xFFFFFFFF` to simulate 32-bit signed wrap-around.""",
        why_optimal_template="Bit-by-bit ripple-carry addition processes bits sequentially in 32 iterations. Parallel bitwise addition processes all 32 bits simultaneously per carry round, terminating as soon as carries settle. On {case_count} verified test cases, the parallel carry loop ran in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for bit-by-bit ripple addition.",
        pitfalls="Python does not natively cap integers to 32 bits. Without masking with 0xFFFFFFFF, negative numbers enter an infinite carry loop.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Adder_(electronics)",
            "https://en.wikipedia.org/wiki/Two%27s_complement",
        ],
        hints=[
            "XOR (a ^ b) gives the sum without any carry.",
            "AND shifted left by one ((a & b) << 1) gives the carry bits.",
            "Repeat the process until the carry becomes 0.",
        ],
    ),

    # 12. power-of-two
    ProblemBundle(
        spec=spec_power_of_two,
        py_brute_code=py_brute_power_of_two,
        py_brute_complexity="Time: O(log n) | Space: O(1)",
        py_optimal_code=py_optimal_power_of_two,
        py_optimal_complexity="Time: O(1) | Space: O(1)",
        input_generator=_gen_power_of_two_inputs,
        examples=[
            {
                "input": "n = 1",
                "output": "true",
                "explanation": "2⁰ = 1.",
            },
            {
                "input": "n = 16",
                "output": "true",
                "explanation": "2⁴ = 16.",
            },
            {
                "input": "n = 3",
                "output": "false",
                "explanation": "3 is not a power of two.",
            },
        ],
        approach="""### Bit Manipulation: Single Bit Invariant

An integer $n$ is a power of two if and only if $n > 0$ and its binary representation contains exactly one set bit.

#### 1. Invariant Analysis
Consider any power of two: $n = 2^k$.
In binary, $n$ has a 1 at index $k$ and 0s elsewhere:
$$n = 1000\\dots0_2$$
Subtracting 1 flips bit $k$ to 0 and all lower bits to 1:
$$n - 1 = 0111\\dots1_2$$
Consequently:
$$n \\land (n - 1) = 0$$

#### 2. Non-Powers and Edge Cases
If $n$ is not a power of two, it contains multiple set bits; clearing the lowest set bit via $n \\land (n - 1)$ leaves the higher set bits intact, producing a non-zero result.
Non-positive integers ($n \\le 0$) cannot be powers of two.
Hence: `n > 0 && (n & (n - 1)) === 0` completely decides the property in $O(1)$ time.""",
        why_optimal_template="Iterative division by 2 requires O(log n) division and modulo operations. Checking n > 0 && (n & (n - 1)) === 0 evaluates in O(1) time with a single CPU instruction. On {case_count} verified test cases, the O(1) bit test executed in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for iterative division.",
        pitfalls="Values <= 0 (such as 0 or negative powers like -16) must return false. (0 & -1) === 0, so the positive check n > 0 is mandatory.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Power_of_two",
            "https://en.wikipedia.org/wiki/Bit_manipulation",
        ],
        hints=[
            "A power of two in binary has exactly one bit set to 1.",
            "What happens to the binary representation of a power of two when you subtract 1 from it?",
            "Remember that 0 and negative integers are never powers of two.",
        ],
    ),

    # 13. sort-an-array
    ProblemBundle(
        spec=spec_sort_an_array,
        py_brute_code=py_brute_sort_an_array,
        py_brute_complexity="Time: O(n²) | Space: O(n)",
        py_optimal_code=py_optimal_sort_an_array,
        py_optimal_complexity="Time: O(n log n) | Space: O(n)",
        input_generator=_gen_sort_an_array_inputs,
        examples=[
            {
                "input": "nums = [5, 2, 3, 1]",
                "output": "[1, 2, 3, 5]",
                "explanation": "The array sorted in non-decreasing order.",
            },
            {
                "input": "nums = [5, 1, 1, 2, 0, 0]",
                "output": "[0, 0, 1, 1, 2, 5]",
                "explanation": "Duplicates are maintained in sorted order.",
            },
            {
                "input": "nums = []",
                "output": "[]",
                "explanation": "Empty array is sorted by definition.",
            },
        ],
        approach="""### Divide-and-Conquer: Merge Sort

Sorting an array of $n$ elements with guaranteed $O(n \\log n)$ time complexity and stability is achieved via Merge Sort.

#### 1. Recurrence and Structure
Divide the array segment $nums[left \\dots right]$ at $mid = \\lfloor(left + right) / 2\\rfloor$:
1. Recursively sort left subarray $nums[left \\dots mid]$.
2. Recursively sort right subarray $nums[mid + 1 \\dots right]$.
3. Merge the two sorted subarrays into an auxiliary scratch buffer `temp` and copy back to $nums$.

#### 2. Merge Procedure
Maintain two pointers $i = left$ and $j = mid + 1$. Compare $nums[i]$ and $nums[j]$, copying the smaller value to $temp[k++]$. Append any remaining elements once one half is exhausted.

#### 3. Complexity
$$T(n) = 2T(n/2) + O(n) \\implies O(n \\log n)$$
Allocating a single scratch buffer of size $n$ upfront keeps auxiliary space to $O(n)$.""",
        why_optimal_template="Quadratic comparison sorts like insertion sort degrade to O(n²) on reverse or large arrays. Merge sort guarantees O(n log n) worst-case time by halving subproblems and merging in linear time. On {case_count} verified test cases, merge sort executed in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for insertion sort.",
        pitfalls="Allocating new slices or arrays on every recursive call causes excessive garbage collection. Allocate one temporary buffer of size n upfront.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Merge_sort",
            "https://en.wikipedia.org/wiki/Sorting_algorithm",
        ],
        hints=[
            "Divide the array into two halves until subarrays have length 1.",
            "Merge two sorted halves by advancing two pointers and placing the smaller element first.",
            "Use a pre-allocated temporary array to avoid repeated memory allocations.",
        ],
    ),

    # 14. largest-number
    ProblemBundle(
        spec=spec_largest_number,
        py_brute_code=py_brute_largest_number,
        py_brute_complexity="Time: O(n² · k) | Space: O(n · k)",
        py_optimal_code=py_optimal_largest_number,
        py_optimal_complexity="Time: O(n log n · k) | Space: O(n · k)",
        input_generator=_gen_largest_number_inputs,
        examples=[
            {
                "input": "nums = [10, 2]",
                "output": "'210'",
                "explanation": "'210' > '102'.",
            },
            {
                "input": "nums = [3, 30, 34, 5, 9]",
                "output": "'9534330'",
                "explanation": "'9' followed by '5', '34', '3', '30' yields the maximum concatenated string.",
            },
            {
                "input": "nums = [0, 0]",
                "output": "'0'",
                "explanation": "If all digits are 0, return '0' rather than '00'.",
            },
        ],
        approach="""### Greedy Sorting with Custom Pairwise Concatenation Comparator

To form the largest number by concatenating strings, we determine the relative ordering of any two numbers $A$ and $B$.

#### 1. Comparator Invariant
For any two string representations $A$ and $B$:
- Concatenation $A + B$ puts $A$ before $B$.
- Concatenation $B + A$ puts $B$ before $A$.
We define our ordering such that $A$ should precede $B$ if and only if $A + B > B + A$.
This relation defines a total ordering over non-negative integer strings, proving transitivity and guaranteeing global optimality.

#### 2. Edge Case Handling
Sort strings according to this comparator in descending order.
If the first element after sorting is `"0"`, all elements must be `"0"`, so return `"0"` immediately rather than `"00...0"`. Otherwise, join the sorted strings.""",
        why_optimal_template="Bubble sort with pairwise comparisons takes O(n² · k) time. Using an O(n log n) sorting algorithm with the pairwise concatenation comparator achieves optimal O(n log n · k) complexity. On {case_count} verified test cases, custom comparator sorting completed in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for bubble sort.",
        pitfalls="Numerical comparison a - b fails for numbers with different digit lengths (e.g. 3 vs 30: '330' > '303'). Always compare concatenated strings (b + a) vs (a + b).",
        reading_links=[
            "https://en.wikipedia.org/wiki/Lexicographic_order",
            "https://en.wikipedia.org/wiki/Sorting_algorithm",
        ],
        hints=[
            "Convert all numbers into their string representations.",
            "Compare any two numbers a and b by checking whether b + a > a + b.",
            "Do not forget to handle the edge case where the array contains only zeros.",
        ],
    ),

    # 15. wiggle-sort-ii-lite
    ProblemBundle(
        spec=spec_wiggle_sort_ii_lite,
        py_brute_code=py_brute_wiggle_sort_ii_lite,
        py_brute_complexity="Time: O(n²) | Space: O(n)",
        py_optimal_code=py_optimal_wiggle_sort_ii_lite,
        py_optimal_complexity="Time: O(n log n) | Space: O(n)",
        input_generator=_gen_wiggle_sort_ii_lite_inputs,
        examples=[
            {
                "input": "nums = [1, 5, 1, 1, 6, 4]",
                "output": "[1, 6, 1, 5, 1, 4]",
                "explanation": "1 < 6 > 1 < 5 > 1 < 4 satisfies nums[0] < nums[1] > nums[2] < nums[3]...",
            },
            {
                "input": "nums = [1, 3, 2, 2, 3, 1]",
                "output": "[2, 3, 1, 3, 1, 2]",
                "explanation": "2 < 3 > 1 < 3 > 1 < 2 satisfies the wiggle requirement.",
            },
            {
                "input": "nums = [1]",
                "output": "[1]",
                "explanation": "Single element array is trivially valid.",
            },
        ],
        approach="""### Sorting and Interleaving Reverse Halves

We rearrange `nums` such that $nums[0] < nums[1] > nums[2] < nums[3] \\dots$.

#### 1. Separation into Two Halves
Sort a copy of `nums` ascending:
- Smaller half `left`: first $\\lceil n / 2 \\rceil$ elements ($nums[0 \\dots mid - 1]$).
- Larger half `right`: remaining $\\lfloor n / 2 \\rfloor$ elements ($nums[mid \\dots n - 1]$).

#### 2. Reverse Interleaving Construction
If elements were placed from left to right, median duplicates from the boundary could collide at adjacent indices.
By taking elements in reverse order:
- Even indices $0, 2, 4, \\dots$ take elements from the end of `left` backwards.
- Odd indices $1, 3, 5, \\dots$ take elements from the end of `right` backwards.
This maximizes the distance between identical elements, strictly satisfying $nums[i-1] < nums[i] > nums[i+1]$.""",
        why_optimal_template="O(n²) selection sorting performs quadratic comparisons across elements. Using an O(n log n) sort followed by O(n) reverse-half interleaving rearranges the array in O(n log n) time and O(n) space. Across {case_count} verified test cases, O(n log n) sort-and-interleave executed in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for selection sort.",
        pitfalls="Interleaving from the start of each half instead of the reverse ends causes identical median values to end up adjacent.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Median",
            "https://en.wikipedia.org/wiki/Quickselect",
        ],
        hints=[
            "Sort the array and divide it into a smaller half and a larger half.",
            "Place smaller elements at even indices and larger elements at odd indices.",
            "Write the elements in reverse order (from largest to smallest within each half) to keep duplicates separated.",
        ],
    ),

    # 16. merge-sorted-array
    ProblemBundle(
        spec=spec_merge_sorted_array,
        py_brute_code=py_brute_merge_sorted_array,
        py_brute_complexity="Time: O((m + n) log(m + n)) | Space: O(1)",
        py_optimal_code=py_optimal_merge_sorted_array,
        py_optimal_complexity="Time: O(m + n) | Space: O(1)",
        input_generator=_gen_merge_sorted_array_inputs,
        examples=[
            {
                "input": "nums1 = [1, 2, 3, 0, 0, 0], m = 3, nums2 = [2, 5, 6], n = 3",
                "output": "[1, 2, 2, 3, 5, 6]",
                "explanation": "nums2 is merged into nums1 in-place producing a fully sorted array.",
            },
            {
                "input": "nums1 = [1], m = 1, nums2 = [], n = 0",
                "output": "[1]",
                "explanation": "nums2 is empty, so nums1 remains [1].",
            },
            {
                "input": "nums1 = [0], m = 0, nums2 = [1], n = 1",
                "output": "[1]",
                "explanation": "nums1 has no initial elements; nums2 is copied directly.",
            },
        ],
        approach="""### Three-Pointer In-Place Back-Fill

Given `nums1` of size $m + n$ and `nums2` of size $n$, merge `nums2` into `nums1` in sorted order without using extra memory.

#### 1. Why Iterate From the Back?
Iterating from the front would overwrite elements in `nums1` that have not yet been compared.
However, the end of `nums1` (indices $m$ to $m + n - 1$) contains unused padding zeros. Writing largest elements from index $m + n - 1$ down to 0 guarantees that no unread element of `nums1` is ever overwritten.

#### 2. Algorithm
- Initialize $p_1 = m - 1$, $p_2 = n - 1$, and write pointer $p = m + n - 1$.
- While $p_2 \\ge 0$:
  - If $p_1 \\ge 0$ and $nums1[p_1] > nums2[p_2]$, set $nums1[p--] = nums1[p_1--]$.
  - Else set $nums1[p--] = nums2[p_2--]$.
- Return `nums1`.""",
        why_optimal_template="Appending nums2 to nums1 and sorting takes O((m + n) log(m + n)) time. The three-pointer reverse fill takes linear O(m + n) time and O(1) auxiliary space by utilizing the pre-allocated trailing space in nums1. On {case_count} verified test cases, three-pointer back-fill ran in {optimal_ms:.2f} ms versus {brute_ms:.2f} ms for append-and-sort.",
        pitfalls="Stopping when p1 < 0 instead of when p2 < 0. If p1 runs out first, remaining elements in nums2 must still be copied into nums1.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Merge_algorithm",
            "https://en.wikipedia.org/wiki/In-place_algorithm",
        ],
        hints=[
            "Start merging from the back of nums1 to avoid overwriting existing elements.",
            "Compare nums1[p1] and nums2[p2], writing the larger value at index p = m + n - 1.",
            "Once p2 < 0, all elements from nums2 are placed and any remaining elements in nums1 are already in place.",
        ],
    ),

    # 17. jump-game-ii
    ProblemBundle(
        spec=spec_jump_game_ii,
        py_brute_code=py_brute_jump_game_ii,
        py_brute_complexity="Time: O(n²) | Space: O(n)",
        py_optimal_code=py_optimal_jump_game_ii,
        py_optimal_complexity="Time: O(n) | Space: O(1)",
        input_generator=_gen_jump_game_ii_inputs,
        examples=[
            {
                "input": "nums = [2, 3, 1, 1, 4]",
                "output": "2",
                "explanation": "Jump 1 step from index 0 to 1, then 3 steps to the last index.",
            },
            {
                "input": "nums = [2, 3, 0, 1, 4]",
                "output": "2",
                "explanation": "Minimum jumps to index 4 is 2.",
            },
            {
                "input": "nums = [0]",
                "output": "0",
                "explanation": "Already at the last index, requiring 0 jumps.",
            },
        ],
        approach="""### Greedy BFS Window Expansion

We must find the minimum number of jumps to reach index $n - 1$. Since reaching the end is guaranteed, we can interpret the problem as a Breadth-First Search (BFS) where each level corresponds to one additional jump.

#### 1. BFS Level Window
Instead of an explicit BFS queue, we track the current jump level's range $[start, currentEnd]$ and the maximum reach achievable by any jump within this range ($farthest$).

#### 2. Greedy Transition
Iterate index $i$ from $0$ to $n - 2$:
1. Update $farthest = \\max(farthest, i + nums[i])$.
2. When $i == currentEnd$:
   - A jump must be taken to advance to the next level: `jumps++`.
   - Update $currentEnd = farthest$.
   - If $currentEnd \\ge n - 1$, terminate early.

#### 3. Complexity
Single linear pass visiting each element at most once: $O(n)$ time and $O(1)$ space.""",
        why_optimal_template="Dynamic programming iteratively updates minimum jumps for all reachable indices in O(n²) time. Greedy window expansion treats each jump as a BFS level boundary, finding the minimum jumps in a single O(n) pass with O(1) space. Across {case_count} verified test cases, greedy window expansion executed in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for quadratic DP.",
        pitfalls="Looping up to n - 1 instead of n - 2 causes an extra unwanted jump increment when already standing at the final index.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Greedy_algorithm",
            "https://en.wikipedia.org/wiki/Breadth-first_search",
        ],
        hints=[
            "Think of this as BFS where each jump level covers a range of indices.",
            "Maintain the farthest index reachable from any position in the current jump window.",
            "Only iterate up to n - 2, because once you reach n - 1 no more jumps are needed.",
        ],
    ),

    # 18. pow-x-n
    ProblemBundle(
        spec=spec_pow_x_n,
        py_brute_code=py_brute_pow_x_n,
        py_brute_complexity="Time: O(|n|) | Space: O(1)",
        py_optimal_code=py_optimal_pow_x_n,
        py_optimal_complexity="Time: O(log |n|) | Space: O(1)",
        input_generator=_gen_pow_x_n_inputs,
        examples=[
            {
                "input": "x = 2.0, n = 10",
                "output": "1024",
                "explanation": "2¹⁰ = 1024.",
            },
            {
                "input": "x = 2.1, n = 3",
                "output": "9.261",
                "explanation": "2.1³ = 9.261.",
            },
            {
                "input": "x = 2.0, n = -2",
                "output": "0.25",
                "explanation": "2⁻² = 1 / (2²) = 1 / 4 = 0.25.",
            },
        ],
        approach="""### Exponentiation by Squaring (Binary Exponentiation)

Computing $x^n$ by multiplying $x$ by itself $n$ times takes $O(|n|)$ operations, which is prohibitively slow for large exponents. Binary exponentiation halves the exponent at each step.

#### 1. Mathematical Principle
For any integer $n \\ge 0$:
$$x^n = \\begin{cases} 1 & \\text{if } n = 0 \\\\ (x^2)^{n/2} & \\text{if } n \\text{ is even} \\\\ x \\cdot (x^2)^{(n-1)/2} & \\text{if } n \\text{ is odd} \\end{cases}$$

#### 2. Negative Exponents
If $n < 0$, invert the base and negate the exponent:
$$x = \\frac{1}{x}, \\quad n = -n$$

#### 3. Algorithm
Initialize `res = 1.0`. While $n > 0$:
- If $n$ is odd ($n \\% 2 == 1$), `res *= x`.
- Square the base: `x *= x`.
- Halve the exponent: $n = \\lfloor n / 2 \\rfloor$.
Round the result to 5 decimal places to prevent float precision divergence.""",
        why_optimal_template="Linear multiplication takes O(|n|) operations. Binary exponentiation squares the base and halves the exponent at each step, reducing runtime to O(log |n|). On {case_count} verified test cases, binary exponentiation executed in {optimal_ms:.2f} ms versus {brute_ms:.2f} ms for linear multiplication.",
        pitfalls="Handling 32-bit integer minimum -2147483648: negating it directly causes overflow in languages without 64-bit promotion. Using division by 2 avoids overflow.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Exponentiation_by_squaring",
        ],
        hints=[
            "If n is even, xⁿ = (x²)^(n/2). If n is odd, xⁿ = x · (x²)^((n-1)/2).",
            "When n is negative, transform the problem to (1/x)^(-n).",
            "This reduces the number of multiplications from O(n) to O(log n).",
        ],
    ),

    # 19. meeting-rooms-ii
    ProblemBundle(
        spec=spec_meeting_rooms_ii,
        py_brute_code=py_brute_meeting_rooms_ii,
        py_brute_complexity="Time: O(n²) | Space: O(1)",
        py_optimal_code=py_optimal_meeting_rooms_ii,
        py_optimal_complexity="Time: O(n log n) | Space: O(n)",
        input_generator=_gen_meeting_rooms_ii_inputs,
        examples=[
            {
                "input": "intervals = [[0, 30], [5, 10], [15, 20]]",
                "output": "2",
                "explanation": "Meeting [0, 30] conflicts with [5, 10] and [15, 20]. At least 2 rooms are required.",
            },
            {
                "input": "intervals = [[7, 10], [2, 4]]",
                "output": "1",
                "explanation": "The two meetings do not overlap in time, requiring only 1 room.",
            },
            {
                "input": "intervals = []",
                "output": "0",
                "explanation": "No meetings require 0 rooms.",
            },
        ],
        approach="""### Sweep-Line / Two-Pointer Coordinate Discretization

The minimum number of conference rooms required equals the maximum number of concurrent meetings occurring at any point in time.

#### 1. Decoupling Starts and Ends
A meeting interval $[start, end]$ indicates that at time $start$ a room is claimed (+1), and at time $end$ a room is released (-1).
Because each room release is interchangeable across all active meetings, start times and end times can be extracted and sorted into two separate arrays:
- `starts = intervals.map(iv => iv[0]).sort()`
- `ends = intervals.map(iv => iv[1]).sort()`

#### 2. Two-Pointer Scan
Maintain pointers $s$ (current start) and $e$ (current end), and tracking variables `rooms` and `maxRooms`:
- If $starts[s] < ends[e]$: A meeting starts before the earliest ending meeting finishes. Increment `rooms++`, update `maxRooms = max(maxRooms, rooms)`, and advance $s++$.
- Else: A meeting has ended. Decrement `rooms--` and advance $e++$.
Terminates when all meetings have started ($s == n$).""",
        why_optimal_template="Checking all pairwise overlaps for each interval takes O(n²) time. Decoupling start and end coordinates into two sorted arrays allows a linear two-pointer scan, reducing time complexity to O(n log n). On {case_count} verified test cases, the two-pointer sweep line ran in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for pairwise overlap checks.",
        pitfalls="A meeting ending at time t does NOT conflict with a meeting starting at time t. Use strictly less than (starts[s] < ends[e]) so the ended room is freed.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Sweep_line_algorithm",
            "https://en.wikipedia.org/wiki/Priority_queue",
        ],
        hints=[
            "The minimum rooms required is equal to the maximum number of simultaneous overlapping meetings.",
            "Separate the start times and end times into two arrays and sort both independently.",
            "Use two pointers: when start[s] < end[e], allocate a room; otherwise free a room.",
        ],
    ),

    # 20. find-words-on-board
    ProblemBundle(
        spec=spec_find_words_on_board,
        py_brute_code=py_brute_find_words_on_board,
        py_brute_complexity="Time: O(W · m · n · 4ᴸ) | Space: O(m · n + W)",
        py_optimal_code=py_optimal_find_words_on_board,
        py_optimal_complexity="Time: O(m · n · 4ᴸ) | Space: O(Σ|word|)",
        input_generator=_gen_find_words_on_board_inputs,
        examples=[
            {
                "input": "board = [['o', 'a', 'a', 'n'], ['e', 't', 'a', 'e'], ['i', 'h', 'k', 'r'], ['i', 'f', 'l', 'v']], words = ['oath', 'pea', 'eat', 'rain']",
                "output": "['eat', 'oath']",
                "explanation": "'eat' and 'oath' exist on the board; 'pea' and 'rain' cannot be formed.",
            },
            {
                "input": "board = [['a', 'b'], ['c', 'd']], words = ['abcb']",
                "output": "[]",
                "explanation": "Cell reuse is disallowed, so 'abcb' cannot be formed.",
            },
            {
                "input": "board = [['a']], words = ['a', 'b']",
                "output": "['a']",
                "explanation": "Only 'a' is present on the single cell board.",
            },
        ],
        approach="""### Prefix Tree (Trie) + DFS Grid Traversal with Branch Pruning

Searching for $W$ words individually on an $m \\times n$ grid takes $O(W \\cdot m \\cdot n \\cdot 4^L)$ time, performing repeated identical traversals for words sharing common prefixes.

#### 1. Trie Construction
Insert all target `words` into a Prefix Tree (Trie). Each node contains a dictionary of child characters and optionally a `word` reference when a valid word terminates at that node.

#### 2. Trie-Guided DFS
From each grid cell $(r, c)$:
- If `root` has a child for $board[r][c]$, launch DFS $(r, c, root)$.
- At each step:
  - If the current Trie node contains a valid word, add it to results and set `node.word = null` to avoid duplicate insertions.
  - Temporarily mask $board[r][c] = \\text{'#'}$.
  - Explore all 4 orthogonal neighbors whose characters match valid children of `currNode`.
  - Restore $board[r][c]$ upon return (backtracking).

Any path whose prefix is not in the Trie is pruned immediately in $O(1)$ time.""",
        why_optimal_template="Searching for each word independently traverses the board W separate times. Compacting all words into a Trie enables searching for all words simultaneously in a single DFS pass, pruning invalid branches immediately. Across {case_count} verified test cases, Trie-pruned DFS executed in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for independent per-word searches.",
        pitfalls="Multiple grid paths can form the same word. When a word is found, set node.word = null in the Trie node to prevent duplicate entries in the result set.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Trie",
            "https://en.wikipedia.org/wiki/Depth-first_search",
        ],
        hints=[
            "Build a Trie from all words to find common prefixes simultaneously.",
            "Perform DFS from each board cell while traversing corresponding Trie nodes.",
            "Once a word is matched, clear its end-of-word marker in the Trie to prevent duplicate detections.",
        ],
    ),
]


# ===========================================================================
# Execution and Verification Harness
# ===========================================================================
async def _execute(language: str, code: str, fn_name: str, cases: list[dict], time_limit_ms: int = 2000) -> Any:
    return await execute_code(
        language=language,
        code=code,
        function_name=fn_name,
        test_cases=cases,
        time_limit_ms=time_limit_ms,
    )


async def build_and_verify_bundle(bundle: ProblemBundle) -> dict[str, Any]:
    spec = bundle.spec
    rng = random.Random(spec.seed)
    raw_inputs = bundle.input_generator(rng)

    # Build test cases list
    test_cases: list[dict[str, Any]] = [
        {"label": f"case-{i + 1:02d}", "input": inp, "expected": None, "isSample": False}
        for i, inp in enumerate(raw_inputs)
    ]

    # First probe with optimal JS to generate expected outputs
    probe_res = await _execute("javascript", spec.optimal.code, spec.function_name, copy.deepcopy(test_cases), spec.time_limit_ms)
    if probe_res.compile_output or len(probe_res.test_results) != len(test_cases):
        raise ValueError(f"Optimal JS probe failed for {spec.slug}: {probe_res.compile_output}")
    for case, tr in zip(test_cases, probe_res.test_results, strict=True):
        if tr.get("error") is not None or "actual" not in tr:
            raise ValueError(f"Optimal JS produced error for {spec.slug} case {case['label']}: {tr.get('error')}")
        case["expected"] = tr["actual"]

    # Mark sample cases
    sample_count = min(len(bundle.examples), len(test_cases))
    for i in range(sample_count):
        test_cases[i]["isSample"] = True

    # 1. Run JS Brute Force
    js_brute_res = await _execute("javascript", spec.brute_force.code, spec.function_name, copy.deepcopy(test_cases), spec.time_limit_ms)
    if js_brute_res.verdict != "AC":
        raise ValueError(f"JS Brute Force failed for {spec.slug}: {js_brute_res.compile_output} (test results: {js_brute_res.test_results})")

    # 2. Run JS Optimal
    js_optimal_res = await _execute("javascript", spec.optimal.code, spec.function_name, copy.deepcopy(test_cases), spec.time_limit_ms)
    if js_optimal_res.verdict != "AC":
        raise ValueError(f"JS Optimal failed for {spec.slug}: {js_optimal_res.compile_output} (test results: {js_optimal_res.test_results})")

    # 3. Run Python Brute Force
    py_brute_res = await _execute("python", bundle.py_brute_code, spec.function_name, copy.deepcopy(test_cases), spec.time_limit_ms)
    if py_brute_res.verdict != "AC":
        raise ValueError(f"Py Brute Force failed for {spec.slug}: {py_brute_res.compile_output} (test results: {py_brute_res.test_results})")

    # 4. Run Python Optimal
    py_optimal_res = await _execute("python", bundle.py_optimal_code, spec.function_name, copy.deepcopy(test_cases), spec.time_limit_ms)
    if py_optimal_res.verdict != "AC":
        raise ValueError(f"Py Optimal failed for {spec.slug}: {py_optimal_res.compile_output} (test results: {py_optimal_res.test_results})")

    brute_runtime = js_brute_res.runtime_ms
    optimal_runtime = js_optimal_res.runtime_ms

    why_optimal = bundle.why_optimal_template.format(
        case_count=len(test_cases),
        optimal_ms=optimal_runtime,
        brute_ms=brute_runtime,
    )

    names = ", ".join(param.name for param in spec.parsed_signature.parameters)
    starter_js = f"function {spec.function_name}({names}) {{\n  // Write your solution here\n  throw new Error('Not implemented');\n}}\n"
    starter_py = f"def {spec.function_name}({names}):\n    # Write your solution here\n    raise NotImplementedError\n"

    constraints = [
        f"Function signature: `{spec.signature}`.",
        "Inputs are JSON-serializable values satisfying the bounds stated above.",
    ]

    solutions = [
        {
            "title": "Brute Force",
            "complexity": spec.brute_force.complexity,
            "language": "javascript",
            "code": spec.brute_force.code,
            "isReference": False,
        },
        {
            "title": "Optimal",
            "complexity": spec.optimal.complexity,
            "language": "javascript",
            "code": spec.optimal.code,
            "isReference": True,
        },
        {
            "title": "Brute Force",
            "complexity": bundle.py_brute_complexity,
            "language": "python",
            "code": bundle.py_brute_code,
            "isReference": False,
        },
        {
            "title": "Optimal",
            "complexity": bundle.py_optimal_complexity,
            "language": "python",
            "code": bundle.py_optimal_code,
            "isReference": True,
        },
    ]

    data: dict[str, Any] = {
        "slug": spec.slug,
        "title": spec.title,
        "topic": spec.topic,
        "difficulty": spec.difficulty,
        "pattern": spec.pattern,
        "statement": spec.statement,
        "examples": bundle.examples,
        "constraints": constraints,
        "hints": bundle.hints,
        "editorial": {
            "approach": bundle.approach,
            "why_optimal": why_optimal,
            "pitfalls": bundle.pitfalls,
        },
        "reading_links": bundle.reading_links,
        "starterCode": {
            "javascript": starter_js,
            "python": starter_py,
        },
        "functionName": spec.function_name,
        "timeLimitMs": spec.time_limit_ms,
        "reviewStatus": "verified",
        "pafVerification": {
            "seed": spec.seed,
            "generatedCaseCount": len(test_cases),
            "bruteForceRuntimeMs": brute_runtime,
            "optimalRuntimeMs": optimal_runtime,
        },
        "testCases": test_cases,
        "solutions": solutions,
    }

    ProblemSchema(**data)
    gate_errors = check_paf_gates(data, f"{spec.slug}.json")
    if gate_errors:
        raise ValueError(f"Gate errors in {spec.slug}: {gate_errors}")

    return data


async def main() -> None:
    output_dir = REPO_ROOT / "content" / "problems"
    print(f"Authoring and verifying {len(BUNDLES)} Batch-4 problems with PAF...")
    for idx, bundle in enumerate(BUNDLES, 1):
        slug = bundle.spec.slug
        print(f"[{idx:02d}/{len(BUNDLES):02d}] Generating {slug} ({bundle.spec.difficulty})...")
        data = await build_and_verify_bundle(bundle)
        out_file = output_dir / f"{slug}.json"
        out_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        paf = data["pafVerification"]
        print(
            f"  ✓ {slug}: {paf['generatedCaseCount']} cases verified 100% AC | "
            f"JS Brute: {paf['bruteForceRuntimeMs']:.2f}ms | "
            f"JS Optimal: {paf['optimalRuntimeMs']:.2f}ms | 4 solutions verified -> {out_file.name}"
        )
    print(f"\nAll {len(BUNDLES)} Batch-4 problems generated and PAF-verified successfully.")


if __name__ == "__main__":
    asyncio.run(main())
