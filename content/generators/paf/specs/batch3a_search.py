"""Authoring and verification script for Batch 3A: Binary Search and Intervals problems."""

from __future__ import annotations

import asyncio
import copy
import json
import math
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
# Problem 1: koko-eating-bananas
# ---------------------------------------------------------------------------
spec_koko = ProblemSpec(
    signature="function minEatingSpeed(piles: number[], h: number)",
    statement="""# Koko Eating Bananas

Koko loves to eat bananas. There are `n` piles of bananas, where the `i`-th pile has `piles[i]` bananas. The guards have gone and will return in `h` hours.

Koko can decide her bananas-per-hour eating speed of `k`. Each hour, she chooses some pile of bananas and eats `k` bananas from that pile. If the pile has fewer than `k` bananas, she eats all of them instead and will not eat any more bananas during that hour.

Koko wants to finish eating all the bananas before the guards return. Return the minimum integer `k` such that she can eat all the bananas within `h` hours.

Constraints: `1 <= piles.length <= 100`, `piles.length <= h <= 10000`, and `1 <= piles[i] <= 1000`.
""",
    brute_force=Algorithm(
        """function minEatingSpeed(piles, h) {
  let maxPile = 0;
  for (let i = 0; i < piles.length; i++) {
    if (piles[i] > maxPile) maxPile = piles[i];
  }
  for (let k = 1; k <= maxPile; k++) {
    let hours = 0;
    for (let i = 0; i < piles.length; i++) {
      hours += Math.ceil(piles[i] / k);
    }
    if (hours <= h) return k;
  }
  return maxPile;
}""",
        complexity="Time: O(m · n) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function minEatingSpeed(piles, h) {
  let low = 1;
  let high = 0;
  for (let i = 0; i < piles.length; i++) {
    if (piles[i] > high) high = piles[i];
  }
  let ans = high;
  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    let hours = 0;
    for (let i = 0; i < piles.length; i++) {
      hours += Math.ceil(piles[i] / mid);
    }
    if (hours <= h) {
      ans = mid;
      high = mid - 1;
    } else {
      low = mid + 1;
    }
  }
  return ans;
}""",
        complexity="Time: O(n log m) | Space: O(1)",
        language="javascript",
    ),
    topic="binary-search",
    difficulty="Medium",
    pattern="binary-search / Answer space",
    time_limit_ms=2000,
    seed=42,
    title="Koko Eating Bananas",
    slug="koko-eating-bananas",
)

py_brute_koko = """def minEatingSpeed(piles: list[int], h: int) -> int:
    import math
    max_pile = max(piles)
    for k in range(1, max_pile + 1):
        hours = sum(math.ceil(p / k) for p in piles)
        if hours <= h:
            return k
    return max_pile
"""

py_optimal_koko = """def minEatingSpeed(piles: list[int], h: int) -> int:
    import math
    low, high = 1, max(piles)
    ans = high
    while low <= high:
        mid = (low + high) // 2
        hours = sum(math.ceil(p / mid) for p in piles)
        if hours <= h:
            ans = mid
            high = mid - 1
        else:
            low = mid + 1
    return ans
"""


def _gen_koko_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[3, 6, 7, 11], 8],
        [[30, 11, 23, 4, 20], 5],
        [[30, 11, 23, 4, 20], 6],
        [[10], 3],
        [[1000], 1000],
        [[1, 1, 1, 1], 4],
        [[10, 10, 10], 100],
        [[100, 200, 300], 600],
        [[4, 11, 20, 23, 30], 27],
        [[500, 500, 500], 3],
        [[1, 2, 3, 4, 5], 15],
        [[10, 20, 30, 40], 10],
    ]
    for _ in range(14):
        n = rng.randint(2, 25)
        piles = [rng.randint(1, 500) for _ in range(n)]
        h = rng.randint(n, n * 6)
        cases.append([piles, h])
    # Stress cases
    cases.append([[rng.randint(800, 1000) for _ in range(100)], 100])
    cases.append([[rng.randint(800, 1000) for _ in range(100)], 150])
    cases.append([[rng.randint(1, 1000) for _ in range(100)], 250])
    cases.append([[rng.randint(1, 1000) for _ in range(100)], 5000])
    return cases


# ---------------------------------------------------------------------------
# Problem 2: search-in-rotated-sorted-array
# ---------------------------------------------------------------------------
spec_rotated_search = ProblemSpec(
    signature="function search(nums: number[], target: number)",
    statement="""# Search in Rotated Sorted Array

Given an array of integers `nums` sorted in ascending order with distinct values, and an integer `target`, suppose that `nums` is rotated at an unknown pivot index `k` (`0 <= k < nums.length`) such that the resulting array is `[nums[k], nums[k+1], ..., nums[n-1], nums[0], nums[1], ..., nums[k-1]]`.

For example, `[0, 1, 2, 4, 5, 6, 7]` might be rotated at pivot index `3` and become `[4, 5, 6, 7, 0, 1, 2]`.

Return the index of `target` if it is present in `nums`, or `-1` if it is not in `nums`.

Constraints: `1 <= nums.length <= 100`, `-1000 <= nums[i] <= 1000`, and `-1000 <= target <= 1000`. All elements of `nums` are unique.
""",
    brute_force=Algorithm(
        """function search(nums, target) {
  for (let i = 0; i < nums.length; i++) {
    if (nums[i] === target) return i;
  }
  return -1;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function search(nums, target) {
  let low = 0;
  let high = nums.length - 1;
  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    if (nums[mid] === target) return mid;
    if (nums[low] <= nums[mid]) {
      if (nums[low] <= target && target < nums[mid]) {
        high = mid - 1;
      } else {
        low = mid + 1;
      }
    } else {
      if (nums[mid] < target && target <= nums[high]) {
        low = mid + 1;
      } else {
        high = mid - 1;
      }
    }
  }
  return -1;
}""",
        complexity="Time: O(log n) | Space: O(1)",
        language="javascript",
    ),
    topic="binary-search",
    difficulty="Medium",
    pattern="binary-search / Half sorted",
    time_limit_ms=2000,
    seed=42,
    title="Search in Rotated Sorted Array",
    slug="search-in-rotated-sorted-array",
)

py_brute_rotated_search = """def search(nums: list[int], target: int) -> int:
    for i, num in enumerate(nums):
        if num == target:
            return i
    return -1
"""

py_optimal_rotated_search = """def search(nums: list[int], target: int) -> int:
    low, high = 0, len(nums) - 1
    while low <= high:
        mid = (low + high) // 2
        if nums[mid] == target:
            return mid
        if nums[low] <= nums[mid]:
            if nums[low] <= target < nums[mid]:
                high = mid - 1
            else:
                low = mid + 1
        else:
            if nums[mid] < target <= nums[high]:
                low = mid + 1
            else:
                high = mid - 1
    return -1
