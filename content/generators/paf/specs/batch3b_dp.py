"""Authoring and verification script for Batch 3B: Dynamic Programming and Greedy problems."""

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


# ---------------------------------------------------------------------------
# Problem 1: house-robber-ii
# ---------------------------------------------------------------------------
spec_rob2 = ProblemSpec(
    signature="function rob2(nums: number[])",
    statement="""# House Robber II

You are a professional robber planning to rob houses along a street. Each house has a certain amount of money stashed. All houses at this place are arranged in a circle. That means the first house is the neighbor of the last one. Meanwhile, adjacent houses have a security system connected, and it will automatically contact the police if two adjacent houses are broken into on the same night.

Given an integer array `nums` representing the amount of money of each house, return the maximum amount of money you can rob tonight without alerting the police.

Constraints: `1 <= nums.length <= 100` and `0 <= nums[i] <= 1000`.
""",
    brute_force=Algorithm(
        """function rob2(nums) {
  if (nums.length === 0) return 0;
  if (nums.length === 1) return nums[0];
  if (nums.length === 2) return Math.max(nums[0], nums[1]);

  function robLinear(arr) {
    const n = arr.length;
    if (n === 0) return 0;
    if (n === 1) return arr[0];
    const dp = new Array(n).fill(0);
    dp[0] = arr[0];
    dp[1] = Math.max(arr[0], arr[1]);
    for (let i = 2; i < n; i++) {
      dp[i] = Math.max(dp[i - 1], dp[i - 2] + arr[i]);
    }
    return dp[n - 1];
  }

  const case1 = robLinear(nums.slice(0, nums.length - 1));
  const case2 = robLinear(nums.slice(1));
  return Math.max(case1, case2);
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function rob2(nums) {
  if (nums.length === 0) return 0;
  if (nums.length === 1) return nums[0];
  if (nums.length === 2) return Math.max(nums[0], nums[1]);

  function robLinear(start, end) {
    let prev2 = 0;
    let prev1 = 0;
    for (let i = start; i <= end; i++) {
      const cur = Math.max(prev1, prev2 + nums[i]);
      prev2 = prev1;
      prev1 = cur;
    }
    return prev1;
  }

  return Math.max(robLinear(0, nums.length - 2), robLinear(1, nums.length - 1));
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    topic="dynamic-programming",
    difficulty="Medium",
    pattern="dp / Circular split",
    time_limit_ms=2000,
    seed=42,
    title="House Robber II",
    slug="house-robber-ii",
)

py_brute_rob2 = """def rob2(nums: list[int]) -> int:
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    if len(nums) == 2:
        return max(nums[0], nums[1])

    def rob_linear(arr: list[int]) -> int:
        n = len(arr)
        if n == 0:
            return 0
        if n == 1:
            return arr[0]
        dp = [0] * n
        dp[0] = arr[0]
        dp[1] = max(arr[0], arr[1])
        for i in range(2, n):
            dp[i] = max(dp[i - 1], dp[i - 2] + arr[i])
        return dp[-1]

    return max(rob_linear(nums[:-1]), rob_linear(nums[1:]))
"""

py_optimal_rob2 = """def rob2(nums: list[int]) -> int:
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    if len(nums) == 2:
        return max(nums[0], nums[1])

    def rob_linear(start: int, end: int) -> int:
        prev2, prev1 = 0, 0
        for i in range(start, end + 1):
            cur = max(prev1, prev2 + nums[i])
            prev2, prev1 = prev1, cur
        return prev1

    return max(rob_linear(0, len(nums) - 2), rob_linear(1, len(nums) - 1))
"""


def _gen_rob2_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[2, 3, 2]],
        [[1, 2, 3, 1]],
        [[1, 2, 1, 1]],
        [[5]],
        [[0]],
        [[2, 3]],
        [[10, 1]],
        [[1, 2, 3]],
        [[10, 10, 10, 10]],
        [[100, 1, 100, 1, 100]],
        [[0, 0, 0]],
        [[20, 1, 1, 20]],
        [[1, 7, 9, 2]],
        [[4, 1, 2, 7, 5, 3, 1]],
    ]
    for _ in range(12):
        n = rng.randint(4, 30)
        cases.append([[rng.randint(0, 500) for _ in range(n)]])
    # Stress cases
    cases.append([[rng.randint(100, 1000) for _ in range(100)]])
    cases.append([[rng.randint(0, 1000) for _ in range(100)]])
    cases.append([[rng.choice([0, 1000]) for _ in range(100)]])
    cases.append([[500] * 100])
    return cases


# ---------------------------------------------------------------------------
# Problem 2: decode-ways
# ---------------------------------------------------------------------------
spec_decode_ways = ProblemSpec(
    signature="function numDecodings(s: string)",
    statement="""# Decode Ways

A message containing letters from `A-Z` can be encoded into numbers using the following mapping:
- `'A'` -> `"1"`
- `'B'` -> `"2"`
- ...
- `'Z'` -> `"26"`

To decode an encoded message, all the digits must be grouped and mapped back into letters using the reverse mapping. There may be multiple valid groupings. For example, `"11106"` can be mapped into:
- `"AAJF"` with grouping `(1, 1, 10, 6)`
- `"KJF"` with grouping `(11, 10, 6)`

Note that the grouping `(1, 11, 06)` is invalid because `"06"` cannot be mapped into `'F'` since `'6'` is different from `"06"`.

Given a string `s` containing only digits, return the number of ways to decode it.

Constraints: `1 <= s.length <= 100` and `s` consists only of digits. The test cases are generated so that the answer fits in a 32-bit integer.
""",
    brute_force=Algorithm(
        """function numDecodings(s) {
  if (!s || s[0] === '0') return 0;
  const n = s.length;
  const dp = new Array(n + 1).fill(0);
  dp[0] = 1;
  dp[1] = 1;
  for (let i = 2; i <= n; i++) {
    const oneDigit = Number(s[i - 1]);
    const twoDigits = Number(s.slice(i - 2, i));
    if (oneDigit >= 1 && oneDigit <= 9) {
      dp[i] += dp[i - 1];
    }
    if (twoDigits >= 10 && twoDigits <= 26) {
      dp[i] += dp[i - 2];
    }
  }
  return dp[n];
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function numDecodings(s) {
  if (!s || s[0] === '0') return 0;
  let prev2 = 1;
  let prev1 = 1;
  for (let i = 2; i <= s.length; i++) {
    let current = 0;
    const oneDigit = Number(s[i - 1]);
    const twoDigits = Number(s.slice(i - 2, i));
    if (oneDigit >= 1 && oneDigit <= 9) {
      current += prev1;
    }
    if (twoDigits >= 10 && twoDigits <= 26) {
      current += prev2;
    }
    prev2 = prev1;
    prev1 = current;
  }
  return prev1;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    topic="dynamic-programming",
    difficulty="Medium",
    pattern="dp / Prefix count",
    time_limit_ms=2000,
    seed=42,
    title="Decode Ways",
    slug="decode-ways",
)

py_brute_decode_ways = """def numDecodings(s: str) -> int:
    if not s or s[0] == "0":
        return 0
    n = len(s)
    dp = [0] * (n + 1)
    dp[0] = 1
    dp[1] = 1
    for i in range(2, n + 1):
        one_digit = int(s[i - 1])
        two_digits = int(s[i - 2 : i])
        if 1 <= one_digit <= 9:
            dp[i] += dp[i - 1]
        if 10 <= two_digits <= 26:
            dp[i] += dp[i - 2]
    return dp[n]
"""

py_optimal_decode_ways = """def numDecodings(s: str) -> int:
    if not s or s[0] == "0":
        return 0
    prev2, prev1 = 1, 1
    for i in range(2, len(s) + 1):
        current = 0
        one_digit = int(s[i - 1])
        two_digits = int(s[i - 2 : i])
        if 1 <= one_digit <= 9:
            current += prev1
        if 10 <= two_digits <= 26:
            current += prev2
        prev2, prev1 = prev1, current
    return prev1
"""


def _gen_decode_ways_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        ["226"],
        ["10"],
        ["06"],
        ["0"],
        ["7"],
        ["12"],
        ["27"],
        ["20"],
        ["30"],
        ["100"],
        ["11106"],
        ["2101"],
        ["1201234"],
        ["2611055971756562"],
        ["1111111111"],
    ]
    for _ in range(11):
        length = rng.randint(4, 25)
        chars: list[str] = []
        for _ in range(length):
            if chars and chars[-1] in ("1", "2") and rng.random() < 0.2:
                chars.append("0")
            else:
                chars.append(str(rng.randint(1, 9)))
        cases.append(["".join(chars)])
    # Stress cases (length 100 with results guaranteed in 32-bit integer)
    cases.append(["1201234789" * 10])
    cases.append(["2101345678" * 10])
    cases.append(["2738495018" * 10])
    cases.append(["10" * 50])
    return cases


# ---------------------------------------------------------------------------
# Problem 3: word-break
# ---------------------------------------------------------------------------
spec_word_break = ProblemSpec(
    signature="function wordBreak(s: string, wordDict: string[])",
    statement="""# Word Break

Given a string `s` and a dictionary of strings `wordDict`, return `true` if `s` can be segmented into a space-separated sequence of one or more dictionary words, or `false` otherwise.

Note that the same word in the dictionary may be reused multiple times in the segmentation.

Constraints: `1 <= s.length <= 100`, `1 <= wordDict.length <= 100`, and `1 <= wordDict[i].length <= 20`. `s` and `wordDict[i]` consist only of lowercase English letters. All strings of `wordDict` are unique.
""",
    brute_force=Algorithm(
        """function wordBreak(s, wordDict) {
  const n = s.length;
  const dp = new Array(n + 1).fill(false);
  dp[0] = true;
  for (let i = 1; i <= n; i++) {
    for (let j = 0; j < i; j++) {
      if (dp[j]) {
        const sub = s.slice(j, i);
        if (wordDict.includes(sub)) {
          dp[i] = true;
          break;
        }
      }
    }
  }
  return dp[n];
}""",
        complexity="Time: O(n² · m) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function wordBreak(s, wordDict) {
  const wordSet = new Set(wordDict);
  let maxLen = 0;
  for (const w of wordDict) {
    if (w.length > maxLen) maxLen = w.length;
  }
  const n = s.length;
  const dp = new Array(n + 1).fill(false);
  dp[0] = true;
  for (let i = 1; i <= n; i++) {
    const start = Math.max(0, i - maxLen);
    for (let j = i - 1; j >= start; j--) {
      if (dp[j] && wordSet.has(s.slice(j, i))) {
        dp[i] = true;
        break;
      }
    }
  }
  return dp[n];
}""",
        complexity="Time: O(n · L) | Space: O(n + W)",
        language="javascript",
    ),
    topic="dynamic-programming",
    difficulty="Medium",
    pattern="dp / Reachability",
    time_limit_ms=2000,
    seed=42,
    title="Word Break",
    slug="word-break",
)

py_brute_word_break = """def wordBreak(s: str, wordDict: list[str]) -> bool:
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True
    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] and s[j:i] in wordDict:
                dp[i] = True
                break
    return dp[n]
"""

py_optimal_word_break = """def wordBreak(s: str, wordDict: list[str]) -> bool:
    word_set = set(wordDict)
    max_len = max(len(w) for w in wordDict) if wordDict else 0
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True
    for i in range(1, n + 1):
        start = max(0, i - max_len)
        for j in range(i - 1, start - 1, -1):
            if dp[j] and s[j:i] in word_set:
                dp[i] = True
                break
    return dp[n]
"""


def _gen_word_break_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        ["applepenapple", ["apple", "pen"]],
        ["catsandog", ["cats", "dog", "sand", "and", "cat"]],
        ["goalspecial", ["go", "goal", "goals", "special"]],
        ["a", ["a"]],
        ["a", ["b"]],
        ["aaaaaaa", ["aaaa", "aaa"]],
        ["leetcode", ["leet", "code"]],
        ["cars", ["car", "ca", "rs"]],
        ["abcd", ["a", "abc", "b", "cd"]],
        ["bb", ["a", "b", "bbb", "bbbb"]],
        ["programmers", ["program", "mer", "mers", "pro", "gram"]],
    ]
    vocab = ["fast", "slow", "code", "coder", "algo", "vista", "run", "runner", "jump", "high"]
    for _ in range(15):
        k = rng.randint(2, 6)
        chosen = [rng.choice(vocab) for _ in range(k)]
        s = "".join(chosen)
        dict_words = list(set(chosen + [rng.choice(vocab) for _ in range(3)]))
        if rng.random() < 0.3:
            s += "xyz"
        cases.append([s, dict_words])
    # Stress cases
    cases.append(["a" * 100, ["a", "aa", "aaa"]])
    cases.append(["a" * 99 + "b", ["a", "aa", "aaa"]])
    cases.append(["code" * 25, ["code", "coder", "co", "de"]])
    cases.append(["ab" * 50, ["a", "b", "ab"]])
    return cases


# ---------------------------------------------------------------------------
# Problem 4: longest-palindromic-substring
# ---------------------------------------------------------------------------
spec_lps = ProblemSpec(
    signature="function longestPalindrome(s: string)",
    statement="""# Longest Palindromic Substring

Given a string `s`, return the longest palindromic substring in `s`.

If there are multiple palindromic substrings of the same maximum length, return the one that appears earliest (smallest start index) in `s`.

Constraints: `1 <= s.length <= 100` and `s` consists only of lowercase English letters.
""",
    brute_force=Algorithm(
        """function longestPalindrome(s) {
  if (s.length <= 1) return s;
  let bestStart = 0;
  let bestLen = 1;
  function isPalindrome(left, right) {
    while (left < right) {
      if (s[left] !== s[right]) return false;
      left++;
      right--;
    }
    return true;
  }
  for (let i = 0; i < s.length; i++) {
    for (let j = i; j < s.length; j++) {
      const len = j - i + 1;
      if (len > bestLen && isPalindrome(i, j)) {
        bestStart = i;
        bestLen = len;
      }
    }
  }
  return s.slice(bestStart, bestStart + bestLen);
}""",
        complexity="Time: O(n³) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function longestPalindrome(s) {
  if (s.length <= 1) return s;
  let bestStart = 0;
  let bestLen = 1;

  function expand(left, right) {
    while (left >= 0 && right < s.length && s[left] === s[right]) {
      left--;
      right++;
    }
    const start = left + 1;
    const len = right - left - 1;
    if (len > bestLen || (len === bestLen && start < bestStart)) {
      bestStart = start;
      bestLen = len;
    }
  }

  for (let i = 0; i < s.length; i++) {
    expand(i, i);
    expand(i, i + 1);
  }
  return s.slice(bestStart, bestStart + bestLen);
}""",
        complexity="Time: O(n²) | Space: O(1)",
        language="javascript",
    ),
    topic="dynamic-programming",
    difficulty="Medium",
    pattern="dp / Expand center",
    time_limit_ms=2000,
    seed=42,
    title="Longest Palindromic Substring",
    slug="longest-palindromic-substring",
)

