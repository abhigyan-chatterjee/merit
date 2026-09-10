import random
from collections import Counter

from content.generators.base import GeneratedQuestion, make_question


def kadane_oracle(nums: list[int]) -> int:
    max_so_far = nums[0]
    curr_max = nums[0]
    for x in nums[1:]:
        curr_max = max(x, curr_max + x)
        max_so_far = max(max_so_far, curr_max)
    return max_so_far


def prefix_sum_oracle(nums: list[int], left: int, right: int) -> int:
    return sum(nums[left : right + 1])


def max_sum_fixed_oracle(nums: list[int], k: int) -> int:
    """Maximum sum of contiguous subarray of length k."""
    curr = sum(nums[:k])
    max_s = curr
    for i in range(k, len(nums)):
        curr += nums[i] - nums[i - k]
        max_s = max(max_s, curr)
    return max_s


def min_window_substring_oracle(s: str, t: str) -> int:
    """Minimum window substring length containing all characters of t, or 0."""
    if not s or not t:
        return 0
    t_count = Counter(t)
    required = len(t_count)
    l = 0
    formed = 0
    window_counts: dict[str, int] = {}
    min_len = float("inf")
    for r in range(len(s)):
        char = s[r]
        window_counts[char] = window_counts.get(char, 0) + 1
        if char in t_count and window_counts[char] == t_count[char]:
            formed += 1
        while l <= r and formed == required:
            min_len = min(min_len, r - l + 1)
            left_char = s[l]
            window_counts[left_char] -= 1
            if left_char in t_count and window_counts[left_char] < t_count[left_char]:
                formed -= 1
            l += 1
    return 0 if min_len == float("inf") else int(min_len)


