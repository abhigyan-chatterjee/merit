"""Authoring and verification script for Batch 1B: Two Pointers and Sliding Window problems."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
api_path = str(REPO_ROOT / "apps" / "api")
if api_path not in sys.path:
    sys.path.insert(0, api_path)

from content.generators.paf import Algorithm, ProblemSpec, build_problem

spec_backspace = ProblemSpec(
    signature="function backspaceCompare(s: string, t: string)",
    statement="""# Backspace String Compare

Given two strings `s` and `t`, return `true` if they are equal when both are typed into empty text editors where `'#'` represents a backspace character, or `false` otherwise.

When a backspace is typed, it removes the preceding non-backspace character if one is present. Backspacing over an empty text buffer leaves the buffer empty.

Constraints: `1 <= s.length <= 100` and `1 <= t.length <= 100`. Strings may contain alphanumeric characters and `'#'`.
""",
    brute_force=Algorithm(
        """function backspaceCompare(s, t) {
  function process(str) {
    const buffer = [];
    for (let i = 0; i < str.length; i++) {
      if (str[i] === '#') {
        if (buffer.length > 0) {
          buffer.pop();
        }
      } else {
        buffer.push(str[i]);
      }
    }
    return buffer.join('');
  }
  return process(s) === process(t);
}""",
        complexity="Time: O(n + m) | Space: O(n + m)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function backspaceCompare(s, t) {
  let p1 = s.length - 1;
  let p2 = t.length - 1;
  let skips1 = 0;
  let skips2 = 0;

  while (p1 >= 0 || p2 >= 0) {
    while (p1 >= 0) {
      if (s[p1] === '#') {
        skips1++;
        p1--;
      } else if (skips1 > 0) {
        skips1--;
        p1--;
      } else {
        break;
      }
    }

    while (p2 >= 0) {
      if (t[p2] === '#') {
        skips2++;
        p2--;
      } else if (skips2 > 0) {
        skips2--;
        p2--;
      } else {
        break;
      }
    }

    const c1 = p1 >= 0 ? s[p1] : null;
    const c2 = p2 >= 0 ? t[p2] : null;

    if (c1 !== c2) {
      return false;
    }

    p1--;
    p2--;
  }

  return true;
}""",
        complexity="Time: O(n + m) | Space: O(1)",
        language="javascript",
    ),
    topic="two-pointers",
    difficulty="Easy",
    pattern="two-pointers / Reverse scan",
    time_limit_ms=2000,
    seed=42,
    title="Backspace String Compare",
    slug="backspace-string-compare",
)