"""


def _gen_rotated_search_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[4, 5, 6, 7, 0, 1, 2], 0],
        [[4, 5, 6, 7, 0, 1, 2], 3],
        [[1], 0],
        [[1], 1],
        [[1, 3], 3],
        [[3, 1], 1],
        [[3, 1], 3],
        [[3, 1], 2],
        [[1, 2, 3, 4, 5], 1],
        [[1, 2, 3, 4, 5], 5],
        [[1, 2, 3, 4, 5], 3],
        [[1, 2, 3, 4, 5], 6],
        [[5, 1, 2, 3, 4], 5],
        [[2, 3, 4, 5, 1], 1],
        [[-10, -5, 0, 5, 10], -5],
        [[-3, -1, 5, -8, -6], -8],
    ]
    for _ in range(12):
        n = rng.randint(3, 30)
        sorted_vals = sorted(rng.sample(range(-500, 501), n))
        k = rng.randint(0, n - 1)
        rotated = sorted_vals[k:] + sorted_vals[:k]
        if rng.random() < 0.7:
            target = rng.choice(rotated)
        else:
            target = rng.randint(-600, 600)
            while target in rotated:
                target = rng.randint(-600, 600)
        cases.append([rotated, target])
    # Stress cases
    for pivot in (25, 50, 75, 99):
        sorted_vals = sorted(rng.sample(range(-1000, 1001), 100))
        rotated = sorted_vals[pivot:] + sorted_vals[:pivot]
        target = rng.choice(rotated) if pivot % 2 == 0 else 9999
        cases.append([rotated, target])
    return cases


# ---------------------------------------------------------------------------
# Problem 3: find-minimum-in-rotated-sorted-array
# ---------------------------------------------------------------------------
spec_find_min = ProblemSpec(
    signature="function findMin(nums: number[])",
    statement="""# Find Minimum in Rotated Sorted Array

Suppose an array of length `n` sorted in ascending order with distinct values is rotated between `1` and `n` times.

For example, the array `nums = [0, 1, 2, 4, 5, 6, 7]` might become:
- `[4, 5, 6, 7, 0, 1, 2]` if rotated `4` times.
- `[0, 1, 2, 4, 5, 6, 7]` if rotated `7` times (fully unrotated).

Given the sorted rotated array `nums` of unique elements, return the minimum element of this array.

Constraints: `1 <= nums.length <= 100` and `-1000 <= nums[i] <= 1000`. All integers in `nums` are unique.
""",
    brute_force=Algorithm(
        """function findMin(nums) {
  let minVal = nums[0];
  for (let i = 1; i < nums.length; i++) {
    if (nums[i] < minVal) minVal = nums[i];
  }
  return minVal;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function findMin(nums) {
  let low = 0;
  let high = nums.length - 1;
  while (low < high) {
    const mid = Math.floor((low + high) / 2);
    if (nums[mid] > nums[high]) {
      low = mid + 1;
    } else {
      high = mid;
    }
  }
  return nums[low];
}""",
        complexity="Time: O(log n) | Space: O(1)",
        language="javascript",
    ),
    topic="binary-search",
    difficulty="Medium",
    pattern="binary-search / Inflection",
    time_limit_ms=2000,
    seed=42,
    title="Find Minimum in Rotated Sorted Array",
    slug="find-minimum-in-rotated-sorted-array",
)

py_brute_find_min = """def findMin(nums: list[int]) -> int:
    min_val = nums[0]
    for x in nums:
        if x < min_val:
            min_val = x
    return min_val
"""

py_optimal_find_min = """def findMin(nums: list[int]) -> int:
    low, high = 0, len(nums) - 1
    while low < high:
        mid = (low + high) // 2
        if nums[mid] > nums[high]:
            low = mid + 1
        else:
            high = mid
    return nums[low]
"""


def _gen_find_min_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[3, 4, 5, 1, 2]],
        [[4, 5, 6, 7, 0, 1, 2]],
        [[11, 13, 15, 17]],
        [[1]],
        [[2, 1]],
        [[1, 2]],
        [[5, 1, 2, 3, 4]],
        [[2, 3, 4, 5, 1]],
        [[10, 20, 30, 40, 50, 5]],
        [[-5, -3, -1, -10, -8]],
        [[50, 60, 70, 80, -100, -50, 0]],
        [[2, 3, 4, 5, 6, 7, 8, 9, 1]],
    ]
    for _ in range(14):
        n = rng.randint(3, 30)
        sorted_vals = sorted(rng.sample(range(-800, 801), n))
        k = rng.randint(0, n - 1)
        cases.append([sorted_vals[k:] + sorted_vals[:k]])
    # Stress cases
    for pivot in (1, 33, 67, 99):
        sorted_vals = sorted(rng.sample(range(-1000, 1001), 100))
        cases.append([sorted_vals[pivot:] + sorted_vals[:pivot]])
    return cases


# ---------------------------------------------------------------------------
# Problem 4: search-a-2d-matrix
# ---------------------------------------------------------------------------
spec_search_2d = ProblemSpec(
    signature="function searchMatrix(matrix: number[][], target: number)",
    statement="""# Search a 2D Matrix

You are given an `m x n` integer matrix `matrix` with the following two properties:
1. Each row is sorted in non-decreasing order.
2. The first integer of each row is greater than the last integer of the previous row.

Given an integer `target`, return `true` if `target` is in `matrix` or `false` otherwise.

Constraints: `1 <= matrix.length <= 50`, `1 <= matrix[0].length <= 50`, `-10000 <= matrix[i][j] <= 10000`, and `-10000 <= target <= 10000`.
""",
    brute_force=Algorithm(
        """function searchMatrix(matrix, target) {
  const m = matrix.length;
  const n = matrix[0].length;
  for (let r = 0; r < m; r++) {
    for (let c = 0; c < n; c++) {
      if (matrix[r][c] === target) return true;
    }
  }
  return false;
}""",
        complexity="Time: O(m · n) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function searchMatrix(matrix, target) {
  const m = matrix.length;
  const n = matrix[0].length;
  let low = 0;
  let high = m * n - 1;
  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    const r = Math.floor(mid / n);
    const c = mid % n;
    const val = matrix[r][c];
    if (val === target) return true;
    if (val < target) {
      low = mid + 1;
    } else {
      high = mid - 1;
    }
  }
  return false;
}""",
        complexity="Time: O(log(m · n)) | Space: O(1)",
        language="javascript",
    ),
    topic="binary-search",
    difficulty="Medium",
    pattern="binary-search / Flattened",
    time_limit_ms=2000,
    seed=42,
    title="Search a 2D Matrix",
    slug="search-a-2d-matrix",
)

