"""Intervals algorithmic question generator with programmatic interval oracles."""

import random

from content.generators.base import GeneratedQuestion, make_question


def merge_intervals_oracle(intervals: list[list[int]]) -> list[list[int]]:
    """Merge overlapping intervals in list."""
    sorted_inv = sorted(intervals, key=lambda x: x[0])
    merged = [list(sorted_inv[0])]
    for cur in sorted_inv[1:]:
        if cur[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], cur[1])
        else:
            merged.append(list(cur))
    return merged


def min_meeting_rooms_oracle(intervals: list[list[int]]) -> int:
    """Minimum conference rooms required for all meetings."""
    starts = sorted(i[0] for i in intervals)
    ends = sorted(i[1] for i in intervals)
    s_ptr = e_ptr = 0
    used_rooms = max_rooms = 0
    while s_ptr < len(starts):
        if starts[s_ptr] < ends[e_ptr]:
            used_rooms += 1
            s_ptr += 1
        else:
            used_rooms -= 1
            e_ptr += 1
        max_rooms = max(max_rooms, used_rooms)
    return max_rooms


def insert_interval_oracle(intervals: list[list[int]], new_interval: list[int]) -> list[list[int]]:
    """Insert new interval into sorted non-overlapping intervals and merge."""
    return merge_intervals_oracle(intervals + [new_interval])


def generate_intervals_questions(count: int = 12, seed: int = 303) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    q_idx = 1

    # Design 1: intervals.merge_count (Easy, 4 instances)
    merge_cases = [
        [[1, 3], [2, 6], [8, 10], [15, 18]],
        [[1, 4], [4, 5]],
        [[1, 4], [2, 3], [5, 8], [6, 9], [11, 14]],
        [[2, 5], [6, 7], [8, 9], [1, 10]],
    ]
    for intervals in merge_cases:
        merged = merge_intervals_oracle(intervals)
        ans_val = len(merged)
        ans = str(ans_val)
        unmerged_count = len(intervals)
        cand = [ans_val + 1, ans_val + 2, ans_val + 3, max(0, ans_val - 1), unmerged_count]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans]
        prompt = (
            f"Given the collection of intervals `intervals = {intervals}`, "
            f"all overlapping intervals are merged together. "
            f"How many non-overlapping intervals remain after merging?"
        )
        exp = (
            f"Sorting by start times and collapsing overlapping ranges gives {merged}, "
            f"which contains exactly {ans_val} non-overlapping interval(s)."
        )
        questions.append(
            make_question(
                id_str=f"gen-inv-merge-{q_idx}",
                topic="intervals",
                subtopic="merge-intervals",
                difficulty="Easy",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="intervals.merge_count",
                rng=rng,
            )
        )
        q_idx += 1

    # Design 2: intervals.min_meeting_rooms (Medium, 4 instances)
    room_cases = [
        [[0, 30], [5, 10], [15, 20]],
        [[7, 10], [2, 4]],
        [[1, 5], [2, 6], [3, 7], [4, 8], [5, 9]],
        [[9, 10], [4, 9], [4, 17]],
    ]
    for intervals in room_cases:
        ans_val = min_meeting_rooms_oracle(intervals)
        ans = str(ans_val)
        cand = [ans_val + 1, ans_val + 2, ans_val + 3, max(1, ans_val - 1), len(intervals)]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans]
        prompt = (
            f"Given meeting time intervals `intervals = {intervals}` where `intervals[i] = [start, end]`, "
            f"what is the minimum number of conference rooms required so no two overlapping meetings share a room?"
        )
        exp = (
            f"The minimum number of rooms equals the maximum number of concurrent overlapping meetings at any point in time. "
            f"A sweep-line or min-heap on end times determines that {ans_val} room(s) are needed."
        )
        questions.append(
            make_question(
                id_str=f"gen-inv-rooms-{q_idx}",
                topic="intervals",
                subtopic="meeting-rooms",
                difficulty="Medium",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="intervals.min_meeting_rooms",
                rng=rng,
            )
        )
        q_idx += 1

    # Design 3: intervals.insert_interval (Hard, 4 instances)
    insert_cases = [
        ([[1, 3], [6, 9]], [2, 5]),
        ([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]),
        ([[1, 5]], [6, 8]),
        ([[1, 5]], [0, 3]),
    ]
    for intervals, new_inv in insert_cases:
        merged = insert_interval_oracle(intervals, new_inv)
        ans = str(merged)
        cand = [
            str(sorted(intervals + [new_inv])),
            str([[merged[0][0], merged[-1][1] + 1]]),
            str([[merged[0][0] + 1, merged[-1][1]]]),
            str([new_inv] + intervals),
            str(intervals + [new_inv]),
            str([[merged[0][0], merged[-1][1] - 1]]),
        ]
        distractors = [d for d in dict.fromkeys(cand) if d != ans]
        prompt = (
            f"Given sorted non-overlapping intervals `intervals = {intervals}` and `newInterval = {new_inv}`, "
            f"insert `newInterval` into `intervals` and merge all overlapping intervals. "
            f"What is the resulting merged intervals list?"
        )
        exp = (
            f"Inserting {new_inv} merges with any overlapping existing intervals. "
            f"The resulting clean non-overlapping list is {merged}."
        )
        questions.append(
            make_question(
                id_str=f"gen-inv-insert-{q_idx}",
                topic="intervals",
                subtopic="insert-interval",
                difficulty="Hard",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="intervals.insert_interval",
                rng=rng,
            )
        )
        q_idx += 1

    return questions[:count]
