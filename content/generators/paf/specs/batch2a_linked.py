"""Authoring and verification script for Batch 2A: Linked List problems (array-formulated)."""

from __future__ import annotations

import asyncio
import copy
import json
import random
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
api_path = str(REPO_ROOT / "apps" / "api")
if api_path not in sys.path:
    sys.path.insert(0, api_path)

from app.services.judge import execute_code
from content.generators.paf.spec import (
    Algorithm,
    GeneratedProblem,
    ProblemSpec,
    ValidationReport,
)

# -----------------------------------------------------------------------------
# 1. Problem Specifications (JavaScript Brute & Optimal)
# -----------------------------------------------------------------------------

spec_reorder_list = ProblemSpec(
    signature="function reorderList(nums: number[])",
    statement="""# Reorder List

You are given an array of integers `nums` representing the node values of a singly linked list in sequence: `[L_0, L_1, ..., L_{n-1}]`.

Reorder the list such that the elements follow the interwoven fold pattern:
`[L_0, L_{n-1}, L_1, L_{n-2}, L_2, L_{n-3}, ...]`

You must construct and return the reordered list of values.

Constraints: `0 <= nums.length <= 100` and `-1000 <= nums[i] <= 1000`.
""",
    brute_force=Algorithm(
        """function reorderList(nums) {
  if (nums.length <= 2) return nums.slice();
  const queue = nums.slice();
  const result = [];
  let fromStart = true;
  while (queue.length > 0) {
    if (fromStart) {
      result.push(queue.shift());
    } else {
      result.push(queue.pop());
    }
    fromStart = !fromStart;
  }
  return result;
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function reorderList(nums) {
  const n = nums.length;
  if (n <= 2) return nums.slice();
  const result = new Array(n);
  let left = 0;
  let right = n - 1;
  let idx = 0;
  while (left <= right) {
    if (left === right) {
      result[idx++] = nums[left++];
    } else {
      result[idx++] = nums[left++];
      result[idx++] = nums[right--];
    }
  }
  return result;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="linked-lists",
    difficulty="Medium",
    pattern="linked-list / Fold ends",
    time_limit_ms=2000,
    seed=42,
    title="Reorder List",
    slug="reorder-list",
    editorial={
        "approach": "Traverse the sequence from both extremities inwards using two pointers, taking one element from the front and one from the back alternately until all elements are collected.",
        "why_optimal": "Single linear pass O(n) time and O(n) auxiliary space to construct the result.",
        "pitfalls": "Handle odd-length arrays carefully so the central element is appended exactly once without duplicate index access.",
    },
    reading_links=[
        "https://en.wikipedia.org/wiki/Linked_list",
        "https://visualgo.net/en/list",
    ],
    hints=[
        "Notice that the resulting sequence alternates taking elements from the beginning and the end of the original list.",
        "A two-pointer approach with pointers at the front and back can alternate selecting elements until they meet in the middle.",
        "For an odd number of elements, ensure the middle element is appended once both pointers coincide.",
    ],
)

spec_rotate_list = ProblemSpec(
    signature="function rotateRight(nums: number[], k: number)",
    statement="""# Rotate List

You are given an integer array `nums` representing the sequence of values in a singly linked list, and a non-negative integer `k`.

Rotate the list to the right by `k` places. In each rotation step, the last element moves to the very front of the list, shifting all other elements one position to the right.

Return the list of values after applying the `k` rotations.

Constraints: `0 <= nums.length <= 100`, `0 <= k <= 1000`, and `-1000 <= nums[i] <= 1000`.
""",
    brute_force=Algorithm(
        """function rotateRight(nums, k) {
  if (nums.length <= 1 || k === 0) return nums.slice();
  const arr = nums.slice();
  const effectiveK = k % arr.length;
  for (let step = 0; step < effectiveK; step++) {
    const last = arr.pop();
    arr.unshift(last);
  }
  return arr;
}""",
        complexity="Time: O(n · (k mod n)) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function rotateRight(nums, k) {
  const n = nums.length;
  if (n <= 1) return nums.slice();
  const effectiveK = k % n;
  if (effectiveK === 0) return nums.slice();
  const splitIdx = n - effectiveK;
  return nums.slice(splitIdx).concat(nums.slice(0, splitIdx));
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="linked-lists",
    difficulty="Medium",
    pattern="linked-list / Rotation",
    time_limit_ms=2000,
    seed=42,
    title="Rotate List",
    slug="rotate-list",
    editorial={
        "approach": "Compute effective rotations using modulo arithmetic k % n. Split the array at n - (k % n) and concatenate the two segments.",
        "why_optimal": "Direct slice and concatenation runs in O(n) time, whereas repeatedly rotating one step at a time costs O(n · (k mod n)).",
        "pitfalls": "Handle division by zero when the input list is empty (nums.length === 0), and handle k % n === 0 where no movement is required.",
    },
    reading_links=[
        "https://en.wikipedia.org/wiki/Circular_buffer",
        "https://visualgo.net/en/list",
    ],
    hints=[
        "When k is greater than or equal to the length of the list, rotating length times returns the list to its starting configuration.",
        "Compute the effective shift as k % nums.length to avoid unnecessary full rotations.",
        "The last effective_k elements become the prefix, and the preceding elements become the suffix.",
    ],
)

spec_swap_pairs = ProblemSpec(
    signature="function swapPairs(nums: number[])",
    statement="""# Swap Nodes in Pairs

You are given an integer array `nums` representing the node values of a singly linked list in sequence.

Swap every two adjacent nodes from left to right. If the total number of elements is odd, the final lone element should remain in its original position.

Return the modified sequence of node values after performing the swaps.

Constraints: `0 <= nums.length <= 100` and `-1000 <= nums[i] <= 1000`.
""",
    brute_force=Algorithm(
        """function swapPairs(nums) {
  if (nums.length <= 1) return nums.slice();
  function swapHelper(arr, i) {
    if (i >= arr.length - 1) return arr.slice(i);
    const pair = [arr[i + 1], arr[i]];
    return pair.concat(swapHelper(arr, i + 2));
  }
  return swapHelper(nums, 0);
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function swapPairs(nums) {
  const result = nums.slice();
  for (let i = 0; i < result.length - 1; i += 2) {
    const temp = result[i];
    result[i] = result[i + 1];
    result[i + 1] = temp;
  }
  return result;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="linked-lists",
    difficulty="Medium",
    pattern="linked-list / Adjacent swap",
    time_limit_ms=2000,
    seed=42,
    title="Swap Nodes in Pairs",
    slug="swap-nodes-in-pairs",
    editorial={
        "approach": "Iterate across the array in strides of 2, swapping adjacent elements nums[i] and nums[i+1] in-place.",
        "why_optimal": "Requires a single linear scan O(n) time and O(n) space to return the swapped array, avoiding recursive call overhead.",
        "pitfalls": "Ensure loop bounds check i < length - 1 to prevent out-of-bounds access when length is odd.",
    },
    reading_links=[
        "https://en.wikipedia.org/wiki/Linked_list",
        "https://visualgo.net/en/list",
    ],
    hints=[
        "Iterate through the array with a step size of 2.",
        "At each step i, swap the elements at index i and i + 1 if i + 1 < length.",
        "If the array length is odd, the final element has no pair and remains unaffected.",
    ],
)

spec_reverse_k_group = ProblemSpec(
    signature="function reverseKGroup(nums: number[], k: number)",
    statement="""# Reverse Nodes in k-Group

You are given an integer array `nums` representing the node values of a singly linked list in sequence, and a positive integer `k`.

Reverse the nodes of the list `k` at a time from left to right, and return the modified sequence. If the number of nodes remaining at the end is less than `k`, those leftover nodes must remain in their original order.

Constraints: `0 <= nums.length <= 100`, `1 <= k <= 100`, and `-1000 <= nums[i] <= 1000`.
""",
    brute_force=Algorithm(
        """function reverseKGroup(nums, k) {
  if (k <= 1 || nums.length <= 1) return nums.slice();
  const result = [];
  let i = 0;
  while (i < nums.length) {
    if (i + k <= nums.length) {
      const chunk = [];
      for (let j = i; j < i + k; j++) {
        chunk.unshift(nums[j]);
      }
      for (let j = 0; j < chunk.length; j++) {
        result.push(chunk[j]);
      }
    } else {
      for (let j = i; j < nums.length; j++) {
        result.push(nums[j]);
      }
    }
    i += k;
  }
  return result;
}""",
        complexity="Time: O(n · k) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function reverseKGroup(nums, k) {
  if (k <= 1 || nums.length <= 1) return nums.slice();
  const result = nums.slice();
  const n = result.length;
  for (let start = 0; start + k <= n; start += k) {
    let left = start;
    let right = start + k - 1;
    while (left < right) {
      const temp = result[left];
      result[left] = result[right];
      result[right] = temp;
      left++;
      right--;
    }
  }
  return result;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="linked-lists",
    difficulty="Hard",
    pattern="linked-list / Chunk reverse",
    time_limit_ms=2000,
    seed=42,
    title="Reverse Nodes in k-Group",
    slug="reverse-nodes-in-k-group",
    editorial={
        "approach": "Iterate over chunks of size k. For each full chunk of length k, reverse its elements using two pointers. If remaining elements are fewer than k, preserve them as-is.",
        "why_optimal": "Reversing each chunk in-place processes each element at most twice, achieving linear O(n) time and O(n) space.",
        "pitfalls": "Do not reverse the leftover tail when its length is strictly less than k.",
    },
    reading_links=[
        "https://en.wikipedia.org/wiki/Linked_list",
        "https://visualgo.net/en/list",
    ],
    hints=[
        "Determine if at least k elements remain starting from current index i.",
        "If at least k elements exist, reverse that subsegment using two pointers between i and i + k - 1.",
        "If fewer than k elements remain, terminate without altering the remainder.",
    ],
)

spec_partition_list = ProblemSpec(
    signature="function partitionList(nums: number[], x: number)",
    statement="""# Partition List

You are given an integer array `nums` representing the node values of a singly linked list, and a target value `x`.

Partition the list such that all nodes with values strictly less than `x` come before all nodes with values greater than or equal to `x`. You must preserve the original relative order of the nodes in each of the two partitions.

Return the partitioned sequence of node values.

Constraints: `0 <= nums.length <= 100`, `-1000 <= x <= 1000`, and `-1000 <= nums[i] <= 1000`.
""",
    brute_force=Algorithm(
        """function partitionList(nums, x) {
  const less = [];
  const greaterOrEqual = [];
  for (let i = 0; i < nums.length; i++) {
    if (nums[i] < x) {
      less.push(nums[i]);
    } else {
      greaterOrEqual.push(nums[i]);
    }
  }
  const result = [];
  for (let i = 0; i < less.length; i++) result.push(less[i]);
  for (let i = 0; i < greaterOrEqual.length; i++) result.push(greaterOrEqual[i]);
  return result;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function partitionList(nums, x) {
  const n = nums.length;
  if (n <= 1) return nums.slice();
  const less = [];
  const greater = [];
  for (let i = 0; i < n; i++) {
    const val = nums[i];
    if (val < x) {
      less.push(val);
    } else {
      greater.push(val);
    }
  }
  return less.concat(greater);
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="linked-lists",
    difficulty="Medium",
    pattern="linked-list / Stable partition",
    time_limit_ms=2000,
    seed=42,
    title="Partition List",
    slug="partition-list",
    editorial={
        "approach": "Filter or split elements into two partitions based on val < x: one partition for smaller values, one for values greater than or equal to x. Then concatenate them.",
        "why_optimal": "Single linear scan O(n) time and O(n) space guarantees stable relative ordering.",
        "pitfalls": "Strictly less than (< x) versus less than or equal (<= x): nodes equal to x must go into the second partition.",
    },
    reading_links=[
        "https://en.wikipedia.org/wiki/Partition_problem",
        "https://visualgo.net/en/list",
    ],
    hints=[
        "Maintain two separate collections: one for values strictly less than x, and another for values greater than or equal to x.",
        "Traverse the original sequence sequentially so relative order is automatically preserved.",
        "Combine the two collections with the 'less than' group first.",
    ],
)

spec_odd_even = ProblemSpec(
    signature="function oddEvenList(nums: number[])",
    statement="""# Odd Even Linked List

You are given an integer array `nums` representing the node values of a singly linked list in sequence.

Group all nodes at 1-indexed odd positions together first, followed by all nodes at 1-indexed even positions. The relative order within the odd-indexed group and within the even-indexed group must be maintained.

Note that the grouping is based on the 1-indexed position in the sequence, not on the numerical value of the nodes.

Return the reordered sequence of node values.

Constraints: `0 <= nums.length <= 100` and `-1000 <= nums[i] <= 1000`.
""",
    brute_force=Algorithm(
        """function oddEvenList(nums) {
  if (nums.length <= 2) return nums.slice();
  const odds = [];
  const evens = [];
  for (let i = 0; i < nums.length; i++) {
    if ((i + 1) % 2 === 1) {
      odds.push(nums[i]);
    } else {
      evens.push(nums[i]);
    }
  }
  const result = [];
  for (let i = 0; i < odds.length; i++) result.push(odds[i]);
  for (let i = 0; i < evens.length; i++) result.push(evens[i]);
  return result;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function oddEvenList(nums) {
  const n = nums.length;
  if (n <= 2) return nums.slice();
  const result = new Array(n);
  let oddPtr = 0;
  for (let i = 0; i < n; i += 2) {
    result[oddPtr++] = nums[i];
  }
  let evenPtr = oddPtr;
  for (let i = 1; i < n; i += 2) {
    result[evenPtr++] = nums[i];
  }
  return result;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="linked-lists",
    difficulty="Medium",
    pattern="linked-list / Index parity",
    time_limit_ms=2000,
    seed=42,
    title="Odd Even Linked List",
    slug="odd-even-linked-list",
    editorial={
        "approach": "Group elements at 0-indexed even positions (1-indexed odd) and 0-indexed odd positions (1-indexed even), maintaining relative order, then concatenate.",
        "why_optimal": "Preallocated dual-pointer insertion visits each element exactly once in O(n) time and O(n) space.",
        "pitfalls": "Do not confuse value parity with position parity. The condition is based solely on 1-indexed node positions.",
    },
    reading_links=[
        "https://en.wikipedia.org/wiki/Linked_list",
        "https://visualgo.net/en/list",
    ],
    hints=[
        "Remember this reorganizes by index position (1-based), not by whether the values themselves are odd or even.",
        "Elements at indices 0, 2, 4, ... are 1-indexed odds. Elements at indices 1, 3, 5, ... are 1-indexed evens.",
        "You can place odds into one array and evens into another, then join them.",
    ],
)

spec_merge_k_lists = ProblemSpec(
    signature="function mergeKLists(lists: number[][])",
    statement="""# Merge k Sorted Lists

You are given an array of `k` sorted integer arrays `lists`, where each individual array represents a singly linked list sorted in non-decreasing order.

Merge all `k` linked lists into a single consolidated list sorted in non-decreasing order, and return the resulting array.

Constraints: `0 <= lists.length <= 30`, each list satisfies `0 <= lists[i].length <= 50`, and `-1000 <= lists[i][j] <= 1000`.
""",
    brute_force=Algorithm(
        """function mergeKLists(lists) {
  const all = [];
  for (let i = 0; i < lists.length; i++) {
    for (let j = 0; j < lists[i].length; j++) {
      all.push(lists[i][j]);
    }
  }
  all.sort((a, b) => a - b);
  return all;
}""",
        complexity="Time: O(N log N) | Space: O(N)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function mergeKLists(lists) {
  if (lists.length === 0) return [];
  function mergeTwo(a, b) {
    const res = [];
    let i = 0, j = 0;
    while (i < a.length && j < b.length) {
      if (a[i] <= b[j]) {
        res.push(a[i++]);
      } else {
        res.push(b[j++]);
      }
    }
    while (i < a.length) res.push(a[i++]);
    while (j < b.length) res.push(b[j++]);
    return res;
  }
  let current = lists.slice();
  while (current.length > 1) {
    const nextRound = [];
    for (let i = 0; i < current.length; i += 2) {
      if (i + 1 < current.length) {
        nextRound.push(mergeTwo(current[i], current[i + 1]));
      } else {
        nextRound.push(current[i]);
      }
    }
    current = nextRound;
  }
  return current[0];
}""",
        complexity="Time: O(N log k) | Space: O(N)",
        language="javascript",
    ),
    topic="linked-lists",
    difficulty="Hard",
    pattern="linked-list / Heap merge",
    time_limit_ms=2000,
    seed=42,
    title="Merge k Sorted Lists",
    slug="merge-k-sorted-lists",
    editorial={
        "approach": "Employ divide-and-conquer pairwise list merging or a min-heap tracking the current smallest available element across all k lists.",
        "why_optimal": "Merging k lists of total N elements with divide-and-conquer or heap takes O(N log k) time, superior to flattening and full sorting O(N log N).",
        "pitfalls": "Handle empty outer lists [] as well as inner empty lists [[], [1], []] gracefully.",
    },
    reading_links=[
        "https://en.wikipedia.org/wiki/K-way_merge_algorithm",
        "https://docs.python.org/3/tutorial/datastructures.html",
    ],
    hints=[
        "You can merge lists pairwise using a divide-and-conquer strategy, similar to merge sort.",
        "Alternatively, a min-priority queue (min-heap) holding the heads of each list can repeatedly extract the global minimum in O(log k) time.",
        "Ensure empty lists within lists are handled cleanly without crashing head element access.",
    ],
)

spec_copy_random = ProblemSpec(
    signature="function copyRandomList(nodes: number[][])",
    statement="""# Copy List with Random Pointer

A linked list of length `n` is given such that each node contains an additional random pointer, which could point to any node in the list, or `null`.

In this problem, the linked list is represented as an array of pairs `nodes`, where each entry `nodes[i] = [val, randomIndex]` specifies the `i`-th node:
- `val`: an integer value stored in the node.
- `randomIndex`: the 0-indexed position of the node that the random pointer references, or `-1` if it points to `null`.

Construct and return a deep copy of the list represented in the exact same format `[[val, randomIndex], ...]`. None of the inner pairs or the outer container in the returned copy should share reference identity with the input.

Constraints: `0 <= nodes.length <= 100`, `-1000 <= nodes[i][0] <= 1000`, and each `nodes[i][1]` is either `-1` or satisfies `0 <= nodes[i][1] < nodes.length`.
""",
    brute_force=Algorithm(
        """function copyRandomList(nodes) {
  if (nodes.length === 0) return [];
  const map = new Map();
  for (let i = 0; i < nodes.length; i++) {
    map.set(i, [nodes[i][0], -1]);
  }
  for (let i = 0; i < nodes.length; i++) {
    const rIdx = nodes[i][1];
    if (rIdx !== -1 && map.has(rIdx)) {
      map.get(i)[1] = rIdx;
    }
  }
  const result = [];
  for (let i = 0; i < nodes.length; i++) {
    result.push(map.get(i));
  }
  return result;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function copyRandomList(nodes) {
  const n = nodes.length;
  if (n === 0) return [];
  const copy = new Array(n);
  for (let i = 0; i < n; i++) {
    copy[i] = [nodes[i][0], nodes[i][1]];
  }
  return copy;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="linked-lists",
    difficulty="Medium",
    pattern="linked-list / Deep copy",
    time_limit_ms=2000,
    seed=42,
    title="Copy List with Random Pointer",
    slug="copy-list-with-random-pointer",
    editorial={
        "approach": "Traverse the sequence, copying each node's value and random index into newly allocated pair arrays without reusing input references.",
        "why_optimal": "Single pass O(n) time and O(n) space creates a full deep clone of the graph structure.",
        "pitfalls": "Do not return shallow slice copies where inner pairs share references with input pairs.",
    },
    reading_links=[
        "https://en.wikipedia.org/wiki/Deep_copy",
        "https://en.wikipedia.org/wiki/Linked_list",
    ],
    hints=[
        "A deep copy requires creating completely new pair instances [val, randomIndex] for each node.",
        "Map original node indices to newly cloned nodes to verify pointers and preserve random index relationships.",
        "Ensure -1 is preserved to represent null random pointers.",
    ],
)

spec_remove_elements = ProblemSpec(
    signature="function removeElements(nums: number[], val: number)",
    statement="""# Remove Linked List Elements

You are given an integer array `nums` representing the sequence of values in a singly linked list, and an integer `val`.

Remove all nodes of the linked list that have value equal to `val`, preserving the relative order of all remaining elements.

Return the filtered sequence of values.

Constraints: `0 <= nums.length <= 100`, `-1000 <= val <= 1000`, and `-1000 <= nums[i] <= 1000`.
""",
    brute_force=Algorithm(
        """function removeElements(nums, val) {
  const result = [];
  for (let i = 0; i < nums.length; i++) {
    if (nums[i] !== val) {
      result.push(nums[i]);
    }
  }
  return result;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function removeElements(nums, val) {
  return nums.filter(x => x !== val);
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="linked-lists",
    difficulty="Easy",
    pattern="linked-list / Filter",
    time_limit_ms=2000,
    seed=42,
    title="Remove Linked List Elements",
    slug="remove-linked-list-elements",
    editorial={
        "approach": "Filter the array by selecting only elements where element !== val.",
        "why_optimal": "Linear O(n) time and O(n) space in a single pass without extra allocations beyond the result.",
        "pitfalls": "Be sure to handle cases where all elements match val (returning empty array) or no elements match (returning identical elements).",
    },
    reading_links=[
        "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array",
        "https://visualgo.net/en/list",
    ],
    hints=[
        "Scan through the array and collect only elements that do not equal val.",
        "Ensure that multiple consecutive matching values (including at the head or tail) are all removed.",
        "If all elements match val, return an empty array.",
    ],
)

spec_reverse_between = ProblemSpec(
    signature="function reverseBetween(nums: number[], left: number, right: number)",
    statement="""# Reverse Linked List II

You are given an integer array `nums` representing the node values of a singly linked list in sequence, and two integers `left` and `right` with `1 <= left <= right <= nums.length`.

Reverse the nodes of the list from 1-indexed position `left` to 1-indexed position `right` (both endpoints inclusive), keeping the rest of the list unchanged.

Return the modified sequence of node values.

Constraints: `1 <= nums.length <= 100`, `1 <= left <= right <= nums.length`, and `-1000 <= nums[i] <= 1000`.
""",
    brute_force=Algorithm(
        """function reverseBetween(nums, left, right) {
  const arr = nums.slice();
  const sub = [];
  for (let i = left - 1; i < right; i++) {
    sub.push(arr[i]);
  }
  sub.reverse();
  for (let i = left - 1; i < right; i++) {
    arr[i] = sub[i - (left - 1)];
  }
  return arr;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function reverseBetween(nums, left, right) {
  const result = nums.slice();
  let l = left - 1;
  let r = right - 1;
  while (l < r) {
    const temp = result[l];
    result[l] = result[r];
    result[r] = temp;
    l++;
    r--;
  }
  return result;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="linked-lists",
    difficulty="Medium",
    pattern="linked-list / Range reverse",
    time_limit_ms=2000,
    seed=42,
    title="Reverse Linked List II",
    slug="reverse-linked-list-ii",
    editorial={
        "approach": "Convert the 1-indexed bounds left and right to 0-indexed bounds left - 1 and right - 1. Reverse the subarray in-place using two converging pointers.",
        "why_optimal": "Reversing only the specified window takes O(right - left) work, bounded by O(n) time and O(n) space.",
        "pitfalls": "1-based indexing off-by-one errors; ensure right endpoint is inclusive.",
    },
    reading_links=[
        "https://en.wikipedia.org/wiki/Linked_list",
        "https://visualgo.net/en/list",
    ],
    hints=[
        "Convert 1-indexed positions left and right to 0-indexed indices: l = left - 1 and r = right - 1.",
        "Only the elements within the range [l, r] need to be reversed; elements before l and after r stay in place.",
        "Use two converging pointers within the subsegment to swap pairs until they meet.",
    ],
)

# -----------------------------------------------------------------------------
# 2. Python Ports (Brute & Optimal)
# -----------------------------------------------------------------------------

PYTHON_SOLUTIONS: dict[str, tuple[str, str, str, str]] = {
    "reorder-list": (
        # brute
        """def reorderList(nums: list[int]) -> list[int]:
    if len(nums) <= 2:
        return list(nums)
    copy = list(nums)
    res = []
    take_left = True
    while copy:
        if take_left:
            res.append(copy.pop(0))
        else:
            res.append(copy.pop())
        take_left = not take_left
    return res
""",
        "Time: O(n²) | Space: O(n)",
        # optimal
        """def reorderList(nums: list[int]) -> list[int]:
    n = len(nums)
    if n <= 2:
        return list(nums)
    res = [0] * n
    left, right = 0, n - 1
    idx = 0
    while left <= right:
        if left == right:
            res[idx] = nums[left]
            left += 1
            idx += 1
        else:
            res[idx] = nums[left]
            res[idx + 1] = nums[right]
            left += 1
            right -= 1
            idx += 2
    return res
""",
        "Time: O(n) | Space: O(n)",
    ),
    "rotate-list": (
        # brute
        """def rotateRight(nums: list[int], k: int) -> list[int]:
    if len(nums) <= 1 or k == 0:
        return list(nums)
    arr = list(nums)
    eff_k = k % len(arr)
    for _ in range(eff_k):
        last = arr.pop()
        arr.insert(0, last)
    return arr
""",
        "Time: O(n · (k mod n)) | Space: O(n)",
        # optimal
        """def rotateRight(nums: list[int], k: int) -> list[int]:
    n = len(nums)
    if n <= 1:
        return list(nums)
    eff_k = k % n
    if eff_k == 0:
        return list(nums)
    split_idx = n - eff_k
    return nums[split_idx:] + nums[:split_idx]
""",
        "Time: O(n) | Space: O(n)",
    ),
    "swap-nodes-in-pairs": (
        # brute
        """def swapPairs(nums: list[int]) -> list[int]:
    if len(nums) <= 1:
        return list(nums)
    def helper(arr: list[int], i: int) -> list[int]:
        if i >= len(arr) - 1:
            return arr[i:]
        pair = [arr[i + 1], arr[i]]
        return pair + helper(arr, i + 2)
    return helper(nums, 0)
""",
        "Time: O(n²) | Space: O(n)",
        # optimal
        """def swapPairs(nums: list[int]) -> list[int]:
    res = list(nums)
    for i in range(0, len(res) - 1, 2):
        res[i], res[i + 1] = res[i + 1], res[i]
    return res
""",
        "Time: O(n) | Space: O(n)",
    ),
    "reverse-nodes-in-k-group": (
        # brute
        """def reverseKGroup(nums: list[int], k: int) -> list[int]:
    if k <= 1 or len(nums) <= 1:
        return list(nums)
    result = []
    i = 0
    while i < len(nums):
        if i + k <= len(nums):
            chunk = []
            for j in range(i, i + k):
                chunk.insert(0, nums[j])
            result.extend(chunk)
        else:
            result.extend(nums[i:])
        i += k
    return result
""",
        "Time: O(n · k) | Space: O(n)",
        # optimal
        """def reverseKGroup(nums: list[int], k: int) -> list[int]:
    if k <= 1 or len(nums) <= 1:
        return list(nums)
    res = list(nums)
    n = len(res)
    for start in range(0, n - k + 1, k):
        left, right = start, start + k - 1
        while left < right:
            res[left], res[right] = res[right], res[left]
            left += 1
            right -= 1
    return res
""",
        "Time: O(n) | Space: O(n)",
    ),
    "partition-list": (
        # brute
        """def partitionList(nums: list[int], x: int) -> list[int]:
    less = []
    greater = []
    for val in nums:
        if val < x:
            less.append(val)
        else:
            greater.append(val)
    res = []
    for val in less:
        res.append(val)
    for val in greater:
        res.append(val)
    return res
""",
        "Time: O(n) | Space: O(n)",
        # optimal
        """def partitionList(nums: list[int], x: int) -> list[int]:
    less = [v for v in nums if v < x]
    greater = [v for v in nums if v >= x]
    return less + greater
""",
        "Time: O(n) | Space: O(n)",
    ),
    "odd-even-linked-list": (
        # brute
        """def oddEvenList(nums: list[int]) -> list[int]:
    if len(nums) <= 2:
        return list(nums)
    odds = []
    evens = []
    for i, val in enumerate(nums, 1):
        if i % 2 == 1:
            odds.append(val)
        else:
            evens.append(val)
    return odds + evens
""",
        "Time: O(n) | Space: O(n)",
        # optimal
        """def oddEvenList(nums: list[int]) -> list[int]:
    n = len(nums)
    if n <= 2:
        return list(nums)
    res = [0] * n
    odd_ptr = 0
    for i in range(0, n, 2):
        res[odd_ptr] = nums[i]
        odd_ptr += 1
    even_ptr = odd_ptr
    for i in range(1, n, 2):
        res[even_ptr] = nums[i]
        even_ptr += 1
    return res
""",
        "Time: O(n) | Space: O(n)",
    ),
    "merge-k-sorted-lists": (
        # brute
        """def mergeKLists(lists: list[list[int]]) -> list[int]:
    all_elements = []
    for sublist in lists:
        for val in sublist:
            all_elements.append(val)
    all_elements.sort()
    return all_elements
""",
        "Time: O(N log N) | Space: O(N)",
        # optimal
        """import heapq

def mergeKLists(lists: list[list[int]]) -> list[int]:
    heap = []
    for list_idx, sublist in enumerate(lists):
        if sublist:
            heapq.heappush(heap, (sublist[0], list_idx, 0))
    result = []
    while heap:
        val, list_idx, elem_idx = heapq.heappop(heap)
        result.append(val)
        next_idx = elem_idx + 1
        if next_idx < len(lists[list_idx]):
            heapq.heappush(heap, (lists[list_idx][next_idx], list_idx, next_idx))
    return result
""",
        "Time: O(N log k) | Space: O(N)",
    ),
    "copy-list-with-random-pointer": (
        # brute
        """def copyRandomList(nodes: list[list[int]]) -> list[list[int]]:
    if not nodes:
        return []
    mapping = {}
    for i, node in enumerate(nodes):
        mapping[i] = [node[0], -1]
    for i, node in enumerate(nodes):
        target = node[1]
        if target != -1 and target in mapping:
            mapping[i][1] = target
    return [mapping[i] for i in range(len(nodes))]
""",
        "Time: O(n) | Space: O(n)",
        # optimal
        """def copyRandomList(nodes: list[list[int]]) -> list[list[int]]:
    return [[node[0], node[1]] for node in nodes]
""",
        "Time: O(n) | Space: O(n)",
    ),
    "remove-linked-list-elements": (
        # brute
        """def removeElements(nums: list[int], val: int) -> list[int]:
    res = []
    for x in nums:
        if x != val:
            res.append(x)
    return res
""",
        "Time: O(n) | Space: O(n)",
        # optimal
        """def removeElements(nums: list[int], val: int) -> list[int]:
    return [x for x in nums if x != val]
""",
        "Time: O(n) | Space: O(n)",
    ),
    "reverse-linked-list-ii": (
        # brute
        """def reverseBetween(nums: list[int], left: number, right: number) -> list[int]:
    arr = list(nums)
    sub = arr[left - 1:right]
    sub.reverse()
    arr[left - 1:right] = sub
    return arr
""".replace("number", "int"),
        "Time: O(n) | Space: O(n)",
        # optimal
        """def reverseBetween(nums: list[int], left: int, right: int) -> list[int]:
    res = list(nums)
    l = left - 1
    r = right - 1
    while l < r:
        res[l], res[r] = res[r], res[l]
        l += 1
        r -= 1
    return res
""",
        "Time: O(n) | Space: O(n)",
    ),
}

# -----------------------------------------------------------------------------
# 3. Hand-Crafted Non-Degenerate Examples with Human Explanations
# -----------------------------------------------------------------------------

EXAMPLES: dict[str, list[dict[str, str]]] = {
    "reorder-list": [
        {
            "input": "nums = [1, 2, 3, 4]",
            "output": "[1, 4, 2, 3]",
            "explanation": "With four elements, the first element 1 is paired with the last element 4, followed by the second element 2 paired with the second-to-last element 3.",
        },
        {
            "input": "nums = [1, 2, 3, 4, 5]",
            "output": "[1, 5, 2, 4, 3]",
            "explanation": "With an odd length of five, 1 pairs with 5, then 2 pairs with 4, and the solitary middle element 3 is placed at the end.",
        },
    ],
    "rotate-list": [
        {
            "input": "nums = [1, 2, 3, 4, 5], k = 2",
            "output": "[4, 5, 1, 2, 3]",
            "explanation": "Rotating right by 2 shifts 5 and 4 to the front, followed by the remaining elements 1, 2, and 3.",
        },
        {
            "input": "nums = [0, 1, 2], k = 4",
            "output": "[2, 0, 1]",
            "explanation": "Here k = 4 exceeds length 3. The effective rotation is 4 % 3 = 1 step to the right, moving 2 to the front.",
        },
    ],
    "swap-nodes-in-pairs": [
        {
            "input": "nums = [1, 2, 3, 4]",
            "output": "[2, 1, 4, 3]",
            "explanation": "Elements 1 and 2 swap positions to become [2, 1], and elements 3 and 4 swap positions to become [4, 3].",
        },
        {
            "input": "nums = [1, 2, 3, 4, 5]",
            "output": "[2, 1, 4, 3, 5]",
            "explanation": "Pairs (1, 2) and (3, 4) swap, leaving the odd 5th element 5 at the end untouched.",
        },
    ],
    "reverse-nodes-in-k-group": [
        {
            "input": "nums = [1, 2, 3, 4, 5], k = 2",
            "output": "[2, 1, 4, 3, 5]",
            "explanation": "The first chunk [1, 2] is reversed to [2, 1]; the second chunk [3, 4] is reversed to [4, 3]; the lone remaining element [5] is left unchanged.",
        },
        {
            "input": "nums = [1, 2, 3, 4, 5], k = 3",
            "output": "[3, 2, 1, 4, 5]",
            "explanation": "The first chunk [1, 2, 3] of length 3 is reversed to [3, 2, 1]; the remaining 2 elements [4, 5] form an incomplete chunk (< k) and remain in original order.",
        },
    ],
    "partition-list": [
        {
            "input": "nums = [1, 4, 3, 2, 5, 2], x = 3",
            "output": "[1, 2, 2, 4, 3, 5]",
            "explanation": "Elements strictly less than 3 are [1, 2, 2]. Elements greater than or equal to 3 are [4, 3, 5]. Combining them while preserving relative order gives [1, 2, 2, 4, 3, 5].",
        },
        {
            "input": "nums = [2, 1], x = 2",
            "output": "[1, 2]",
            "explanation": "1 is less than 2 and placed first; 2 is greater than or equal to 2 and placed second.",
        },
    ],
    "odd-even-linked-list": [
        {
            "input": "nums = [1, 2, 3, 4, 5]",
            "output": "[1, 3, 5, 2, 4]",
            "explanation": "Nodes at 1-indexed positions 1, 3, 5 are values [1, 3, 5]. Nodes at positions 2, 4 are [2, 4]. Connecting odds then evens yields [1, 3, 5, 2, 4].",
        },
        {
            "input": "nums = [2, 1, 3, 5, 6, 4, 7]",
            "output": "[2, 3, 6, 7, 1, 5, 4]",
            "explanation": "Odd positions (1st, 3rd, 5th, 7th) have values [2, 3, 6, 7]; even positions (2nd, 4th, 6th) have values [1, 5, 4].",
        },
    ],
    "merge-k-sorted-lists": [
        {
            "input": "lists = [[1, 4, 5], [1, 3, 4], [2, 6]]",
            "output": "[1, 1, 2, 3, 4, 4, 5, 6]",
            "explanation": "Merging the three sorted lists yields all elements in ascending order: [1, 1, 2, 3, 4, 4, 5, 6].",
        },
        {
            "input": "lists = [[], [1, 5], [2, 3, 8], []]",
            "output": "[1, 2, 3, 5, 8]",
            "explanation": "Empty sublists contribute no elements. Merging [1, 5] and [2, 3, 8] produces [1, 2, 3, 5, 8].",
        },
    ],
    "copy-list-with-random-pointer": [
        {
            "input": "nodes = [[7, -1], [13, 0], [11, 4], [10, 2], [1, 0]]",
            "output": "[[7, -1], [13, 0], [11, 4], [10, 2], [1, 0]]",
            "explanation": "A 5-node list where node 0 has no random target (-1), node 1 points to node 0, node 2 points to node 4, node 3 points to node 2, and node 4 points to node 0. A distinct deep copy with identical structure is created.",
        },
        {
            "input": "nodes = [[1, 1], [2, 1]]",
            "output": "[[1, 1], [2, 1]]",
            "explanation": "Node 0 points to node 1 as random, and node 1 points to itself as random (index 1). A deep copy mirroring these pointers is returned.",
        },
    ],
    "remove-linked-list-elements": [
        {
            "input": "nums = [1, 2, 6, 3, 4, 5, 6], val = 6",
            "output": "[1, 2, 3, 4, 5]",
            "explanation": "Both occurrences of 6 (at indices 2 and 6) are removed, leaving [1, 2, 3, 4, 5].",
        },
        {
            "input": "nums = [7, 7, 7, 7], val = 7",
            "output": "[]",
            "explanation": "Every element in the list matches val = 7, resulting in an empty list.",
        },
        {
            "input": "nums = [1, 2, 3], val = 4",
            "output": "[1, 2, 3]",
            "explanation": "The value 4 is not present in the list, so the original sequence is preserved unchanged.",
        },
    ],
    "reverse-linked-list-ii": [
        {
            "input": "nums = [1, 2, 3, 4, 5], left = 2, right = 4",
            "output": "[1, 4, 3, 2, 5]",
            "explanation": "The subsegment from 1-indexed position 2 to 4 corresponds to values [2, 3, 4]. Reversing this segment gives [4, 3, 2], producing the final sequence [1, 4, 3, 2, 5].",
        },
        {
            "input": "nums = [1, 2, 3, 4], left = 1, right = 4",
            "output": "[4, 3, 2, 1]",
            "explanation": "Here left = 1 and right = 4 spans the entire list, reversing all elements.",
        },
    ],
}

# -----------------------------------------------------------------------------
# 4. Deterministic Valid Test Input Synthesis
# -----------------------------------------------------------------------------

def _generate_valid_inputs_for_spec(spec: ProblemSpec) -> list[list[Any]]:
    rng = random.Random(spec.seed)
    slug = spec.slug
    inputs: list[list[Any]] = []

    if slug == "reorder-list":
        inputs = [
            [[1, 2, 3, 4]],
            [[1, 2, 3, 4, 5]],
            [[]],
            [[1]],
            [[1, 2]],
            [[10, 20, 30]],
            [[1, 2, 3, 4, 5, 6]],
            [[-5, 10, -2, 8]],
            [[3, 3, 3, 3]],
            [[7, -7]],
        ]
        for _ in range(12):
            length = rng.randint(0, 24)
            inputs.append([[rng.randint(-100, 100) for _ in range(length)]])
        # Stress cases
        for _ in range(4):
            length = rng.randint(40, 80)
            inputs.append([[rng.randint(-1000, 1000) for _ in range(length)]])

    elif slug == "rotate-list":
        inputs = [
            [[1, 2, 3, 4, 5], 2],
            [[0, 1, 2], 4],
            [[], 5],
            [[], 0],
            [[1], 0],
            [[1], 99],
            [[1, 2], 1],
            [[1, 2], 2],
            [[1, 2], 3],
            [[1, 2, 3, 4], 0],
            [[1, 2, 3, 4], 4],
            [[1, 2, 3, 4], 8],
        ]
        for _ in range(10):
            length = rng.randint(1, 20)
            arr = [rng.randint(-100, 100) for _ in range(length)]
            k = rng.randint(0, 50)
            inputs.append([arr, k])
        # Stress cases
        for _ in range(4):
            length = rng.randint(30, 80)
            arr = [rng.randint(-1000, 1000) for _ in range(length)]
            k = rng.randint(0, 1000)
            inputs.append([arr, k])

    elif slug == "swap-nodes-in-pairs":
        inputs = [
            [[1, 2, 3, 4]],
            [[1, 2, 3, 4, 5]],
            [[]],
            [[1]],
            [[1, 2]],
            [[1, 2, 3]],
            [[10, 20, 30, 40, 50, 60]],
            [[-1, -2, -3, -4]],
            [[0, 0, 0]],
            [[5, 4, 3, 2, 1]],
        ]
        for _ in range(12):
            length = rng.randint(0, 24)
            inputs.append([[rng.randint(-100, 100) for _ in range(length)]])
        # Stress cases
        for _ in range(4):
            length = rng.randint(40, 80)
            inputs.append([[rng.randint(-1000, 1000) for _ in range(length)]])

    elif slug == "reverse-nodes-in-k-group":
        inputs = [
            [[1, 2, 3, 4, 5], 2],
            [[1, 2, 3, 4, 5], 3],
            [[], 2],
            [[1], 1],
            [[1], 2],
            [[1, 2, 3], 1],
            [[1, 2, 3], 5],
            [[1, 2, 3, 4], 4],
            [[1, 2, 3, 4, 5, 6], 2],
            [[1, 2, 3, 4, 5, 6], 3],
            [[1, 2, 3, 4, 5, 6, 7], 3],
            [[1, 2, 3, 4, 5, 6, 7], 4],
        ]
        for _ in range(10):
            length = rng.randint(1, 20)
            arr = [rng.randint(-100, 100) for _ in range(length)]
            k = rng.randint(1, max(1, length + 2))
            inputs.append([arr, k])
        # Stress cases
        for _ in range(4):
            length = rng.randint(30, 80)
            arr = [rng.randint(-1000, 1000) for _ in range(length)]
            k = rng.randint(1, max(1, length))
            inputs.append([arr, k])

    elif slug == "partition-list":
        inputs = [
            [[1, 4, 3, 2, 5, 2], 3],
            [[2, 1], 2],
            [[], 0],
            [[1], 2],
            [[2], 1],
            [[2], 2],
            [[1, 2, 0, -3], 5],
            [[5, 8, 9, 5], 5],
            [[3, 3, 3, 3], 3],
            [[-5, -1, 0, 4, 2], 0],
        ]
        for _ in range(12):
            length = rng.randint(0, 20)
            arr = [rng.randint(-100, 100) for _ in range(length)]
            x = rng.randint(-50, 50)
            inputs.append([arr, x])
        # Stress cases
        for _ in range(4):
            length = rng.randint(30, 80)
            arr = [rng.randint(-1000, 1000) for _ in range(length)]
            x = rng.choice(arr) if arr else 0
            inputs.append([arr, x])

    elif slug == "odd-even-linked-list":
        inputs = [
            [[1, 2, 3, 4, 5]],
            [[2, 1, 3, 5, 6, 4, 7]],
            [[]],
            [[1]],
            [[1, 2]],
            [[1, 2, 3]],
            [[1, 2, 3, 4]],
            [[-1, 10, -3, 20, -5]],
            [[0, 0, 0, 0]],
            [[9, 8, 7, 6, 5, 4, 3, 2, 1]],
        ]
        for _ in range(12):
            length = rng.randint(0, 24)
            inputs.append([[rng.randint(-100, 100) for _ in range(length)]])
        # Stress cases
        for _ in range(4):
            length = rng.randint(40, 80)
            inputs.append([[rng.randint(-1000, 1000) for _ in range(length)]])

    elif slug == "merge-k-sorted-lists":
        inputs = [
            [[[1, 4, 5], [1, 3, 4], [2, 6]]],
            [[[], [1, 5], [2, 3, 8], []]],
            [[]],
            [[[]]],
            [[[], [], []]],
            [[[1, 2, 3]]],
            [[[1, 3], [2, 4]]],
            [[[-10, -5, 0], [-8, 2, 5]]],
            [[[1, 1], [1, 1]]],
            [[[], [0]]],
        ]
        for _ in range(12):
            k = rng.randint(1, 8)
            lists = []
            for _ in range(k):
                size = rng.randint(0, 10)
                sub = sorted([rng.randint(-100, 100) for _ in range(size)])
                lists.append(sub)
            inputs.append([lists])
        # Stress cases
        for _ in range(4):
            k = rng.randint(10, 20)
            lists = []
            for _ in range(k):
                size = rng.randint(5, 25)
                sub = sorted([rng.randint(-1000, 1000) for _ in range(size)])
                lists.append(sub)
            inputs.append([lists])

    elif slug == "copy-list-with-random-pointer":
        inputs = [
            [[[7, -1], [13, 0], [11, 4], [10, 2], [1, 0]]],
            [[[1, 1], [2, 1]]],
            [[]],
            [[[7, -1]]],
            [[[7, 0]]],
            [[[1, -1], [2, -1], [3, -1]]],
            [[[3, 2], [3, 0], [3, -1]]],
            [[[-1, 0], [-2, 1]]],
        ]
        for _ in range(14):
            n = rng.randint(1, 15)
            nodes = []
            for _ in range(n):
                val = rng.randint(-100, 100)
                r_idx = rng.choice([-1] + list(range(n)))
                nodes.append([val, r_idx])
            inputs.append([nodes])
        # Stress cases
        for _ in range(4):
            n = rng.randint(30, 60)
            nodes = []
            for _ in range(n):
                val = rng.randint(-1000, 1000)
                r_idx = rng.choice([-1] + list(range(n)))
                nodes.append([val, r_idx])
            inputs.append([nodes])

    elif slug == "remove-linked-list-elements":
        inputs = [
            [[1, 2, 6, 3, 4, 5, 6], 6],
            [[7, 7, 7, 7], 7],
            [[1, 2, 3], 4],
            [[], 1],
            [[1], 1],
            [[1], 2],
            [[6, 6, 1, 2], 6],
            [[1, 2, 6, 6], 6],
            [[1, 6, 2, 6, 3], 6],
            [[-1, -2, -1], -1],
        ]
        for _ in range(12):
            length = rng.randint(0, 20)
            val = rng.randint(-20, 20)
            arr = [rng.randint(-20, 20) for _ in range(length)]
            inputs.append([arr, val])
        # Stress cases
        for _ in range(4):
            length = rng.randint(40, 80)
            val = rng.randint(-1000, 1000)
            arr = [rng.randint(-1000, 1000) for _ in range(length)]
            inputs.append([arr, val])

    elif slug == "reverse-linked-list-ii":
        inputs = [
            [[1, 2, 3, 4, 5], 2, 4],
            [[1, 2, 3, 4], 1, 4],
            [[5], 1, 1],
            [[1, 2, 3, 4], 2, 2],
            [[1, 2, 3, 4, 5], 1, 3],
            [[1, 2, 3, 4, 5], 3, 5],
            [[1, 2], 1, 2],
            [[1, 2, 3], 2, 3],
            [[-1, -2, -3, -4], 1, 2],
            [[10, 20, 30, 40, 50], 1, 5],
        ]
        for _ in range(12):
            length = rng.randint(1, 20)
            arr = [rng.randint(-100, 100) for _ in range(length)]
            left = rng.randint(1, length)
            right = rng.randint(left, length)
            inputs.append([arr, left, right])
        # Stress cases
        for _ in range(4):
            length = rng.randint(30, 80)
            arr = [rng.randint(-1000, 1000) for _ in range(length)]
            left = rng.randint(1, length)
            right = rng.randint(left, length)
            inputs.append([arr, left, right])

    return inputs

# -----------------------------------------------------------------------------
# 5. Build, Verify and Assemble Problem Artifacts
# -----------------------------------------------------------------------------

async def _build_and_verify_spec(spec: ProblemSpec) -> GeneratedProblem:
    inputs = _generate_valid_inputs_for_spec(spec)
    # Deduplicate input calls
    seen: set[str] = set()
    deduped_inputs: list[list[Any]] = []
    for inp in inputs:
        fp = json.dumps(inp, sort_keys=True, separators=(",", ":"))
        if fp not in seen:
            seen.add(fp)
            deduped_inputs.append(inp)

    pending = [
        {
            "label": f"case-{i + 1:02d}",
            "input": val,
            "expected": None,
            "isSample": (i < 2),
        }
        for i, val in enumerate(deduped_inputs)
    ]

    # Invariant 3: Derive expected outputs through judge using optimal JS code
    probe = await execute_code(
        language="javascript",
        code=spec.optimal.code,
        function_name=spec.function_name,
        test_cases=pending,
        time_limit_ms=spec.time_limit_ms,
    )
    if probe.compile_output or len(probe.test_results) != len(pending):
        raise ValueError(f"Optimal probe failed for {spec.slug}: {probe.compile_output}")

    for case, res in zip(pending, probe.test_results, strict=True):
        if res.get("error") is not None or "actual" not in res:
            raise ValueError(f"Optimal execution error for {spec.slug}: {res.get('error')}")
        case["expected"] = res["actual"]

    # Cross-verify both JS brute and JS optimal
    brute_res, opt_res = await asyncio.gather(
        execute_code(
            language="javascript",
            code=spec.brute_force.code,
            function_name=spec.function_name,
            test_cases=copy.deepcopy(pending),
            time_limit_ms=spec.time_limit_ms,
        ),
        execute_code(
            language="javascript",
            code=spec.optimal.code,
            function_name=spec.function_name,
            test_cases=copy.deepcopy(pending),
            time_limit_ms=spec.time_limit_ms,
        ),
    )
    if brute_res.verdict != "AC":
        raise ValueError(f"Brute-force JS failed for {spec.slug}: {brute_res.compile_output or brute_res.verdict}")
    if opt_res.verdict != "AC":
        raise ValueError(f"Optimal JS failed for {spec.slug}: {opt_res.compile_output or opt_res.verdict}")

    report = ValidationReport(
        test_cases=pending,
        brute_force_runtime_ms=brute_res.runtime_ms,
        optimal_runtime_ms=opt_res.runtime_ms,
        brute_force_case_runtimes_ms=[row["runtime_ms"] for row in brute_res.test_results],
        optimal_case_runtimes_ms=[row["runtime_ms"] for row in opt_res.test_results],
    )

    # Prepare starter codes
    names = ", ".join(param.name for param in spec.parsed_signature.parameters)
    starter_code = {
        "javascript": f"function {spec.function_name}({names}) {{\n  // Write your solution here\n  throw new Error('Not implemented');\n}}\n",
        "python": f"def {spec.function_name}({names}):\n    # Write your solution here\n    raise NotImplementedError\n",
    }

    # Editorial gate: cite measured PAF runtimes
    editorial = dict(spec.editorial or {})
    base_why = editorial.get("why_optimal", "")
    editorial["why_optimal"] = (
        f"{base_why} Measured PAF benchmark runtimes: Optimal {report.optimal_runtime_ms:.2f}ms vs "
        f"Brute Force {report.brute_force_runtime_ms:.2f}ms across {report.total_cases} test cases."
    )

    examples = EXAMPLES.get(spec.slug, [])
    if not examples:
        examples = [
            {
                "input": ", ".join(
                    f"{p.name} = {json.dumps(val, ensure_ascii=False)}"
                    for p, val in zip(spec.parsed_signature.parameters, case["input"], strict=True)
                ),
                "output": json.dumps(case["expected"], ensure_ascii=False),
                "explanation": "Generated from the verified optimal implementation.",
            }
            for case in pending[:2]
        ]

    # Retrieve python solutions
    py_brute_code, py_brute_comp, py_opt_code, py_opt_comp = PYTHON_SOLUTIONS[spec.slug]

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
            "complexity": py_brute_comp,
            "language": "python",
            "code": py_brute_code,
            "isReference": False,
        },
        {
            "title": "Optimal",
            "complexity": py_opt_comp,
            "language": "python",
            "code": py_opt_code,
            "isReference": True,
        },
    ]

    data: dict[str, Any] = {
        "slug": spec.resolved_slug,
        "title": spec.resolved_title,
        "topic": spec.topic,
        "difficulty": spec.difficulty,
        "pattern": spec.pattern,
        "statement": spec.statement,
        "examples": examples,
        "constraints": [
            f"Function signature: `{spec.signature.strip()}`.",
            "Inputs are JSON-serializable values satisfying the bounds stated above.",
        ],
        "hints": list(spec.hints or []),
        "editorial": editorial,
        "reading_links": list(spec.reading_links),
        "starterCode": starter_code,
        "functionName": spec.function_name,
        "timeLimitMs": spec.time_limit_ms,
        "reviewStatus": "verified",
        "pafVerification": {
            "seed": spec.seed,
            "generatedCaseCount": report.total_cases,
            "bruteForceRuntimeMs": report.brute_force_runtime_ms,
            "optimalRuntimeMs": report.optimal_runtime_ms,
        },
        "testCases": pending,
        "solutions": solutions,
    }

    return GeneratedProblem(data=data, report=report)

# -----------------------------------------------------------------------------
# 6. Verification and Main Entrypoint
# -----------------------------------------------------------------------------

async def verify_python(path: Path, fn: str, brute: str, optimal: str) -> None:
    d = json.load(open(path))
    cases = [{"label": t["label"], "input": t["input"], "expected": t["expected"]} for t in d["testCases"]]
    for role, code in (("brute", brute), ("optimal", optimal)):
        r = await execute_code(
            language="python",
            code=code,
            function_name=fn,
            test_cases=cases,
            time_limit_ms=d.get("timeLimitMs", 2000),
        )
        assert r.verdict == "AC", (role, r.verdict, r.compile_output)
    print("PYTHON AC", str(path))

SPECS: list[ProblemSpec] = [
    spec_reorder_list,
    spec_rotate_list,
    spec_swap_pairs,
    spec_reverse_k_group,
    spec_partition_list,
    spec_odd_even,
    spec_merge_k_lists,
    spec_copy_random,
    spec_remove_elements,
    spec_reverse_between,
]

async def main_async() -> None:
    output_dir = REPO_ROOT / "content" / "problems"
    print(f"Authoring, verifying and emitting {len(SPECS)} Batch-2A Linked List problems with PAF...")
    for idx, spec in enumerate(SPECS, 1):
        print(f"[{idx}/{len(SPECS)}] Processing {spec.slug} ({spec.difficulty})...")
        problem = await _build_and_verify_spec(spec)
        out_file = problem.write_to(output_dir)
        print(
            f"  ✓ PAF JS Verified: {problem.report.total_cases} cases | "
            f"Brute: {problem.report.brute_force_runtime_ms:.2f}ms | "
            f"Optimal: {problem.report.optimal_runtime_ms:.2f}ms"
        )
        py_brute, _, py_opt, _ = PYTHON_SOLUTIONS[spec.slug]
        await verify_python(out_file, spec.function_name, py_brute, py_opt)

    print("\nAll 10 Batch-2A problems successfully PAF-verified and Python-verified.")

def main() -> None:
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
