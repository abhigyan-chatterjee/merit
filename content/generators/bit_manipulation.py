"""Bit manipulation question generator with exact programmatic bitwise oracles."""

import random
from content.generators.base import GeneratedQuestion, make_question


def generate_bit_manipulation_questions(count: int = 100, seed: int = 50) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    q_idx = 1

    # 1. Brian Kernighan bit count & lowest set bit tricks
    bit_inputs = [
        12, 7, 16, 23, 31, 64, 53, 40, 15, 29, 48, 63, 100, 127, 255, 128, 77, 85, 96, 150
    ]

    for n in bit_inputs:
        set_bits = bin(n).count("1")
        ans = str(set_bits)
        cand_b = [set_bits + 1, set_bits + 2, set_bits + 3]
        if set_bits > 1:
            cand_b.append(set_bits - 1)
        distractors = [str(d) for d in cand_b if str(d) != ans]
        prompt = (
            f"How many set bits (1s in binary representation) are in the integer `{n}` (`0b{bin(n)[2:]}`)? "
            f"This can be computed in O(k) iterations using Brian Kernighan's algorithm `n = n & (n - 1)`."
        )
        q = make_question(
            id_str=f"gen-bit-count-{q_idx}",
            topic="bit-manipulation",
            subtopic="popcount",
            difficulty="Easy",
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=f"Integer {n} has binary representation 0b{bin(n)[2:]}, containing exactly {set_bits} set bit(s).",
            generator_key="bit_manipulation.popcount",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

        lowest_set_bit = n & (-n)
        ans_low = str(lowest_set_bit)
        cand_l = [
            lowest_set_bit * 2,
            lowest_set_bit * 4,
            lowest_set_bit + 2,
            lowest_set_bit + 3,
            (lowest_set_bit // 2) if lowest_set_bit > 1 else 0,
        ]
        distractors_low = [str(d) for d in dict.fromkeys(cand_l) if str(d) != ans_low]
        prompt_low = (
            f"What is the result of evaluating the bitwise expression `n & (-n)` when `n = {n}`? "
            f"(This expression isolates the lowest set bit using two's complement arithmetic)."
        )
        q_low = make_question(
            id_str=f"gen-bit-lowest-{q_idx}",
            topic="bit-manipulation",
            subtopic="bit-tricks",
            difficulty="Medium",
            prompt=prompt_low,
            correct_answer=ans_low,
            distractors=distractors_low,
            explanation=f"In two's complement, -n = ~n + 1. Performing n & (-n) isolates the rightmost 1-bit, yielding {lowest_set_bit}.",
            generator_key="bit_manipulation.lowest_bit",
            rng=rng,
        )
        questions.append(q_low)
        q_idx += 1

    # 2. XOR Properties & Applications
    xor_concepts = [
        ("What is the result of applying XOR between any integer x and itself (`x ^ x`)?", "0", ["1", "x", "-1"], "The XOR operation returns 1 only when bits differ. For identical inputs, every corresponding bit pair is identical, yielding 0.", "Easy"),
        ("What bitwise expression checks whether a positive integer n is an exact power of 2 in O(1) time?", "(n & (n - 1)) == 0", ["(n & 1) == 0", "(n | (n - 1)) == 0", "(n ^ (n + 1)) == 0"], "A power of 2 has exactly one set bit (100...0). Subtracting 1 yields (011...1). Bitwise AND between them clears that single bit to 0.", "Easy"),
        ("Given an array where every element appears twice except for one unique element, how can the unique element be found in O(n) time and O(1) space?", "Compute the cumulative XOR sum of all elements in the array", ["Sort the array with QuickSort", "Insert all elements into a balanced BST", "Compute the sum of array elements minus n"], "Because XOR is commutative and associative, and x ^ x = 0, all paired numbers cancel each other out to 0, leaving 0 ^ unique = unique.", "Easy"),
        ("What is the time complexity of reversing the bits of a 32-bit integer using divide-and-conquer bit masks (swapping 16, 8, 4, 2, and 1-bit chunks)?", "O(1)", ["O(log 32)", "O(32)", "O(n)"], "Because the word size is fixed at 32 bits, swapping bitfields using 5 constant bit masks executes in a constant number of CPU cycles (O(1) time).", "Medium"),
    ]

    for prompt, ans, distractors, exp, diff in xor_concepts:
        q = make_question(
            id_str=f"gen-bit-concept-{q_idx}",
            topic="bit-manipulation",
            subtopic="xor-properties",
            difficulty=diff,
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=exp,
            generator_key="bit_manipulation.concepts",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    return questions[:count]
