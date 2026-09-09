"""Sorting and searching algorithm generator with exact algorithmic trace oracles."""

import random
from content.generators.base import GeneratedQuestion, make_question


def binary_search_trace(arr: list[int], target: int) -> tuple[int, list[int]]:
    low = 0
    high = len(arr) - 1
    mids = []
    found_idx = -1
    while low <= high:
        mid = (low + high) // 2
        mids.append(mid)
        if arr[mid] == target:
            found_idx = mid
            break
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return found_idx, mids


def generate_sorting_searching_questions(count: int = 120, seed: int = 47) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    q_idx = 1

    # 1. Binary Search Midpoint Index Traces
    search_arrays = [
        ([2, 5, 8, 12, 16, 23, 38, 45, 56, 72, 91], 23),
        ([1, 3, 7, 9, 11, 15, 19, 21, 27, 33], 7),
        ([4, 8, 15, 16, 23, 42, 50, 68, 79, 90, 105], 50),
        ([10, 20, 30, 40, 50, 60, 70, 80], 40),
        ([3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36], 18),
        ([5, 10, 15, 20, 25, 30, 35, 40, 45, 50], 35),
        ([2, 4, 6, 8, 10, 12, 14, 16, 18, 20], 6),
        ([11, 22, 33, 44, 55, 66, 77, 88, 99], 88),
        ([7, 14, 21, 28, 35, 42, 49, 56, 63, 70], 21),
        ([1, 5, 9, 13, 17, 21, 25, 29, 33, 37], 33),
        ([12, 24, 36, 48, 60, 72, 84, 96], 24),
        ([3, 8, 13, 18, 23, 28, 33, 38, 43, 48], 13),
        ([100, 200, 300, 400, 500, 600, 700], 600),
        ([2, 6, 12, 20, 30, 42, 56, 72, 90], 30),
        ([4, 9, 14, 19, 24, 29, 34, 39, 44], 39),
    ]

    for arr, target in search_arrays:
        _, mids = binary_search_trace(arr, target)
        ans = ", ".join(map(str, mids))
        cand_d = [
            ", ".join(map(str, [m + 1 for m in mids])),
            ", ".join(map(str, [m + 2 for m in mids])),
            ", ".join(map(str, [max(0, m - 1) for m in mids])),
            ", ".join(map(str, [max(0, m - 2) for m in mids])),
        ]
        distractors = [d for d in cand_d if d != ans]
        prompt = (
            f"Binary search with integer division `mid = (low + high) // 2` searches for target `{target}` "
            f"in the sorted array:\n`{arr}`\n\n"
            f"What is the exact sequence of indices checked at `mid` until finding the target?"
        )
        q = make_question(
            id_str=f"gen-sort-bs-{q_idx}",
            topic="binary-search",
            subtopic="binary-search",
            difficulty="Medium",
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=f"Tracing standard binary search: low and high intervals update, checking index sequence [{ans}] where arr[{mids[-1]}] == {target}.",
            generator_key="sorting_searching.bs_trace",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 2. Sorting Properties & Complexities
    sorting_properties = [
        ("Which of the following comparison-based sorting algorithms is guaranteed to be STABLE and runs in O(n log n) worst-case time?", "Merge Sort", ["Quick Sort", "Heap Sort", "Selection Sort"], "Merge Sort stably maintains relative order of duplicate elements and guarantees O(n log n) time across best, average, and worst cases.", "Easy"),
        ("What causes Quick Sort to degrade to its worst-case O(n²) time complexity?", "Consistently selecting the minimum or maximum element as the pivot", ["Array containing only distinct random elements", "Choosing the median element as pivot", "Splitting the array into equal halves"], "When the pivot does not partition elements into balanced sub-arrays (e.g. partition of size 0 and n-1), recursion depth reaches n, requiring n + (n-1) + ... + 1 = O(n²) comparisons.", "Easy"),
        ("Why is Heap Sort typically not preferred for cache-sensitive performance compared to Quick Sort, despite having O(n log n) worst-case guarantee?", "Heap Sort makes non-contiguous parent-child jumps in memory, causing frequent CPU cache misses", ["Heap Sort uses O(n) auxiliary memory", "Heap Sort requires O(n²) operations on average", "Heap Sort is not in-place"], "Heap navigation hops between index i and 2i+1, which rapidly breaks cache locality on modern processor hierarchies. Quick Sort exhibits excellent contiguous sequential spatial locality.", "Medium"),
        ("What is the theoretical lower bound on the number of comparisons required for any comparison-based sorting algorithm on n items?", "Ω(n log n)", ["Ω(n)", "Ω(log n)", "Ω(n²)"], "Any comparison sort can be modeled as a decision tree with n! leaf nodes. The height of a binary tree with n! leaves is at least log₂(n!) = Θ(n log n) comparisons.", "Medium"),
        ("Which non-comparison sorting algorithm runs in O(n + k) time where k is the range of non-negative integer input values?", "Counting Sort", ["Radix Sort", "Bucket Sort", "Shell Sort"], "Counting Sort tallies frequencies of keys in range [0..k] and computes prefix sums in O(n + k) time and space.", "Easy"),
    ]

    for prompt, ans, distractors, exp, diff in sorting_properties:
        q = make_question(
            id_str=f"gen-sort-prop-{q_idx}",
            topic="sorting",
            subtopic="sorting-properties",
            difficulty=diff,
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=exp,
            generator_key="sorting_searching.properties",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    return questions[:count]
