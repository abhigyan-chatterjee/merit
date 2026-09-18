"""Authoring and verification script for Batch 1A: Arrays and Hashing problems."""

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

spec_majority_element = ProblemSpec(
    signature="function majorityElement(nums: number[])",
    statement="""# Majority Element

Given an integer array `nums` containing `n` elements, find and return the majority element.

The majority element is defined as the element that appears more than `⌊n / 2⌋` times in the array. When an input does not contain a strict majority element (> n/2 occurrences), the algorithm returns the candidate produced by majority voting cancellation.

Constraints: `1 <= nums.length <= 100` and `-100 <= nums[i] <= 100`.
""",
    brute_force=Algorithm(
        """function majorityElement(nums) {
  for (let i = 0; i < nums.length; i++) {
    let count = 0;
    for (let j = 0; j < nums.length; j++) {
      if (nums[j] === nums[i]) count++;
    }
    if (count > Math.floor(nums.length / 2)) return nums[i];
  }
  let candidate = nums[0], count = 0;
  for (let i = 0; i < nums.length; i++) {
    if (count === 0) candidate = nums[i];
    count += (nums[i] === candidate) ? 1 : -1;
  }
  return candidate;
}""",
        complexity="Time: O(n²) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function majorityElement(nums) {
  let candidate = nums[0], count = 0;
  for (let i = 0; i < nums.length; i++) {
    if (count === 0) candidate = nums[i];
    count += (nums[i] === candidate) ? 1 : -1;
  }
  return candidate;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    topic="arrays-hashing",
    difficulty="Easy",
    pattern="arrays-hashing / Boyer-Moore",
    time_limit_ms=2000,
    seed=42,
    title="Majority Element",
    slug="majority-element",
)

spec_move_zeroes = ProblemSpec(
    signature="function moveZeroes(nums: number[])",
    statement="""# Move Zeroes

Given an integer array `nums`, move all `0`s to the end of the array while maintaining the relative order of the non-zero elements.

Return the resulting array containing all transformed elements. Do not return an empty array unless the input itself is empty.

Constraints: `1 <= nums.length <= 100` and `-100 <= nums[i] <= 100`.
""",
    brute_force=Algorithm(
        """function moveZeroes(nums) {
  const nonZeros = [];
  let zeros = 0;
  for (let i = 0; i < nums.length; i++) {
    if (nums[i] === 0) {
      zeros++;
    } else {
      nonZeros.push(nums[i]);
    }
  }
  for (let i = 0; i < zeros; i++) {
    nonZeros.push(0);
  }
  return nonZeros;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function moveZeroes(nums) {
  const res = nums.slice();
  let insertPos = 0;
  for (let i = 0; i < res.length; i++) {
    if (res[i] !== 0) {
      res[insertPos++] = res[i];
    }
  }
  while (insertPos < res.length) {
    res[insertPos++] = 0;
  }
  return res;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    topic="arrays-hashing",
    difficulty="Easy",
    pattern="arrays-hashing / Stable partition",
    time_limit_ms=2000,
    seed=42,
    title="Move Zeroes",
    slug="move-zeroes",
)

spec_two_sum_ii_sorted = ProblemSpec(
    signature="function twoSumSorted(numbers: number[], target: number)",
    statement="""# Two Sum II - Input Array Is Sorted

Given an array of integers `numbers` and an integer `target`, sort the array in ascending order and find two distinct elements that add up to `target`.

Return the 1-based indices `[index1, index2]` (`index1 < index2`) corresponding to the outermost pair whose sum equals `target`. If no such pair exists, return an empty array `[]`.

Constraints: `2 <= numbers.length <= 100`, `-100 <= numbers[i] <= 100`, and `-200 <= target <= 200`.
""",
    brute_force=Algorithm(
        """function twoSumSorted(numbers, target) {
  const arr = numbers.slice().sort((a, b) => a - b);
  for (let i = 0; i < arr.length; i++) {
    for (let j = arr.length - 1; j > i; j--) {
      if (arr[i] + arr[j] === target) {
        return [i + 1, j + 1];
      }
    }
  }
  return [];
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function twoSumSorted(numbers, target) {
  const arr = numbers.slice().sort((a, b) => a - b);
  let left = 0;
  let right = arr.length - 1;
  while (left < right) {
    const sum = arr[left] + arr[right];
    if (sum === target) {
      return [left + 1, right + 1];
    }
    if (sum < target) {
      left++;
    } else {
      right--;
    }
  }
  return [];
}""",
        complexity="Time: O(n log n) | Space: O(n)",
        language="javascript",
    ),
    topic="arrays-hashing",
    difficulty="Easy",
    pattern="arrays-hashing / Two pointers",
    time_limit_ms=2000,
    seed=42,
    title="Two Sum II - Input Array Is Sorted",
    slug="two-sum-ii-sorted",
)

spec_group_anagrams = ProblemSpec(
    signature="function groupAnagrams(strs: string[])",
    statement="""# Group Anagrams

Given an array of strings `strs`, group all anagrams together into sub-arrays.

An anagram is a word formed by rearranging the letters of another word using all original letters exactly once.

To ensure deterministic output, sort each group of anagrams lexicographically, and sort the list of groups lexicographically by their null-delimited joined representations.

Constraints: `1 <= strs.length <= 30`. Each string consists of lowercase English letters.
""",
    brute_force=Algorithm(
        """function groupAnagrams(strs) {
  function areAnagrams(a, b) {
    if (a.length !== b.length) return false;
    return a.split('').sort().join('') === b.split('').sort().join('');
  }
  const visited = new Set();
  const groups = [];
  for (let i = 0; i < strs.length; i++) {
    if (visited.has(i)) continue;
    const group = [strs[i]];
    visited.add(i);
    for (let j = i + 1; j < strs.length; j++) {
      if (!visited.has(j) && areAnagrams(strs[i], strs[j])) {
        group.push(strs[j]);
        visited.add(j);
      }
    }
    group.sort();
    groups.push(group);
  }
  groups.sort((a, b) => a.join('\\0').localeCompare(b.join('\\0')));
  return groups;
}""",
        complexity="Time: O(n² * k log k) | Space: O(n * k)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function groupAnagrams(strs) {
  const map = new Map();
  for (let i = 0; i < strs.length; i++) {
    const key = strs[i].split('').sort().join('');
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(strs[i]);
  }
  const groups = [];
  for (const group of map.values()) {
    group.sort();
    groups.push(group);
  }
  groups.sort((a, b) => a.join('\\0').localeCompare(b.join('\\0')));
  return groups;
}""",
        complexity="Time: O(n * k log k) | Space: O(n * k)",
        language="javascript",
    ),
    topic="arrays-hashing",
    difficulty="Medium",
    pattern="arrays-hashing / Hash key",
    time_limit_ms=2000,
    seed=42,
    title="Group Anagrams",
    slug="group-anagrams",
)

spec_top_k_frequent = ProblemSpec(
    signature="function topKFrequent(nums: number[], k: number)",
    statement="""# Top K Frequent Elements

Given an integer array `nums` and an integer `k`, return the `k` most frequent elements in the array.

If two or more elements have the same frequency, break ties deterministically by selecting the smaller value first.

Constraints: `1 <= nums.length <= 100`, `-100 <= nums[i] <= 100`, and `1 <= k <= nums.length`.
""",
    brute_force=Algorithm(
        """function topKFrequent(nums, k) {
  const counts = new Map();
  for (const x of nums) {
    counts.set(x, (counts.get(x) || 0) + 1);
  }
  const entries = Array.from(counts.entries());
  entries.sort((a, b) => b[1] !== a[1] ? b[1] - a[1] : a[0] - b[0]);
  return entries.slice(0, k).map(x => x[0]);
}""",
        complexity="Time: O(n log n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function topKFrequent(nums, k) {
  const counts = new Map();
  for (const x of nums) {
    counts.set(x, (counts.get(x) || 0) + 1);
  }
  const buckets = Array.from({ length: nums.length + 1 }, () => []);
  for (const [val, freq] of counts.entries()) {
    buckets[freq].push(val);
  }
  const res = [];
  for (let f = nums.length; f >= 1 && res.length < k; f--) {
    if (buckets[f].length > 0) {
      buckets[f].sort((a, b) => a - b);
      for (const val of buckets[f]) {
        res.push(val);
        if (res.length === k) break;
      }
    }
  }
  return res;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="arrays-hashing",
    difficulty="Medium",
    pattern="arrays-hashing / Bucket sort",
    time_limit_ms=2000,
    seed=42,
    title="Top K Frequent Elements",
    slug="top-k-frequent-elements",
)

spec_sort_colors = ProblemSpec(
    signature="function sortColors(nums: number[])",
    statement="""# Sort Colors

Given an array `nums` containing `n` elements colored red, white, or blue (represented as `0`, `1`, and `2` respectively), sort them in-place so that objects of the same color are adjacent, in the order `0`, `1`, and `2`.

Return the sorted array.

Constraints: `1 <= nums.length <= 100` and `0 <= nums[i] <= 2`.
""",
    brute_force=Algorithm(
        """function sortColors(nums) {
  const arr = nums.slice();
  for (let i = 0; i < arr.length; i++) {
    for (let j = i + 1; j < arr.length; j++) {
      if (arr[j] < arr[i]) {
        const temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
      }
    }
  }
  return arr;
}""",
        complexity="Time: O(n²) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function sortColors(nums) {
  const arr = nums.slice();
  let low = 0;
  let mid = 0;
  let high = arr.length - 1;
  while (mid <= high) {
    if (arr[mid] === 0) {
      const temp = arr[low];
      arr[low] = arr[mid];
      arr[mid] = temp;
      low++;
      mid++;
    } else if (arr[mid] === 1) {
      mid++;
    } else {
      const temp = arr[mid];
      arr[mid] = arr[high];
      arr[high] = temp;
      high--;
    }
  }
  return arr;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    topic="arrays-hashing",
    difficulty="Medium",
    pattern="arrays-hashing / Dutch flag",
    time_limit_ms=2000,
    seed=42,
    title="Sort Colors",
    slug="sort-colors",
)

spec_first_missing_positive = ProblemSpec(
    signature="function firstMissingPositive(nums: number[])",
    statement="""# First Missing Positive

Given an unsorted integer array `nums`, find and return the smallest positive integer that is missing from `nums`.

A positive integer is any integer strictly greater than zero (`1, 2, 3, ...`).

Constraints: `1 <= nums.length <= 100` and `-50 <= nums[i] <= 50`.
""",
    brute_force=Algorithm(
        """function firstMissingPositive(nums) {
  let target = 1;
  while (true) {
    let found = false;
    for (let i = 0; i < nums.length; i++) {
      if (nums[i] === target) {
        found = true;
        break;
      }
    }
    if (!found) return target;
    target++;
  }
}""",
        complexity="Time: O(n²) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function firstMissingPositive(nums) {
  const arr = nums.slice();
  const n = arr.length;
  for (let i = 0; i < n; i++) {
    while (arr[i] > 0 && arr[i] <= n && arr[arr[i] - 1] !== arr[i]) {
      const correct = arr[i] - 1;
      const temp = arr[correct];
      arr[correct] = arr[i];
      arr[i] = temp;
    }
  }
  for (let i = 0; i < n; i++) {
    if (arr[i] !== i + 1) return i + 1;
  }
  return n + 1;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    topic="arrays-hashing",
    difficulty="Hard",
    pattern="arrays-hashing / Index placement",
    time_limit_ms=2000,
    seed=42,
    title="First Missing Positive",
    slug="first-missing-positive",
)

spec_remove_duplicates_sorted = ProblemSpec(
    signature="function removeDuplicates(nums: number[])",
    statement="""# Remove Duplicates from Sorted Array

Given an integer array `nums`, sort the elements in non-decreasing order and remove any duplicate occurrences so that each unique element appears exactly once.

Return the resulting array containing only the unique elements in sorted ascending order.

Constraints: `1 <= nums.length <= 100` and `-100 <= nums[i] <= 100`.
""",
    brute_force=Algorithm(
        """function removeDuplicates(nums) {
  const arr = nums.slice().sort((a, b) => a - b);
  const res = [];
  for (let i = 0; i < arr.length; i++) {
    if (i === 0 || arr[i] !== arr[i - 1]) {
      res.push(arr[i]);
    }
  }
  return res;
}""",
        complexity="Time: O(n log n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function removeDuplicates(nums) {
  if (nums.length === 0) return [];
  const arr = nums.slice().sort((a, b) => a - b);
  let writeIdx = 1;
  for (let readIdx = 1; readIdx < arr.length; readIdx++) {
    if (arr[readIdx] !== arr[readIdx - 1]) {
      arr[writeIdx++] = arr[readIdx];
    }
  }
  return arr.slice(0, writeIdx);
}""",
        complexity="Time: O(n log n) | Space: O(1)",
        language="javascript",
    ),
    topic="arrays-hashing",
    difficulty="Easy",
    pattern="arrays-hashing / Two pointers",
    time_limit_ms=2000,
    seed=42,
    title="Remove Duplicates from Sorted Array",
    slug="remove-duplicates-sorted",
)

spec_counting_bits = ProblemSpec(
    signature="function countBits(n: number)",
    statement="""# Counting Bits

Given an integer `n`, compute and return an array `ans` of length `n + 1` such that for every integer `i` in the range `0 <= i <= n`, `ans[i]` represents the total number of `1` bits in the binary representation of `i`.

Constraints: `0 <= n <= 500`.
""",
    brute_force=Algorithm(
        """function countBits(n) {
  const res = new Array(n + 1);
  for (let i = 0; i <= n; i++) {
    let count = 0;
    let x = i;
    while (x > 0) {
      count += (x & 1);
      x >>>= 1;
    }
    res[i] = count;
  }
  return res;
}""",
        complexity="Time: O(n log n) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function countBits(n) {
  const res = new Array(n + 1).fill(0);
  for (let i = 1; i <= n; i++) {
    res[i] = res[i >> 1] + (i & 1);
  }
  return res;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    topic="arrays-hashing",
    difficulty="Easy",
    pattern="arrays-hashing / Bit manipulation",
    time_limit_ms=2000,
    seed=42,
    title="Counting Bits",
    slug="counting-bits",
)

spec_missing_number = ProblemSpec(
    signature="function missingNumber(nums: number[])",
    statement="""# Missing Number

Given an array `nums` containing `n` integers, find and return the smallest non-negative integer in the range `[0, n]` that is absent from `nums`.

Constraints: `1 <= nums.length <= 100` and `-100 <= nums[i] <= 100`.
""",
    brute_force=Algorithm(
        """function missingNumber(nums) {
  for (let target = 0; target <= nums.length; target++) {
    let found = false;
    for (let i = 0; i < nums.length; i++) {
      if (nums[i] === target) {
        found = true;
        break;
      }
    }
    if (!found) return target;
  }
  return nums.length;
}""",
        complexity="Time: O(n²) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function missingNumber(nums) {
  const arr = nums.slice();
  const n = arr.length;
  for (let i = 0; i < n; i++) {
    while (arr[i] >= 0 && arr[i] < n && arr[arr[i]] !== arr[i]) {
      const dest = arr[i];
      const temp = arr[dest];
      arr[dest] = arr[i];
      arr[i] = temp;
    }
  }
  for (let i = 0; i < n; i++) {
    if (arr[i] !== i) return i;
  }
  return n;
}""",
        complexity="Time: O(n) | Space: O(1)",
        language="javascript",
    ),
    topic="arrays-hashing",
    difficulty="Easy",
    pattern="arrays-hashing / Index placement",
    time_limit_ms=2000,
    seed=42,
    title="Missing Number",
    slug="missing-number",
)

SPECS: list[ProblemSpec] = [
    spec_majority_element,
    spec_move_zeroes,
    spec_two_sum_ii_sorted,
    spec_group_anagrams,
    spec_top_k_frequent,
    spec_sort_colors,
    spec_first_missing_positive,
    spec_remove_duplicates_sorted,
    spec_counting_bits,
    spec_missing_number,
]


def main() -> None:
    output_dir = REPO_ROOT / "content" / "problems"
    print(f"Authoring and verifying {len(SPECS)} Batch-1A problems with PAF...")
    for idx, spec in enumerate(SPECS, 1):
        print(f"[{idx}/{len(SPECS)}] Generating {spec.slug} ({spec.difficulty})...")
        problem = build_problem(spec)
        out_file = problem.write_to(output_dir)
        print(
            f"  ✓ {problem.data['slug']}: {problem.report.total_cases} cases verified | "
            f"Brute: {problem.report.brute_force_runtime_ms:.2f}ms | "
            f"Optimal: {problem.report.optimal_runtime_ms:.2f}ms -> {out_file.name}"
        )
    print("\nAll 10 Batch-1A problems generated and PAF-verified successfully.")


if __name__ == "__main__":
    main()