spec_valid_palindrome_ii = ProblemSpec(
    signature="function validPalindromeII(s: string)",
    statement="""# Valid Palindrome II

Given a string `s`, return `true` if `s` can be made a palindrome after deleting at most one character from it, or `false` otherwise.

A sequence is a palindrome when it reads identically forwards and backwards.

Constraints: `1 <= s.length <= 100`.
""",
    brute_force=Algorithm(
        """function validPalindromeII(s) {
  function isPalindrome(str, left, right) {
    while (left < right) {
      if (str[left] !== str[right]) {
        return false;
      }
      left++;
      right--;
    }
    return true;
  }

  if (isPalindrome(s, 0, s.length - 1)) {
    return true;
  }

  for (let i = 0; i < s.length; i++) {
    const candidate = s.slice(0, i) + s.slice(i + 1);
    if (isPalindrome(candidate, 0, candidate.length - 1)) {
      return true;
    }
  }

  return false;
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function validPalindromeII(s) {
  function checkRange(str, left, right) {
    while (left < right) {
      if (str[left] !== str[right]) {
        return false;
      }
      left++;
      right--;
    }
    return true;
  }

  let left = 0;
  let right = s.length - 1;

  while (left < right) {
    if (s[left] !== s[right]) {
      return (
        checkRange(s, left + 1, right) ||
        checkRange(s, left, right - 1)
      );
    }
    left++;
    right--;
  }

  return true;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    topic="two-pointers",
    difficulty="Easy",
    pattern="two-pointers / One deletion",
    time_limit_ms=2000,
    seed=42,
    title="Valid Palindrome II",
    slug="valid-palindrome-ii",
)

spec_squares = ProblemSpec(
    signature="function sortedSquares(nums: number[])",
    statement="""# Squares of a Sorted Array

Given an integer array `nums` arranged in non-decreasing numerical order, return a new array containing the squares of each number, also sorted in non-decreasing order.

Constraints: `1 <= nums.length <= 100` and `-1000 <= nums[i] <= 1000`.
""",
    brute_force=Algorithm(
        """function sortedSquares(nums) {
  const sorted = [...nums].sort((a, b) => a - b);
  const squared = [];
  for (let i = 0; i < sorted.length; i++) {
    squared.push(sorted[i] * sorted[i]);
  }
  squared.sort((a, b) => a - b);
  return squared;
}""",
        complexity="Time: O(n log n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function sortedSquares(nums) {
  const sorted = [...nums].sort((a, b) => a - b);
  const n = sorted.length;
  const result = new Array(n);
  let left = 0;
  let right = n - 1;
  let writeIdx = n - 1;

  while (left <= right) {
    const leftSq = sorted[left] * sorted[left];
    const rightSq = sorted[right] * sorted[right];

    if (leftSq > rightSq) {
      result[writeIdx] = leftSq;
      left++;
    } else {
      result[writeIdx] = rightSq;
      right--;
    }
    writeIdx--;
  }

  return result;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="two-pointers",
    difficulty="Easy",
    pattern="two-pointers / Converge ends",
    time_limit_ms=2000,
    seed=42,
    title="Squares of a Sorted Array",
    slug="squares-of-sorted-array",
)

spec_boats = ProblemSpec(
    signature="function numRescueBoats(people: number[], limit: number)",
    statement="""# Boats to Save People

You are provided an array of integers `people` where `people[i]` denotes the weight of the `i`-th person, alongside an integer `limit` representing the maximum capacity of each rescue boat.

Each boat can carry at most two people simultaneously, provided the sum of their weights does not exceed `limit`.

Return the minimum number of boats required to carry every person.

Constraints: `1 <= people.length <= 100`, `1 <= people[i] <= 50`, and `50 <= limit <= 100`.
""",
    brute_force=Algorithm(
        """function numRescueBoats(people, limit) {
  const sorted = [...people].sort((a, b) => a - b);
  const used = new Array(sorted.length).fill(false);
  let boats = 0;

  for (let i = sorted.length - 1; i >= 0; i--) {
    if (used[i]) continue;
    used[i] = true;
    boats++;

    for (let j = 0; j < i; j++) {
      if (!used[j] && sorted[i] + sorted[j] <= limit) {
        used[j] = true;
        break;
      }
    }
  }

  return boats;
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function numRescueBoats(people, limit) {
  const sorted = [...people].sort((a, b) => a - b);
  let left = 0;
  let right = sorted.length - 1;
  let boats = 0;

  while (left <= right) {
    if (left === right) {
      boats++;
      break;
    }
    if (sorted[left] + sorted[right] <= limit) {
      left++;
    }
    right--;
    boats++;
  }

  return boats;
}""",
        complexity="Time: O(n log n) | Space: O(n)",
        language="javascript",
    ),
    topic="two-pointers",
    difficulty="Medium",
    pattern="two-pointers / Greedy pairing",
    time_limit_ms=2000,
    seed=42,
    title="Boats to Save People",
    slug="boats-to-save-people",
)

spec_three_sum = ProblemSpec(
    signature="function threeSum(nums: number[])",
    statement="""# Three Sum

Given an array of integers `nums`, find all unique triplets `[nums[i], nums[j], nums[k]]` such that `i != j`, `i != k`, `j != k`, and `nums[i] + nums[j] + nums[k] == 0`.

The solution set must not contain duplicate triplets. Each individual triplet must be sorted in non-decreasing order, and the outer list of triplets must be sorted in lexicographical order.

Constraints: `3 <= nums.length <= 50` and `-20 <= nums[i] <= 20`.
""",
    brute_force=Algorithm(
        """function threeSum(nums) {
  const n = nums.length;
  const seen = new Set();
  const result = [];

  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      for (let k = j + 1; k < n; k++) {
        if (nums[i] + nums[j] + nums[k] === 0) {
          const triplet = [nums[i], nums[j], nums[k]].sort((a, b) => a - b);
          const key = `${triplet[0]},${triplet[1]},${triplet[2]}`;
          if (!seen.has(key)) {
            seen.add(key);
            result.push(triplet);
          }
        }
      }
    }
  }

  result.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
  return result;
}""",
        complexity="Time: O(n³) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function threeSum(nums) {
  const sorted = [...nums].sort((a, b) => a - b);
  const n = sorted.length;
  const result = [];

  for (let i = 0; i < n - 2; i++) {
    if (i > 0 && sorted[i] === sorted[i - 1]) {
      continue;
    }
    let left = i + 1;
    let right = n - 1;

    while (left < right) {
      const sum = sorted[i] + sorted[left] + sorted[right];
      if (sum === 0) {
        result.push([sorted[i], sorted[left], sorted[right]]);
        while (left < right && sorted[left] === sorted[left + 1]) {
          left++;
        }
        while (left < right && sorted[right] === sorted[right - 1]) {
          right--;
        }
        left++;
        right--;
      } else if (sum < 0) {
        left++;
      } else {
        right--;
      }
    }
  }

  for (let i = 0; i < result.length; i++) {
    result[i].sort((a, b) => a - b);
  }
  result.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
  return result;
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    topic="two-pointers",
    difficulty="Medium",
    pattern="two-pointers / Sort+scan",
    time_limit_ms=2000,
    seed=42,
    title="Three Sum",
    slug="three-sum",
)

spec_character_replacement = ProblemSpec(
    signature="function characterReplacement(s: string, k: number)",
    statement="""# Longest Repeating Character Replacement

You are given a string `s` and an integer `k`. You can choose any character of the string and change it to any other character at most `k` times.

Return the length of the longest contiguous substring containing identical characters that can be obtained after performing at most `k` replacements.

Constraints: `1 <= s.length <= 100` and `0 <= k <= 50`.
""",
    brute_force=Algorithm(
        """function characterReplacement(s, k) {
  let maxLen = 0;
  const n = s.length;

  for (let i = 0; i < n; i++) {
    const counts = {};
    let maxFreq = 0;

    for (let j = i; j < n; j++) {
      const ch = s[j];
      counts[ch] = (counts[ch] || 0) + 1;
      if (counts[ch] > maxFreq) {
        maxFreq = counts[ch];
      }

      const windowLen = j - i + 1;
      if (windowLen - maxFreq <= k) {
        if (windowLen > maxLen) {
          maxLen = windowLen;
        }
      }
    }
  }

  return maxLen;
}""",
        complexity="Time: O(n²) | Space: O(Σ)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function characterReplacement(s, k) {
  const counts = {};
  let left = 0;
  let maxLen = 0;

  for (let right = 0; right < s.length; right++) {
    const ch = s[right];
    counts[ch] = (counts[ch] || 0) + 1;

    let maxFreq = 0;
    for (const key in counts) {
      if (counts[key] > maxFreq) {
        maxFreq = counts[key];
      }
    }

    while ((right - left + 1) - maxFreq > k) {
      counts[s[left]]--;
      left++;
      maxFreq = 0;
      for (const key in counts) {
        if (counts[key] > maxFreq) {
          maxFreq = counts[key];
        }
      }
    }

    const windowLen = right - left + 1;
    if (windowLen > maxLen) {
      maxLen = windowLen;
    }
  }

  return maxLen;
}""",
        complexity="Time: O(n) | Space: O(Σ)",
        language="javascript",
    ),
    topic="sliding-windows",
    difficulty="Medium",
    pattern="sliding-window / Frequency max",
    time_limit_ms=2000,
    seed=42,
    title="Longest Repeating Character Replacement",
    slug="longest-repeating-character-replacement",
)

