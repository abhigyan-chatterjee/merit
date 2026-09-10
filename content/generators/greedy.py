"""Greedy algorithmic question generator with exact programmatic oracles."""

import random

from content.generators.base import GeneratedQuestion, make_question


def coin_change_greedy_oracle(amount: int, coins: list[int] | None = None) -> int:
    """Minimum coins needed using standard canonical greedy denominations [25, 10, 5, 1]."""
    if coins is None:
        coins = [25, 10, 5, 1]
    total_coins = 0
    rem = amount
    for c in coins:
        total_coins += rem // c
        rem %= c
    return total_coins


def jump_game_min_jumps_oracle(nums: list[int]) -> int:
    """Minimum jumps to reach the last index (Jump Game II)."""
    if len(nums) <= 1:
        return 0
    jumps = 0
    curr_end = 0
    farthest = 0
    for i in range(len(nums) - 1):
        farthest = max(farthest, i + nums[i])
        if i == curr_end:
            jumps += 1
            curr_end = farthest
            if curr_end >= len(nums) - 1:
                break
    return jumps


def gas_station_start_oracle(gas: list[int], cost: list[int]) -> int:
    """Starting gas station index to complete circular tour, or -1 if impossible."""
    if sum(gas) < sum(cost):
        return -1
    total = 0
    start = 0
    for i in range(len(gas)):
        total += gas[i] - cost[i]
        if total < 0:
            total = 0
            start = i + 1
    return start


def generate_greedy_questions(count: int = 12, seed: int = 304) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    q_idx = 1

    # Design 1: greedy.coin_change_greedy (Easy, 4 instances)
    coin_cases = [67, 41, 99, 30]
    for amount in coin_cases:
        ans_val = coin_change_greedy_oracle(amount)
        ans = str(ans_val)
        cand = [ans_val + 1, ans_val - 1, ans_val + 2, max(1, ans_val - 2), ans_val + 3]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans and d > 0]
        prompt = (
            f"In a canonical currency system with denominations `[25, 10, 5, 1]` cents, "
            f"what is the minimum number of coins needed to make `{amount}` cents using a greedy approach?"
        )
        exp = (
            f"Greedily picking largest coins first: {amount // 25}x25c, "
            f"{(amount % 25) // 10}x10c, {((amount % 25) % 10) // 5}x5c, and "
            f"{((amount % 25) % 10) % 5}x1c totals {ans_val} coins."
        )
        questions.append(
            make_question(
                id_str=f"gen-greedy-coin-{q_idx}",
                topic="greedy",
                subtopic="canonical-coin-change",
                difficulty="Easy",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="greedy.coin_change_greedy",
                rng=rng,
            )
        )
        q_idx += 1

    # Design 2: greedy.jump_game_min_jumps (Medium, 4 instances)
    jump_cases = [
        [2, 3, 1, 1, 4],
        [2, 3, 0, 1, 4],
        [1, 2, 1, 1, 1],
        [3, 4, 2, 1, 2, 1],
    ]
    for nums in jump_cases:
        ans_val = jump_game_min_jumps_oracle(nums)
        ans = str(ans_val)
        cand = [ans_val + 1, max(1, ans_val - 1), ans_val + 2, max(1, ans_val - 2), ans_val + 3]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans]
        prompt = (
            f"Given array `nums = {nums}` where `nums[i]` is the maximum jump length from index `i`, "
            f"what is the minimum number of jumps needed to reach the last index (`{len(nums)-1}`)?"
        )
        exp = (
            f"Using BFS level-by-level greedy interval expansion, each jump extends to the farthest reachable "
            f"boundary. Reaching index {len(nums)-1} requires at minimum {ans_val} jump(s)."
        )
        questions.append(
            make_question(
                id_str=f"gen-greedy-jump-{q_idx}",
                topic="greedy",
                subtopic="jump-game",
                difficulty="Medium",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="greedy.jump_game_min_jumps",
                rng=rng,
            )
        )
        q_idx += 1

    # Design 3: greedy.gas_station_start (Hard, 4 instances)
    gas_cases = [
        ([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]),
        ([2, 3, 4], [3, 4, 3]),
        ([5, 1, 2, 3, 4], [4, 4, 1, 5, 1]),
        ([3, 1, 1], [1, 2, 2]),
    ]
    for gas, cost in gas_cases:
        ans_val = gas_station_start_oracle(gas, cost)
        ans = str(ans_val)
        cand = [str(i) for i in range(len(gas))] + ["-1"]
        distractors = [d for d in dict.fromkeys(cand) if d != ans]
        prompt = (
            f"There are {len(gas)} circular gas stations with `gas = {gas}` and travel costs `cost = {cost}`. "
            f"What is the unique starting gas station index (0-indexed) that allows completing the full circuit, "
            f"or -1 if impossible?"
        )
        if ans_val == -1:
            exp = (
                f"Total gas ({sum(gas)}) is strictly less than total cost ({sum(cost)}), "
                f"meaning completing the full circle is impossible (returns -1)."
            )
        else:
            exp = (
                f"Total gas ({sum(gas)}) >= total cost ({sum(cost)}), guaranteeing a solution exists. "
                f"Starting at index {ans_val} maintains a non-negative fuel balance across all stations."
            )
        questions.append(
            make_question(
                id_str=f"gen-greedy-gas-{q_idx}",
                topic="greedy",
                subtopic="gas-station",
                difficulty="Hard",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="greedy.gas_station_start",
                rng=rng,
            )
        )
        q_idx += 1

    return questions[:count]
