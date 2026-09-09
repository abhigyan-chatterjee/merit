export interface ProblemExample {
  input: string;
  output: string;
  explanation?: string;
}

export interface ProblemSolution {
  title: string;
  complexity: string;
  code: string;
}

export interface TestCase {
  input: any[];
  expected: any;
  label: string;
}

export interface Problem {
  id: string;
  slug: string;
  title: string;
  topic: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  pattern: string;
  statement: string;
  examples: ProblemExample[];
  constraints: string[];
  hints: string[];
  solutions: ProblemSolution[];
  starterCode: string;
  functionName: string;
  testCases: TestCase[];
  sequence?: number | null;
  prevSlug?: string | null;
  nextSlug?: string | null;
}


export const PROBLEMS: Problem[] = [

  // ARRAYS-HASHING (7 problems)
  {
    id: "arr-1",
    slug: "two-sum",
    title: "Two Sum",
    topic: "arrays-hashing",
    difficulty: "Easy",
    pattern: "Hash Map / Complement",
    statement: "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target. You may assume that each input would have exactly one solution.",
    examples: [
      { input: "nums = [2, 7, 11, 15], target = 9", output: "[0, 1]", explanation: "nums[0] + nums[1] == 9, so we return [0, 1]." },
      { input: "nums = [3, 2, 4], target = 6", output: "[1, 2]" },
    ],
    constraints: ["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9", "Only one valid answer exists."],
    hints: [
      "A brute force approach inspects all pairs (i, j) in O(n²) time.",
      "Can we look up the complement (target - nums[i]) in O(1) time?",
      "Store previously visited numbers and their indices in a Map.",
    ],
    solutions: [
      {
        title: "Brute Force Nested Loops",
        complexity: "Time: O(n²) | Space: O(1)",
        code: "function solve(nums, target) {\n  for (let i = 0; i < nums.length; i++) {\n    for (let j = i + 1; j < nums.length; j++) {\n      if (nums[i] + nums[j] === target) return [i, j];\n    }\n  }\n  return [];\n}",
      },
      {
        title: "One-Pass Hash Map",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(nums, target) {\n  const seen = new Map();\n  for (let i = 0; i < nums.length; i++) {\n    const diff = target - nums[i];\n    if (seen.has(diff)) return [seen.get(diff), i];\n    seen.set(nums[i], i);\n  }\n  return [];\n}",
      },
    ],
    starterCode: "function solve(nums, target) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 1,
    nextSlug: "contains-duplicate",
    testCases: [
      { input: [[2, 7, 11, 15], 9], expected: [0, 1], label: "nums=[2,7,11,15], target=9" },
      { input: [[3, 2, 4], 6], expected: [1, 2], label: "nums=[3,2,4], target=6" },
      { input: [[3, 3], 6], expected: [0, 1], label: "nums=[3,3], target=6" },
    ],
  },
  {
    id: "arr-5",
    slug: "contains-duplicate",
    title: "Contains Duplicate",
    topic: "arrays-hashing",
    difficulty: "Easy",
    pattern: "Hash Set",
    statement: "Given an integer array nums, return true if any value appears at least twice in the array, and return false if every element is distinct.",
    examples: [
      { input: "nums = [1,2,3,1]", output: "true" },
      { input: "nums = [1,2,3,4]", output: "false" },
    ],
    constraints: ["1 <= nums.length <= 10^5"],
    hints: [
      "Sorting the array puts identical items next to each other in O(n log n).",
      "A Set stores unique elements in O(1) average lookup.",
      "Compare new Set(nums).size !== nums.length.",
    ],
    solutions: [
      {
        title: "Sort & Scan Neighbor",
        complexity: "Time: O(n log n) | Space: O(1)",
        code: "function solve(nums) {\n  nums.sort((a,b) => a - b);\n  for (let i = 1; i < nums.length; i++) if (nums[i] === nums[i-1]) return true;\n  return false;\n}",
      },
      {
        title: "Hash Set Early Exit",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(nums) {\n  return new Set(nums).size !== nums.length;\n}",
      },
    ],
    starterCode: "function solve(nums) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 2,
    prevSlug: "two-sum",
    nextSlug: "valid-anagram",
    testCases: [
      { input: [[1, 2, 3, 1]], expected: true, label: "[1,2,3,1]" },
      { input: [[1, 2, 3, 4]], expected: false, label: "[1,2,3,4]" },
      { input: [[1, 1, 1, 3, 3, 4, 3, 2, 4, 2]], expected: true, label: "[1,1,1,3,3...]" },
    ],
  },
  {
    id: "str-1",
    slug: "valid-anagram",
    title: "Valid Anagram",
    topic: "arrays-hashing",
    difficulty: "Easy",
    pattern: "Frequency Counter",
    statement: "Given two strings s and t, return true if t is an anagram of s, and false otherwise.",
    examples: [
      { input: "s = \"anagram\", t = \"nagaram\"", output: "true" },
      { input: "s = \"rat\", t = \"car\"", output: "false" },
    ],
    constraints: ["1 <= s.length, t.length <= 5 * 10^4"],
    hints: [
      "Anagrams must have identical lengths.",
      "Count occurrences of each character in s using an array of size 26.",
      "Decrement counts while iterating through t.",
    ],
    solutions: [
      {
        title: "Sorting Characters",
        complexity: "Time: O(n log n) | Space: O(n)",
        code: "function solve(s, t) {\n  return s.split('').sort().join('') === t.split('').sort().join('');\n}",
      },
      {
        title: "Fixed Array Counter",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(s, t) {\n  if (s.length !== t.length) return false;\n  const counts = {};\n  for (const c of s) counts[c] = (counts[c] || 0) + 1;\n  for (const c of t) {\n    if (!counts[c]) return false;\n    counts[c]--;\n  }\n  return true;\n}",
      },
    ],
    starterCode: "function solve(s, t) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 3,
    prevSlug: "contains-duplicate",
    nextSlug: "product-of-array-except-self",
    testCases: [
      { input: ["anagram", "nagaram"], expected: true, label: "\"anagram\", \"nagaram\"" },
      { input: ["rat", "car"], expected: false, label: "\"rat\", \"car\"" },
      { input: ["listen", "silent"], expected: true, label: "\"listen\", \"silent\"" },
    ],
  },
  {
    id: "arr-3",
    slug: "product-of-array-except-self",
    title: "Product of Array Except Self",
    topic: "arrays-hashing",
    difficulty: "Medium",
    pattern: "Prefix & Suffix Products",
    statement: "Given an integer array nums, return an array answer such that answer[i] is equal to the product of all the elements of nums except nums[i]. Must run in O(n) without division.",
    examples: [
      { input: "nums = [1, 2, 3, 4]", output: "[24, 12, 8, 6]" },
      { input: "nums = [-1, 1, 0, -3, 3]", output: "[0, 0, 9, 0, 0]" },
    ],
    constraints: ["2 <= nums.length <= 10^5", "-30 <= nums[i] <= 30"],
    hints: [
      "Maintain running prefix product from left to right.",
      "Multiply by running suffix product from right to left.",
      "Use the output array itself to achieve O(1) auxiliary space.",
    ],
    solutions: [
      {
        title: "Left and Right Arrays",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(nums) {\n  const n = nums.length;\n  const res = new Array(n).fill(1);\n  let prefix = 1;\n  for (let i = 0; i < n; i++) { res[i] = prefix; prefix *= nums[i]; }\n  let suffix = 1;\n  for (let i = n - 1; i >= 0; i--) { res[i] *= suffix; suffix *= nums[i]; }\n  return res;\n}",
      },
      {
        title: "In-Place Prefix/Suffix",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(nums) {\n  const n = nums.length, res = new Array(n).fill(1);\n  for (let i = 1; i < n; i++) res[i] = res[i - 1] * nums[i - 1];\n  let right = 1;\n  for (let i = n - 1; i >= 0; i--) { res[i] *= right; right *= nums[i]; }\n  return res;\n}",
      },
    ],
    starterCode: "function solve(nums) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 4,
    prevSlug: "valid-anagram",
    nextSlug: "subarray-sum-equals-k",
    testCases: [
      { input: [[1, 2, 3, 4]], expected: [24, 12, 8, 6], label: "[1,2,3,4]" },
      { input: [[-1, 1, 0, -3, 3]], expected: [0, 0, 9, 0, 0], label: "[-1,1,0,-3,3]" },
      { input: [[2, 5]], expected: [5, 2], label: "[2,5]" },
    ],
  },
  {
    id: "arr-9",
    slug: "subarray-sum-equals-k",
    title: "Subarray Sum Equals K",
    topic: "arrays-hashing",
    difficulty: "Medium",
    pattern: "Prefix Sum Hash Map",
    statement: "Given an array of integers nums and an integer k, return the number of contiguous subarrays whose elements sum to exactly k.",
    examples: [
      { input: "nums = [1,1,1], k = 2", output: "2", explanation: "Subarrays [1,1] starting at index 0 and starting at index 1." },
      { input: "nums = [1,2,3], k = 3", output: "2", explanation: "Subarrays [1,2] and [3]." },
    ],
    constraints: ["1 <= nums.length <= 2 * 10^4", "-1000 <= nums[i] <= 1000", "-10^7 <= k <= 10^7"],
    hints: [
      "A subarray (j+1..i) sums to k exactly when prefix[i] - prefix[j] == k.",
      "So for each running prefix sum s, count how many earlier prefixes equal s - k.",
      "Store prefix frequencies in a Map seeded with {0: 1} for subarrays starting at index 0.",
    ],
    solutions: [
      {
        title: "All Start-End Pairs",
        complexity: "Time: O(n²) | Space: O(1)",
        code: "function solve(nums, k) {\n  let count = 0;\n  for (let i = 0; i < nums.length; i++) {\n    let sum = 0;\n    for (let j = i; j < nums.length; j++) {\n      sum += nums[j];\n      if (sum === k) count++;\n    }\n  }\n  return count;\n}",
      },
      {
        title: "Prefix Sum Frequencies",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(nums, k) {\n  const freq = new Map([[0, 1]]);\n  let sum = 0, count = 0;\n  for (const n of nums) {\n    sum += n;\n    if (freq.has(sum - k)) count += freq.get(sum - k);\n    freq.set(sum, (freq.get(sum) || 0) + 1);\n  }\n  return count;\n}",
      },
    ],
    starterCode: "function solve(nums, k) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 5,
    prevSlug: "product-of-array-except-self",
    nextSlug: "best-time-to-buy-and-sell-stock",
    testCases: [
      { input: [[1, 1, 1], 2], expected: 2, label: "[1,1,1], k=2" },
      { input: [[1, 2, 3], 3], expected: 2, label: "[1,2,3], k=3" },
      { input: [[1, -1, 0], 0], expected: 3, label: "[1,-1,0], k=0" },
    ],
  },
  {
    id: "arr-6",
    slug: "best-time-to-buy-and-sell-stock",
    title: "Best Time to Buy and Sell Stock",
    topic: "arrays-hashing",
    difficulty: "Easy",
    pattern: "One-Pass Min Tracking",
    statement: "You are given an array prices where prices[i] is the price of a stock on day i. Choose one day to buy and a later day to sell to maximize profit. Return the maximum profit achievable, or 0 if no profit is possible.",
    examples: [
      { input: "prices = [7,1,5,3,6,4]", output: "5", explanation: "Buy on day 2 (price 1) and sell on day 5 (price 6) for profit 5." },
      { input: "prices = [7,6,4,3,1]", output: "0", explanation: "Prices only fall, so no profitable trade exists." },
    ],
    constraints: ["1 <= prices.length <= 10^5", "0 <= prices[i] <= 10^4"],
    hints: [
      "Track the minimum price seen so far while scanning left to right.",
      "At each day, the best profit ending today is prices[i] - minPriceSoFar.",
      "Keep the maximum of those daily profits across the whole scan.",
    ],
    solutions: [
      {
        title: "All Pairs Check",
        complexity: "Time: O(n²) | Space: O(1)",
        code: "function solve(prices) {\n  let best = 0;\n  for (let i = 0; i < prices.length; i++) {\n    for (let j = i + 1; j < prices.length; j++) {\n      best = Math.max(best, prices[j] - prices[i]);\n    }\n  }\n  return best;\n}",
      },
      {
        title: "One-Pass Min Tracking",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(prices) {\n  let minPrice = Infinity, best = 0;\n  for (const p of prices) {\n    minPrice = Math.min(minPrice, p);\n    best = Math.max(best, p - minPrice);\n  }\n  return best;\n}",
      },
    ],
    starterCode: "function solve(prices) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 6,
    prevSlug: "subarray-sum-equals-k",
    nextSlug: "longest-consecutive-sequence",
    testCases: [
      { input: [[7, 1, 5, 3, 6, 4]], expected: 5, label: "[7,1,5,3,6,4]" },
      { input: [[7, 6, 4, 3, 1]], expected: 0, label: "[7,6,4,3,1]" },
      { input: [[1, 2]], expected: 1, label: "[1,2]" },
    ],
  },
  {
    id: "graph-6",
    slug: "longest-consecutive-sequence",
    title: "Longest Consecutive Sequence",
    topic: "arrays-hashing",
    difficulty: "Medium",
    pattern: "Union-Find / Set Streaks",
    statement: "Given an unsorted array of integers nums, return the length of the longest run of consecutive integers. The algorithm must run in O(n) time.",
    examples: [
      { input: "nums = [100,4,200,1,3,2]", output: "4", explanation: "The consecutive run [1,2,3,4] has length 4." },
      { input: "nums = [0,3,7,2,5,8,4,6,0,1]", output: "9", explanation: "The run [0..8] has length 9." },
    ],
    constraints: ["0 <= nums.length <= 10^5", "-10^9 <= nums[i] <= 10^9"],
    hints: [
      "Sorting gives O(n log n), which misses the required bound; use a Set.",
      "Only start counting from numbers with no predecessor (n - 1 not in the set).",
      "From each streak start, walk upward while n + 1 exists and track the best length.",
    ],
    solutions: [
      {
        title: "Sort & Linear Scan",
        complexity: "Time: O(n log n) | Space: O(n)",
        code: "function solve(nums) {\n  if (!nums.length) return 0;\n  const s = [...new Set(nums)].sort((a, b) => a - b);\n  let best = 1, cur = 1;\n  for (let i = 1; i < s.length; i++) {\n    if (s[i] === s[i - 1] + 1) { cur++; best = Math.max(best, cur); }\n    else cur = 1;\n  }\n  return best;\n}",
      },
      {
        title: "Hash Set Streak Starts",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(nums) {\n  const seen = new Set(nums);\n  let best = 0;\n  for (const n of seen) {\n    if (!seen.has(n - 1)) {\n      let cur = 1, x = n;\n      while (seen.has(x + 1)) { x++; cur++; }\n      best = Math.max(best, cur);\n    }\n  }\n  return best;\n}",
      },
    ],
    starterCode: "function solve(nums) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 7,
    prevSlug: "best-time-to-buy-and-sell-stock",
    testCases: [
      { input: [[100, 4, 200, 1, 3, 2]], expected: 4, label: "[100,4,200,1,3,2]" },
      { input: [[0, 3, 7, 2, 5, 8, 4, 6, 0, 1]], expected: 9, label: "[0,3,7,2,5,8,4,6,0,1]" },
      { input: [[]], expected: 0, label: "[] empty" },
    ],
  },

  // TWO-POINTERS (4 problems)
  {
    id: "arr-4",
    slug: "container-with-most-water",
    title: "Container With Most Water",
    topic: "two-pointers",
    difficulty: "Medium",
    pattern: "Two Pointers",
    statement: "Given n non-negative integers height where each represents a point at coordinate (i, height[i]), find two lines that together with the x-axis form a container that holds the most water.",
    examples: [
      { input: "height = [1,8,6,2,5,4,8,3,7]", output: "49" },
      { input: "height = [1,1]", output: "1" },
    ],
    constraints: ["n == height.length", "2 <= n <= 10^5"],
    hints: [
      "Start with left = 0 and right = n - 1 for maximum width.",
      "Area is (right - left) * Math.min(height[left], height[right]).",
      "Always advance the pointer pointing to the shorter vertical line.",
    ],
    solutions: [
      {
        title: "All Pairs Check",
        complexity: "Time: O(n²) | Space: O(1)",
        code: "function solve(height) {\n  let max = 0;\n  for (let i = 0; i < height.length; i++) {\n    for (let j = i + 1; j < height.length; j++) {\n      max = Math.max(max, (j - i) * Math.min(height[i], height[j]));\n    }\n  }\n  return max;\n}",
      },
      {
        title: "Two Pointers Converging",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(height) {\n  let l = 0, r = height.length - 1, max = 0;\n  while (l < r) {\n    max = Math.max(max, (r - l) * Math.min(height[l], height[r]));\n    if (height[l] < height[r]) l++; else r--;\n  }\n  return max;\n}",
      },
    ],
    starterCode: "function solve(height) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 1,
    nextSlug: "valid-palindrome",
    testCases: [
      { input: [[1, 8, 6, 2, 5, 4, 8, 3, 7]], expected: 49, label: "[1,8,6,2,5,4,8,3,7]" },
      { input: [[1, 1]], expected: 1, label: "[1,1]" },
      { input: [[4, 3, 2, 1, 4]], expected: 16, label: "[4,3,2,1,4]" },
    ],
  },
  {
    id: "str-2",
    slug: "valid-palindrome",
    title: "Valid Palindrome",
    topic: "two-pointers",
    difficulty: "Easy",
    pattern: "Two Pointers",
    statement: "A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward.",
    examples: [
      { input: "s = \"A man, a plan, a canal: Panama\"", output: "true" },
      { input: "s = \"race a car\"", output: "false" },
    ],
    constraints: ["1 <= s.length <= 2 * 10^5"],
    hints: [
      "Filter non-alphanumeric characters using regex /[^a-z0-9]/gi.",
      "Use two pointers at start and end moving toward the middle.",
      "Return false immediately if s[left] !== s[right].",
    ],
    solutions: [
      {
        title: "Reverse String Compare",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(s) {\n  const clean = s.toLowerCase().replace(/[^a-z0-9]/g, '');\n  return clean === clean.split('').reverse().join('');\n}",
      },
      {
        title: "Two Pointers In-Place",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(s) {\n  const clean = s.toLowerCase().replace(/[^a-z0-9]/g, '');\n  let l = 0, r = clean.length - 1;\n  while (l < r) if (clean[l++] !== clean[r--]) return false;\n  return true;\n}",
      },
    ],
    starterCode: "function solve(s,) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 2,
    prevSlug: "container-with-most-water",
    nextSlug: "merge-two-sorted-lists",
    testCases: [
      { input: ["A man, a plan, a canal: Panama"], expected: true, label: "\"A man, a plan...\"" },
      { input: ["race a car"], expected: false, label: "\"race a car\"" },
      { input: [" "], expected: true, label: "\" \"" },
    ],
  },
  {
    id: "ll-3",
    slug: "merge-two-sorted-lists",
    title: "Merge Two Sorted Lists",
    topic: "two-pointers",
    difficulty: "Easy",
    pattern: "Two-Pointer Merge",
    statement: "You are given two sorted linked lists list1 and list2. Merge the two lists into one sorted list and return its values.",
    examples: [
      { input: "list1 = [1,2,4], list2 = [1,3,4]", output: "[1,1,2,3,4,4]" },
      { input: "list1 = [], list2 = [0]", output: "[0]" },
    ],
    constraints: ["0 <= list.length <= 50"],
    hints: [
      "Create a dummy head node to simplify attaching the first element.",
      "Compare current heads of list1 and list2, advance the smaller one.",
      "Append any remaining elements when one list is exhausted.",
    ],
    solutions: [
      {
        title: "Iterative Dummy Node Merge",
        complexity: "Time: O(n + m) | Space: O(1)",
        code: "function solve(l1, l2) {\n  const res = [];\n  let i = 0, j = 0;\n  while (i < l1.length && j < l2.length) {\n    if (l1[i] <= l2[j]) res.push(l1[i++]);\n    else res.push(l2[j++]);\n  }\n  return res.concat(l1.slice(i)).concat(l2.slice(j));\n}",
      },
      {
        title: "Recursive Merge",
        complexity: "Time: O(n + m) | Space: O(n + m)",
        code: "function solve(l1, l2) {\n  return [...l1, ...l2].sort((a,b) => a - b);\n}",
      },
    ],
    starterCode: "function solve(l1, l2) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 3,
    prevSlug: "valid-palindrome",
    nextSlug: "remove-nth-node-from-end",
    testCases: [
      { input: [[1, 2, 4], [1, 3, 4]], expected: [1, 1, 2, 3, 4, 4], label: "[1,2,4], [1,3,4]" },
      { input: [[], [0]], expected: [0], label: "[], [0]" },
      { input: [[2, 5], [1, 3, 6]], expected: [1, 2, 3, 5, 6], label: "[2,5], [1,3,6]" },
    ],
  },
  {
    id: "ll-4",
    slug: "remove-nth-node-from-end",
    title: "Remove Nth Node From End of List",
    topic: "two-pointers",
    difficulty: "Medium",
    pattern: "Two Pointers with Gap N",
    statement: "Given the head of a linked list, remove the nth node from the end of the list and return the resulting node values.",
    examples: [
      { input: "head = [1,2,3,4,5], n = 2", output: "[1,2,3,5]" },
      { input: "head = [1], n = 1", output: "[]" },
    ],
    constraints: ["1 <= sz <= 30", "1 <= n <= sz"],
    hints: [
      "Advance lead pointer n steps ahead of trail pointer.",
      "Move both pointers together until lead reaches the tail.",
      "Skip trail.next = trail.next.next.",
    ],
    solutions: [
      {
        title: "Two-Pass Length Calculation",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(head, n) {\n  const idx = head.length - n;\n  return head.filter((_, i) => i !== idx);\n}",
      },
      {
        title: "Single-Pass Two Pointers",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(head, n) {\n  const res = [...head];\n  res.splice(res.length - n, 1);\n  return res;\n}",
      },
    ],
    starterCode: "function solve(head, n) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 4,
    prevSlug: "merge-two-sorted-lists",
    testCases: [
      { input: [[1, 2, 3, 4, 5], 2], expected: [1, 2, 3, 5], label: "[1,2,3,4,5], n=2" },
      { input: [[1], 1], expected: [], label: "[1], n=1" },
      { input: [[1, 2], 1], expected: [1], label: "[1,2], n=1" },
    ],
  },

  // SLIDING-WINDOWS (1 problems)
  {
    id: "str-3",
    slug: "longest-substring-without-repeating",
    title: "Longest Substring Without Repeating Characters",
    topic: "sliding-windows",
    difficulty: "Medium",
    pattern: "Sliding Window",
    statement: "Given a string s, find the length of the longest substring without repeating characters.",
    examples: [
      { input: "s = \"abcabcbb\"", output: "3", explanation: "The answer is \"abc\", with length 3." },
      { input: "s = \"bbbbb\"", output: "1" },
    ],
    constraints: ["0 <= s.length <= 5 * 10^4"],
    hints: [
      "Maintain a sliding window [left, right] with unique characters.",
      "Use a Map or Set to store characters inside the current window.",
      "When duplicate is seen, advance left pointer past previous occurrence.",
    ],
    solutions: [
      {
        title: "Set Sliding Window",
        complexity: "Time: O(n) | Space: O(min(n, m))",
        code: "function solve(s) {\n  const set = new Set();\n  let l = 0, max = 0;\n  for (let r = 0; r < s.length; r++) {\n    while (set.has(s[r])) set.delete(s[l++]);\n    set.add(s[r]);\n    max = Math.max(max, r - l + 1);\n  }\n  return max;\n}",
      },
      {
        title: "Index Jump Map",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(s) {\n  const map = new Map();\n  let l = 0, max = 0;\n  for (let r = 0; r < s.length; r++) {\n    if (map.has(s[r])) l = Math.max(l, map.get(s[r]) + 1);\n    map.set(s[r], r);\n    max = Math.max(max, r - l + 1);\n  }\n  return max;\n}",
      },
    ],
    starterCode: "function solve(s,) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 1,
    testCases: [
      { input: ["abcabcbb"], expected: 3, label: "\"abcabcbb\"" },
      { input: ["bbbbb"], expected: 1, label: "\"bbbbb\"" },
      { input: ["pwwkew"], expected: 3, label: "\"pwwkew\"" },
    ],
  },

  // STACK (2 problems)
  {
    id: "str-6",
    slug: "decode-string",
    title: "Decode String",
    topic: "stack",
    difficulty: "Medium",
    pattern: "Stack Unwinding",
    statement: "Given an encoded string where k[encoded] means the encoded part repeats exactly k times, return the fully decoded string. Inputs are always valid with balanced brackets.",
    examples: [
      { input: "s = \"3[a]2[bc]\"", output: "\"aaabcbc\"" },
      { input: "s = \"3[a2[c]]\"", output: "\"accaccacc\"", explanation: "Inner 2[c] becomes cc, then 3[acc] repeats it three times." },
    ],
    constraints: ["1 <= s.length <= 30", "s contains lowercase letters, digits, and brackets", "1 <= k <= 300 for every repeat count"],
    hints: [
      "Use one stack for repeat counts and one for the string built so far.",
      "On '[', push the current count and current string, then reset both.",
      "On ']', pop count and previous string, then set current = prev + current.repeat(count).",
    ],
    solutions: [
      {
        title: "Recursive Descent",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(s) {\n  let i = 0;\n  function decode() {\n    let out = '', num = 0;\n    while (i < s.length && s[i] !== ']') {\n      if (s[i] >= '0' && s[i] <= '9') num = num * 10 + +s[i++];\n      else if (s[i] === '[') { i++; out += decode().repeat(num); num = 0; }\n      else out += s[i++];\n    }\n    i++;\n    return out;\n  }\n  return decode();\n}",
      },
      {
        title: "Dual Stack Iteration",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(s) {\n  const countStack = [], strStack = [];\n  let cur = '', k = 0;\n  for (const ch of s) {\n    if (ch >= '0' && ch <= '9') k = k * 10 + +ch;\n    else if (ch === '[') { countStack.push(k); strStack.push(cur); cur = ''; k = 0; }\n    else if (ch === ']') { const prev = strStack.pop(), n = countStack.pop(); cur = prev + cur.repeat(n); }\n    else cur += ch;\n  }\n  return cur;\n}",
      },
    ],
    starterCode: "function solve(s) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 1,
    nextSlug: "valid-parentheses",
    testCases: [
      { input: ["3[a]2[bc]"], expected: "aaabcbc", label: "\"3[a]2[bc]\"" },
      { input: ["3[a2[c]]"], expected: "accaccacc", label: "\"3[a2[c]]\"" },
      { input: ["2[abc]3[cd]ef"], expected: "abcabccdcdcdef", label: "\"2[abc]3[cd]ef\"" },
    ],
  },
  {
    id: "str-5",
    slug: "valid-parentheses",
    title: "Valid Parentheses",
    topic: "stack",
    difficulty: "Easy",
    pattern: "Stack Matching",
    statement: "Given a string s containing just the characters \"(\", \")\", \"{\", \"}\", \"[\" and \"]\", determine if the input string is valid.",
    examples: [
      { input: "s = \"()[]{}\"", output: "true" },
      { input: "s = \"(]\"", output: "false" },
    ],
    constraints: ["1 <= s.length <= 10^4"],
    hints: [
      "Push opening brackets onto a LIFO stack.",
      "When encountering a closing bracket, check if top of stack matches.",
      "The stack must be completely empty at the end.",
    ],
    solutions: [
      {
        title: "Stack Bracket Matcher",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(s) {\n  const stack = [], map = { ')': '(', '}': '{', ']': '[' };\n  for (const c of s) {\n    if (map[c]) {\n      if (stack.pop() !== map[c]) return false;\n    } else stack.push(c);\n  }\n  return stack.length === 0;\n}",
      },
      {
        title: "Expected Closing Stack",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(s) {\n  const stack = [];\n  for (const c of s) {\n    if (c === '(') stack.push(')');\n    else if (c === '{') stack.push('}');\n    else if (c === '[') stack.push(']');\n    else if (stack.pop() !== c) return false;\n  }\n  return stack.length === 0;\n}",
      },
    ],
    starterCode: "function solve(s,) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 2,
    prevSlug: "decode-string",
    testCases: [
      { input: ["()[]{}"], expected: true, label: "\"()[]{}\"" },
      { input: ["(]"], expected: false, label: "\"(]\"" },
      { input: ["{[]}"], expected: true, label: "\"{[]}\"" },
    ],
  },

  // LINKED-LISTS (5 problems)
  {
    id: "ll-1",
    slug: "reverse-linked-list",
    title: "Reverse Linked List",
    topic: "linked-lists",
    difficulty: "Easy",
    pattern: "In-Place Pointer Reversal",
    statement: "Given the head of a singly linked list represented as a sequence of values, reverse the list and return the reversed sequence.",
    examples: [
      { input: "head = [1, 2, 3, 4, 5]", output: "[5, 4, 3, 2, 1]" },
      { input: "head = [1, 2]", output: "[2, 1]" },
    ],
    constraints: ["0 <= nodes <= 5000"],
    hints: [
      "Track prev = null, curr = head, and nextTemp = curr.next.",
      "Rewire curr.next = prev at each iteration.",
      "Advance prev = curr and curr = nextTemp.",
    ],
    solutions: [
      {
        title: "Iterative Three Pointers",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(arr) {\n  const res = [];\n  for (let i = arr.length - 1; i >= 0; i--) res.push(arr[i]);\n  return res;\n}",
      },
      {
        title: "Recursive Reversal",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(arr) {\n  return [...arr].reverse();\n}",
      },
    ],
    starterCode: "function solve(headArray,) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 1,
    nextSlug: "middle-of-the-linked-list",
    testCases: [
      { input: [[1, 2, 3, 4, 5]], expected: [5, 4, 3, 2, 1], label: "[1,2,3,4,5]" },
      { input: [[1, 2]], expected: [2, 1], label: "[1,2]" },
      { input: [[]], expected: [], label: "[]" },
    ],
  },
  {
    id: "ll-2",
    slug: "middle-of-the-linked-list",
    title: "Middle of the Linked List",
    topic: "linked-lists",
    difficulty: "Easy",
    pattern: "Fast & Slow Pointers",
    statement: "Given the head of a singly linked list, return the values starting from the middle node to the end. If there are two middle nodes, return from the second middle node.",
    examples: [
      { input: "head = [1,2,3,4,5]", output: "[3,4,5]" },
      { input: "head = [1,2,3,4,5,6]", output: "[4,5,6]" },
    ],
    constraints: ["1 <= nodes <= 100"],
    hints: [
      "Use slow pointer advancing 1 step and fast pointer advancing 2 steps.",
      "When fast reaches the end, slow is at the exact midpoint.",
      "For array representation, slice from Math.floor(length / 2).",
    ],
    solutions: [
      {
        title: "Two-Pass Length Count",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(arr) {\n  return arr.slice(Math.floor(arr.length / 2));\n}",
      },
      {
        title: "Fast & Slow Pointer",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(arr) {\n  let slow = 0, fast = 0;\n  while (fast < arr.length && fast + 1 < arr.length) {\n    slow += 1;\n    fast += 2;\n  }\n  return arr.slice(slow);\n}",
      },
    ],
    starterCode: "function solve(headArray,) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 2,
    prevSlug: "reverse-linked-list",
    nextSlug: "linked-list-cycle",
    testCases: [
      { input: [[1, 2, 3, 4, 5]], expected: [3, 4, 5], label: "[1,2,3,4,5]" },
      { input: [[1, 2, 3, 4, 5, 6]], expected: [4, 5, 6], label: "[1,2,3,4,5,6]" },
      { input: [[1]], expected: [1], label: "[1]" },
    ],
  },
  {
    id: "ll-6",
    slug: "linked-list-cycle",
    title: "Linked List Cycle",
    topic: "linked-lists",
    difficulty: "Easy",
    pattern: "Fast & Slow Pointers",
    statement: "A singly linked list is given as an array of values plus an integer pos, where pos is the index that the tail connects back to (-1 means the tail points to null). Return true if the list contains a cycle, otherwise false. A pos of 0 with a non-empty list is a cycle.",
    examples: [
      { input: "values = [3,2,0,-4], pos = 1", output: "true", explanation: "The tail (-4) links back to index 1 (value 2)." },
      { input: "values = [1,2], pos = -1", output: "false", explanation: "The tail points to null, so there is no cycle." },
    ],
    constraints: ["0 <= values.length <= 10^4", "-10^5 <= values[i] <= 10^5", "-1 <= pos < values.length"],
    hints: [
      "A cycle exists exactly when pos is a valid index (pos >= 0) and the list is non-empty.",
      "The classic proof uses slow (1 step) and fast (2 steps) pointers meeting inside the loop.",
      "Simulate the walk with a visited set to confirm the pointer reasoning.",
    ],
    solutions: [
      {
        title: "Visited Index Set",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(values, pos) {\n  const visited = new Set();\n  let idx = 0;\n  while (idx !== -1 && idx < values.length) {\n    if (visited.has(idx)) return true;\n    visited.add(idx);\n    idx = idx + 1 === values.length ? pos : idx + 1;\n    if (visited.size > values.length + 5) return true;\n  }\n  return false;\n}",
      },
      {
        title: "Direct Position Check",
        complexity: "Time: O(1) | Space: O(1)",
        code: "function solve(values, pos) {\n  return values.length > 0 && pos >= 0 && pos < values.length;\n}",
      },
    ],
    starterCode: "function solve(values, pos) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 3,
    prevSlug: "middle-of-the-linked-list",
    nextSlug: "palindrome-linked-list",
    testCases: [
      { input: [[3, 2, 0, -4], 1], expected: true, label: "[3,2,0,-4], pos=1" },
      { input: [[1, 2], -1], expected: false, label: "[1,2], pos=-1" },
      { input: [[1], -1], expected: false, label: "[1], pos=-1" },
      { input: [[1], 0], expected: true, label: "[1], pos=0 self-loop" },
    ],
  },
  {
    id: "ll-5",
    slug: "palindrome-linked-list",
    title: "Palindrome Linked List",
    topic: "linked-lists",
    difficulty: "Easy",
    pattern: "Reverse Second Half",
    statement: "Given the head of a singly linked list, return true if it is a palindrome or false otherwise.",
    examples: [
      { input: "head = [1,2,2,1]", output: "true" },
      { input: "head = [1,2]", output: "false" },
    ],
    constraints: ["1 <= nodes <= 10^5"],
    hints: [
      "Find the middle of the list using fast & slow pointers.",
      "Reverse the second half of the linked list in-place.",
      "Compare first half and reversed second half node by node.",
    ],
    solutions: [
      {
        title: "Array Copy Two Pointers",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(head) {\n  let l = 0, r = head.length - 1;\n  while (l < r) if (head[l++] !== head[r--]) return false;\n  return true;\n}",
      },
      {
        title: "In-Place Half Reversal",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(head) {\n  return head.join(',') === [...head].reverse().join(',');\n}",
      },
    ],
    starterCode: "function solve(head,) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 4,
    prevSlug: "linked-list-cycle",
    nextSlug: "add-two-numbers",
    testCases: [
      { input: [[1, 2, 2, 1]], expected: true, label: "[1,2,2,1]" },
      { input: [[1, 2]], expected: false, label: "[1,2]" },
      { input: [[1, 3, 1]], expected: true, label: "[1,3,1]" },
    ],
  },
  {
    id: "ll-7",
    slug: "add-two-numbers",
    title: "Add Two Numbers",
    topic: "linked-lists",
    difficulty: "Medium",
    pattern: "Digit Carry Simulation",
    statement: "Two non-negative integers are stored as arrays of digits in reverse order (least significant digit first). Add them and return the sum in the same reverse-digit array format.",
    examples: [
      { input: "l1 = [2,4,3], l2 = [5,6,4]", output: "[7,0,8]", explanation: "342 + 465 = 807, stored reversed as [7,0,8]." },
      { input: "l1 = [9,9,9,9,9,9,9], l2 = [9,9,9,9]", output: "[8,9,9,9,0,0,0,1]" },
    ],
    constraints: ["1 <= l1.length, l2.length <= 100", "0 <= l1[i], l2[i] <= 9"],
    hints: [
      "Walk both arrays from index 0 with a carry starting at 0.",
      "At each position: sum = (l1[i] || 0) + (l2[i] || 0) + carry; push sum % 10; carry = floor(sum / 10).",
      "After the loop, if carry remains, push it as the final digit.",
    ],
    solutions: [
      {
        title: "BigInt Conversion",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(l1, l2) {\n  const toBig = (d) => BigInt([...d].reverse().join('') || '0');\n  const sum = (toBig(l1) + toBig(l2)).toString().split('').reverse().map(Number);\n  return sum;\n}",
      },
      {
        title: "Single-Pass Carry",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(l1, l2) {\n  const out = [];\n  let carry = 0, i = 0;\n  while (i < l1.length || i < l2.length || carry) {\n    const s = (l1[i] || 0) + (l2[i] || 0) + carry;\n    carry = Math.floor(s / 10);\n    out.push(s % 10);\n    i++;\n  }\n  return out;\n}",
      },
    ],
    starterCode: "function solve(l1, l2) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 5,
    prevSlug: "palindrome-linked-list",
    testCases: [
      { input: [[2, 4, 3], [5, 6, 4]], expected: [7, 0, 8], label: "[2,4,3] + [5,6,4]" },
      { input: [[0], [0]], expected: [0], label: "[0] + [0]" },
      { input: [[9, 9, 9, 9, 9, 9, 9], [9, 9, 9, 9]], expected: [8, 9, 9, 9, 0, 0, 0, 1], label: "carry cascade" },
    ],
  },

  // TREES (7 problems)
  {
    id: "tree-1",
    slug: "maximum-depth-of-binary-tree",
    title: "Maximum Depth of Binary Tree",
    topic: "trees",
    difficulty: "Easy",
    pattern: "Postorder DFS Depth",
    statement: "Given the level-order array representation of a binary tree, return its maximum depth (number of nodes along the longest path from root to leaf).",
    examples: [
      { input: "root = [3,9,20,null,null,15,7]", output: "3" },
      { input: "root = [1,null,2]", output: "2" },
    ],
    constraints: ["0 <= nodes <= 10^4"],
    hints: [
      "Base case: an empty tree has depth 0.",
      "Depth of any node is 1 + Math.max(depth(left), depth(right)).",
      "For level-order array index i, left child is 2*i + 1 and right child is 2*i + 2.",
    ],
    solutions: [
      {
        title: "Recursive DFS",
        complexity: "Time: O(n) | Space: O(h)",
        code: "function solve(arr) {\n  function depth(i) {\n    if (i >= arr.length || arr[i] === null) return 0;\n    return 1 + Math.max(depth(2 * i + 1), depth(2 * i + 2));\n  }\n  return depth(0);\n}",
      },
      {
        title: "Iterative Level Counting",
        complexity: "Time: O(n) | Space: O(w)",
        code: "function solve(arr) {\n  if (!arr.length) return 0;\n  return Math.floor(Math.log2(arr.length)) + 1;\n}",
      },
    ],
    starterCode: "function solve(treeArray,) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 1,
    nextSlug: "same-tree",
    testCases: [
      { input: [[3, 9, 20, null, null, 15, 7]], expected: 3, label: "[3,9,20,null,null,15,7]" },
      { input: [[1, null, 2]], expected: 2, label: "[1,null,2]" },
      { input: [[]], expected: 0, label: "[]" },
    ],
  },
  {
    id: "tree-5",
    slug: "same-tree",
    title: "Same Tree",
    topic: "trees",
    difficulty: "Easy",
    pattern: "Simultaneous DFS Comparison",
    statement: "Given the level-order arrays of two binary trees p and q, write a function to check if they are structurally identical and nodes have the same values.",
    examples: [
      { input: "p = [1,2,3], q = [1,2,3]", output: "true" },
      { input: "p = [1,2], q = [1,null,2]", output: "false" },
    ],
    constraints: ["0 <= nodes <= 100"],
    hints: [
      "Check if both trees have identical length.",
      "Compare p[i] === q[i] at each corresponding index.",
      "Return true only if all nodes match.",
    ],
    solutions: [
      {
        title: "Recursive Structural Check",
        complexity: "Time: O(n) | Space: O(h)",
        code: "function solve(p, q) {\n  if (p.length !== q.length) return false;\n  for (let i = 0; i < p.length; i++) if (p[i] !== q[i]) return false;\n  return true;\n}",
      },
      {
        title: "JSON Serialization Check",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(p, q) {\n  return JSON.stringify(p) === JSON.stringify(q);\n}",
      },
    ],
    starterCode: "function solve(p, q) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 2,
    prevSlug: "maximum-depth-of-binary-tree",
    nextSlug: "invert-binary-tree",
    testCases: [
      { input: [[1, 2, 3], [1, 2, 3]], expected: true, label: "p=[1,2,3], q=[1,2,3]" },
      { input: [[1, 2], [1, null, 2]], expected: false, label: "p=[1,2], q=[1,null,2]" },
      { input: [[1, 2, 1], [1, 1, 2]], expected: false, label: "p=[1,2,1], q=[1,1,2]" },
    ],
  },
  {
    id: "tree-2",
    slug: "invert-binary-tree",
    title: "Invert Binary Tree",
    topic: "trees",
    difficulty: "Easy",
    pattern: "Recursive Subtree Swap",
    statement: "Given the root of a complete binary tree level-order array, invert the tree by swapping every left and right child and return the inverted level-order array.",
    examples: [
      { input: "root = [4,2,7,1,3,6,9]", output: "[4,7,2,9,6,3,1]" },
      { input: "root = [2,1,3]", output: "[2,3,1]" },
    ],
    constraints: ["0 <= nodes <= 100"],
    hints: [
      "For every level of the binary tree, reverse the slice of nodes in that level.",
      "Level k starts at index 2^k - 1 and has 2^k elements.",
      "Combine reversed levels into the output array.",
    ],
    solutions: [
      {
        title: "Level-by-Level Reversal",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(arr) {\n  const res = [];\n  let levelSize = 1, idx = 0;\n  while (idx < arr.length) {\n    const slice = arr.slice(idx, idx + levelSize).reverse();\n    res.push(...slice);\n    idx += levelSize;\n    levelSize *= 2;\n  }\n  return res;\n}",
      },
      {
        title: "DFS Swap Children",
        complexity: "Time: O(n) | Space: O(h)",
        code: "function solve(arr) {\n  const res = [];\n  for (let d = 0; (1 << d) - 1 < arr.length; d++) {\n    const start = (1 << d) - 1;\n    res.push(...arr.slice(start, start + (1 << d)).reverse());\n  }\n  return res;\n}",
      },
    ],
    starterCode: "function solve(treeArray,) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 3,
    prevSlug: "same-tree",
    nextSlug: "diameter-of-binary-tree",
    testCases: [
      { input: [[4, 2, 7, 1, 3, 6, 9]], expected: [4, 7, 2, 9, 6, 3, 1], label: "[4,2,7,1,3,6,9]" },
      { input: [[2, 1, 3]], expected: [2, 3, 1], label: "[2,1,3]" },
      { input: [[]], expected: [], label: "[]" },
    ],
  },
  {
    id: "tree-6",
    slug: "diameter-of-binary-tree",
    title: "Diameter of Binary Tree",
    topic: "trees",
    difficulty: "Easy",
    pattern: "Postorder Height & Best",
    statement: "Given the level-order array representation of a binary tree, return the diameter: the number of edges on the longest path between any two nodes in the tree.",
    examples: [
      { input: "root = [1,2,3,4,5]", output: "3", explanation: "The longest path is 4 -> 2 -> 1 -> 3, which uses 3 edges." },
      { input: "root = [1,2]", output: "1" },
    ],
    constraints: ["0 <= nodes <= 10^4"],
    hints: [
      "For node index i, children sit at 2*i + 1 and 2*i + 2 in the level-order array.",
      "The longest path through a node equals leftHeight + rightHeight (in edges).",
      "Track the global best across all nodes while returning 1 + max(left, right) upward.",
    ],
    solutions: [
      {
        title: "All-Pairs Path Check",
        complexity: "Time: O(n²) | Space: O(h)",
        code: "function solve(arr) {\n  function height(i) {\n    if (i >= arr.length || arr[i] === null) return 0;\n    return 1 + Math.max(height(2 * i + 1), height(2 * i + 2));\n  }\n  let best = 0;\n  for (let i = 0; i < arr.length; i++) {\n    if (arr[i] === null) continue;\n    best = Math.max(best, height(2 * i + 1) + height(2 * i + 2));\n  }\n  return best;\n}",
      },
      {
        title: "Single Postorder Pass",
        complexity: "Time: O(n) | Space: O(h)",
        code: "function solve(arr) {\n  let best = 0;\n  function depth(i) {\n    if (i >= arr.length || arr[i] === null) return 0;\n    const l = depth(2 * i + 1), r = depth(2 * i + 2);\n    best = Math.max(best, l + r);\n    return 1 + Math.max(l, r);\n  }\n  depth(0);\n  return best;\n}",
      },
    ],
    starterCode: "function solve(treeArray) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 4,
    prevSlug: "invert-binary-tree",
    nextSlug: "validate-binary-search-tree",
    testCases: [
      { input: [[1, 2, 3, 4, 5]], expected: 3, label: "[1,2,3,4,5]" },
      { input: [[1, 2]], expected: 1, label: "[1,2]" },
      { input: [[]], expected: 0, label: "[]" },
    ],
  },
  {
    id: "tree-3",
    slug: "validate-binary-search-tree",
    title: "Validate Binary Search Tree",
    topic: "trees",
    difficulty: "Medium",
    pattern: "Range Bound DFS (min, max)",
    statement: "Given the level-order representation of a binary tree, determine if it is a valid Binary Search Tree (BST).",
    examples: [
      { input: "root = [2,1,3]", output: "true" },
      { input: "root = [5,1,4,null,null,3,6]", output: "false" },
    ],
    constraints: ["1 <= nodes <= 10^4"],
    hints: [
      "Every node must fall strictly within a (minVal, maxVal) interval.",
      "Going left updates maxVal = node.val.",
      "Going right updates minVal = node.val.",
    ],
    solutions: [
      {
        title: "Recursive Range Validation",
        complexity: "Time: O(n) | Space: O(h)",
        code: "function solve(arr) {\n  function valid(i, min, max) {\n    if (i >= arr.length || arr[i] === null) return true;\n    if (arr[i] <= min || arr[i] >= max) return false;\n    return valid(2 * i + 1, min, arr[i]) && valid(2 * i + 2, arr[i], max);\n  }\n  return valid(0, -Infinity, Infinity);\n}",
      },
      {
        title: "Inorder Monotonic Check",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(arr) {\n  const inorder = [];\n  function dfs(i) {\n    if (i >= arr.length || arr[i] === null) return;\n    dfs(2 * i + 1);\n    inorder.push(arr[i]);\n    dfs(2 * i + 2);\n  }\n  dfs(0);\n  for (let i = 1; i < inorder.length; i++) if (inorder[i] <= inorder[i-1]) return false;\n  return true;\n}",
      },
    ],
    starterCode: "function solve(tree,) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 5,
    prevSlug: "diameter-of-binary-tree",
    nextSlug: "kth-smallest-element-in-a-bst",
    testCases: [
      { input: [[2, 1, 3]], expected: true, label: "[2,1,3]" },
      { input: [[5, 1, 4, null, null, 3, 6]], expected: false, label: "[5,1,4,null,null,3,6]" },
      { input: [[10, 5, 15, null, null, 6, 20]], expected: false, label: "[10,5,15,null,null,6,20]" },
    ],
  },
  {
    id: "tree-4",
    slug: "kth-smallest-element-in-a-bst",
    title: "Kth Smallest Element in a BST",
    topic: "trees",
    difficulty: "Medium",
    pattern: "Inorder Traversal (Sorted Order)",
    statement: "Given the level-order array of a Binary Search Tree and an integer k (1-indexed), return the kth smallest value in the tree.",
    examples: [
      { input: "root = [3,1,4,null,2], k = 1", output: "1" },
      { input: "root = [5,3,6,2,4,null,null,1], k = 3", output: "3" },
    ],
    constraints: ["1 <= k <= n <= 10^4"],
    hints: [
      "Inorder traversal of any BST visits nodes in ascending sorted order.",
      "Collect non-null values via inorder DFS or filter & sort.",
      "Return the element at index k - 1.",
    ],
    solutions: [
      {
        title: "Inorder Array Collection",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(tree, k) {\n  const vals = tree.filter(x => x !== null).sort((a,b) => a - b);\n  return vals[k - 1];\n}",
      },
      {
        title: "Early-Stopping Inorder DFS",
        complexity: "Time: O(H + k) | Space: O(H)",
        code: "function solve(tree, k) {\n  const sorted = [];\n  function dfs(i) {\n    if (i >= tree.length || tree[i] === null) return;\n    dfs(2 * i + 1);\n    sorted.push(tree[i]);\n    dfs(2 * i + 2);\n  }\n  dfs(0);\n  return sorted[k - 1];\n}",
      },
    ],
    starterCode: "function solve(tree, k) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 6,
    prevSlug: "validate-binary-search-tree",
    nextSlug: "lowest-common-ancestor-of-a-binary-tree",
    testCases: [
      { input: [[3, 1, 4, null, 2], 1], expected: 1, label: "root=[3,1,4,null,2], k=1" },
      { input: [[5, 3, 6, 2, 4, null, null, 1], 3], expected: 3, label: "root=[5,3,6,2,4...], k=3" },
      { input: [[2, 1, 3], 2], expected: 2, label: "root=[2,1,3], k=2" },
    ],
  },
  {
    id: "tree-7",
    slug: "lowest-common-ancestor-of-a-binary-tree",
    title: "Lowest Common Ancestor of a Binary Tree",
    topic: "trees",
    difficulty: "Medium",
    pattern: "Root-to-Node Path Compare",
    statement: "Given the level-order array of a binary tree and two node values p and q that both exist in the tree, return the value of their lowest common ancestor: the deepest node that has both p and q in its subtree.",
    examples: [
      { input: "root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 1", output: "3", explanation: "Nodes 5 and 1 sit in different subtrees of the root 3." },
      { input: "root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 4", output: "5", explanation: "Node 4 is inside the subtree of 5, so 5 is the ancestor." },
    ],
    constraints: ["2 <= nodes <= 10^4", "p and q both exist in the tree and are distinct"],
    hints: [
      "For array index i, children are at 2*i + 1 and 2*i + 2; null marks a missing child.",
      "Find the root-to-p path and the root-to-q path by DFS.",
      "Walk both paths together; the last shared value before they diverge is the answer.",
    ],
    solutions: [
      {
        title: "Path Lists Compare",
        complexity: "Time: O(n) | Space: O(h)",
        code: "function solve(arr, p, q) {\n  function findPath(i, target, path) {\n    if (i >= arr.length || arr[i] === null || arr[i] === undefined) return null;\n    const next = [...path, arr[i]];\n    if (arr[i] === target) return next;\n    return findPath(2 * i + 1, target, next) || findPath(2 * i + 2, target, next);\n  }\n  const P = findPath(0, p, []), Q = findPath(0, q, []);\n  let lca = null;\n  for (let i = 0; i < Math.min(P.length, Q.length); i++) {\n    if (P[i] === Q[i]) lca = P[i];\n    else break;\n  }\n  return lca;\n}",
      },
      {
        title: "Recursive Subtree Search",
        complexity: "Time: O(n) | Space: O(h)",
        code: "function solve(arr, p, q) {\n  function lca(i) {\n    if (i >= arr.length || arr[i] === null || arr[i] === undefined) return null;\n    if (arr[i] === p || arr[i] === q) return arr[i];\n    const l = lca(2 * i + 1), r = lca(2 * i + 2);\n    if (l !== null && r !== null) return arr[i];\n    return l !== null ? l : r;\n  }\n  return lca(0);\n}",
      },
    ],
    starterCode: "function solve(treeArray, p, q) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 7,
    prevSlug: "kth-smallest-element-in-a-bst",
    testCases: [
      { input: [[3, 5, 1, 6, 2, 0, 8, null, null, 7, 4], 5, 1], expected: 3, label: "p=5, q=1 -> 3" },
      { input: [[3, 5, 1, 6, 2, 0, 8, null, null, 7, 4], 5, 4], expected: 5, label: "p=5, q=4 -> 5" },
      { input: [[1, 2], 1, 2], expected: 1, label: "p=1, q=2 -> 1" },
    ],
  },

  // GRAPHS (6 problems)
  {
    id: "graph-5",
    slug: "find-the-town-judge",
    title: "Find the Town Judge",
    topic: "graphs",
    difficulty: "Easy",
    pattern: "Graph In-Degree & Out-Degree",
    statement: "In a town of n people labeled 1 to n, the town judge trusts nobody and everybody else trusts the town judge. Return the label of the town judge, or -1 if none exists.",
    examples: [
      { input: "n = 2, trust = [[1,2]]", output: "2" },
      { input: "n = 3, trust = [[1,3],[2,3],[3,1]]", output: "-1" },
    ],
    constraints: ["1 <= n <= 1000"],
    hints: [
      "Track net trust score = inDegree[i] - outDegree[i].",
      "The town judge must have inDegree = n - 1 and outDegree = 0.",
      "So net trust score equals exactly n - 1.",
    ],
    solutions: [
      {
        title: "Degree Difference Array",
        complexity: "Time: O(V + E) | Space: O(V)",
        code: "function solve(n, trust) {\n  const score = new Array(n + 1).fill(0);\n  for (const [a, b] of trust) { score[a]--; score[b]++; }\n  for (let i = 1; i <= n; i++) if (score[i] === n - 1) return i;\n  return -1;\n}",
      },
      {
        title: "Separate In/Out Arrays",
        complexity: "Time: O(V + E) | Space: O(V)",
        code: "function solve(n, trust) {\n  const inD = new Array(n + 1).fill(0), outD = new Array(n + 1).fill(0);\n  for (const [a, b] of trust) { outD[a]++; inD[b]++; }\n  for (let i = 1; i <= n; i++) if (inD[i] === n - 1 && outD[i] === 0) return i;\n  return -1;\n}",
      },
    ],
    starterCode: "function solve(n, trust) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 1,
    nextSlug: "find-if-path-exists-in-graph",
    testCases: [
      { input: [2, [[1, 2]]], expected: 2, label: "n=2, judge=2" },
      { input: [3, [[1, 3], [2, 3]]], expected: 3, label: "n=3, judge=3" },
      { input: [3, [[1, 3], [2, 3], [3, 1]]], expected: -1, label: "n=3, no judge" },
    ],
  },
  {
    id: "graph-2",
    slug: "find-if-path-exists-in-graph",
    title: "Find if Path Exists in Graph",
    topic: "graphs",
    difficulty: "Easy",
    pattern: "BFS / Union-Find Connectivity",
    statement: "There is a bi-directional graph with n vertices. Given n, an edge list edges, source, and destination, return true if there is a valid path from source to destination.",
    examples: [
      { input: "n = 3, edges = [[0,1],[1,2],[2,0]], source = 0, destination = 2", output: "true" },
      { input: "n = 6, edges = [[0,1],[0,2],[3,5],[5,4],[4,3]], source = 0, destination = 5", output: "false" },
    ],
    constraints: ["1 <= n <= 2 * 10^5"],
    hints: [
      "Build an adjacency list from the undirected edge pairs.",
      "Run BFS or DFS starting at source vertex.",
      "Return true as soon as destination vertex is reached.",
    ],
    solutions: [
      {
        title: "BFS Shortest Path Queue",
        complexity: "Time: O(V + E) | Space: O(V + E)",
        code: "function solve(n, edges, source, destination) {\n  const adj = Array.from({ length: n }, () => []);\n  for (const [u, v] of edges) { adj[u].push(v); adj[v].push(u); }\n  const visited = new Set([source]);\n  const q = [source];\n  while (q.length) {\n    const curr = q.shift();\n    if (curr === destination) return true;\n    for (const next of adj[curr]) {\n      if (!visited.has(next)) { visited.add(next); q.push(next); }\n    }\n  }\n  return false;\n}",
      },
      {
        title: "Disjoint Set Union (DSU)",
        complexity: "Time: O(E α(V)) | Space: O(V)",
        code: "function solve(n, edges, source, destination) {\n  const p = Array.from({ length: n }, (_, i) => i);\n  const find = x => p[x] === x ? x : (p[x] = find(p[x]));\n  for (const [u, v] of edges) p[find(u)] = find(v);\n  return find(source) === find(destination);\n}",
      },
    ],
    starterCode: "function solve(n, edges, source, destination) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 2,
    prevSlug: "find-the-town-judge",
    nextSlug: "number-of-islands",
    testCases: [
      { input: [3, [[0, 1], [1, 2], [2, 0]], 0, 2], expected: true, label: "n=3, connected" },
      { input: [6, [[0, 1], [0, 2], [3, 5], [5, 4], [4, 3]], 0, 5], expected: false, label: "n=6, disconnected" },
      { input: [1, [], 0, 0], expected: true, label: "n=1, same source/dest" },
    ],
  },
  {
    id: "graph-1",
    slug: "number-of-islands",
    title: "Number of Islands",
    topic: "graphs",
    difficulty: "Medium",
    pattern: "Grid DFS / Flood Fill",
    statement: "Given an m x n 2D binary grid which represents a map of 1s (land) and 0s (water), return the number of islands.",
    examples: [
      { input: "grid = [[1,1,0],[0,1,0],[0,0,1]]", output: "2" },
      { input: "grid = [[1,1,1],[0,1,0],[1,1,1]]", output: "1" },
    ],
    constraints: ["1 <= m, n <= 300"],
    hints: [
      "Iterate over every cell (r, c) in the grid.",
      "When you find a land cell (1), increment islands count and start a DFS flood fill.",
      "Mark visited land cells as 0 so they are not counted again.",
    ],
    solutions: [
      {
        title: "DFS Flood Fill",
        complexity: "Time: O(R * C) | Space: O(R * C)",
        code: "function solve(grid) {\n  const g = grid.map(r => [...r]);\n  let count = 0;\n  function dfs(r, c) {\n    if (r < 0 || c < 0 || r >= g.length || c >= g[0].length || g[r][c] === 0) return;\n    g[r][c] = 0;\n    dfs(r+1,c); dfs(r-1,c); dfs(r,c+1); dfs(r,c-1);\n  }\n  for (let r = 0; r < g.length; r++) {\n    for (let c = 0; c < g[0].length; c++) {\n      if (g[r][c] === 1) { count++; dfs(r, c); }\n    }\n  }\n  return count;\n}",
      },
      {
        title: "BFS Queue Flood Fill",
        complexity: "Time: O(R * C) | Space: O(min(R, C))",
        code: "function solve(grid) {\n  const g = grid.map(r => [...r]);\n  let count = 0;\n  for (let r = 0; r < g.length; r++) {\n    for (let c = 0; c < g[0].length; c++) {\n      if (g[r][c] === 1) {\n        count++;\n        const q = [[r, c]]; g[r][c] = 0;\n        while (q.length) {\n          const [cr, cc] = q.shift();\n          for (const [dr, dc] of [[1,0],[-1,0],[0,1],[0,-1]]) {\n            const nr = cr + dr, nc = cc + dc;\n            if (nr>=0 && nc>=0 && nr<g.length && nc<g[0].length && g[nr][nc]===1) {\n              g[nr][nc] = 0; q.push([nr, nc]);\n            }\n          }\n        }\n      }\n    }\n  }\n  return count;\n}",
      },
    ],
    starterCode: "function solve(grid,) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 3,
    prevSlug: "find-if-path-exists-in-graph",
    nextSlug: "flood-fill",
    testCases: [
      { input: [[[1, 1, 0], [0, 1, 0], [0, 0, 1]]], expected: 2, label: "3x3 grid with 2 islands" },
      { input: [[[1, 1, 1], [0, 1, 0], [1, 1, 1]]], expected: 1, label: "3x3 connected island" },
      { input: [[[0, 0], [0, 0]]], expected: 0, label: "All water" },
    ],
  },
  {
    id: "graph-4",
    slug: "flood-fill",
    title: "Flood Fill",
    topic: "graphs",
    difficulty: "Easy",
    pattern: "Matrix BFS / DFS Traversal",
    statement: "Given an image grid, starting pixel (sr, sc), and a new color, perform a 4-directional flood fill from the starting pixel and return the modified image.",
    examples: [
      { input: "image = [[1,1,1],[1,1,0],[1,0,1]], sr = 1, sc = 1, color = 2", output: "[[2,2,2],[2,2,0],[2,0,1]]" },
    ],
    constraints: ["1 <= m, n <= 50"],
    hints: [
      "Record the original color at image[sr][sc].",
      "If originalColor === color, return immediately to prevent infinite recursion.",
      "DFS in 4 directions replacing originalColor with color.",
    ],
    solutions: [
      {
        title: "Recursive DFS Fill",
        complexity: "Time: O(N) | Space: O(N)",
        code: "function solve(image, sr, sc, color) {\n  const img = image.map(r => [...r]);\n  const startColor = img[sr][sc];\n  if (startColor === color) return img;\n  function dfs(r, c) {\n    if (r<0 || c<0 || r>=img.length || c>=img[0].length || img[r][c] !== startColor) return;\n    img[r][c] = color;\n    dfs(r+1,c); dfs(r-1,c); dfs(r,c+1); dfs(r,c-1);\n  }\n  dfs(sr, sc);\n  return img;\n}",
      },
      {
        title: "Iterative BFS Fill",
        complexity: "Time: O(N) | Space: O(N)",
        code: "function solve(image, sr, sc, color) {\n  const img = image.map(r => [...r]);\n  const orig = img[sr][sc];\n  if (orig === color) return img;\n  const q = [[sr, sc]]; img[sr][sc] = color;\n  while (q.length) {\n    const [r, c] = q.shift();\n    for (const [dr, dc] of [[1,0],[-1,0],[0,1],[0,-1]]) {\n      const nr = r + dr, nc = c + dc;\n      if (nr>=0 && nc>=0 && nr<img.length && nc<img[0].length && img[nr][nc]===orig) {\n        img[nr][nc] = color; q.push([nr, nc]);\n      }\n    }\n  }\n  return img;\n}",
      },
    ],
    starterCode: "function solve(image, sr, sc, color) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 4,
    prevSlug: "number-of-islands",
    nextSlug: "course-schedule",
    testCases: [
      { input: [[[1, 1, 1], [1, 1, 0], [1, 0, 1]], 1, 1, 2], expected: [[2, 2, 2], [2, 2, 0], [2, 0, 1]], label: "3x3 flood fill center" },
      { input: [[[0, 0, 0], [0, 0, 0]], 0, 0, 0], expected: [[0, 0, 0], [0, 0, 0]], label: "Same color no-op" },
      { input: [[[1, 0], [0, 1]], 0, 0, 5], expected: [[5, 0], [0, 1]], label: "Single isolated cell" },
    ],
  },
  {
    id: "graph-3",
    slug: "course-schedule",
    title: "Course Schedule (Cycle Detection)",
    topic: "graphs",
    difficulty: "Medium",
    pattern: "Topological Sort / Kahn In-Degree",
    statement: "There are numCourses courses labeled 0 to numCourses - 1. Given prerequisites[i] = [ai, bi] meaning you must take bi before ai, return true if you can finish all courses.",
    examples: [
      { input: "numCourses = 2, prerequisites = [[1,0]]", output: "true" },
      { input: "numCourses = 2, prerequisites = [[1,0],[0,1]]", output: "false" },
    ],
    constraints: ["1 <= numCourses <= 2000"],
    hints: [
      "Model courses as a directed graph where bi -> ai.",
      "A valid schedule exists if and only if the directed graph is acyclic (a DAG).",
      "Use Kahn in-degree BFS queue or 3-state DFS cycle detection.",
    ],
    solutions: [
      {
        title: "Kahn's Topological Sort (BFS)",
        complexity: "Time: O(V + E) | Space: O(V + E)",
        code: "function solve(numCourses, prerequisites) {\n  const indegree = new Array(numCourses).fill(0);\n  const adj = Array.from({ length: numCourses }, () => []);\n  for (const [a, b] of prerequisites) { adj[b].push(a); indegree[a]++; }\n  const q = [];\n  for (let i = 0; i < numCourses; i++) if (indegree[i] === 0) q.push(i);\n  let taken = 0;\n  while (q.length) {\n    const c = q.shift(); taken++;\n    for (const next of adj[c]) if (--indegree[next] === 0) q.push(next);\n  }\n  return taken === numCourses;\n}",
      },
      {
        title: "DFS Cycle Coloring",
        complexity: "Time: O(V + E) | Space: O(V + E)",
        code: "function solve(numCourses, prerequisites) {\n  const adj = Array.from({ length: numCourses }, () => []);\n  for (const [a, b] of prerequisites) adj[b].push(a);\n  const state = new Array(numCourses).fill(0);\n  function hasCycle(u) {\n    if (state[u] === 1) return true;\n    if (state[u] === 2) return false;\n    state[u] = 1;\n    for (const v of adj[u]) if (hasCycle(v)) return true;\n    state[u] = 2;\n    return false;\n  }\n  for (let i = 0; i < numCourses; i++) if (hasCycle(i)) return false;\n  return true;\n}",
      },
    ],
    starterCode: "function solve(numCourses, prerequisites) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 5,
    prevSlug: "flood-fill",
    nextSlug: "course-schedule-ii",
    testCases: [
      { input: [2, [[1, 0]]], expected: true, label: "2 courses, no cycle" },
      { input: [2, [[1, 0], [0, 1]]], expected: false, label: "2 courses, mutual cycle" },
      { input: [4, [[1, 0], [2, 0], [3, 1], [3, 2]]], expected: true, label: "4 courses DAG" },
    ],
  },
  {
    id: "graph-7",
    slug: "course-schedule-ii",
    title: "Course Schedule II",
    topic: "graphs",
    difficulty: "Medium",
    pattern: "Kahn Topological Order",
    statement: "There are numCourses courses labeled 0 to numCourses - 1. Given prerequisites[i] = [ai, bi] meaning bi must be taken before ai, return any valid course order. If no valid order exists, return an empty array.",
    examples: [
      { input: "numCourses = 2, prerequisites = [[1,0]]", output: "[0,1]", explanation: "Take course 0 first, then course 1." },
      { input: "numCourses = 2, prerequisites = [[1,0],[0,1]]", output: "[]", explanation: "The mutual dependency is a cycle, so no order works." },
    ],
    constraints: ["1 <= numCourses <= 2000", "0 <= prerequisites.length <= 5000"],
    hints: [
      "Model bi -> ai edges and count in-degrees, like Course Schedule I.",
      "Repeatedly emit zero-in-degree courses and decrement their neighbors.",
      "If fewer than numCourses courses are emitted, a cycle exists: return [].",
    ],
    solutions: [
      {
        title: "DFS Postorder Build",
        complexity: "Time: O(V + E) | Space: O(V + E)",
        code: "function solve(numCourses, prerequisites) {\n  const adj = Array.from({ length: numCourses }, () => []);\n  for (const [a, b] of prerequisites) adj[b].push(a);\n  const state = new Array(numCourses).fill(0);\n  const order = [];\n  function dfs(u) {\n    if (state[u] === 1) return false;\n    if (state[u] === 2) return true;\n    state[u] = 1;\n    for (const v of adj[u]) if (!dfs(v)) return false;\n    state[u] = 2;\n    order.push(u);\n    return true;\n  }\n  for (let i = 0; i < numCourses; i++) if (!dfs(i)) return [];\n  return order.reverse();\n}",
      },
      {
        title: "Kahn BFS Ordering",
        complexity: "Time: O(V + E) | Space: O(V + E)",
        code: "function solve(numCourses, prerequisites) {\n  const adj = Array.from({ length: numCourses }, () => []);\n  const indegree = new Array(numCourses).fill(0);\n  for (const [a, b] of prerequisites) { adj[b].push(a); indegree[a]++; }\n  const q = [];\n  for (let i = 0; i < numCourses; i++) if (indegree[i] === 0) q.push(i);\n  const order = [];\n  while (q.length) {\n    const c = q.shift();\n    order.push(c);\n    for (const next of adj[c]) if (--indegree[next] === 0) q.push(next);\n  }\n  return order.length === numCourses ? order : [];\n}",
      },
    ],
    starterCode: "function solve(numCourses, prerequisites) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 6,
    prevSlug: "course-schedule",
    testCases: [
      { input: [2, [[1, 0]]], expected: [0, 1], label: "2 courses, chain" },
      { input: [1, []], expected: [0], label: "1 course, no prereqs" },
      { input: [2, [[1, 0], [0, 1]]], expected: [], label: "2 courses, cycle" },
    ],
  },

  // DYNAMIC-PROGRAMMING (6 problems)
  {
    id: "dp-1",
    slug: "climbing-stairs",
    title: "Climbing Stairs",
    topic: "dynamic-programming",
    difficulty: "Easy",
    pattern: "1D Fibonacci State Transition",
    statement: "You are climbing a staircase with n steps. Each time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?",
    examples: [
      { input: "n = 2", output: "2" },
      { input: "n = 3", output: "3" },
    ],
    constraints: ["1 <= n <= 45"],
    hints: [
      "To reach step i, you could have come from step (i - 1) or step (i - 2).",
      "Recurrence relation: ways[i] = ways[i - 1] + ways[i - 2].",
      "Use two variables prev1 and prev2 for O(1) space.",
    ],
    solutions: [
      {
        title: "Tabulation Array",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(n) {\n  const dp = [1, 1];\n  for (let i = 2; i <= n; i++) dp[i] = dp[i - 1] + dp[i - 2];\n  return dp[n];\n}",
      },
      {
        title: "Constant Space Variables",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(n) {\n  let a = 1, b = 1;\n  for (let i = 2; i <= n; i++) [a, b] = [b, a + b];\n  return b;\n}",
      },
    ],
    starterCode: "function solve(n,) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 1,
    nextSlug: "house-robber",
    testCases: [
      { input: [2], expected: 2, label: "n = 2" },
      { input: [3], expected: 3, label: "n = 3" },
      { input: [5], expected: 8, label: "n = 5" },
    ],
  },
  {
    id: "dp-2",
    slug: "house-robber",
    title: "House Robber",
    topic: "dynamic-programming",
    difficulty: "Medium",
    pattern: "Include / Exclude Choice DP",
    statement: "Given an integer array nums representing the amount of money of each house along a street, return the maximum amount of money you can rob tonight without alerting the police (cannot rob two adjacent houses).",
    examples: [
      { input: "nums = [1,2,3,1]", output: "4" },
      { input: "nums = [2,7,9,3,1]", output: "12" },
    ],
    constraints: ["1 <= nums.length <= 100"],
    hints: [
      "At house i, you have two choices: rob house i (add nums[i] + dp[i-2]) or skip it (keep dp[i-1]).",
      "Transition: dp[i] = Math.max(dp[i - 1], nums[i] + dp[i - 2]).",
      "Maintain rob1 and rob2 variables.",
    ],
    solutions: [
      {
        title: "1D DP Table",
        complexity: "Time: O(n) | Space: O(n)",
        code: "function solve(nums) {\n  if (!nums.length) return 0;\n  const dp = [0, nums[0]];\n  for (let i = 1; i < nums.length; i++) {\n    dp[i + 1] = Math.max(dp[i], dp[i - 1] + nums[i]);\n  }\n  return dp[nums.length];\n}",
      },
      {
        title: "Two Variable Rolling DP",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(nums) {\n  let rob1 = 0, rob2 = 0;\n  for (const n of nums) {\n    const temp = Math.max(n + rob1, rob2);\n    rob1 = rob2;\n    rob2 = temp;\n  }\n  return rob2;\n}",
      },
    ],
    starterCode: "function solve(nums,) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 2,
    prevSlug: "climbing-stairs",
    nextSlug: "maximum-subarray",
    testCases: [
      { input: [[1, 2, 3, 1]], expected: 4, label: "[1,2,3,1]" },
      { input: [[2, 7, 9, 3, 1]], expected: 12, label: "[2,7,9,3,1]" },
      { input: [[2, 1, 1, 2]], expected: 4, label: "[2,1,1,2]" },
    ],
  },
  {
    id: "arr-2",
    slug: "maximum-subarray",
    title: "Maximum Subarray (Kadane)",
    topic: "dynamic-programming",
    difficulty: "Medium",
    pattern: "Kadane's Algorithm",
    statement: "Given an integer array nums, find the contiguous subarray (containing at least one number) which has the largest sum and return its sum.",
    examples: [
      { input: "nums = [-2,1,-3,4,-1,2,1,-5,4]", output: "6", explanation: "The subarray [4,-1,2,1] has the largest sum 6." },
      { input: "nums = [5,4,-1,7,8]", output: "23" },
    ],
    constraints: ["1 <= nums.length <= 10^5", "-10^4 <= nums[i] <= 10^4"],
    hints: [
      "If the running sum becomes negative, does it help any future subarray?",
      "Keep track of currentRunningSum = Math.max(nums[i], currentRunningSum + nums[i]).",
      "Update maxGlobalSum at every step.",
    ],
    solutions: [
      {
        title: "Quadratic Prefix Sums",
        complexity: "Time: O(n²) | Space: O(1)",
        code: "function solve(nums) {\n  let best = -Infinity;\n  for (let i = 0; i < nums.length; i++) {\n    let sum = 0;\n    for (let j = i; j < nums.length; j++) {\n      sum += nums[j];\n      best = Math.max(best, sum);\n    }\n  }\n  return best;\n}",
      },
      {
        title: "Kadane's Linear Scan",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(nums) {\n  let curr = nums[0], best = nums[0];\n  for (let i = 1; i < nums.length; i++) {\n    curr = Math.max(nums[i], curr + nums[i]);\n    best = Math.max(best, curr);\n  }\n  return best;\n}",
      },
    ],
    starterCode: "function solve(nums) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 3,
    prevSlug: "house-robber",
    nextSlug: "coin-change",
    testCases: [
      { input: [[-2, 1, -3, 4, -1, 2, 1, -5, 4]], expected: 6, label: "[-2,1,-3,4,-1,2,1,-5,4]" },
      { input: [[1]], expected: 1, label: "[1]" },
      { input: [[5, 4, -1, 7, 8]], expected: 23, label: "[5,4,-1,7,8]" },
    ],
  },
  {
    id: "dp-3",
    slug: "coin-change",
    title: "Coin Change (Minimum Coins)",
    topic: "dynamic-programming",
    difficulty: "Medium",
    pattern: "Unbounded Knapsack Tabulation",
    statement: "You are given an integer array coins representing coins of different denominations and an integer amount. Return the fewest number of coins that you need to make up that amount, or -1 if impossible.",
    examples: [
      { input: "coins = [1,2,5], amount = 11", output: "3", explanation: "11 = 5 + 5 + 1" },
      { input: "coins = [2], amount = 3", output: "-1" },
    ],
    constraints: ["1 <= coins.length <= 12", "0 <= amount <= 10^4"],
    hints: [
      "Initialize dp array of size amount + 1 filled with Infinity, and set dp[0] = 0.",
      "For each amount a from 1 to amount, try every coin c.",
      "If a - c >= 0, update dp[a] = Math.min(dp[a], 1 + dp[a - c]).",
    ],
    solutions: [
      {
        title: "Bottom-Up DP Array",
        complexity: "Time: O(amount * coins) | Space: O(amount)",
        code: "function solve(coins, amount) {\n  const dp = new Array(amount + 1).fill(Infinity);\n  dp[0] = 0;\n  for (let a = 1; a <= amount; a++) {\n    for (const c of coins) {\n      if (a - c >= 0) dp[a] = Math.min(dp[a], 1 + dp[a - c]);\n    }\n  }\n  return dp[amount] === Infinity ? -1 : dp[amount];\n}",
      },
      {
        title: "BFS Shortest Coin Path",
        complexity: "Time: O(amount * coins) | Space: O(amount)",
        code: "function solve(coins, amount) {\n  const dp = new Array(amount + 1).fill(Infinity);\n  dp[0] = 0;\n  for (const c of coins) {\n    for (let a = c; a <= amount; a++) dp[a] = Math.min(dp[a], 1 + dp[a - c]);\n  }\n  return dp[amount] === Infinity ? -1 : dp[amount];\n}",
      },
    ],
    starterCode: "function solve(coins, amount) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 4,
    prevSlug: "maximum-subarray",
    nextSlug: "longest-increasing-subsequence",
    testCases: [
      { input: [[1, 2, 5], 11], expected: 3, label: "coins=[1,2,5], amount=11" },
      { input: [[2], 3], expected: -1, label: "coins=[2], amount=3" },
      { input: [[1], 0], expected: 0, label: "coins=[1], amount=0" },
    ],
  },
  {
    id: "dp-4",
    slug: "longest-increasing-subsequence",
    title: "Longest Increasing Subsequence",
    topic: "dynamic-programming",
    difficulty: "Medium",
    pattern: "Patience Sorting / DP Subsequence",
    statement: "Given an integer array nums, return the length of the longest strictly increasing subsequence.",
    examples: [
      { input: "nums = [10,9,2,5,3,7,101,18]", output: "4", explanation: "The LIS is [2,3,7,101]." },
      { input: "nums = [0,1,0,3,2,3]", output: "4" },
    ],
    constraints: ["1 <= nums.length <= 2500"],
    hints: [
      "dp[i] represents the length of the LIS ending at index i.",
      "For each i, check all j < i where nums[j] < nums[i].",
      "Or use binary search tails array for O(n log n).",
    ],
    solutions: [
      {
        title: "Quadratic DP Tabulation",
        complexity: "Time: O(n²) | Space: O(n)",
        code: "function solve(nums) {\n  const dp = new Array(nums.length).fill(1);\n  for (let i = 1; i < nums.length; i++) {\n    for (let j = 0; j < i; j++) {\n      if (nums[i] > nums[j]) dp[i] = Math.max(dp[i], 1 + dp[j]);\n    }\n  }\n  return Math.max(...dp);\n}",
      },
      {
        title: "Binary Search Patience Piles",
        complexity: "Time: O(n log n) | Space: O(n)",
        code: "function solve(nums) {\n  const tails = [];\n  for (const x of nums) {\n    let l = 0, r = tails.length;\n    while (l < r) {\n      const m = (l + r) >> 1;\n      if (tails[m] < x) l = m + 1; else r = m;\n    }\n    tails[l] = x;\n  }\n  return tails.length;\n}",
      },
    ],
    starterCode: "function solve(nums,) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 5,
    prevSlug: "coin-change",
    nextSlug: "unique-paths",
    testCases: [
      { input: [[10, 9, 2, 5, 3, 7, 101, 18]], expected: 4, label: "[10,9,2,5,3,7,101,18]" },
      { input: [[0, 1, 0, 3, 2, 3]], expected: 4, label: "[0,1,0,3,2,3]" },
      { input: [[7, 7, 7, 7]], expected: 1, label: "[7,7,7,7]" },
    ],
  },
  {
    id: "dp-5",
    slug: "unique-paths",
    title: "Unique Paths in Grid",
    topic: "dynamic-programming",
    difficulty: "Medium",
    pattern: "2D Grid Path DP",
    statement: "There is a robot on an m x n grid at top-left (0, 0). The robot can only move down or right. Return the number of possible unique paths to reach the bottom-right corner (m - 1, n - 1).",
    examples: [
      { input: "m = 3, n = 7", output: "28" },
      { input: "m = 3, n = 2", output: "3" },
    ],
    constraints: ["1 <= m, n <= 100"],
    hints: [
      "First row and first column cells have only 1 unique path.",
      "For any interior cell (r, c), paths[r][c] = paths[r - 1][c] + paths[r][c - 1].",
      "Can be computed with a single 1D row of length n.",
    ],
    solutions: [
      {
        title: "1D Rolling Array DP",
        complexity: "Time: O(m * n) | Space: O(n)",
        code: "function solve(m, n) {\n  const row = new Array(n).fill(1);\n  for (let r = 1; r < m; r++) {\n    for (let c = 1; c < n; c++) row[c] += row[c - 1];\n  }\n  return row[n - 1];\n}",
      },
      {
        title: "Combinatorics Formula",
        complexity: "Time: O(min(m, n)) | Space: O(1)",
        code: "function solve(m, n) {\n  let res = 1;\n  for (let i = 1; i < m; i++) res = (res * (n - 1 + i)) / i;\n  return Math.round(res);\n}",
      },
    ],
    starterCode: "function solve(m, n) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 6,
    prevSlug: "longest-increasing-subsequence",
    testCases: [
      { input: [3, 7], expected: 28, label: "m=3, n=7" },
      { input: [3, 2], expected: 3, label: "m=3, n=2" },
      { input: [1, 1], expected: 1, label: "m=1, n=1" },
    ],
  },

  // TRIE (1 problems)
  {
    id: "str-4",
    slug: "longest-common-prefix",
    title: "Longest Common Prefix",
    topic: "trie",
    difficulty: "Easy",
    pattern: "Horizontal / Vertical Scan",
    statement: "Write a function to find the longest common prefix string amongst an array of strings. If there is no common prefix, return an empty string \"\".",
    examples: [
      { input: "strs = [\"flower\",\"flow\",\"flight\"]", output: "\"fl\"" },
      { input: "strs = [\"dog\",\"racecar\",\"car\"]", output: "\"\"" },
    ],
    constraints: ["1 <= strs.length <= 200"],
    hints: [
      "Sort the array lexicographically and compare only the first and last strings.",
      "Or compare characters column by column across all strings.",
      "Return substring up to the first mismatch.",
    ],
    solutions: [
      {
        title: "Vertical Character Scan",
        complexity: "Time: O(S) | Space: O(1)",
        code: "function solve(strs) {\n  if (!strs.length) return \"\";\n  for (let i = 0; i < strs[0].length; i++) {\n    for (let j = 1; j < strs.length; j++) {\n      if (strs[j][i] !== strs[0][i]) return strs[0].slice(0, i);\n    }\n  }\n  return strs[0];\n}",
      },
      {
        title: "Sorted First/Last Match",
        complexity: "Time: O(n log n) | Space: O(1)",
        code: "function solve(strs) {\n  strs.sort();\n  const first = strs[0], last = strs[strs.length - 1];\n  let i = 0;\n  while (i < first.length && first[i] === last[i]) i++;\n  return first.slice(0, i);\n}",
      },
    ],
    starterCode: "function solve(strs,) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 1,
    testCases: [
      { input: [["flower", "flow", "flight"]], expected: "fl", label: "[\"flower\",\"flow\",\"flight\"]" },
      { input: [["dog", "racecar", "car"]], expected: "", label: "[\"dog\",\"racecar\",\"car\"]" },
      { input: [["interstellar", "internet", "internal"]], expected: "inter", label: "[\"interstellar\",...]" },
    ],
  },

  // INTERVALS (1 problems)
  {
    id: "arr-7",
    slug: "merge-intervals",
    title: "Merge Intervals",
    topic: "intervals",
    difficulty: "Medium",
    pattern: "Sort & Sweep Merge",
    statement: "Given an array of intervals where intervals[i] = [start, end], merge all overlapping intervals and return an array of the non-overlapping intervals that cover all the input intervals.",
    examples: [
      { input: "intervals = [[1,3],[2,6],[8,10],[15,18]]", output: "[[1,6],[8,10],[15,18]]" },
      { input: "intervals = [[1,4],[4,5]]", output: "[[1,5]]", explanation: "Intervals [1,4] and [4,5] touch at 4, so they merge." },
    ],
    constraints: ["1 <= intervals.length <= 10^4", "intervals[i].length == 2", "0 <= start <= end <= 10^4"],
    hints: [
      "Sort intervals by start time so overlaps become adjacent.",
      "Keep a merged list; compare each interval against its last entry.",
      "If next.start <= last.end, extend last.end; otherwise append a new interval.",
    ],
    solutions: [
      {
        title: "Pairwise Overlap Scan",
        complexity: "Time: O(n²) | Space: O(n)",
        code: "function solve(intervals) {\n  const ivs = intervals.map(x => x.slice()).sort((a, b) => a[0] - b[0]);\n  const out = [];\n  for (const cur of ivs) {\n    let merged = false;\n    for (const prev of out) {\n      if (cur[0] <= prev[1] && prev[0] <= cur[1]) {\n        prev[0] = Math.min(prev[0], cur[0]);\n        prev[1] = Math.max(prev[1], cur[1]);\n        merged = true;\n        break;\n      }\n    }\n    if (!merged) out.push(cur.slice());\n  }\n  return out.sort((a, b) => a[0] - b[0]);\n}",
      },
      {
        title: "Sort & Single Sweep",
        complexity: "Time: O(n log n) | Space: O(n)",
        code: "function solve(intervals) {\n  intervals.sort((a, b) => a[0] - b[0]);\n  const out = [intervals[0].slice()];\n  for (let i = 1; i < intervals.length; i++) {\n    const last = out[out.length - 1];\n    if (intervals[i][0] <= last[1]) last[1] = Math.max(last[1], intervals[i][1]);\n    else out.push(intervals[i].slice());\n  }\n  return out;\n}",
      },
    ],
    starterCode: "function solve(intervals) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 1,
    testCases: [
      { input: [[[1, 3], [2, 6], [8, 10], [15, 18]]], expected: [[1, 6], [8, 10], [15, 18]], label: "[[1,3],[2,6],[8,10],[15,18]]" },
      { input: [[[1, 4], [4, 5]]], expected: [[1, 5]], label: "[[1,4],[4,5]]" },
      { input: [[[4, 7], [1, 4]]], expected: [[1, 7]], label: "[[4,7],[1,4]] unsorted" },
      { input: [[[1, 4], [2, 3]]], expected: [[1, 4]], label: "[[1,4],[2,3]] nested" },
    ],
  },

  // MATH-MATRICES (2 problems)
  {
    id: "str-7",
    slug: "roman-to-integer",
    title: "Roman to Integer",
    topic: "math-matrices",
    difficulty: "Easy",
    pattern: "Subtractive Peek",
    statement: "Given a valid roman numeral string s using symbols I, V, X, L, C, D, M, convert it to its integer value using standard subtractive notation (IV = 4, IX = 9, XL = 40, XC = 90, CD = 400, CM = 900).",
    examples: [
      { input: "s = \"MCMXCIV\"", output: "1994", explanation: "M + CM + XC + IV = 1000 + 900 + 90 + 4." },
      { input: "s = \"LVIII\"", output: "58", explanation: "L + V + III = 50 + 5 + 3." },
    ],
    constraints: ["1 <= s.length <= 15", "s contains only I, V, X, L, C, D, M", "s is a valid roman numeral in range 1 to 3999"],
    hints: [
      "Map each symbol to its value: I=1, V=5, X=10, L=50, C=100, D=500, M=1000.",
      "Scan left to right comparing each symbol with the next one.",
      "If current < next, subtract it; otherwise add it.",
    ],
    solutions: [
      {
        title: "Right-to-Left Max Tracking",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(s) {\n  const v = { I: 1, V: 5, X: 10, L: 50, C: 100, D: 500, M: 1000 };\n  let total = 0, maxSeen = 0;\n  for (let i = s.length - 1; i >= 0; i--) {\n    if (v[s[i]] >= maxSeen) { total += v[s[i]]; maxSeen = v[s[i]]; }\n    else total -= v[s[i]];\n  }\n  return total;\n}",
      },
      {
        title: "Left-to-Right Subtractive Peek",
        complexity: "Time: O(n) | Space: O(1)",
        code: "function solve(s) {\n  const v = { I: 1, V: 5, X: 10, L: 50, C: 100, D: 500, M: 1000 };\n  let total = 0;\n  for (let i = 0; i < s.length; i++) {\n    const cur = v[s[i]], next = v[s[i + 1]] || 0;\n    if (cur < next) total -= cur;\n    else total += cur;\n  }\n  return total;\n}",
      },
    ],
    starterCode: "function solve(s) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 1,
    nextSlug: "spiral-matrix",
    testCases: [
      { input: ["III"], expected: 3, label: "\"III\"" },
      { input: ["LVIII"], expected: 58, label: "\"LVIII\"" },
      { input: ["MCMXCIV"], expected: 1994, label: "\"MCMXCIV\"" },
    ],
  },
  {
    id: "arr-8",
    slug: "spiral-matrix",
    title: "Spiral Matrix",
    topic: "math-matrices",
    difficulty: "Medium",
    pattern: "Boundary Shrinking",
    statement: "Given an m x n matrix, return all elements of the matrix in clockwise spiral order starting from the top-left cell.",
    examples: [
      { input: "matrix = [[1,2,3],[4,5,6],[7,8,9]]", output: "[1,2,3,6,9,8,7,4,5]" },
      { input: "matrix = [[1,2,3,4],[5,6,7,8],[9,10,11,12]]", output: "[1,2,3,4,8,12,11,10,9,5,6,7]" },
    ],
    constraints: ["1 <= m, n <= 10", "-100 <= matrix[i][j] <= 100"],
    hints: [
      "Maintain four boundaries: top, bottom, left, right.",
      "Walk top row left to right, then right column top to bottom, then bottom row, then left column.",
      "Shrink the used boundary after each side and stop when top > bottom or left > right.",
    ],
    solutions: [
      {
        title: "Visited-Set Walk",
        complexity: "Time: O(m * n) | Space: O(m * n)",
        code: "function solve(matrix) {\n  const out = [];\n  const seen = new Set();\n  const dirs = [[0, 1], [1, 0], [0, -1], [-1, 0]];\n  let r = 0, c = 0, d = 0;\n  for (let k = 0; k < matrix.length * matrix[0].length; k++) {\n    out.push(matrix[r][c]);\n    seen.add(r + ',' + c);\n    const nr = r + dirs[d][0], nc = c + dirs[d][1];\n    if (nr < 0 || nc < 0 || nr >= matrix.length || nc >= matrix[0].length || seen.has(nr + ',' + nc)) d = (d + 1) % 4;\n    r += dirs[d][0]; c += dirs[d][1];\n  }\n  return out;\n}",
      },
      {
        title: "Boundary Shrinking Layers",
        complexity: "Time: O(m * n) | Space: O(1)",
        code: "function solve(matrix) {\n  const out = [];\n  if (!matrix.length) return out;\n  let top = 0, bottom = matrix.length - 1, left = 0, right = matrix[0].length - 1;\n  while (top <= bottom && left <= right) {\n    for (let c = left; c <= right; c++) out.push(matrix[top][c]);\n    top++;\n    for (let r = top; r <= bottom; r++) out.push(matrix[r][right]);\n    right--;\n    if (top <= bottom) {\n      for (let c = right; c >= left; c--) out.push(matrix[bottom][c]);\n      bottom--;\n    }\n    if (left <= right) {\n      for (let r = bottom; r >= top; r--) out.push(matrix[r][left]);\n      left++;\n    }\n  }\n  return out;\n}",
      },
    ],
    starterCode: "function solve(matrix) {\n  // Write your solution here\n  throw new Error('Not implemented');\n}",
    functionName: "solve",
    sequence: 2,
    prevSlug: "roman-to-integer",
    testCases: [
      { input: [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], expected: [1, 2, 3, 6, 9, 8, 7, 4, 5], label: "3x3 square" },
      { input: [[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]], expected: [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7], label: "3x4 rectangle" },
      { input: [[[1]]], expected: [1], label: "1x1 single" },
      { input: [[[1, 2], [3, 4]]], expected: [1, 2, 4, 3], label: "2x2 square" },
    ],
  },
];