py_brute_search_2d = """def searchMatrix(matrix: list[list[int]], target: int) -> bool:
    for row in matrix:
        for val in row:
            if val == target:
                return True
    return False
"""

py_optimal_search_2d = """def searchMatrix(matrix: list[list[int]], target: int) -> bool:
    m, n = len(matrix), len(matrix[0])
    low, high = 0, m * n - 1
    while low <= high:
        mid = (low + high) // 2
        r, c = mid // n, mid % n
        val = matrix[r][c]
        if val == target:
            return True
        if val < target:
            low = mid + 1
        else:
            high = mid - 1
    return False
"""


def _gen_search_2d_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 3],
        [[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 13],
        [[[1]], 1],
        [[[1]], 0],
        [[[1, 3, 5, 7]], 5],
        [[[1, 3, 5, 7]], 4],
        [[[1], [3], [5], [7]], 7],
        [[[1], [3], [5], [7]], 2],
        [[[2, 4], [6, 8]], 2],
        [[[2, 4], [6, 8]], 8],
        [[[2, 4], [6, 8]], 1],
        [[[2, 4], [6, 8]], 9],
    ]
    for _ in range(12):
        m = rng.randint(2, 6)
        n = rng.randint(2, 6)
        total = m * n
        vals = sorted(rng.sample(range(-5000, 5001), total))
        grid = [vals[i * n : (i + 1) * n] for i in range(m)]
        if rng.random() < 0.6:
            target = rng.choice(vals)
        else:
            target = rng.randint(-6000, 6000)
            while target in vals:
                target = rng.randint(-6000, 6000)
        cases.append([grid, target])
    # Stress cases
    for m, n in ((10, 10), (12, 12), (15, 15), (20, 20)):
        total = m * n
        vals = sorted(rng.sample(range(-10000, 10001), total))
        grid = [vals[i * n : (i + 1) * n] for i in range(m)]
        target = rng.choice(vals) if m % 2 == 0 else 99999
        cases.append([grid, target])
    return cases


# ---------------------------------------------------------------------------
# Problem 5: insert-interval
# ---------------------------------------------------------------------------
spec_insert_interval = ProblemSpec(
    signature="function insert(intervals: number[][], newInterval: number[])",
    statement="""# Insert Interval

You are given an array of non-overlapping intervals `intervals` where `intervals[i] = [start_i, end_i]` represents the start and the end of the `i`-th interval, and `intervals` is sorted in ascending order by `start_i`. You are also given an interval `newInterval = [start, end]` representing the start and end of another interval.

Insert `newInterval` into `intervals` such that `intervals` is still sorted in ascending order by start time and `intervals` still contains no overlapping intervals (merge overlapping intervals if necessary).

Return `intervals` after the insertion.

Constraints: `0 <= intervals.length <= 100`, `intervals[i].length == 2`, `newInterval.length == 2`, and `0 <= start_i <= end_i <= 10000`.
""",
    brute_force=Algorithm(
        """function insert(intervals, newInterval) {
  const combined = intervals.concat([[newInterval[0], newInterval[1]]]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const merged = [[combined[0][0], combined[0][1]]];
  for (let i = 1; i < combined.length; i++) {
    const prev = merged[merged.length - 1];
    const curr = combined[i];
    if (curr[0] <= prev[1]) {
      prev[1] = Math.max(prev[1], curr[1]);
    } else {
      merged.push([curr[0], curr[1]]);
    }
  }
  return merged;
}""",
        complexity="Time: O(n log n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function insert(intervals, newInterval) {
  const result = [];
  let i = 0;
  const n = intervals.length;
  let cur = [newInterval[0], newInterval[1]];
  while (i < n && intervals[i][1] < cur[0]) {
    result.push([intervals[i][0], intervals[i][1]]);
    i++;
  }
  while (i < n && intervals[i][0] <= cur[1]) {
    cur[0] = Math.min(cur[0], intervals[i][0]);
    cur[1] = Math.max(cur[1], intervals[i][1]);
    i++;
  }
  result.push(cur);
  while (i < n) {
    result.push([intervals[i][0], intervals[i][1]]);
    i++;
  }
  return result;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="intervals",
    difficulty="Medium",
    pattern="intervals / Merge scan",
    time_limit_ms=2000,
    seed=42,
    title="Insert Interval",
    slug="insert-interval",
)

py_brute_insert_interval = """def insert(intervals: list[list[int]], newInterval: list[int]) -> list[list[int]]:
    combined = sorted(intervals + [list(newInterval)], key=lambda x: (x[0], x[1]))
    merged = [list(combined[0])]
    for curr in combined[1:]:
        if curr[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], curr[1])
        else:
            merged.append(list(curr))
    return merged
"""

py_optimal_insert_interval = """def insert(intervals: list[list[int]], newInterval: list[int]) -> list[list[int]]:
    result = []
    i = 0
    n = len(intervals)
    cur = [newInterval[0], newInterval[1]]
    while i < n and intervals[i][1] < cur[0]:
        result.append(list(intervals[i]))
        i += 1
    while i < n and intervals[i][0] <= cur[1]:
        cur[0] = min(cur[0], intervals[i][0])
        cur[1] = max(cur[1], intervals[i][1])
        i += 1
    result.append(cur)
    while i < n:
        result.append(list(intervals[i]))
        i += 1
    return result
"""


def _gen_insert_interval_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[[1, 3], [6, 9]], [2, 5]],
        [[[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]],
        [[], [5, 7]],
        [[[3, 5], [6, 8]], [0, 2]],
        [[[1, 2], [3, 4]], [5, 6]],
        [[[2, 4], [6, 8], [10, 12]], [1, 15]],
        [[[1, 3], [4, 6]], [3, 4]],
        [[[1, 5]], [2, 3]],
        [[[1, 5]], [0, 6]],
        [[[1, 5]], [1, 5]],
        [[[1, 5], [6, 8]], [0, 9]],
        [[[1, 2], [3, 5]], [5, 8]],
    ]
    for _ in range(12):
        k = rng.randint(2, 15)
        curr = rng.randint(0, 50)
        intervals: list[list[int]] = []
        for _ in range(k):
            span = rng.randint(1, 10)
            gap = rng.randint(1, 10)
            intervals.append([curr, curr + span])
            curr += span + gap
        s = rng.randint(0, curr)
        e = s + rng.randint(1, 25)
        cases.append([intervals, [s, e]])
    # Stress cases
    for count in (40, 60, 80, 100):
        curr = 0
        intervals = []
        for _ in range(count):
            span = rng.randint(2, 5)
            gap = rng.randint(2, 5)
            intervals.append([curr, curr + span])
            curr += span + gap
        s = rng.randint(10, curr // 2)
        e = s + rng.randint(20, curr // 2)
        cases.append([intervals, [s, e]])
    return cases


# ---------------------------------------------------------------------------
# Problem 6: non-overlapping-intervals
# ---------------------------------------------------------------------------
spec_erase_overlap = ProblemSpec(
    signature="function eraseOverlapIntervals(intervals: number[][])",
    statement="""# Non-overlapping Intervals

Given an array of intervals `intervals` where `intervals[i] = [start_i, end_i]`, return the minimum number of intervals you need to remove to make the rest of the intervals non-overlapping.

Note that intervals which touch at a single point (such as `[1, 2]` and `[2, 3]`) are considered non-overlapping.

Constraints: `1 <= intervals.length <= 100`, `intervals[i].length == 2`, and `-10000 <= start_i < end_i <= 10000`.
""",
    brute_force=Algorithm(
        """function eraseOverlapIntervals(intervals) {
  if (intervals.length <= 1) return 0;
  const sorted = intervals.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const n = sorted.length;
  const dp = new Array(n).fill(1);
  let maxKeep = 1;
  for (let i = 1; i < n; i++) {
    for (let j = 0; j < i; j++) {
      if (sorted[j][1] <= sorted[i][0]) {
        if (dp[j] + 1 > dp[i]) dp[i] = dp[j] + 1;
      }
    }
    if (dp[i] > maxKeep) maxKeep = dp[i];
  }
  return n - maxKeep;
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function eraseOverlapIntervals(intervals) {
  if (intervals.length <= 1) return 0;
  const sorted = intervals.slice().sort((a, b) => a[1] - b[1]);
  let count = 0;
  let prevEnd = sorted[0][1];
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i][0] < prevEnd) {
      count++;
    } else {
      prevEnd = sorted[i][1];
    }
  }
  return count;
}""",
        complexity="Time: O(n log n) | Space: O(n)",
        language="javascript",
    ),
    topic="intervals",
    difficulty="Medium",
    pattern="intervals / Greedy end-sort",
    time_limit_ms=2000,
    seed=42,
    title="Non-overlapping Intervals",
    slug="non-overlapping-intervals",
)

py_brute_erase_overlap = """def eraseOverlapIntervals(intervals: list[list[int]]) -> int:
    if len(intervals) <= 1:
        return 0
    sorted_intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
    n = len(sorted_intervals)
    dp = [1] * n
    for i in range(1, n):
        for j in range(i):
            if sorted_intervals[j][1] <= sorted_intervals[i][0]:
                dp[i] = max(dp[i], dp[j] + 1)
    return n - max(dp)
"""

py_optimal_erase_overlap = """def eraseOverlapIntervals(intervals: list[list[int]]) -> int:
    if len(intervals) <= 1:
        return 0
    sorted_intervals = sorted(intervals, key=lambda x: x[1])
    count = 0
    prev_end = sorted_intervals[0][1]
    for i in range(1, len(sorted_intervals)):
        if sorted_intervals[i][0] < prev_end:
            count += 1
        else:
            prev_end = sorted_intervals[i][1]
    return count
"""


def _gen_erase_overlap_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[[1, 2], [2, 3], [3, 4], [1, 3]]],
        [[[1, 2], [1, 2], [1, 2]]],
        [[[1, 2], [2, 3]]],
        [[[1, 10]]],
        [[[1, 10], [2, 3], [4, 5], [6, 7]]],
        [[[1, 4], [2, 5], [3, 6], [4, 7]]],
        [[[1, 100], [2, 3], [4, 5], [6, 7], [8, 9]]],
        [[[0, 2], [1, 3], [2, 4], [3, 5], [4, 6]]],
        [[[1, 5], [2, 3], [3, 4], [1, 2], [4, 5]]],
        [[[-10, -5], [-7, -3], [-4, 0], [1, 5]]],
    ]
    for _ in range(14):
        k = rng.randint(3, 25)
        intervals: list[list[int]] = []
        for _ in range(k):
            s = rng.randint(-100, 100)
            e = s + rng.randint(1, 30)
            intervals.append([s, e])
        cases.append([intervals])
    # Stress cases (cap at 60 so O(n^2) brute force executes under 2ms)
    for count in (40, 50, 55, 60):
        intervals = []
        for _ in range(count):
            s = rng.randint(-2000, 2000)
            e = s + rng.randint(1, 100)
            intervals.append([s, e])
        cases.append([intervals])
    return cases