py_brute_lps = """def longestPalindrome(s: str) -> str:
    if len(s) <= 1:
        return s
    best_start = 0
    best_len = 1

    def is_palindrome(left: int, right: int) -> bool:
        while left < right:
            if s[left] != s[right]:
                return False
            left += 1
            right -= 1
        return True

    for i in range(len(s)):
        for j in range(i, len(s)):
            length = j - i + 1
            if length > best_len and is_palindrome(i, j):
                best_start = i
                best_len = length
    return s[best_start : best_start + best_len]
"""

py_optimal_lps = """def longestPalindrome(s: str) -> str:
    if len(s) <= 1:
        return s
    best_start = 0
    best_len = 1

    def expand(left: int, right: int) -> None:
        nonlocal best_start, best_len
        while left >= 0 and right < len(s) and s[left] == s[right]:
            left -= 1
            right += 1
        start = left + 1
        length = right - left - 1
        if length > best_len or (length == best_len and start < best_start):
            best_start = start
            best_len = length

    for i in range(len(s)):
        expand(i, i)
        expand(i, i + 1)
    return s[best_start : best_start + best_len]
"""


def _gen_lps_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        ["babad"],
        ["cbbd"],
        ["abacdfgdcaba"],
        ["a"],
        ["aa"],
        ["ab"],
        ["racecar"],
        ["bananas"],
        ["aaaa"],
        ["ccc"],
        ["noon"],
        ["ac"],
        ["adam"],
        ["forgeeksskeegfor"],
    ]
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    for _ in range(12):
        length = rng.randint(4, 30)
        # Often embed a palindrome inside random text
        sub_len = rng.randint(2, length)
        half = "".join(rng.choice(alphabet[:6]) for _ in range(sub_len // 2))
        pal = half + ("x" if sub_len % 2 != 0 else "") + half[::-1]
        pre = "".join(rng.choice(alphabet[:6]) for _ in range(rng.randint(0, length - len(pal))))
        post = "".join(rng.choice(alphabet[:6]) for _ in range(max(0, length - len(pal) - len(pre))))
        cases.append([pre + pal + post])
    # Stress cases
    cases.append(["a" * 100])
    cases.append(["ab" * 50])
    cases.append(["b" * 45 + "racecar" + "c" * 48])
    cases.append(["abcdefghij" * 10])
    return cases


# ---------------------------------------------------------------------------
# Problem 5: partition-equal-subset-sum
# ---------------------------------------------------------------------------
spec_partition_sum = ProblemSpec(
    signature="function canPartition(nums: number[])",
    statement="""# Partition Equal Subset Sum

Given an integer array `nums` containing positive integers, determine whether the array can be partitioned into two subsets such that the sum of elements in both subsets is equal.

Constraints: `1 <= nums.length <= 100` and `1 <= nums[i] <= 100`.
""",
    brute_force=Algorithm(
        """function canPartition(nums) {
  let sum = 0;
  for (let i = 0; i < nums.length; i++) sum += nums[i];
  if (sum % 2 !== 0) return false;
  const target = sum / 2;
  const n = nums.length;
  const dp = Array.from({ length: n + 1 }, () => new Array(target + 1).fill(false));
  for (let i = 0; i <= n; i++) dp[i][0] = true;
  for (let i = 1; i <= n; i++) {
    const val = nums[i - 1];
    for (let w = 1; w <= target; w++) {
      dp[i][w] = dp[i - 1][w] || (w >= val ? dp[i - 1][w - val] : false);
    }
  }
  return dp[n][target];
}""",
        complexity="Time: O(n · target) | Space: O(n · target)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function canPartition(nums) {
  let sum = 0;
  let maxVal = 0;
  for (let i = 0; i < nums.length; i++) {
    sum += nums[i];
    if (nums[i] > maxVal) maxVal = nums[i];
  }
  if (sum % 2 !== 0) return false;
  const target = sum / 2;
  if (maxVal > target) return false;
  const dp = new Array(target + 1).fill(false);
  dp[0] = true;
  for (let i = 0; i < nums.length; i++) {
    const num = nums[i];
    for (let w = target; w >= num; w--) {
      if (dp[w - num]) dp[w] = true;
    }
    if (dp[target]) return true;
  }
  return dp[target];
}""",
        complexity="Time: O(n · target) | Space: O(target)",
        language="javascript",
    ),
    topic="dynamic-programming",
    difficulty="Medium",
    pattern="dp / Subset sum",
    time_limit_ms=2000,
    seed=42,
    title="Partition Equal Subset Sum",
    slug="partition-equal-subset-sum",
)

py_brute_partition_sum = """def canPartition(nums: list[int]) -> bool:
    total = sum(nums)
    if total % 2 != 0:
        return False
    target = total // 2
    n = len(nums)
    dp = [[False] * (target + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = True
    for i in range(1, n + 1):
        val = nums[i - 1]
        for w in range(1, target + 1):
            dp[i][w] = dp[i - 1][w] or (dp[i - 1][w - val] if w >= val else False)
    return dp[n][target]
"""

py_optimal_partition_sum = """def canPartition(nums: list[int]) -> bool:
    total = sum(nums)
    if total % 2 != 0:
        return False
    target = total // 2
    if max(nums) > target:
        return False
    dp = [False] * (target + 1)
    dp[0] = True
    for num in nums:
        for w in range(target, num - 1, -1):
            if dp[w - num]:
                dp[w] = True
        if dp[target]:
            return True
    return dp[target]
"""


def _gen_partition_sum_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[1, 5, 11, 5]],
        [[1, 2, 3, 5]],
        [[1, 2, 5]],
        [[5]],
        [[2, 2]],
        [[3, 5]],
        [[1, 1]],
        [[100, 100]],
        [[1, 2, 3, 4, 5, 6, 7]],
        [[2, 2, 2, 2]],
        [[1, 2, 3, 4]],
        [[14, 9, 8, 4, 3, 2]],
    ]
    for _ in range(14):
        n = rng.randint(4, 25)
        # Create half partitionable, half random
        if rng.random() < 0.5:
            half = [rng.randint(1, 30) for _ in range(n // 2)]
            nums = half + half
            rng.shuffle(nums)
        else:
            nums = [rng.randint(1, 50) for _ in range(n)]
        cases.append([nums])
    # Stress cases
    cases.append([[1] * 100])
    cases.append([[1] * 99])
    cases.append([[2] * 50 + [4] * 25])
    cases.append([[rng.randint(1, 100) for _ in range(100)]])
    return cases


# ---------------------------------------------------------------------------
# Problem 6: jump-game
# ---------------------------------------------------------------------------
spec_jump_game = ProblemSpec(
    signature="function canJump(nums: number[])",
    statement="""# Jump Game

You are given an integer array `nums`. You are initially positioned at the array's first index, and each element in the array represents your maximum jump length at that position.

Return `true` if you can reach the last index, or `false` otherwise.

Constraints: `1 <= nums.length <= 100` and `0 <= nums[i] <= 100`.
""",
    brute_force=Algorithm(
        """function canJump(nums) {
  const n = nums.length;
  const dp = new Array(n).fill(false);
  dp[n - 1] = true;
  for (let i = n - 2; i >= 0; i--) {
    const furthest = Math.min(i + nums[i], n - 1);
    for (let j = i + 1; j <= furthest; j++) {
      if (dp[j]) {
        dp[i] = true;
        break;
      }
    }
  }
  return dp[0];
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function canJump(nums) {
  let maxReach = 0;
  for (let i = 0; i < nums.length; i++) {
    if (i > maxReach) return false;
    if (i + nums[i] > maxReach) {
      maxReach = i + nums[i];
    }
    if (maxReach >= nums.length - 1) return true;
  }
  return true;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    topic="greedy",
    difficulty="Medium",
    pattern="greedy / Max reach",
    time_limit_ms=2000,
    seed=42,
    title="Jump Game",
    slug="jump-game",
)

py_brute_jump_game = """def canJump(nums: list[int]) -> bool:
    n = len(nums)
    dp = [False] * n
    dp[-1] = True
    for i in range(n - 2, -1, -1):
        furthest = min(i + nums[i], n - 1)
        for j in range(i + 1, furthest + 1):
            if dp[j]:
                dp[i] = True
                break
    return dp[0]
"""

py_optimal_jump_game = """def canJump(nums: list[int]) -> bool:
    max_reach = 0
    for i, jump in enumerate(nums):
        if i > max_reach:
            return False
        if i + jump > max_reach:
            max_reach = i + jump
        if max_reach >= len(nums) - 1:
            return True
    return True
"""


def _gen_jump_game_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[2, 3, 1, 1, 4]],
        [[3, 2, 1, 0, 4]],
        [[0]],
        [[0, 2, 3]],
        [[2, 0, 0]],
        [[1, 1, 1, 1]],
        [[10, 0, 0, 0, 0]],
        [[2, 5, 0, 0]],
        [[1, 0, 1, 0]],
        [[1, 2, 0, 1]],
        [[5, 4, 3, 2, 1, 0, 0]],
    ]
    for _ in range(15):
        n = rng.randint(4, 30)
        nums = [rng.randint(0, 4) for _ in range(n)]
        nums[0] = rng.randint(1, 4)
        cases.append([nums])
    # Stress cases
    cases.append([[1] * 100])
    cases.append([[0] * 100])
    cases.append([[100] + [0] * 99])
    cases.append([[rng.randint(0, 5) for _ in range(100)]])
    return cases


# ---------------------------------------------------------------------------
# Problem 7: gas-station
# ---------------------------------------------------------------------------
spec_gas_station = ProblemSpec(
    signature="function canCompleteCircuit(gas: number[], cost: number[])",
    statement="""# Gas Station

There are `n` gas stations along a circular route, where the amount of gas at the `i`-th station is `gas[i]`.

You have a car with an unlimited gas tank and it costs `cost[i]` of gas to travel from the `i`-th station to its next `(i + 1)`-th station. You begin the journey with an empty tank at one of the gas stations.

Given two integer arrays `gas` and `cost`, return the starting gas station's index if you can travel around the circuit once in the clockwise direction, or `-1` if it is impossible. If there exists a solution, it is guaranteed to be unique.

Constraints: `gas.length == cost.length`, `1 <= gas.length <= 100`, and `0 <= gas[i], cost[i] <= 1000`.
""",
    brute_force=Algorithm(
        """function canCompleteCircuit(gas, cost) {
  const n = gas.length;
  for (let start = 0; start < n; start++) {
    let tank = 0;
    let possible = true;
    for (let step = 0; step < n; step++) {
      const idx = (start + step) % n;
      tank += gas[idx] - cost[idx];
      if (tank < 0) {
        possible = false;
        break;
      }
    }
    if (possible) return start;
  }
  return -1;
}""",
        complexity="Time: O(n²) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function canCompleteCircuit(gas, cost) {
  let totalSurplus = 0;
  let currentTank = 0;
  let startStation = 0;
  for (let i = 0; i < gas.length; i++) {
    const net = gas[i] - cost[i];
    totalSurplus += net;
    currentTank += net;
    if (currentTank < 0) {
      startStation = i + 1;
      currentTank = 0;
    }
  }
  return totalSurplus >= 0 ? startStation : -1;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    topic="greedy",
    difficulty="Medium",
    pattern="greedy / Surplus",
    time_limit_ms=2000,
    seed=42,
    title="Gas Station",
    slug="gas-station",
)

py_brute_gas_station = """def canCompleteCircuit(gas: list[int], cost: list[int]) -> int:
    n = len(gas)
    for start in range(n):
        tank = 0
        possible = True
        for step in range(n):
            idx = (start + step) % n
            tank += gas[idx] - cost[idx]
            if tank < 0:
                possible = False
                break
        if possible:
            return start
    return -1
"""

py_optimal_gas_station = """def canCompleteCircuit(gas: list[int], cost: list[int]) -> int:
    total_surplus = 0
    current_tank = 0
    start_station = 0
    for i in range(len(gas)):
        net = gas[i] - cost[i]
        total_surplus += net
        current_tank += net
        if current_tank < 0:
            start_station = i + 1
            current_tank = 0
    return start_station if total_surplus >= 0 else -1
"""


def _gen_gas_station_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[1, 2, 3, 4, 5], [3, 4, 5, 1, 2]],
        [[2, 3, 4], [3, 4, 3]],
        [[5, 1, 2, 3, 4], [4, 4, 1, 5, 1]],
        [[5], [4]],
        [[2], [3]],
        [[3, 1, 1], [1, 2, 2]],
        [[1, 1, 1], [1, 1, 1]],
        [[5, 8, 2, 8], [6, 5, 6, 6]],
        [[3, 3, 4], [3, 4, 4]],
    ]
    for _ in range(17):
        n = rng.randint(3, 25)
        gas = [rng.randint(1, 50) for _ in range(n)]
        cost = [rng.randint(1, 50) for _ in range(n)]
        if rng.random() < 0.5:
            # Force solvable
            diff = sum(cost) - sum(gas)
            if diff > 0:
                gas[0] += diff + 5
        cases.append([gas, cost])
    # Stress cases
    cases.append([[10] * 100, [10] * 100])
    cases.append([[5] * 100, [6] * 100])
    cases.append([[100] + [0] * 99, [1] * 100])
    cases.append([[rng.randint(1, 100) for _ in range(100)], [rng.randint(1, 100) for _ in range(100)]])
    return cases


# ---------------------------------------------------------------------------
# Problem 8: maximum-product-subarray
# ---------------------------------------------------------------------------
spec_max_product = ProblemSpec(
    signature="function maxProduct(nums: number[])",
    statement="""# Maximum Product Subarray

Given an integer array `nums`, find a contiguous non-empty subarray within the array that has the largest product, and return that product.

Constraints: `1 <= nums.length <= 100` and `-10 <= nums[i] <= 10`. The product of any prefix or suffix of `nums` is guaranteed to fit in a 32-bit integer.
""",
    brute_force=Algorithm(
        """function maxProduct(nums) {
  let maxProd = nums[0];
  for (let i = 0; i < nums.length; i++) {
    let current = 1;
    for (let j = i; j < nums.length; j++) {
      current *= nums[j];
      if (current > maxProd) {
        maxProd = current;
      }
    }
  }
  return maxProd;
}""",
        complexity="Time: O(n²) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function maxProduct(nums) {
  let globalMax = nums[0];
  let curMax = nums[0];
  let curMin = nums[0];
  for (let i = 1; i < nums.length; i++) {
    const x = nums[i];
    if (x < 0) {
      const temp = curMax;
      curMax = curMin;
      curMin = temp;
    }
    curMax = Math.max(x, curMax * x);
    curMin = Math.min(x, curMin * x);
    if (curMax > globalMax) {
      globalMax = curMax;
    }
  }
  return globalMax;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    topic="dynamic-programming",
    difficulty="Medium",
    pattern="dp / Min-max track",
    time_limit_ms=2000,
    seed=42,
    title="Maximum Product Subarray",
    slug="maximum-product-subarray",
)

py_brute_max_product = """def maxProduct(nums: list[int]) -> int:
    max_prod = nums[0]
    for i in range(len(nums)):
        current = 1
        for j in range(i, len(nums)):
            current *= nums[j]
            if current > max_prod:
                max_prod = current
    return max_prod
"""

py_optimal_max_product = """def maxProduct(nums: list[int]) -> int:
    global_max = nums[0]
    cur_max = nums[0]
    cur_min = nums[0]
    for i in range(1, len(nums)):
        x = nums[i]
        if x < 0:
            cur_max, cur_min = cur_min, cur_max
        cur_max = max(x, cur_max * x)
        cur_min = min(x, cur_min * x)
        if cur_max > global_max:
            global_max = cur_max
    return global_max
"""


def _gen_max_product_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[2, 3, -2, 4]],
        [[-2, 0, -1]],
        [[-2, 3, -4]],
        [[-2]],
        [[3]],
        [[0, 2]],
        [[0, -3, 1, 1]],
        [[-1, -2, -3, -4]],
        [[-2, -3, -1]],
        [[2, -5, -2, -4, 3]],
        [[-1, 0, -2]],
        [[0, 0, 0]],
        [[3, -1, 4]],
    ]
    for _ in range(13):
        n = rng.randint(4, 25)
        # Bounded elements so product stays within 32-bit int bounds
        arr: list[int] = []
        for _ in range(n):
            if rng.random() < 0.2:
                arr.append(0)
            elif rng.random() < 0.35:
                arr.append(rng.choice([-1, 1]))
            else:
                arr.append(rng.choice([-3, -2, 2, 3]))
        cases.append([arr])
    # Stress cases (interspersed zeros and unit multipliers to prevent 32-bit overflow)
    cases.append([[1, -1] * 50])
    cases.append([[0] * 100])
    cases.append([[2, 1, 1, 0] * 25])
    cases.append([[-1] * 100])
    return cases


# ---------------------------------------------------------------------------
# Problem 9: edit-distance
# ---------------------------------------------------------------------------
spec_edit_distance = ProblemSpec(
    signature="function minDistance(word1: string, word2: string)",
    statement="""# Edit Distance

Given two strings `word1` and `word2`, return the minimum number of operations required to convert `word1` to `word2`.

You have the following three operations permitted on a word:
- Insert a character
- Delete a character
- Replace a character

Constraints: `0 <= word1.length, word2.length <= 100` and `word1` and `word2` consist only of lowercase English letters.
""",
    brute_force=Algorithm(
        """function minDistance(word1, word2) {
  const m = word1.length;
  const n = word2.length;
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (word1[i - 1] === word2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1];
      } else {
        dp[i][j] = 1 + Math.min(
          dp[i - 1][j],
          dp[i][j - 1],
          dp[i - 1][j - 1]
        );
      }
    }
  }
  return dp[m][n];
}""",
        complexity="Time: O(m · n) | Space: O(m · n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function minDistance(word1, word2) {
  if (word1.length < word2.length) {
    const tmp = word1;
    word1 = word2;
    word2 = tmp;
  }
  const m = word1.length;
  const n = word2.length;
  const dp = new Array(n + 1);
  for (let j = 0; j <= n; j++) dp[j] = j;
  for (let i = 1; i <= m; i++) {
    let prevDiag = dp[0];
    dp[0] = i;
    for (let j = 1; j <= n; j++) {
      const temp = dp[j];
      if (word1[i - 1] === word2[j - 1]) {
        dp[j] = prevDiag;
      } else {
        dp[j] = 1 + Math.min(prevDiag, dp[j], dp[j - 1]);
      }
      prevDiag = temp;
    }
  }
  return dp[n];
}""",
        complexity="Time: O(m · n) | Space: O(min(m, n))",
        language="javascript",
    ),
    topic="dynamic-programming",
    difficulty="Hard",
    pattern="dp / 2D table",
    time_limit_ms=2000,
    seed=42,
    title="Edit Distance",
    slug="edit-distance",
)

py_brute_edit_distance = """def minDistance(word1: str, word2: str) -> int:
    m = len(word1)
    n = len(word2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i - 1] == word2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],
                    dp[i][j - 1],
                    dp[i - 1][j - 1],
                )
    return dp[m][n]
"""

py_optimal_edit_distance = """def minDistance(word1: str, word2: str) -> int:
    if len(word1) < len(word2):
        word1, word2 = word2, word1
    m, n = len(word1), len(word2)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev_diag = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            if word1[i - 1] == word2[j - 1]:
                dp[j] = prev_diag
            else:
                dp[j] = 1 + min(prev_diag, dp[j], dp[j - 1])
            prev_diag = temp
    return dp[n]
"""


def _gen_edit_distance_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        ["horse", "ros"],
        ["intention", "execution"],
        ["", "abc"],
        ["abc", ""],
        ["", ""],
        ["a", "a"],
        ["a", "b"],
        ["cat", "hat"],
        ["cat", "cats"],
        ["cats", "cat"],
        ["zoologico", "zoology"],
        ["dinitrophenylhydrazine", "phenylhydrazine"],
        ["distance", "editing"],
    ]
    chars = "abcdefghijklmnopqrstuvwxyz"
    for _ in range(13):
        len1 = rng.randint(3, 25)
        len2 = rng.randint(3, 25)
        w1 = "".join(rng.choice(chars[:8]) for _ in range(len1))
        # Often make w2 a mutated version of w1
        w2_list = list(w1)
        for _ in range(rng.randint(1, 4)):
            if w2_list and rng.random() < 0.5:
                w2_list[rng.randint(0, len(w2_list) - 1)] = rng.choice(chars[:8])
            elif rng.random() < 0.5:
                w2_list.append(rng.choice(chars[:8]))
            elif len(w2_list) > 1:
                w2_list.pop(rng.randint(0, len(w2_list) - 1))
        cases.append([w1, "".join(w2_list)])
    # Stress cases
    cases.append(["a" * 100, "b" * 100])
    cases.append(["a" * 100, "a" * 100])
    cases.append(["abcdefghij" * 10, "jihgfedcba" * 10])
    cases.append(["algo" * 25, "vista" * 20])
    return cases


# ---------------------------------------------------------------------------
# BUNDLES DEFINITION
# ---------------------------------------------------------------------------
BUNDLES: list[ProblemBundle] = [
    # 1. House Robber II
    ProblemBundle(
        spec=spec_rob2,
        py_brute_code=py_brute_rob2,
        py_brute_complexity="Time: O(n) | Space: O(n)",
        py_optimal_code=py_optimal_rob2,
        py_optimal_complexity="Time: O(n) | Space: O(1)",
        input_generator=_gen_rob2_inputs,
        examples=[
            {
                "input": "nums = [2, 3, 2]",
                "output": "3",
                "explanation": "You cannot rob house 1 (money = 2) and house 3 (money = 2) because they are adjacent in the circular street. Robbing house 2 yields 3.",
            },
            {
                "input": "nums = [1, 2, 3, 1]",
                "output": "4",
                "explanation": "Rob house 1 (money = 1) and house 3 (money = 3). Total amount robbed is 1 + 3 = 4. Note that house 1 and house 4 cannot both be robbed.",
            },
            {
                "input": "nums = [1, 2, 1, 1]",
                "output": "3",
                "explanation": "Rob house 2 (money = 2) and house 4 (money = 1). Total amount robbed is 2 + 1 = 3.",
            },
        ],
        approach="""### Dynamic Programming with Circular Decomposition

In a linear street of houses, house 0 and house n - 1 are not adjacent. In a circular street, however, robbing house 0 strictly prohibits robbing house n - 1. This circular dependency can be resolved by decomposing the problem into two independent linear subproblems:
1. **Exclude the last house**: Rob houses from index 0 to n - 2.
2. **Exclude the first house**: Rob houses from index 1 to n - 1.

The maximum amount achievable is the greater of these two linear runs: max(robLinear(0, n - 2), robLinear(1, n - 1)).

#### 1. DP State Definition
For a linear subarray A, define dp[i] as the maximum amount of money that can be robbed from the prefix A[0...i].

#### 2. Recurrence Relation & State Transition
At each house i, we make a binary choice:
- **Skip house i**: The accumulated money remains dp[i - 1].
- **Rob house i**: We cannot rob house i - 1, so the accumulated money is dp[i - 2] + A[i].

dp[i] = max(dp[i - 1], dp[i - 2] + A[i])

Since computing dp[i] only depends on the two preceding states (dp[i - 1] and dp[i - 2]), we can maintain two rolling scalar variables prev1 and prev2, reducing auxiliary space from O(n) to O(1).

#### 3. Base Cases
- When n = 1: Only one house exists, so return nums[0].
- When n = 2: Return max(nums[0], nums[1]).
- For linear DP starting at an empty prefix: prev2 = 0, prev1 = 0.

#### 4. Answer Extraction
ans = max(robLinear(nums[0...n - 2]), robLinear(nums[1...n - 1]))""",
        why_optimal_template="Allocating separate DP tables for each slice requires O(n) space, whereas tracking two rolling variables (prev1 and prev2) reduces space complexity to O(1) while maintaining O(n) linear time. On {case_count} verified test cases, the space-optimized solution finished in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for tabular dynamic programming.",
        pitfalls="A common mistake is neglecting the single-house edge case: when nums has only 1 element, slicing [0, n - 2] produces an empty array and evaluates to 0 instead of nums[0]. Always handle n = 1 as an explicit guard condition.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Dynamic_programming",
            "https://algo.monster/problems/house_robber_ii",
        ],
        hints=[
            "Because the houses form a circle, the first and last houses are adjacent; you cannot rob both.",
            "Divide the problem into two linear subproblems: robbing houses 0 to n - 2, and robbing houses 1 to n - 1.",
            "Solve each linear subproblem in O(n) time and O(1) space using two rolling variables, then take the maximum of the two results.",
        ],
    ),
    # 2. Decode Ways
    ProblemBundle(
        spec=spec_decode_ways,
        py_brute_code=py_brute_decode_ways,
        py_brute_complexity="Time: O(n) | Space: O(n)",
        py_optimal_code=py_optimal_decode_ways,
        py_optimal_complexity="Time: O(n) | Space: O(1)",
        input_generator=_gen_decode_ways_inputs,
        examples=[
            {
                "input": "s = '226'",
                "output": "3",
                "explanation": "It could be decoded as 'BZ' (2, 26), 'VF' (22, 6), or 'BBF' (2, 2, 6).",
            },
            {
                "input": "s = '10'",
                "output": "1",
                "explanation": "It can only be decoded as 'J' (10). Digits '0' cannot be parsed independently.",
            },
            {
                "input": "s = '06'",
                "output": "0",
                "explanation": "'06' cannot be mapped to 'F' because of the leading zero. There are 0 valid decodings.",
            },
        ],
        approach="""### Dynamic Programming: Counting Valid Decodings

A digit sequence can be decoded by reading characters either one digit at a time (if 1 <= d <= 9) or two digits at a time (if 10 <= dd <= 26). Any digit '0' cannot form a letter on its own and is valid only when preceded by '1' or '2'.

#### 1. DP State Definition
Let dp[i] be the number of valid ways to decode the prefix s[0...i - 1] of length i.

#### 2. Recurrence Relation & State Transition
For position i from 2 to n:
- **Single-digit transition**: Look at character s[i - 1]. If s[i - 1] is between '1' and '9', it forms a valid letter, contributing dp[i - 1] decodings:
  dp[i] += dp[i - 1]
- **Two-digit transition**: Look at the two-character substring s[i - 2...i - 1]. If its numeric value lies in [10, 26], it forms a valid letter, contributing dp[i - 2] decodings:
  dp[i] += dp[i - 2]

dp[i] = (dp[i - 1] if s[i - 1] != '0') + (dp[i - 2] if 10 <= int(s[i - 2...i - 1]) <= 26)

Because dp[i] only depends on dp[i - 1] and dp[i - 2], the full table can be compressed into two scalar variables prev1 and prev2, achieving O(1) auxiliary space.

#### 3. Base Cases
- dp[0] = 1: An empty string has 1 valid decoding (the empty decoding).
- If s[0] == '0', the string starts with a leading zero and cannot be decoded, immediately yielding 0. Otherwise, dp[1] = 1.

#### 4. Answer Extraction
ans = dp[n] (stored in prev1).""",
        why_optimal_template="A full DP table requires O(n) auxiliary memory, whereas rolling two state variables (prev1 and prev2) requires only O(1) space while traversing the string in a single O(n) linear pass. Across {case_count} verified test cases, the space-optimized solution finished in {optimal_ms:.2f} ms versus {brute_ms:.2f} ms for the full array allocation.",
        pitfalls="Handling '0' requires strict care: a single '0' cannot be decoded on its own, and invalid pairs like '30', '70', or consecutive zeros like '100' must immediately collapse subsequent counts to 0.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Dynamic_programming",
            "https://algo.monster/problems/decode_ways",
        ],
        hints=[
            "If the string starts with '0', it cannot be decoded at all; return 0 immediately.",
            "At each character s[i], you can decode s[i] as a single digit (if 1-9) or s[i-1..i] as a two-digit number (if 10-26).",
            "This recurrence matches Fibonacci numbers with condition checks, allowing O(1) space with two rolling variables.",
        ],
    ),
    # 3. Word Break
    ProblemBundle(
        spec=spec_word_break,
        py_brute_code=py_brute_word_break,
        py_brute_complexity="Time: O(n² · m) | Space: O(n)",
        py_optimal_code=py_optimal_word_break,
        py_optimal_complexity="Time: O(n · L) | Space: O(n + W)",
        input_generator=_gen_word_break_inputs,
        examples=[
            {
                "input": "s = 'applepenapple', wordDict = ['apple', 'pen']",
                "output": "true",
                "explanation": "'applepenapple' can be segmented as 'apple pen apple'. Dictionary words can be reused.",
            },
            {
                "input": "s = 'catsandog', wordDict = ['cats', 'dog', 'sand', 'and', 'cat']",
                "output": "false",
                "explanation": "The string cannot be segmented into dictionary words because the remaining 'og' is not in wordDict.",
            },
            {
                "input": "s = 'goalspecial', wordDict = ['go', 'goal', 'goals', 'special']",
                "output": "true",
                "explanation": "'goalspecial' can be segmented into 'goal' + 'special'.",
            },
        ],
        approach="""### Dynamic Programming: Prefix Reachability

To decide if a string s of length n can be partitioned into valid dictionary words, we determine reachability for each prefix of s from left to right.

#### 1. DP State Definition
Let dp[i] be a boolean value indicating whether the prefix s[0...i - 1] of length i can be completely segmented into words from wordDict.

#### 2. Recurrence Relation & State Transition
For each length i from 1 to n, dp[i] is true if there exists some split point j (0 <= j < i) such that:
1. Prefix s[0...j - 1] is segmentable: dp[j] == true.
2. Suffix substring s[j...i - 1] is a dictionary word: s[j...i - 1] in wordDict.

dp[i] = OR_{j = max(0, i - L)}^{i - 1} (dp[j] and (s[j...i - 1] in wordDictSet))

where L = max_{w in wordDict} length(w) is the maximum length of any word in the dictionary. Limiting j to [i - L, i - 1] bounds the inner loop to at most L steps instead of i steps.

#### 3. Base Cases
- dp[0] = true: An empty prefix requires zero words and is valid by definition.
- All dp[i] = false for i > 0 initially.

#### 4. Answer Extraction
ans = dp[n].""",
        why_optimal_template="Converting wordDict into a hash set enables O(1) word lookups, and bounding the inner loop search by the maximum word length L reduces the time complexity from O(n² · m) to O(n · L). On {case_count} verified test cases, the optimized set-based DP completed in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for linear dictionary scans.",
        pitfalls="Scanning all 0 <= j < i with array.includes takes O(n² · m) time and can time out on long strings. Bounding j >= i - L and using a hash set avoids redundant comparisons.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Dynamic_programming",
            "https://algo.monster/problems/word_break",
        ],
        hints=[
            "Define a boolean array dp of length n + 1, where dp[i] indicates whether prefix s[0..i-1] can be segmented.",
            "Convert wordDict to a hash set for O(1) average lookup time.",
            "Notice that substrings longer than the longest dictionary word cannot match, so bound the inner search window.",
        ],
    ),
    # 4. Longest Palindromic Substring
    ProblemBundle(
        spec=spec_lps,
        py_brute_code=py_brute_lps,
        py_brute_complexity="Time: O(n³) | Space: O(1)",
        py_optimal_code=py_optimal_lps,
        py_optimal_complexity="Time: O(n²) | Space: O(1)",
        input_generator=_gen_lps_inputs,
        examples=[
            {
                "input": "s = 'babad'",
                "output": "'bab'",
                "explanation": "Both 'bab' and 'aba' are palindromic substrings of length 3. Because 'bab' begins at index 0 and 'aba' begins at index 1, the tie is broken by the earliest start index, yielding 'bab'.",
            },
            {
                "input": "s = 'cbbd'",
                "output": "'bb'",
                "explanation": "The longest palindromic substring is 'bb' with length 2 starting at index 1.",
            },
            {
                "input": "s = 'abacdfgdcaba'",
                "output": "'aba'",
                "explanation": "Both the prefix 'aba' (index 0) and suffix 'aba' (index 9) have length 3. The earliest occurrence at index 0 is returned.",
            },
        ],
        approach="""### Dynamic Programming & Center Expansion

A palindrome mirrors around its center. A string of length n has 2n - 1 possible centers: n single-character centers (odd-length palindromes) and n - 1 between-character centers (even-length palindromes).

#### 1. DP State Definition
In 2D tabular DP, let dp[i][j] be a boolean indicating whether substring s[i...j] is a palindrome.

#### 2. Recurrence Relation & State Transition
A substring s[i...j] is a palindrome if and only if its endpoint characters match and the inner substring is also a palindrome:
dp[i][j] = (s[i] == s[j]) and (j - i < 2 or dp[i + 1][j - 1])

Rather than storing an O(n²) table, we can expand outwards from each center (c1, c2) while s[left] == s[right].

#### 3. Deterministic Tie-Breaking Invariant
When comparing candidate palindromes with start index i and length L:
update if L > bestLen or (L == bestLen and i < bestStart)
This guarantees that if two different substrings attain the maximum length, the one appearing earliest in the string is chosen deterministically in both implementations.

#### 4. Base Cases
- Single characters are palindromes of length 1: dp[i][i] = true.
- Adjacent pairs are palindromes of length 2 if s[i] == s[i + 1].

#### 5. Answer Extraction
ans = s.slice(bestStart, bestStart + bestLen).""",
        why_optimal_template="Brute force checks all O(n²) substrings with an O(n) palindrome test, taking O(n³) time. Center expansion evaluates all 2n - 1 centers in O(n²) time and O(1) auxiliary space without matrix allocations. Across {case_count} verified test cases, center expansion executed in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for cubic brute force.",
        pitfalls="Remember to test both odd centers (i, i) and even centers (i, i + 1). When breaking ties, using strictly greater length (> bestLen) naturally keeps earlier occurrences for the same center orientation, but when comparing across odd and even centers, an explicit start index check (len === bestLen && start < bestStart) prevents incorrect overrides.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Longest_palindromic_substring",
            "https://algo.monster/problems/longest_palindromic_substring",
        ],
        hints=[
            "A palindrome reads the same forwards and backwards and is symmetric around its center.",
            "There are 2n - 1 possible centers: n single characters and n - 1 adjacent character pairs.",
            "Whenever a candidate matches the current best length, preserve the one with the smaller starting index.",
        ],
    ),
    # 5. Partition Equal Subset Sum
    ProblemBundle(
        spec=spec_partition_sum,
        py_brute_code=py_brute_partition_sum,
        py_brute_complexity="Time: O(n · target) | Space: O(n · target)",
        py_optimal_code=py_optimal_partition_sum,
        py_optimal_complexity="Time: O(n · target) | Space: O(target)",
        input_generator=_gen_partition_sum_inputs,
        examples=[
            {
                "input": "nums = [1, 5, 11, 5]",
                "output": "true",
                "explanation": "The total sum is 22. The array can be partitioned into [1, 5, 5] and [11], each with sum 11.",
            },
            {
                "input": "nums = [1, 2, 3, 5]",
                "output": "false",
                "explanation": "The total sum is 11, which is odd. It cannot be partitioned into two equal integer subsets.",
            },
            {
                "input": "nums = [1, 2, 5]",
                "output": "false",
                "explanation": "The total sum is 8 (target 4), but no subset sums to 4.",
            },
        ],
        approach="""### Dynamic Programming: 0/1 Knapsack Reduction

The problem asks if a subset of nums has a sum equal to exactly half of the total sum: target = sum(nums) / 2.

#### 1. DP State Definition
Let dp[w] be a boolean indicating whether a subset sum of exactly w can be formed using a subset of the numbers processed so far, for 0 <= w <= target.

#### 2. Recurrence Relation & State Transition
For each number x in nums, iterate the weight w backwards from target down to x:
dp[w] = dp[w] or dp[w - x]

Iterating backwards guarantees that each element x is used at most once (0/1 knapsack property), avoiding unbounded reuse.

#### 3. Base Cases
- If sum(nums) is odd, return false immediately.
- If max(nums) > target, return false immediately.
- dp[0] = true: A subset sum of 0 is always achievable (the empty subset).
- dp[w] = false for all w > 0.

#### 4. Answer Extraction
ans = dp[target].""",
        why_optimal_template="A full 2D DP matrix requires O(n · target) memory, whereas rolling a 1D boolean array backwards reduces auxiliary memory to O(target) while retaining O(n · target) pseudo-polynomial time. On {case_count} verified test cases, the 1D rolling DP finished in {optimal_ms:.2f} ms versus {brute_ms:.2f} ms for the 2D table allocation.",
        pitfalls="Looping forwards over weights in the 1D array would allow an element to be added multiple times, turning it into an unbounded knapsack. Always loop backwards from target down to num.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Partition_problem",
            "https://en.wikipedia.org/wiki/Knapsack_problem",
        ],
        hints=[
            "If the total sum of all elements is odd, it is impossible to partition into two equal integers; return false.",
            "The problem reduces to finding a subset that sums to sum(nums) / 2 (0/1 Knapsack).",
            "Use a 1D boolean array updated from target down to num to ensure each number is used at most once.",
        ],
    ),
    # 6. Jump Game
    ProblemBundle(
        spec=spec_jump_game,
        py_brute_code=py_brute_jump_game,
        py_brute_complexity="Time: O(n²) | Space: O(n)",
        py_optimal_code=py_optimal_jump_game,
        py_optimal_complexity="Time: O(n) | Space: O(1)",
        input_generator=_gen_jump_game_inputs,
        examples=[
            {
                "input": "nums = [2, 3, 1, 1, 4]",
                "output": "true",
                "explanation": "Jump 1 step from index 0 to 1, then 3 steps to the last index.",
            },
            {
                "input": "nums = [3, 2, 1, 0, 4]",
                "output": "false",
                "explanation": "You will always arrive at index 3 no matter what. Its maximum jump length is 0, which makes it impossible to reach the last index.",
            },
            {
                "input": "nums = [0]",
                "output": "true",
                "explanation": "You are already at the last index (index 0).",
            },
        ],
        approach="""### Greedy Furthest-Reach & Dynamic Programming Equivalence

This problem can be modeled as dynamic programming reachability, which simplifies to a greedy single-pass scan.

#### 1. DP State & Recurrence Formulation
Let dp[i] be a boolean indicating whether the target index n - 1 can be reached starting from index i:
dp[i] = OR_{j = i + 1}^{min(i + nums[i], n - 1)} dp[j]
with base case dp[n - 1] = true. A backward DP computes this in O(n²) time.

#### 2. Greedy Invariant & Transition
Instead of quadratic search, observe the prefix reachability invariant: all indices in [0, maxReach] are reachable. At index i:
1. If i > maxReach, we cannot reach index i, so return false.
2. Otherwise, update the furthest reachable boundary:
   maxReach = max(maxReach, i + nums[i])
3. If maxReach >= n - 1, the destination is reachable; return true immediately.

#### 3. Base Cases
- maxReach = 0: Initially, only index 0 is reached.
- If n = 1, return true immediately.

#### 4. Answer Extraction
ans = (maxReach >= n - 1).""",
        why_optimal_template="Backward dynamic programming examines every possible jump from each index in O(n²) time, whereas tracking the single greedy maxReach boundary solves the problem in a single O(n) pass with O(1) memory. On {case_count} verified test cases, the greedy approach executed in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for the quadratic DP.",
        pitfalls="Do not assume a 0 is always an impassable blocker: as long as a preceding index had a jump length capable of vaulting over the 0, maxReach will exceed the 0's index and continue progressing.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Greedy_algorithm",
            "https://algo.monster/problems/jump_game",
        ],
        hints=[
            "Think of the problem in terms of the maximum index you can currently reach.",
            "Iterate through the array: if the current index is greater than your maximum reach, you are stuck.",
            "Update your maximum reach as max(maxReach, i + nums[i]) and return true as soon as it reaches or exceeds the last index.",
        ],
    ),
    # 7. Gas Station
    ProblemBundle(
        spec=spec_gas_station,
        py_brute_code=py_brute_gas_station,
        py_brute_complexity="Time: O(n²) | Space: O(1)",
        py_optimal_code=py_optimal_gas_station,
        py_optimal_complexity="Time: O(n) | Space: O(1)",
        input_generator=_gen_gas_station_inputs,
        examples=[
            {
                "input": "gas = [1, 2, 3, 4, 5], cost = [3, 4, 5, 1, 2]",
                "output": "3",
                "explanation": "Start at station 3 (index 3). Fill with 4 gas. Tank = 4. Cost to next is 1. Tank = 3. Fill 5, cost 2. Tank = 6. Wrap around to station 0, fill 1, cost 3. Tank = 4. Continue through stations 1 and 2, completing the circuit with 0 gas remaining.",
            },
            {
                "input": "gas = [2, 3, 4], cost = [3, 4, 3]",
                "output": "-1",
                "explanation": "Total gas = 9, total cost = 10. Because total gas < total cost, it is impossible to complete the circuit regardless of where you start.",
            },
            {
                "input": "gas = [5, 1, 2, 3, 4], cost = [4, 4, 1, 5, 1]",
                "output": "4",
                "explanation": "Station 4 has gas 4 and cost 1 (surplus +3). Starting at station 4 enables completing the circuit.",
            },
        ],
        approach="""### Greedy Prefix Surplus Analysis

The net fuel gain or loss at station i is delta_i = gas[i] - cost[i].

#### 1. Solvability Condition (Global Invariant)
If the total net fuel over the entire circular route is negative (sum_{i=0}^{n-1} delta_i < 0), no starting station can ever complete the circuit because the journey demands more fuel than is available. Conversely, if total surplus >= 0, a valid starting station is guaranteed to exist.

#### 2. Greedy Reset Property (State Transition)
Suppose we start at station S and run out of gas at station K (where sum_{i=S}^K delta_i < 0). Could any intermediate station S <= j <= K serve as a valid start?
- Because the car successfully reached station j from S, the accumulated fuel arriving at j was non-negative: sum_{i=S}^{j-1} delta_i >= 0.
- Starting fresh at j with 0 fuel would have even less fuel than arriving at j from S.
- Therefore, no station between S and K can complete the circuit.

Thus, when the running tank dips below 0 at station i, we greedily discard all candidates up to i and reset:
start = i + 1, currentTank = 0

#### 3. Base Cases
totalSurplus = 0, currentTank = 0, start = 0.

#### 4. Answer Extraction
ans = start if totalSurplus >= 0 else -1.""",
        why_optimal_template="Brute force simulates a full circular trip from every station in O(n²) time. By leveraging the greedy reset property, the candidate starting station is identified in a single O(n) pass with O(1) extra space. Across {case_count} verified test cases, the greedy approach executed in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for quadratic simulation.",
        pitfalls="Do not run a second loop to verify the start station if totalSurplus >= 0: the mathematical property ensures that whenever total gas >= total cost, the uniquely surviving start candidate from the first pass is guaranteed to succeed.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Greedy_algorithm",
            "https://algo.monster/problems/gas_station",
        ],
        hints=[
            "If the total gas is less than the total cost, completing the circuit is impossible; return -1.",
            "If you run out of gas between station A and station B, no station between A and B can be a valid start.",
            "Reset your candidate starting station to B + 1 whenever your current tank drops below 0.",
        ],
    ),
    # 8. Maximum Product Subarray
    ProblemBundle(
        spec=spec_max_product,
        py_brute_code=py_brute_max_product,
        py_brute_complexity="Time: O(n²) | Space: O(1)",
        py_optimal_code=py_optimal_max_product,
        py_optimal_complexity="Time: O(n) | Space: O(1)",
        input_generator=_gen_max_product_inputs,
        examples=[
            {
                "input": "nums = [2, 3, -2, 4]",
                "output": "6",
                "explanation": "[2, 3] has the largest product 6.",
            },
            {
                "input": "nums = [-2, 0, -1]",
                "output": "0",
                "explanation": "The result cannot be 2, because [-2, -1] is not a contiguous subarray. The maximum product subarray is [0] with product 0.",
            },
            {
                "input": "nums = [-2, 3, -4]",
                "output": "24",
                "explanation": "The entire subarray [-2, 3, -4] has product (-2) * 3 * (-4) = 24.",
            },
        ],
        approach="""### Dynamic Programming: Dual Extremum Tracking (Kadane Extension)

Unlike maximum sum subarray where adding negative numbers strictly decreases the sum, multiplying two negative numbers creates a positive product. Therefore, a very small negative product can become a large positive product when multiplied by another negative number.

#### 1. DP State Definition
For prefix ending at index i:
- maxProd[i]: Maximum product of a non-empty contiguous subarray ending at index i.
- minProd[i]: Minimum product of a non-empty contiguous subarray ending at index i.

#### 2. Recurrence Relation & State Transition
At index i, the new subarray ending at i can either start at nums[i] alone, or extend the previous maximum or minimum:
candidates = {nums[i], maxProd[i - 1] * nums[i], minProd[i - 1] * nums[i]}
maxProd[i] = max(candidates)
minProd[i] = min(candidates)

When nums[i] < 0, multiplying by a negative number inverts order, so swapping curMax and curMin before multiplying cleanly handles the sign flip.

Since only the previous index's values are needed, we maintain two scalar variables curMax and curMin, reducing space to O(1).

#### 3. Base Cases
curMax = nums[0], curMin = nums[0], globalMax = nums[0].

#### 4. Answer Extraction
ans = max_{0 <= i < n} maxProd[i] (tracked in globalMax).""",
        why_optimal_template="Brute force checks all O(n²) contiguous subarrays and computes their products, taking O(n²) time. Tracking running minimum and maximum products in a single pass achieves O(n) linear time with O(1) auxiliary space. Across {case_count} verified test cases, the linear DP finished in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for the quadratic search.",
        pitfalls="Do not discard minimum products: when a negative number appears, the current minimum (most negative) product multiplied by that number yields a large positive candidate. Also, be sure to update curMax and curMin simultaneously or swap them when num < 0 so the new curMax does not overwrite the value needed to compute curMin.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Maximum_subarray_problem",
            "https://algo.monster/problems/maximum_product_subarray",
        ],
        hints=[
            "Multiplying a negative number by another negative number produces a positive number.",
            "Track both the maximum product and the minimum product ending at the current position.",
            "When the current number is negative, the minimum product can become the new maximum product.",
        ],
    ),
    # 9. Edit Distance
    ProblemBundle(
        spec=spec_edit_distance,
        py_brute_code=py_brute_edit_distance,
        py_brute_complexity="Time: O(m · n) | Space: O(m · n)",
        py_optimal_code=py_optimal_edit_distance,
        py_optimal_complexity="Time: O(m · n) | Space: O(min(m, n))",
        input_generator=_gen_edit_distance_inputs,
        examples=[
            {
                "input": "word1 = 'horse', word2 = 'ros'",
                "output": "3",
                "explanation": "horse -> rorse (replace 'h' with 'r') -> rose (remove 'r') -> ros (remove 'e').",
            },
            {
                "input": "word1 = 'intention', word2 = 'execution'",
                "output": "5",
                "explanation": "intention -> inention (remove 't') -> enention (replace 'i' with 'e') -> exention (replace 'n' with 'x') -> exection (replace 'n' with 'c') -> execution (insert 'u').",
            },
            {
                "input": "word1 = '', word2 = 'abc'",
                "output": "3",
                "explanation": "Three insertions are needed to turn the empty string into 'abc'.",
            },
        ],
        approach="""### Dynamic Programming: Wagner-Fischer 2D Grid

The minimum edit distance between prefixes of word1 (length m) and word2 (length n) exhibits optimal substructure.

#### 1. DP State Definition
Let dp[i][j] denote the minimum number of operations required to convert the prefix word1[0...i - 1] of length i into the prefix word2[0...j - 1] of length j.

#### 2. Recurrence Relation & State Transition
Consider matching character word1[i - 1] with word2[j - 1]:
- **Match (word1[i - 1] == word2[j - 1])**: No operation needed:
  dp[i][j] = dp[i - 1][j - 1]
- **Mismatch (word1[i - 1] != word2[j - 1])**: Take the best of three operations:
  1. **Deletion from word1**: dp[i - 1][j] + 1
  2. **Insertion into word1**: dp[i][j - 1] + 1
  3. **Substitution**: dp[i - 1][j - 1] + 1

dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

Because computing row i only requires row i - 1 and the current row, the 2D matrix can be compressed into a 1D array of size min(m, n) + 1, maintaining the diagonal element dp[i - 1][j - 1] in a temporary variable.

#### 3. Base Cases
- dp[i][0] = i: Transforming a prefix of length i to an empty string requires i deletions.
- dp[0][j] = j: Transforming an empty string to a prefix of length j requires j insertions.

#### 4. Answer Extraction
ans = dp[m][n].""",
        why_optimal_template="A naive 2D dynamic programming grid allocates an O(m · n) matrix. Rolling a single 1D row reduces memory usage to O(min(m, n)) while preserving the same O(m · n) time complexity. Across {case_count} verified test cases, the 1D space-optimized solution executed in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for the full 2D table allocation.",
        pitfalls="Be sure to account for empty strings on either input: when word1 is empty, length(word2) insertions are needed; when word2 is empty, length(word1) deletions are needed. In the 1D space optimization, save the top-left diagonal element in a variable before overwriting dp[j].",
        reading_links=[
            "https://en.wikipedia.org/wiki/Levenshtein_distance",
            "https://en.wikipedia.org/wiki/Wagner%E2%80%93Fischer_algorithm",
        ],
        hints=[
            "Define dp[i][j] as the edit distance between word1[0..i-1] and word2[0..j-1].",
            "If the characters match, dp[i][j] = dp[i-1][j-1]. If they differ, take 1 + min of deletion, insertion, and replacement.",
            "You can optimize space to O(min(m, n)) by using a single 1D array and saving the previous diagonal value.",
        ],
    ),
]


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

    # Mark first 2 or 3 as samples
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

    # Validate against schema and gate checks before saving
    ProblemSchema(**data)
    gate_errors = check_paf_gates(data, f"{spec.slug}.json")
    if gate_errors:
        raise ValueError(f"Gate errors in {spec.slug}: {gate_errors}")

    return data


async def main() -> None:
    output_dir = REPO_ROOT / "content" / "problems"
    print(f"Authoring and verifying {len(BUNDLES)} Batch-3B problems with PAF...")
    for idx, bundle in enumerate(BUNDLES, 1):
        slug = bundle.spec.slug
        print(f"[{idx}/{len(BUNDLES)}] Generating {slug} ({bundle.spec.difficulty})...")
        data = await build_and_verify_bundle(bundle)
        out_file = output_dir / f"{slug}.json"
        out_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        paf = data["pafVerification"]
        print(
            f"  ✓ {slug}: {paf['generatedCaseCount']} cases verified 100% AC | "
            f"JS Brute: {paf['bruteForceRuntimeMs']:.2f}ms | "
            f"JS Optimal: {paf['optimalRuntimeMs']:.2f}ms | 4 solutions verified -> {out_file.name}"
        )
    print("\nAll 9 Batch-3B problems generated and PAF-verified successfully.")


if __name__ == "__main__":
    asyncio.run(main())
