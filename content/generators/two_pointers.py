"""Two pointers question generator with exact programmatic oracles."""

import random

from content.generators.base import GeneratedQuestion, make_question


def two_sum_sorted_oracle(numbers: list[int], target: int) -> list[int]:
    """1-based indices of two numbers in sorted array summing to target."""
    left = 0
    right = len(numbers) - 1
    while left < right:
        curr_sum = numbers[left] + numbers[right]
        if curr_sum == target:
            return [left + 1, right + 1]
        if curr_sum < target:
            left += 1
        else:
            right -= 1
    return [-1, -1]


def container_water_oracle(height: list[int]) -> int:
    """Maximum water area trapped between two vertical lines."""
    left = 0
    right = len(height) - 1
    max_area = 0
    while left < right:
        area = min(height[left], height[right]) * (right - left)
        max_area = max(max_area, area)
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1
    return max_area


def trapping_rain_water_oracle(height: list[int]) -> int:
    """Total trapped rain water between bars."""
    left = 0
    right = len(height) - 1
    left_max = 0
    right_max = 0
    water = 0
    while left < right:
        if height[left] < height[right]:
            if height[left] >= left_max:
                left_max = height[left]
            else:
                water += left_max - height[left]
            left += 1
        else:
            if height[right] >= right_max:
                right_max = height[right]
            else:
                water += right_max - height[right]
            right -= 1
    return water


def generate_two_pointers_questions(count: int = 12, seed: int = 301) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    q_idx = 1

    # Design 1: two_pointers.two_sum_sorted (Easy, 4 instances)
    two_sum_cases = [
        ([2, 7, 11, 15], 9),
        ([2, 3, 4], 6),
        ([1, 3, 5, 9, 12], 14),
        ([-3, 0, 3, 4, 8], 5),
    ]
    for numbers, target in two_sum_cases:
        res = two_sum_sorted_oracle(numbers, target)
        ans = f"[{res[0]}, {res[1]}]"
        distractors = [
            f"[{res[0] - 1}, {res[1] - 1}]",
            f"[{res[0]}, {res[1] - 1}]" if res[1] - 1 > res[0] else f"[{res[0] + 1}, {res[1]}]",
            f"[{max(1, res[0] - 1)}, {res[1]}]",
            f"[{res[0] + 1}, {res[1] + 1}]",
        ]
        distractors = [d for d in dict.fromkeys(distractors) if d != ans]
        prompt = (
            f"Given the 1-indexed sorted array `numbers = {numbers}` and `target = {target}`, "
            f"two converging pointers are used to find two numbers that sum up to `target`. "
            f"What are the 1-based indices `[index1, index2]` returned by this algorithm?"
        )
        exp = (
            f"Left pointer at index {res[0]} (val {numbers[res[0]-1]}) and right pointer at index {res[1]} "
            f"(val {numbers[res[1]-1]}) sum to {numbers[res[0]-1]} + {numbers[res[1]-1]} = {target}. "
            f"Indices are 1-based."
        )
        questions.append(
            make_question(
                id_str=f"gen-2ptr-twosum-{q_idx}",
                topic="two-pointers",
                subtopic="two-sum-sorted",
                difficulty="Easy",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="two_pointers.two_sum_sorted",
                rng=rng,
            )
        )
        q_idx += 1

    # Design 2: two_pointers.container_water (Medium, 4 instances)
    water_cases = [
        [1, 8, 6, 2, 5, 4, 8, 3, 7],
        [4, 3, 2, 1, 4],
        [1, 2, 4, 3],
        [2, 3, 10, 5, 7, 8, 9],
    ]
    for height in water_cases:
        ans_val = container_water_oracle(height)
        ans = str(ans_val)
        cand = [ans_val + 2, ans_val - 2, ans_val + 7, ans_val - 5, max(1, ans_val // 2)]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans and d > 0]
        prompt = (
            f"Given the array of vertical line heights `height = {height}`, "
            f"a two-pointer approach starts at the two ends and moves the pointer pointing to the shorter line inward. "
            f"What is the maximum container area of water that can be trapped?"
        )
        exp = (
            f"The maximum area is computed by min(h[i], h[j]) * (j - i). "
            f"By greedily shifting the shorter boundary inward, the global maximum area achieved is {ans_val}."
        )
        questions.append(
            make_question(
                id_str=f"gen-2ptr-water-{q_idx}",
                topic="two-pointers",
                subtopic="container-with-most-water",
                difficulty="Medium",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="two_pointers.container_water",
                rng=rng,
            )
        )
        q_idx += 1

    # Design 3: two_pointers.trapping_rain_water (Hard, 4 instances)
    rain_cases = [
        [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1],
        [4, 2, 0, 3, 2, 5],
        [3, 0, 2, 0, 4],
        [2, 1, 0, 2],
    ]
    for height in rain_cases:
        ans_val = trapping_rain_water_oracle(height)
        ans = str(ans_val)
        cand = [ans_val + 1, ans_val - 1, ans_val + 2, max(0, ans_val - 2), ans_val + 3]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans and d >= 0]
        prompt = (
            f"Given the elevation map bar heights `height = {height}` where width of each bar is 1, "
            f"two converging pointers track `left_max` and `right_max` to compute trapped water. "
            f"How many total units of rain water are trapped after raining?"
        )
        exp = (
            f"At each position, water trapped is bounded by min(left_max, right_max) - height[i]. "
            f"Summing across all bars yields exactly {ans_val} units of trapped rain water."
        )
        questions.append(
            make_question(
                id_str=f"gen-2ptr-rain-{q_idx}",
                topic="two-pointers",
                subtopic="trapping-rain-water",
                difficulty="Hard",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="two_pointers.trapping_rain_water",
                rng=rng,
            )
        )
        q_idx += 1

    return questions[:count]