spec_permutation_in_string = ProblemSpec(
    signature="function checkInclusion(s1: string, s2: string)",
    statement="""# Permutation in String

Given two strings `s1` and `s2`, return `true` if `s2` contains a permutation of `s1`, or `false` otherwise.

In other words, check if some rearrangement of `s1`'s characters exists as a contiguous substring of `s2`.

Constraints: `1 <= s1.length <= 100` and `1 <= s2.length <= 100`.
""",
    brute_force=Algorithm(
        """function checkInclusion(s1, s2) {
  const m = s1.length;
  const n = s2.length;
  if (m > n) return false;

  const targetSorted = s1.split('').sort().join('');
  for (let i = 0; i <= n - m; i++) {
    const windowStr = s2.slice(i, i + m).split('').sort().join('');
    if (windowStr === targetSorted) {
      return true;
    }
  }
  return false;
}""",
        complexity="Time: O((n - m + 1) * m log m) | Space: O(m)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function checkInclusion(s1, s2) {
  const m = s1.length;
  const n = s2.length;
  if (m > n) return false;

  const count1 = {};
  const count2 = {};
  for (let i = 0; i < m; i++) {
    count1[s1[i]] = (count1[s1[i]] || 0) + 1;
    count2[s2[i]] = (count2[s2[i]] || 0) + 1;
  }

  function isMatch(c1, c2) {
    for (const ch in c1) {
      if (c1[ch] !== (c2[ch] || 0)) return false;
    }
    for (const ch in c2) {
      if (c2[ch] > 0 && (c1[ch] || 0) !== c2[ch]) return false;
    }
    return true;
  }

  if (isMatch(count1, count2)) return true;

  for (let i = m; i < n; i++) {
    const incoming = s2[i];
    const outgoing = s2[i - m];
    count2[incoming] = (count2[incoming] || 0) + 1;
    count2[outgoing]--;
    if (count2[outgoing] === 0) {
      delete count2[outgoing];
    }
    if (isMatch(count1, count2)) {
      return true;
    }
  }

  return false;
}""",
        complexity="Time: O(m + (n - m) * Σ) | Space: O(Σ)",
        language="javascript",
    ),
    topic="sliding-windows",
    difficulty="Medium",
    pattern="sliding-window / Fixed window",
    time_limit_ms=2000,
    seed=42,
    title="Permutation in String",
    slug="permutation-in-string",
)

spec_max_consecutive_ones = ProblemSpec(
    signature="function longestOnes(nums: number[], k: number)",
    statement="""# Max Consecutive Ones III

Given a binary array `nums` and an integer `k`, return the maximum number of consecutive `1`s in the array if you can flip at most `k` zeros to ones.

Constraints: `1 <= nums.length <= 100`, `0 <= nums[i] <= 1`, and `0 <= k <= 50`.
""",
    brute_force=Algorithm(
        """function longestOnes(nums, k) {
  let best = 0;
  const n = nums.length;

  for (let i = 0; i < n; i++) {
    let zeroCount = 0;
    for (let j = i; j < n; j++) {
      if (nums[j] === 0) {
        zeroCount++;
      }
      if (zeroCount <= k) {
        const currentLength = j - i + 1;
        if (currentLength > best) {
          best = currentLength;
        }
      } else {
        break;
      }
    }
  }

  return best;
}""",
        complexity="Time: O(n²) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function longestOnes(nums, k) {
  let left = 0;
  let zeroCount = 0;
  let best = 0;

  for (let right = 0; right < nums.length; right++) {
    if (nums[right] === 0) {
      zeroCount++;
    }

    while (zeroCount > k) {
      if (nums[left] === 0) {
        zeroCount--;
      }
      left++;
    }

    const currentLength = right - left + 1;
    if (currentLength > best) {
      best = currentLength;
    }
  }

  return best;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    topic="sliding-windows",
    difficulty="Medium",
    pattern="sliding-window / At-most-K",
    time_limit_ms=2000,
    seed=42,
    title="Max Consecutive Ones III",
    slug="max-consecutive-ones-iii",
)

spec_trapping_rain_water = ProblemSpec(
    signature="function trap(height: number[])",
    statement="""# Trapping Rain Water

Given an elevation map represented by an array of non-negative integers `height` where the width of each bar is `1`, compute the total volume of rainwater it can retain after raining.

Constraints: `0 <= height.length <= 100` and `0 <= height[i] <= 100`.
""",
    brute_force=Algorithm(
        """function trap(height) {
  const n = height.length;
  if (n === 0) return 0;

  let totalWater = 0;
  for (let i = 0; i < n; i++) {
    let maxLeft = 0;
    for (let l = 0; l <= i; l++) {
      if (height[l] > maxLeft) maxLeft = height[l];
    }
    let maxRight = 0;
    for (let r = i; r < n; r++) {
      if (height[r] > maxRight) maxRight = height[r];
    }
    const waterAtI = Math.min(maxLeft, maxRight) - height[i];
    if (waterAtI > 0) {
      totalWater += waterAtI;
    }
  }

  return totalWater;
}""",
        complexity="Time: O(n²) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function trap(height) {
  const n = height.length;
  if (n === 0) return 0;

  let left = 0;
  let right = n - 1;
  let leftMax = 0;
  let rightMax = 0;
  let totalWater = 0;

  while (left < right) {
    if (height[left] < height[right]) {
      if (height[left] >= leftMax) {
        leftMax = height[left];
      } else {
        totalWater += leftMax - height[left];
      }
      left++;
    } else {
      if (height[right] >= rightMax) {
        rightMax = height[right];
      } else {
        totalWater += rightMax - height[right];
      }
      right--;
    }
  }

  return totalWater;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    topic="two-pointers",
    difficulty="Hard",
    pattern="two-pointers / Precompute max",
    time_limit_ms=2000,
    seed=42,
    title="Trapping Rain Water",
    slug="trapping-rain-water",
)

spec_sliding_window_max = ProblemSpec(
    signature="function maxSlidingWindow(nums: number[], k: number)",
    statement="""# Sliding Window Maximum

You are given an integer array `nums` and a sliding window of size `k` that traverses from the left of the array to the right. You can only observe the `k` numbers in the window at each position. Each time, the window advances to the right by one position.

Return an array containing the maximum value inside the sliding window at each step.

Constraints: `1 <= nums.length <= 100`, `-1000 <= nums[i] <= 1000`, and `1 <= k <= nums.length`.
""",
    brute_force=Algorithm(
        """function maxSlidingWindow(nums, k) {
  if (nums.length === 0 || k <= 0) return [];
  const result = [];
  const limit = nums.length - k;

  for (let i = 0; i <= limit; i++) {
    let currentMax = nums[i];
    for (let j = i + 1; j < i + k; j++) {
      if (nums[j] > currentMax) {
        currentMax = nums[j];
      }
    }
    result.push(currentMax);
  }

  return result;
}""",
        complexity="Time: O(n * k) | Space: O(n - k + 1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function maxSlidingWindow(nums, k) {
  if (nums.length === 0 || k <= 0) return [];
  const result = [];
  const deque = [];

  for (let i = 0; i < nums.length; i++) {
    while (deque.length > 0 && deque[0] < i - k + 1) {
      deque.shift();
    }

    while (deque.length > 0 && nums[deque[deque.length - 1]] <= nums[i]) {
      deque.pop();
    }

    deque.push(i);

    if (i >= k - 1) {
      result.push(nums[deque[0]]);
    }
  }

  return result;
}""",
        complexity="Time: O(n) | Space: O(k)",
        language="javascript",
    ),
    topic="sliding-windows",
    difficulty="Hard",
    pattern="sliding-window / Monotonic deque",
    time_limit_ms=2000,
    seed=42,
    title="Sliding Window Maximum",
    slug="sliding-window-maximum",
)

SPECS: list[ProblemSpec] = [
    spec_backspace,
    spec_valid_palindrome_ii,
    spec_squares,
    spec_boats,
    spec_three_sum,
    spec_character_replacement,
    spec_permutation_in_string,
    spec_max_consecutive_ones,
    spec_trapping_rain_water,
    spec_sliding_window_max,
]


def main() -> None:
    output_dir = REPO_ROOT / "content" / "problems"
    print(f"Authoring and verifying {len(SPECS)} Batch-1B problems with PAF...")
    for idx, spec in enumerate(SPECS, 1):
        print(f"[{idx}/{len(SPECS)}] Generating {spec.slug} ({spec.difficulty})...")
        problem = build_problem(spec)
        out_file = problem.write_to(output_dir)
        print(
            f"  ✓ {problem.data['slug']}: {problem.report.total_cases} cases verified | "
            f"Brute: {problem.report.brute_force_runtime_ms:.2f}ms | "
            f"Optimal: {problem.report.optimal_runtime_ms:.2f}ms -> {out_file.name}"
        )
    print("\nAll 10 Batch-1B problems generated and PAF-verified successfully.")


if __name__ == "__main__":
    main()