# ---------------------------------------------------------------------------
# Problem 7: meeting-rooms
# ---------------------------------------------------------------------------
spec_meeting_rooms = ProblemSpec(
    signature="function canAttendMeetings(intervals: number[][])",
    statement="""# Meeting Rooms

Given an array of meeting time intervals `intervals` where `intervals[i] = [start_i, end_i]`, determine if a person could attend all meetings.

Touching boundaries are allowed: a meeting ending at time `t` does not conflict with another meeting beginning at time `t`.

Constraints: `0 <= intervals.length <= 100`, `intervals[i].length == 2`, and `0 <= start_i <= end_i <= 10000`.
""",
    brute_force=Algorithm(
        """function canAttendMeetings(intervals) {
  for (let i = 0; i < intervals.length; i++) {
    for (let j = i + 1; j < intervals.length; j++) {
      const s1 = intervals[i][0], e1 = intervals[i][1];
      const s2 = intervals[j][0], e2 = intervals[j][1];
      if (Math.max(s1, s2) < Math.min(e1, e2)) {
        return false;
      }
    }
  }
  return true;
}""",
        complexity="Time: O(n²) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function canAttendMeetings(intervals) {
  const sorted = intervals.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i][0] < sorted[i - 1][1]) {
      return false;
    }
  }
  return true;
}""",
        complexity="Time: O(n log n) | Space: O(n)",
        language="javascript",
    ),
    topic="intervals",
    difficulty="Easy",
    pattern="intervals / Sort+scan",
    time_limit_ms=2000,
    seed=42,
    title="Meeting Rooms",
    slug="meeting-rooms",
)

py_brute_meeting_rooms = """def canAttendMeetings(intervals: list[list[int]]) -> bool:
    for i in range(len(intervals)):
        for j in range(i + 1, len(intervals)):
            s1, e1 = intervals[i]
            s2, e2 = intervals[j]
            if max(s1, s2) < min(e1, e2):
                return False
    return True
"""

py_optimal_meeting_rooms = """def canAttendMeetings(intervals: list[list[int]]) -> bool:
    sorted_intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
    for i in range(1, len(sorted_intervals)):
        if sorted_intervals[i][0] < sorted_intervals[i - 1][1]:
            return False
    return True