def generate_array_string_questions(count: int = 150, seed: int = 49) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    q_idx = 1

    # 1. Kadane's Algorithm Maximum Subarray Sum
    kadane_arrays = [
        [-2, 1, -3, 4, -1, 2, 1, -5, 4],
        [1],
        [5, 4, -1, 7, 8],
        [-1, -2, -3, -4],
        [2, 3, -2, 4],
        [-2, -3, 4, -1, -2, 1, 5, -3],
        [3, -1, 2, -1, -2, 4],
        [-1, 2, 3, -4, 5, 1],
        [1, -2, 3, 10, -4, 7, 2, -5],
        [-2, 11, -4, 13, -5, 2],
        [1, 2, 3, 4, 5],
        [-5, 6, -2, 3, -1, 4],
        [8, -19, 5, -4, 20],
        [-3, 4, -1, 2, 1, -5],
        [2, -1, 2, 3, 4, -5],
    ]

    for arr in kadane_arrays:
        max_sum = kadane_oracle(arr)
        ans = str(max_sum)
        cand_k = [max_sum + 2, max_sum + 4, max_sum + 6]
        if max_sum > -10:
            cand_k.append(max_sum - 2)
            cand_k.append(max_sum - 4)
        distractors = [str(d) for d in dict.fromkeys(cand_k) if str(d) != ans]
        prompt = (
            f"Using Kadane's algorithm, what is the maximum subarray sum in the integer array:\n"
            f"`{arr}`?"
        )
        q = make_question(
            id_str=f"gen-arr-kadane-{q_idx}",
            topic="arrays-hashing",
            subtopic="kadane",
            difficulty="Medium" if len(arr) > 4 else "Easy",
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=f"Kadane's algorithm maintains `currMax = max(x, currMax + x)`. The maximum contiguous subarray sum is {max_sum}.",
            generator_key="arrays_strings.kadane",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 2. Prefix Sum Range Query
    prefix_arrays = [
        ([1, 4, 2, 8, 5, 7], 1, 4),
        ([3, 1, 4, 1, 5, 9, 2], 2, 5),
        ([10, 20, 30, 40, 50], 0, 3),
        ([5, -2, 3, 1, -4, 8, 2], 2, 6),
        ([7, 3, 9, 1, 4, 6], 0, 5),
        ([12, 18, 6, 24, 30], 1, 3),
        ([2, 4, 6, 8, 10, 12], 2, 4),
        ([15, 25, 35, 45], 0, 2),
        ([1, 2, 3, 4, 5, 6, 7, 8], 3, 7),
        ([9, -3, 6, -1, 4], 1, 3),
        ([8, 16, 24, 32, 40], 2, 4),
        ([11, 22, 33, 44], 1, 2),
    ]

    for arr, L, R in prefix_arrays:
        range_sum = prefix_sum_oracle(arr, L, R)
        ans = str(range_sum)
        cand_p = [range_sum + arr[0], range_sum - 3, range_sum + 5, range_sum + 10]
        distractors = [str(d) for d in dict.fromkeys(cand_p) if str(d) != ans]
        prompt = (
            f"Given array `{arr}`, what is the range sum of elements from index {L} to {R} inclusive (`nums[{L}..{R}]`) "
            f"computed in O(1) time using a precomputed prefix sum array?"
        )
        q = make_question(
            id_str=f"gen-arr-prefix-{q_idx}",
            topic="arrays-hashing",
            subtopic="prefix-sums",
            difficulty="Easy",
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=f"Using prefix sums P[i], RangeSum(L, R) = P[R] - (P[L-1] if L > 0 else 0) = {range_sum}.",
            generator_key="arrays_strings.prefix_sum",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 3. Sliding Window Maximum Sum of Size K
    window_cases = [
        ([2, 1, 5, 1, 3, 2], 3),
        ([2, 3, 4, 1, 5], 2),
        ([1, 4, 2, 10, 23, 3, 1, 0, 20], 4),
        ([100, 200, 300, 400], 2),
        ([1, 2, 3, 4, 5, 6, 7], 3),
        ([5, -1, 3, 4, 2, -2, 6], 3),
        ([4, 2, 1, 7, 8, 1, 2, 8, 1, 0], 3),
        ([10, 5, 2, 7, 8, 7], 3),
        ([1, 9, 3, 5, 6, 2], 2),
        ([8, 2, 4, 7, 9, 3], 3),
        ([6, 3, 8, 2, 9, 1], 4),
        ([12, 1, 78, 90, 57, 89, 56], 3),
    ]

    for arr, k in window_cases:
        max_win_sum = max(sum(arr[i : i + k]) for i in range(len(arr) - k + 1))
        ans = str(max_win_sum)
        cand_w = [max_win_sum + 3, max_win_sum + 6, max_win_sum - 2, max_win_sum - 5]
        distractors = [str(d) for d in dict.fromkeys(cand_w) if str(d) != ans]
        prompt = (
            f"Using a sliding window of fixed size `k = {k}`, what is the **maximum subarray sum** "
            f"over all contiguous subarrays of size {k} in array `{arr}`?"
        )
        q = make_question(
            id_str=f"gen-arr-win-{q_idx}",
            topic="arrays-hashing",
            subtopic="sliding-window",
            difficulty="Easy",
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=f"By maintaining a sliding window of size {k} and updating sum in O(1) time per shift, the maximum window sum is {max_win_sum}.",
            generator_key="arrays_strings.sliding_window",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 4. String Algorithms & Pattern Matching
    string_concepts = [
        ("What is the worst-case time complexity of the Knuth-Morris-Pratt (KMP) string matching algorithm for text of length N and pattern of length M?", "O(N + M)", ["O(N * M)", "O(N log M)", "O(N²)"], "KMP precomputes the Longest Prefix Suffix (LPS) table in O(M) time and scans the text in O(N) time without backtracking, achieving O(N + M) total worst-case time.", "Medium"),
        ("In the Rabin-Karp string matching algorithm, what technique enables O(1) computation of the hash of the next substring window?", "Rolling hash (Rabin fingerprint)", ["Cryptographic SHA-256", "Huffman frequency tree", "Suffix automaton"], "A rolling hash removes the leading character's contribution and adds the trailing character's contribution in O(1) arithmetic operations.", "Medium"),
        ("What data structure allows querying the Longest Common Prefix (LCP) and finding all occurrences of any substring in a text of length N in O(M) time after O(N) construction?", "Suffix Tree or Suffix Automaton", ["Binary Search Tree", "Disjoint Set Union", "Adjacency Matrix"], "A Suffix Tree exposes all substrings as root-to-node paths, enabling linear-time pattern search and LCP queries.", "Hard"),
        ("How does the Boyer-Moore string matching algorithm achieve sublinear average-case time complexity?", "By scanning the pattern from right-to-left and applying the Bad Character and Good Suffix skip heuristics", ["By sorting all characters in the text first", "By compressing the text using Huffman encoding", "By hashing every character to 32 bits"], "Boyer-Moore matches characters backwards from the end of the pattern, allowing it to skip up to M characters at a time when a mismatch occurs.", "Medium"),
    ]

    for prompt, ans, distractors, exp, diff in string_concepts:
        q = make_question(
            id_str=f"gen-str-concept-{q_idx}",
            topic="sliding-windows",
            subtopic="string-algorithms",
            difficulty=diff,
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=exp,
            generator_key="arrays_strings.concepts",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 5. Fixed Sliding Window Maximum Subarray Sum (sliding_windows.max_sum_fixed, Easy, 4 instances)
    fixed_cases = [
        ([2, 1, 5, 1, 3, 2], 3),
        ([2, 3, 4, 1, 5], 2),
        ([1, 4, 2, 10, 23, 3, 1, 0, 20], 4),
        ([100, 200, 300, 400], 2),
    ]
    for nums, k in fixed_cases:
        ans_val = max_sum_fixed_oracle(nums, k)
        ans = str(ans_val)
        cand = [ans_val + 2, max(1, ans_val - 2), ans_val + 4, max(1, ans_val - 4), ans_val + 7]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans]
        prompt = (
            f"Given array `nums = {nums}` and window size `k = {k}`, what is the maximum sum of "
            f"any contiguous subarray of length {k} computed using a fixed-size sliding window?"
        )
        exp = (
            f"Maintaining a sliding window of size {k} and updating the sum in O(1) time per step "
            f"finds the maximum subarray sum of {ans_val}."
        )
        questions.append(
            make_question(
                id_str=f"gen-sw-maxsum-{q_idx}",
                topic="sliding-windows",
                subtopic="fixed-window-max-sum",
                difficulty="Easy",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="sliding_windows.max_sum_fixed",
                rng=rng,
            )
        )
        q_idx += 1

    # 6. Variable Sliding Window Minimum Window Substring Length (sliding_windows.min_window_substring, Hard, 4 instances)
    min_win_cases = [
        ("ADOBECODEBANC", "ABC"),
        ("a", "a"),
        ("a", "aa"),
        ("ABAACBAB", "ABC"),
    ]
    for s_str, t_str in min_win_cases:
        ans_val = min_window_substring_oracle(s_str, t_str)
        ans = str(ans_val)
        cand = [ans_val + 1, max(0, ans_val - 1), ans_val + 2, max(0, ans_val - 2), len(t_str) + 2]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans]
        prompt = (
            f"Given strings `s = \"{s_str}\"` and `t = \"{t_str}\"`, a variable sliding window with two pointers "
            f"finds the minimum window substring of `s` containing all characters in `t`. "
            f"What is the length of this minimum window substring (or 0 if no valid window exists)?"
        )
        if ans_val == 0:
            exp = (
                "String `s` does not contain the required character frequencies of `t`, "
                "so no valid window exists (length is 0)."
            )
        else:
            exp = (
                f"Expanding the right pointer to satisfy all characters and shrinking the left pointer "
                f"to minimize window width achieves a minimum window length of {ans_val}."
            )
        questions.append(
            make_question(
                id_str=f"gen-sw-minwin-{q_idx}",
                topic="sliding-windows",
                subtopic="minimum-window-substring",
                difficulty="Hard",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="sliding_windows.min_window_substring",
                rng=rng,
            )
        )
        q_idx += 1

    return questions[:count]
