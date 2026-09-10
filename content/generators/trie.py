"""Trie data structure algorithmic question generator with programmatic oracles."""

import random

from content.generators.base import GeneratedQuestion, make_question


def trie_prefix_count_oracle(words: list[str], prefix: str) -> int:
    """Count words in list starting with prefix."""
    return sum(1 for w in words if w.startswith(prefix))


def trie_node_count_oracle(words: list[str]) -> int:
    """Total nodes in Trie including empty root node."""
    root: dict = {}
    node_count = 1  # root node
    for w in words:
        curr = root
        for ch in w:
            if ch not in curr:
                curr[ch] = {}
                node_count += 1
            curr = curr[ch]
    return node_count


def trie_max_xor_pair_oracle(nums: list[int]) -> int:
    """Maximum XOR value between any two numbers in array."""
    max_xor = 0
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            max_xor = max(max_xor, nums[i] ^ nums[j])
    return max_xor


def generate_trie_questions(count: int = 12, seed: int = 302) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    q_idx = 1

    # Design 1: trie.prefix_count (Easy, 4 instances)
    prefix_cases = [
        (["apple", "app", "apricot", "banana", "band", "bandwidth"], "ban"),
        (["car", "cart", "carpet", "care", "carbon", "dog"], "car"),
        (["code", "coder", "coding", "codec", "data", "date"], "cod"),
        (["flow", "flower", "flight", "flat", "fleet", "fly"], "fl"),
    ]
    for words, prefix in prefix_cases:
        ans_val = trie_prefix_count_oracle(words, prefix)
        ans = str(ans_val)
        cand = [ans_val + 1, max(1, ans_val - 1), ans_val + 2, max(0, ans_val - 2)]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans]
        prompt = (
            f"A standard Trie is populated with the word list: `{words}`. "
            f"How many words in the Trie have the prefix `\"{prefix}\"`?"
        )
        exp = (
            f"Traversing the Trie down the characters of prefix '{prefix}' reaches a node whose subtree "
            f"contains exactly {ans_val} marked terminal word nodes."
        )
        questions.append(
            make_question(
                id_str=f"gen-trie-pfx-{q_idx}",
                topic="trie",
                subtopic="prefix-queries",
                difficulty="Easy",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="trie.prefix_count",
                rng=rng,
            )
        )
        q_idx += 1

    # Design 2: trie.node_count (Medium, 4 instances)
    node_cases = [
        ["cat", "car", "cart"],
        ["to", "tea", "ted", "ten", "a", "inn"],
        ["be", "bee", "been", "bear"],
        ["he", "she", "his", "her"],
    ]
    for words in node_cases:
        ans_val = trie_node_count_oracle(words)
        ans = str(ans_val)
        unshared = sum(len(w) for w in words) + 1
        cand = [ans_val + 1, ans_val - 1, unshared, ans_val + 2, ans_val - 2]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans and d > 0]
        prompt = (
            f"The following list of words is inserted into an initially empty Trie:\n"
            f"`{words}`\n\n"
            f"Including the empty root node, what is the total number of distinct nodes in the resulting Trie?"
        )
        exp = (
            f"Shared common prefixes reuse existing nodes along the path. "
            f"Counting the root node plus every distinct prefix character path produces exactly {ans_val} nodes."
        )
        questions.append(
            make_question(
                id_str=f"gen-trie-nodes-{q_idx}",
                topic="trie",
                subtopic="trie-structure",
                difficulty="Medium",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="trie.node_count",
                rng=rng,
            )
        )
        q_idx += 1

    # Design 3: trie.max_xor_pair (Hard, 4 instances)
    xor_cases = [
        [3, 10, 5, 25, 2, 8],
        [14, 70, 53, 83, 49, 91, 36, 80],
        [8, 1, 2, 12, 7, 6],
        [4, 6, 7],
    ]
    for nums in xor_cases:
        ans_val = trie_max_xor_pair_oracle(nums)
        ans = str(ans_val)
        cand = [ans_val + 2, ans_val - 3, ans_val + 4, max(1, ans_val - 1), ans_val + 7]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans and d >= 0]
        prompt = (
            f"Given the integer array `nums = {nums}`, a bitwise 0/1 binary Trie is constructed to query "
            f"the maximum possible bitwise XOR value (`nums[i] ^ nums[j]`) in O(32 * N) time. "
            f"What is the maximum XOR value attainable between any pair of elements?"
        )
        exp = (
            f"By storing numbers in a bitwise binary Trie and greedily traversing opposite bits (1 vs 0) "
            f"from most significant bit to least significant bit, the maximum XOR value found is {ans_val}."
        )
        questions.append(
            make_question(
                id_str=f"gen-trie-xor-{q_idx}",
                topic="trie",
                subtopic="binary-trie-xor",
                difficulty="Hard",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="trie.max_xor_pair",
                rng=rng,
            )
        )
        q_idx += 1

    return questions[:count]