"""


def _gen_meeting_rooms_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[[0, 30], [5, 10], [15, 20]]],
        [[[7, 10], [2, 4]]],
        [[[0, 5], [5, 10]]],
        [[]],
        [[[1, 5]]],
        [[[1, 5], [1, 5]]],
        [[[1, 5], [4, 6]]],
        [[[1, 2], [3, 4], [5, 6]]],
        [[[1, 10], [2, 3]]],
        [[[5, 5], [5, 6]]],
        [[[10, 20], [20, 30], [30, 40], [40, 50]]],
        [[[10, 20], [20, 30], [25, 35]]],
    ]
    for _ in range(12):
        k = rng.randint(3, 20)
        make_disjoint = rng.random() < 0.5
        if make_disjoint:
            intervals = []
            curr = 0
            for _ in range(k):
                span = rng.randint(1, 15)
                gap = rng.randint(0, 10)
                intervals.append([curr, curr + span])
                curr += span + gap
            rng.shuffle(intervals)
        else:
            intervals = []
            for _ in range(k):
                s = rng.randint(0, 100)
                e = s + rng.randint(5, 30)
                intervals.append([s, e])
        cases.append([intervals])
    # Stress cases
    for count in (40, 50, 65, 80):
        intervals = []
        curr = 0
        for _ in range(count):
            span = rng.randint(2, 10)
            gap = rng.randint(0, 5)
            intervals.append([curr, curr + span])
            curr += span + gap
        if count % 2 == 0:
            intervals.append([5, 25])  # inject conflict
        rng.shuffle(intervals)
        cases.append([intervals])
    return cases


# ---------------------------------------------------------------------------
# Problem 8: binary-search
# ---------------------------------------------------------------------------
spec_binary_search = ProblemSpec(
    signature="function binarySearch(nums: number[], target: number)",
    statement="""# Binary Search

Given an array of integers `nums` which is sorted in ascending order, and an integer `target`, write a function to search `target` in `nums`. If `target` exists, then return its index. Otherwise, return `-1`.

You must write an algorithm with `O(log n)` runtime complexity.

Constraints: `1 <= nums.length <= 100`, `-1000 <= nums[i] <= 1000`, and `-1000 <= target <= 1000`. All the integers in `nums` are unique and sorted in ascending order.
""",
    brute_force=Algorithm(
        """function binarySearch(nums, target) {
  for (let i = 0; i < nums.length; i++) {
    if (nums[i] === target) return i;
  }
  return -1;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function binarySearch(nums, target) {
  let left = 0;
  let right = nums.length - 1;
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    if (nums[mid] === target) {
      return mid;
    } else if (nums[mid] < target) {
      left = mid + 1;
    } else {
      right = mid - 1;
    }
  }
  return -1;
}""",
        complexity="Time: O(log n) | Space: O(1)",
        language="javascript",
    ),
    topic="binary-search",
    difficulty="Easy",
    pattern="binary-search / Classic",
    time_limit_ms=2000,
    seed=42,
    title="Binary Search",
    slug="binary-search",
)

py_brute_binary_search = """def binarySearch(nums: list[int], target: int) -> int:
    for i, num in enumerate(nums):
        if num == target:
            return i
    return -1
"""

py_optimal_binary_search = """def binarySearch(nums: list[int], target: int) -> int:
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
"""


def _gen_binary_search_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[-1, 0, 3, 5, 9, 12], 9],
        [[-1, 0, 3, 5, 9, 12], 2],
        [[5], 5],
        [[5], 2],
        [[1, 3], 1],
        [[1, 3], 3],
        [[1, 3], 2],
        [[1, 3, 5, 7, 9], 1],
        [[1, 3, 5, 7, 9], 9],
        [[1, 3, 5, 7, 9], 0],
        [[1, 3, 5, 7, 9], 10],
        [[-50, -40, -30, -20, -10], -30],
        [[-100, 0, 100], 0],
        [[2, 4, 6, 8, 10, 12, 14, 16], 14],
    ]
    for _ in range(12):
        n = rng.randint(3, 30)
        vals = sorted(rng.sample(range(-500, 501), n))
        if rng.random() < 0.6:
            target = rng.choice(vals)
        else:
            target = rng.randint(-600, 600)
            while target in vals:
                target = rng.randint(-600, 600)
        cases.append([vals, target])
    # Stress cases
    for i in range(4):
        vals = sorted(rng.sample(range(-1000, 1001), 100))
        target = rng.choice(vals) if i % 2 == 0 else 9999
        cases.append([vals, target])
    return cases


# ---------------------------------------------------------------------------
# Problem 9: search-insert-position
# ---------------------------------------------------------------------------
spec_search_insert = ProblemSpec(
    signature="function searchInsert(nums: number[], target: number)",
    statement="""# Search Insert Position

Given a sorted array of distinct integers `nums` and a target value `target`, return the index if the target is found. If not, return the index where it would be if it were inserted in order.

You must write an algorithm with `O(log n)` runtime complexity.

Constraints: `1 <= nums.length <= 100`, `-1000 <= nums[i] <= 1000`, and `-1000 <= target <= 1000`. `nums` contains distinct values sorted in ascending order.
""",
    brute_force=Algorithm(
        """function searchInsert(nums, target) {
  for (let i = 0; i < nums.length; i++) {
    if (nums[i] >= target) return i;
  }
  return nums.length;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function searchInsert(nums, target) {
  let left = 0;
  let right = nums.length - 1;
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    if (nums[mid] === target) {
      return mid;
    } else if (nums[mid] < target) {
      left = mid + 1;
    } else {
      right = mid - 1;
    }
  }
  return left;
}""",
        complexity="Time: O(log n) | Space: O(1)",
        language="javascript",
    ),
    topic="binary-search",
    difficulty="Easy",
    pattern="binary-search / Lower bound",
    time_limit_ms=2000,
    seed=42,
    title="Search Insert Position",
    slug="search-insert-position",
)

py_brute_search_insert = """def searchInsert(nums: list[int], target: int) -> int:
    for i, num in enumerate(nums):
        if num >= target:
            return i
    return len(nums)
"""

py_optimal_search_insert = """def searchInsert(nums: list[int], target: int) -> int:
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return left
"""


def _gen_search_insert_inputs(rng: random.Random) -> list[list[Any]]:
    cases: list[list[Any]] = [
        [[1, 3, 5, 6], 5],
        [[1, 3, 5, 6], 2],
        [[1, 3, 5, 6], 7],
        [[1, 3, 5, 6], 0],
        [[1], 0],
        [[1], 1],
        [[1], 2],
        [[2, 4, 6, 8, 10], 6],
        [[2, 4, 6, 8, 10], 5],
        [[2, 4, 6, 8, 10], 1],
        [[2, 4, 6, 8, 10], 11],
        [[-10, -5, 0, 5, 10], -7],
        [[-10, -5, 0, 5, 10], -15],
        [[-10, -5, 0, 5, 10], 15],
    ]
    for _ in range(12):
        n = rng.randint(3, 30)
        vals = sorted(rng.sample(range(-500, 501), n))
        target = rng.randint(-600, 600)
        cases.append([vals, target])
    # Stress cases
    for i in range(4):
        vals = sorted(rng.sample(range(-1000, 1001), 100))
        target = rng.choice(vals) if i % 2 == 0 else rng.randint(-1100, 1100)
        cases.append([vals, target])
    return cases


# ---------------------------------------------------------------------------
# BUNDLES
# ---------------------------------------------------------------------------
BUNDLES: list[ProblemBundle] = [
    ProblemBundle(
        spec=spec_koko,
        py_brute_code=py_brute_koko,
        py_brute_complexity="Time: O(m · n) | Space: O(1)",
        py_optimal_code=py_optimal_koko,
        py_optimal_complexity="Time: O(n log m) | Space: O(1)",
        input_generator=_gen_koko_inputs,
        examples=[
            {
                "input": "piles = [3, 6, 7, 11], h = 8",
                "output": "4",
                "explanation": "At eating speed 4, Koko requires 1 + 2 + 2 + 3 = 8 hours to finish all piles, which fits within the guard limit of 8 hours.",
            },
            {
                "input": "piles = [30, 11, 23, 4, 20], h = 5",
                "output": "30",
                "explanation": "Because h equals the number of piles (5), Koko has exactly 1 hour per pile, forcing her speed to match the largest pile size (30).",
            },
            {
                "input": "piles = [30, 11, 23, 4, 20], h = 6",
                "output": "23",
                "explanation": "At speed 23, the hours required are 2 + 1 + 1 + 1 + 1 = 6 hours, satisfying the deadline.",
            },
        ],
        approach="Binary search the answer space for eating speed k between 1 and the largest pile size. For each candidate speed, compute total hours required by summing ceiling division across all piles.",
        why_optimal_template="Brute-force linear checking tests each speed sequentially taking O(m · n) time, whereas binary search over the monotonic answer space runs in O(n log m) time and O(1) extra space. On the {case_count} verified test cases, the optimal implementation took {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for brute force.",
        pitfalls="Ensure integer ceiling division when calculating hours for each pile. Watch for off-by-one errors when updating search boundaries low and high.",
        reading_links=["https://en.wikipedia.org/wiki/Binary_search_algorithm"],
        hints=[
            "Notice the monotonicity: if Koko can finish all bananas at speed k, she can also finish at any speed greater than k.",
            "The search space for speed k is bounded between 1 and the maximum pile size.",
            "Use binary search on this answer range. For candidate speed mid, compute total hours needed by summing Math.ceil(pile / mid).",
        ],
    ),
    ProblemBundle(
        spec=spec_rotated_search,
        py_brute_code=py_brute_rotated_search,
        py_brute_complexity="Time: O(n) | Space: O(1)",
        py_optimal_code=py_optimal_rotated_search,
        py_optimal_complexity="Time: O(log n) | Space: O(1)",
        input_generator=_gen_rotated_search_inputs,
        examples=[
            {
                "input": "nums = [4, 5, 6, 7, 0, 1, 2], target = 0",
                "output": "4",
                "explanation": "Target 0 is located at index 4 in the rotated array.",
            },
            {
                "input": "nums = [4, 5, 6, 7, 0, 1, 2], target = 3",
                "output": "-1",
                "explanation": "Target 3 is not present in nums, so the function returns -1.",
            },
            {
                "input": "nums = [1], target = 0",
                "output": "-1",
                "explanation": "Single-element array where the element does not equal target.",
            },
        ],
        approach="In a rotated sorted array of distinct elements, at least one half of any subarray split by the midpoint is always strictly ordered. Identify the ordered half and check if target falls inside its range.",
        why_optimal_template="Linear scanning inspects all n elements taking O(n) time, while modified binary search halves the search space at each iteration in O(log n) time and O(1) space. On the {case_count} verified test cases, optimal search ran in {optimal_ms:.2f} ms versus {brute_ms:.2f} ms for brute force.",
        pitfalls="Remember to check inclusive bounds (e.g. nums[low] <= target && target < nums[mid]) when confirming if target lies in the sorted half.",
        reading_links=["https://en.wikipedia.org/wiki/Binary_search_algorithm"],
        hints=[
            "Even after rotation, dividing the array at any midpoint leaves at least one half strictly sorted.",
            "Check if nums[low] <= nums[mid] to determine whether the left half is normally sorted. If not, the right half must be sorted.",
            "If the target lies within the boundaries of the sorted half, narrow your binary search there; otherwise, search the opposite half.",
        ],
    ),
    ProblemBundle(
        spec=spec_find_min,
        py_brute_code=py_brute_find_min,
        py_brute_complexity="Time: O(n) | Space: O(1)",
        py_optimal_code=py_optimal_find_min,
        py_optimal_complexity="Time: O(log n) | Space: O(1)",
        input_generator=_gen_find_min_inputs,
        examples=[
            {
                "input": "nums = [3, 4, 5, 1, 2]",
                "output": "1",
                "explanation": "The original sorted array was [1, 2, 3, 4, 5] rotated 3 positions, giving minimum element 1.",
            },
            {
                "input": "nums = [4, 5, 6, 7, 0, 1, 2]",
                "output": "0",
                "explanation": "The inflection point contains 0 at index 4, which is the global minimum.",
            },
            {
                "input": "nums = [11, 13, 15, 17]",
                "output": "11",
                "explanation": "The array is completely unrotated (rotated 4 times), so the minimum is the first element.",
            },
        ],
        approach="Binary search for the inflection point by comparing the midpoint with the rightmost boundary nums[high]. If nums[mid] > nums[high], the minimum must lie strictly to the right.",
        why_optimal_template="Linear scanning requires O(n) comparisons, while binary search converges to the inflection point in O(log n) time and O(1) space. On the {case_count} verified test cases, the optimal search finished in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for brute force.",
        pitfalls="Set high = mid (not mid - 1) when nums[mid] <= nums[high], because mid itself could be the minimum element.",
        reading_links=["https://en.wikipedia.org/wiki/Binary_search_algorithm"],
        hints=[
            "Compare the middle element with the rightmost element nums[high].",
            "If nums[mid] > nums[high], the inflection point (and thus the minimum) must lie strictly to the right of mid.",
            "If nums[mid] <= nums[high], the minimum is either at mid or to its left; set high = mid.",
        ],
    ),
    ProblemBundle(
        spec=spec_search_2d,
        py_brute_code=py_brute_search_2d,
        py_brute_complexity="Time: O(m · n) | Space: O(1)",
        py_optimal_code=py_optimal_search_2d,
        py_optimal_complexity="Time: O(log(m · n)) | Space: O(1)",
        input_generator=_gen_search_2d_inputs,
        examples=[
            {
                "input": "matrix = [[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], target = 3",
                "output": "true",
                "explanation": "Target 3 exists at row 0, column 1.",
            },
            {
                "input": "matrix = [[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], target = 13",
                "output": "false",
                "explanation": "13 is not present anywhere in the matrix.",
            },
            {
                "input": "matrix = [[1]], target = 1",
                "output": "true",
                "explanation": "A 1x1 matrix containing exactly the searched value.",
            },
        ],
        approach="Treat the m x n grid as a virtual flattened 1D array of length m * n. Convert a 1D index to matrix coordinates via r = Math.floor(idx / n) and c = idx % n, then apply standard binary search.",
        why_optimal_template="Scanning all matrix cells takes O(m · n) time, whereas binary searching the flattened index takes O(log(m · n)) time and O(1) space. On the {case_count} verified test cases, optimal binary search completed in {optimal_ms:.2f} ms versus {brute_ms:.2f} ms for brute force.",
        pitfalls="Be careful to divide and modulo by the column count n (not row count m) when mapping 1D indices to 2D coordinates.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Binary_search_algorithm",
            "https://en.wikipedia.org/wiki/Row-_and_column-major_order",
        ],
        hints=[
            "Because the first element of each row exceeds the last element of the preceding row, the entire matrix behaves like a single sorted 1D array.",
            "A 1D index idx in range 0 <= idx < m * n maps to matrix coordinates row = Math.floor(idx / n) and col = idx % n.",
            "Perform standard binary search over the range [0, m * n - 1] using this coordinate mapping.",
        ],
    ),
    ProblemBundle(
        spec=spec_insert_interval,
        py_brute_code=py_brute_insert_interval,
        py_brute_complexity="Time: O(n log n) | Space: O(n)",
        py_optimal_code=py_optimal_insert_interval,
        py_optimal_complexity="Time: O(n) | Space: O(n)",
        input_generator=_gen_insert_interval_inputs,
        examples=[
            {
                "input": "intervals = [[1, 3], [6, 9]], newInterval = [2, 5]",
                "output": "[[1, 5], [6, 9]]",
                "explanation": "The interval [2, 5] overlaps with [1, 3], merging them into [1, 5].",
            },
            {
                "input": "intervals = [[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], newInterval = [4, 8]",
                "output": "[[1, 2], [3, 10], [12, 16]]",
                "explanation": "[4, 8] overlaps with [3, 5], [6, 7], and [8, 10], combining all four into a single merged interval [3, 10].",
            },
            {
                "input": "intervals = [], newInterval = [5, 7]",
                "output": "[[5, 7]]",
                "explanation": "Inserting into an empty interval list returns a list containing only newInterval.",
            },
        ],
        approach="Scan the sorted intervals in three consecutive phases: collect all intervals ending before newInterval, merge all intervals overlapping with newInterval, and append all intervals starting after newInterval.",
        why_optimal_template="Appending and sorting from scratch takes O(n log n) time, whereas a single three-phase linear pass exploits the pre-sorted input to finish in O(n) time and O(n) space. Across {case_count} verified test cases, the optimal linear pass took {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for sorting.",
        pitfalls="Update newInterval's start and end boundaries cumulatively while iterating through all overlapping candidates.",
        reading_links=["https://en.wikipedia.org/wiki/Interval_(mathematics)"],
        hints=[
            "Partition the process into three distinct phases: intervals ending before newInterval starts, intervals overlapping with newInterval, and intervals starting after newInterval ends.",
            "For any interval that overlaps with newInterval, update newInterval's start to the minimum of both starts and its end to the maximum of both ends.",
            "Push the merged newInterval into your result list once all overlapping intervals are processed, then append the remaining trailing intervals.",
        ],
    ),
    ProblemBundle(
        spec=spec_erase_overlap,
        py_brute_code=py_brute_erase_overlap,
        py_brute_complexity="Time: O(n²) | Space: O(n)",
        py_optimal_code=py_optimal_erase_overlap,
        py_optimal_complexity="Time: O(n log n) | Space: O(n)",
        input_generator=_gen_erase_overlap_inputs,
        examples=[
            {
                "input": "intervals = [[1, 2], [2, 3], [3, 4], [1, 3]]",
                "output": "1",
                "explanation": "Removing interval [1, 3] leaves [[1, 2], [2, 3], [3, 4]], which are all mutually non-overlapping.",
            },
            {
                "input": "intervals = [[1, 2], [1, 2], [1, 2]]",
                "output": "2",
                "explanation": "Two identical copies must be eliminated so that no overlaps remain.",
            },
            {
                "input": "intervals = [[1, 2], [2, 3]]",
                "output": "0",
                "explanation": "Intervals that touch at endpoint 2 are non-overlapping by definition, requiring 0 removals.",
            },
        ],
        approach="Sort intervals by their ending times ascending. Greedily keep intervals that finish earliest to leave maximum remaining time for subsequent intervals, incrementing the removal count whenever an overlap occurs.",
        why_optimal_template="Dynamic programming over sorted intervals takes O(n²) time, whereas greedy interval scheduling by end time runs in O(n log n) time and O(n) space. Across {case_count} verified test cases, optimal greedy selection executed in {optimal_ms:.2f} ms versus {brute_ms:.2f} ms for the quadratic approach.",
        pitfalls="Remember that touching boundaries (e.g. [1, 2] and [2, 3]) do not conflict; only strictly overlapping intervals (start < prevEnd) should be counted for removal.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Interval_scheduling",
            "https://en.wikipedia.org/wiki/Greedy_algorithm",
        ],
        hints=[
            "Finding the minimum number of intervals to remove is equivalent to finding the maximum number of mutually non-overlapping intervals you can keep.",
            "This is classic interval scheduling: sort intervals by their ending times.",
            "Always pick the interval that finishes earliest to leave as much room as possible for future intervals.",
        ],
    ),
    ProblemBundle(
        spec=spec_meeting_rooms,
        py_brute_code=py_brute_meeting_rooms,
        py_brute_complexity="Time: O(n²) | Space: O(1)",
        py_optimal_code=py_optimal_meeting_rooms,
        py_optimal_complexity="Time: O(n log n) | Space: O(n)",
        input_generator=_gen_meeting_rooms_inputs,
        examples=[
            {
                "input": "intervals = [[0, 30], [5, 10], [15, 20]]",
                "output": "false",
                "explanation": "Meeting [0, 30] overlaps with both [5, 10] and [15, 20], making it impossible for one person to attend all.",
            },
            {
                "input": "intervals = [[7, 10], [2, 4]]",
                "output": "true",
                "explanation": "Sorting reveals disjoint meetings [[2, 4], [7, 10]] with no conflict.",
            },
            {
                "input": "intervals = [[0, 5], [5, 10]]",
                "output": "true",
                "explanation": "Meetings touch at time 5, which is permitted as non-overlapping.",
            },
        ],
        approach="Sort meetings by start time. Then scan adjacent pairs to verify that no meeting begins before the prior meeting has completed.",
        why_optimal_template="Pairwise all-pairs collision checking takes O(n²) time, whereas sorting followed by an adjacent-neighbor scan runs in O(n log n) time and O(n) auxiliary space. On {case_count} verified test cases, the sorted scan executed in {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for pairwise checking.",
        pitfalls="Touching endpoints (start[i] === end[i-1]) are valid and do not cause a collision. Handle empty arrays gracefully.",
        reading_links=[
            "https://en.wikipedia.org/wiki/Interval_(mathematics)",
            "https://en.wikipedia.org/wiki/Sorting_algorithm",
        ],
        hints=[
            "Two meetings [s1, e1] and [s2, e2] conflict if and only if they strictly overlap in time: Math.max(s1, s2) < Math.min(e1, e2).",
            "Sorting meetings by their start times allows you to verify conflicts simply by checking adjacent pairs.",
            "If any meeting starts before the previous meeting finishes (start[i] < end[i - 1]), attendance is impossible.",
        ],
    ),
    ProblemBundle(
        spec=spec_binary_search,
        py_brute_code=py_brute_binary_search,
        py_brute_complexity="Time: O(n) | Space: O(1)",
        py_optimal_code=py_optimal_binary_search,
        py_optimal_complexity="Time: O(log n) | Space: O(1)",
        input_generator=_gen_binary_search_inputs,
        examples=[
            {
                "input": "nums = [-1, 0, 3, 5, 9, 12], target = 9",
                "output": "4",
                "explanation": "9 exists in nums and its index is 4.",
            },
            {
                "input": "nums = [-1, 0, 3, 5, 9, 12], target = 2",
                "output": "-1",
                "explanation": "2 does not exist in nums so -1 is returned.",
            },
            {
                "input": "nums = [5], target = 5",
                "output": "0",
                "explanation": "Single-element array where the only element matches target.",
            },
        ],
        approach="Maintain left and right boundary pointers. In each iteration, evaluate the middle element and discard the half that cannot contain target.",
        why_optimal_template="Linear search takes O(n) time, whereas classic binary search halves the search space at each comparison, achieving O(log n) time and O(1) space. On {case_count} verified test cases, binary search took {optimal_ms:.2f} ms compared to {brute_ms:.2f} ms for linear search.",
        pitfalls="Use left <= right in the while loop condition so single-element ranges are properly checked.",
        reading_links=["https://en.wikipedia.org/wiki/Binary_search_algorithm"],
        hints=[
            "Initialize two pointers left = 0 and right = nums.length - 1 spanning the array.",
            "Examine the middle element: if nums[mid] === target, return mid.",
            "If nums[mid] < target, discard the left half by setting left = mid + 1; otherwise set right = mid - 1.",
        ],
    ),
    ProblemBundle(
        spec=spec_search_insert,
        py_brute_code=py_brute_search_insert,
        py_brute_complexity="Time: O(n) | Space: O(1)",
        py_optimal_code=py_optimal_search_insert,
        py_optimal_complexity="Time: O(log n) | Space: O(1)",
        input_generator=_gen_search_insert_inputs,
        examples=[
            {
                "input": "nums = [1, 3, 5, 6], target = 5",
                "output": "2",
                "explanation": "5 is found at index 2.",
            },
            {
                "input": "nums = [1, 3, 5, 6], target = 2",
                "output": "1",
                "explanation": "2 is not present; inserting at index 1 maintains ascending order: [1, 2, 3, 5, 6].",
            },
            {
                "input": "nums = [1, 3, 5, 6], target = 7",
                "output": "4",
                "explanation": "7 is greater than all elements, so it should be appended at index 4.",
            },
        ],
        approach="Perform binary search for the lower bound: the first element with value greater than or equal to target. If the value is absent, pointer left settles at the exact insertion index.",
        why_optimal_template="Linear scan checks every element in O(n) time, while binary search finds the insertion index in O(log n) time and O(1) space. Across {case_count} verified test cases, binary search executed in {optimal_ms:.2f} ms versus {brute_ms:.2f} ms for linear scanning.",
        pitfalls="When target exceeds all elements in the array, pointer left correctly ends at nums.length.",
        reading_links=["https://en.wikipedia.org/wiki/Binary_search_algorithm"],
        hints=[
            "This is equivalent to finding the lower bound: the first index i such that nums[i] >= target.",
            "When the binary search loop terminates with left > right, the left pointer points precisely to the correct insertion position.",
            "If all elements are smaller than target, left will naturally advance to nums.length.",
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
        raise ValueError(f"JS Brute Force failed for {spec.slug}: {js_brute_res.compile_output}")

    # 2. Run JS Optimal
    js_optimal_res = await _execute("javascript", spec.optimal.code, spec.function_name, copy.deepcopy(test_cases), spec.time_limit_ms)
    if js_optimal_res.verdict != "AC":
        raise ValueError(f"JS Optimal failed for {spec.slug}: {js_optimal_res.compile_output}")

    # 3. Run Python Brute Force
    py_brute_res = await _execute("python", bundle.py_brute_code, spec.function_name, copy.deepcopy(test_cases), spec.time_limit_ms)
    if py_brute_res.verdict != "AC":
        raise ValueError(f"Py Brute Force failed for {spec.slug}: {py_brute_res.compile_output}")

    # 4. Run Python Optimal
    py_optimal_res = await _execute("python", bundle.py_optimal_code, spec.function_name, copy.deepcopy(test_cases), spec.time_limit_ms)
    if py_optimal_res.verdict != "AC":
        raise ValueError(f"Py Optimal failed for {spec.slug}: {py_optimal_res.compile_output}")

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
    print(f"Authoring and verifying {len(BUNDLES)} Batch-3A problems with PAF...")
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
    print("\nAll 9 Batch-3A problems generated and PAF-verified successfully.")


if __name__ == "__main__":
    asyncio.run(main())
