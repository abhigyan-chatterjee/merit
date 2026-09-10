"""Data structure operations generator (stacks, queues, heaps, hash maps, linked lists) with programmatic state oracles."""

import heapq
import random

from content.generators.base import GeneratedQuestion, make_question


def eval_rpn_oracle(tokens: list[str]) -> int:
    stk: list[int] = []
    for tok in tokens:
        if tok in "+-*/":
            b = stk.pop()
            a = stk.pop()
            if tok == "+":
                stk.append(a + b)
            elif tok == "-":
                stk.append(a - b)
            elif tok == "*":
                stk.append(a * b)
            elif tok == "/":
                stk.append(int(a / b))
        else:
            stk.append(int(tok))
    return stk[0]


def largest_rectangle_histogram_oracle(heights: list[int]) -> int:
    stk: list[int] = []
    max_area = 0
    h = heights + [0]
    for i, x in enumerate(h):
        while stk and h[stk[-1]] >= x:
            top_h = h[stk.pop()]
            w = i if not stk else i - stk[-1] - 1
            max_area = max(max_area, top_h * w)
        stk.append(i)
    return max_area


def kth_smallest_matrix_oracle(mat: list[list[int]], k: int) -> int:
    h: list[tuple[int, int, int]] = []
    n = len(mat)
    for r in range(min(n, k)):
        heapq.heappush(h, (mat[r][0], r, 0))
    val = -1
    for _ in range(k):
        val, r, c = heapq.heappop(h)
        if c + 1 < len(mat[r]):
            heapq.heappush(h, (mat[r][c + 1], r, c + 1))
    return val


def floyd_meeting_oracle(n: int, pos: int) -> int:
    succ = list(range(1, n)) + [pos]
    slow = succ[0]
    fast = succ[succ[0]]
    while slow != fast:
        slow = succ[slow]
        fast = succ[succ[fast]]
    return slow


def reverse_sublist_oracle(n: int, left: int, right: int) -> list[int]:
    vals = list(range(1, n + 1))
    vals[left - 1 : right] = reversed(vals[left - 1 : right])
    return vals


def generate_ds_questions(count: int = 140, seed: int = 44) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    q_idx = 1

    # 1. Stack Sequence Simulation
    stack_scenarios = [
        (["push(10)", "push(20)", "pop()", "push(30)", "push(40)", "pop()", "push(50)"], "50", ["40", "30", "10"], "Top of stack is 50"),
        (["push(5)", "push(15)", "push(25)", "pop()", "pop()", "push(35)"], "35", ["15", "5", "25"], "Top of stack is 35"),
        (["push(1)", "push(2)", "push(3)", "pop()", "push(4)", "pop()", "pop()"], "1", ["2", "3", "4"], "Top of stack is 1"),
        (["push(7)", "push(14)", "push(21)", "push(28)", "pop()", "push(35)"], "35", ["28", "21", "14"], "Top of stack is 35"),
        (["push(100)", "push(200)", "pop()", "push(300)", "pop()", "push(400)"], "400", ["100", "200", "300"], "Top of stack is 400"),
        (["push(2)", "push(4)", "push(6)", "push(8)", "pop()", "pop()"], "4", ["2", "6", "8"], "Top of stack is 4"),
        (["push(9)", "push(18)", "pop()", "push(27)", "push(36)", "push(45)", "pop()"], "36", ["27", "18", "45"], "Top of stack is 36"),
        (["push(11)", "push(22)", "push(33)", "pop()", "push(44)"], "44", ["33", "22", "11"], "Top of stack is 44"),
        (["push(3)", "push(6)", "push(9)", "pop()", "pop()", "pop()", "push(12)"], "12", ["9", "6", "3"], "Top of stack is 12"),
        (["push(15)", "push(30)", "push(45)", "pop()", "push(60)", "pop()"], "30", ["45", "15", "60"], "Top of stack is 30"),
        (["push(8)", "push(16)", "push(24)", "push(32)", "pop()", "push(40)", "pop()"], "24", ["16", "32", "40"], "Top of stack is 24"),
        (["push(13)", "push(26)", "pop()", "push(39)", "pop()", "push(52)"], "52", ["39", "26", "13"], "Top of stack is 52"),
        (["push(50)", "push(100)", "push(150)", "pop()", "push(200)", "push(250)", "pop()"], "200", ["150", "100", "250"], "Top of stack is 200"),
        (["push(4)", "push(8)", "pop()", "push(12)", "push(16)", "pop()", "pop()"], "4", ["8", "12", "16"], "Top of stack is 4"),
        (["push(17)", "push(34)", "push(51)", "pop()", "pop()", "push(68)"], "68", ["51", "34", "17"], "Top of stack is 68"),
    ]

    for ops, ans, distractors, desc in stack_scenarios:
        ops_str = " -> ".join(ops)
        prompt = (
            f"An initially empty LIFO stack undergoes the following sequence of operations:\n"
            f"`{ops_str}`\n\n"
            f"What value is currently at the top of the stack?"
        )
        q = make_question(
            id_str=f"gen-ds-stack-{q_idx}",
            topic="stack",
            subtopic="stack-operations",
            difficulty="Easy",
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=f"Simulating operations in LIFO order: {desc}.",
            generator_key="ds_operations.stack_sim",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 2. Circular Queue Array Indices
    queue_configs = [
        (8, 0, 5, 2, 4),   # capacity, initial_front, initial_count, dequeues, enqueues
        (6, 2, 4, 3, 2),
        (10, 7, 3, 1, 5),
        (5, 3, 2, 2, 3),
        (12, 10, 2, 1, 4),
        (8, 4, 4, 3, 1),
        (7, 1, 3, 2, 4),
        (9, 5, 3, 4, 2),
        (11, 8, 2, 3, 5),
        (14, 12, 2, 2, 3),
        (6, 4, 2, 3, 1),
        (10, 9, 1, 2, 4),
        (8, 6, 2, 3, 3),
        (7, 3, 3, 1, 2),
        (12, 5, 5, 4, 2),
    ]

    for cap, front, initial_cnt, deq, enq in queue_configs:
        final_front = (front + deq) % cap

        prompt = (
            f"A circular queue is implemented using a 0-indexed array of capacity {cap}. "
            f"Currently, `front = {front}` and it contains {initial_cnt} elements. "
            f"If {deq} `dequeue()` operations are performed, followed by {enq} `enqueue()` operations, "
            f"what will be the new index of `front` in the array?"
        )
        ans = str(final_front)
        distractors = [
            str((final_front + 1) % cap),
            str((final_front - 1 + cap) % cap),
            str((final_front + 2) % cap),
        ]
        q = make_question(
            id_str=f"gen-ds-queue-{q_idx}",
            topic="data-structures",
            subtopic="circular-queue",
            difficulty="Medium",
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=f"Each dequeue advances front modulo capacity: new_front = (front + dequeues) % capacity = ({front} + {deq}) % {cap} = {final_front}.",
            generator_key="ds_operations.circular_queue",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 3. Min-Heap Array Representation
    heap_inputs = [
        [10, 20, 15, 30, 40, 25],
        [5, 8, 12, 16, 20, 15, 30],
        [4, 10, 3, 5, 1],
        [50, 30, 20, 15, 10, 8, 16],
        [18, 14, 22, 9, 7, 31, 45],
        [100, 70, 60, 50, 40, 30, 20],
        [25, 17, 36, 2, 19, 10],
        [42, 35, 28, 14, 7, 21, 49],
        [60, 55, 45, 35, 25, 15, 5],
        [13, 26, 39, 52, 65, 78],
        [88, 77, 66, 55, 44, 33, 22],
        [12, 3, 17, 8, 34, 40, 9],
        [31, 24, 19, 11, 4, 15, 2],
        [95, 85, 75, 65, 55, 45, 35],
        [9, 18, 27, 36, 45, 54, 63],
    ]

    for arr in heap_inputs:
        heap_arr = list(arr)
        heapq.heapify(heap_arr)
        ans = str(heap_arr)
        # Distractors: permutations that violate heap property
        cand_heap = [
            str(sorted(arr, reverse=True)),
            str(arr[1:] + [arr[0]]),
            str([arr[-1]] + arr[:-1]),
            str(list(reversed(arr))),
            str(sorted(arr)),
        ]
        distractors = [d for d in dict.fromkeys(cand_heap) if d != ans]

        prompt = (
            f"Elements `{arr}` are placed into an array and converted into a Min-Heap using Floyd's bottom-up buildHeap algorithm. "
            f"Which array representation satisfies the min-heap parent-child invariant `A[i] <= A[2i+1]` and `A[i] <= A[2i+2]`?"
        )
        q = make_question(
            id_str=f"gen-ds-heap-{q_idx}",
            topic="heap",
            subtopic="binary-heap",
            difficulty="Medium",
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=f"A valid binary min-heap must satisfy A[i] <= children for every parent. Bottom-up heapify rearranges `{arr}` to `{heap_arr}`.",
            generator_key="ds_operations.heapify",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 4. Hash Table Linear Probing Simulation
    hash_tables = [
        (7, [10, 20, 5, 12, 26]),
        (11, [22, 33, 44, 15, 26, 37]),
        (13, [18, 26, 35, 9, 64, 47]),
        (7, [14, 21, 28, 7, 35]),
        (10, [15, 25, 35, 45, 55]),
        (9, [18, 27, 36, 45, 9]),
        (11, [12, 23, 34, 45, 56]),
        (13, [26, 39, 52, 65, 13]),
        (8, [16, 24, 32, 40, 8]),
        (7, [3, 10, 17, 24, 31]),
        (10, [20, 30, 40, 50, 60]),
        (11, [5, 16, 27, 38, 49]),
        (13, [7, 20, 33, 46, 59]),
        (9, [4, 13, 22, 31, 40]),
        (7, [8, 15, 22, 29, 36]),
    ]

    for table_size, keys in hash_tables:
        table = [None] * table_size
        probe_counts = []
        for key in keys:
            h = key % table_size
            probes = 1
            while table[h] is not None:
                h = (h + 1) % table_size
                probes += 1
            table[h] = key
            probe_counts.append((key, h, probes))

        # Ask where the last key landed
        last_key, final_pos, probes_needed = probe_counts[-1]
        prompt = (
            f"A hash table of size {table_size} uses open addressing with linear probing (hash function `h(k) = k mod {table_size}`). "
            f"Keys are inserted in the following order: `{keys}`.\n"
            f"At which slot index in the table will key `{last_key}` be placed?"
        )
        ans = str(final_pos)
        distractors = [
            str((final_pos + 1) % table_size),
            str((final_pos - 1 + table_size) % table_size),
            str((final_pos + 2) % table_size),
        ]
        explanation = (
            f"Key {last_key} has initial hash {last_key} % {table_size} = {last_key % table_size}. "
            f"Due to prior collisions, it requires {probes_needed} probe(s) and lands in slot {final_pos}."
        )
        q = make_question(
            id_str=f"gen-ds-hash-{q_idx}",
            topic="arrays-hashing",
            subtopic="collision-resolution",
            difficulty="Hard",
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=explanation,
            generator_key="ds_operations.linear_probing",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 5. Trie & Disjoint Set Conceptual Invariants
    dsu_trie_cases = [
        ("In a Disjoint Set Union (DSU) structure using both Union by Rank and Path Compression, what is the maximum tree height after any sequence of operations on n elements?", "O(α(n))", ["O(log n)", "O(1)", "O(√n)"], "Union by rank and path compression together bound the depth to the inverse Ackermann function α(n).", "Hard"),
        ("What is the time complexity of searching for a word of length L in a standard Trie containing N total words of average length M?", "O(L)", ["O(N * L)", "O(log N)", "O(M * log N)"], "Trie lookup checks one edge per character of the query string. Finding or failing a word of length L takes exactly O(L) time, completely independent of the number of words N stored in the Trie.", "Easy"),
        ("In a Singly Linked List with head and tail pointers, which operation CANNOT be performed in O(1) time without extra pointers?", "Deleting the tail node", ["Inserting at head", "Inserting at tail", "Deleting the head node"], "Deleting the tail requires updating the second-to-last node's next pointer to null. In a singly linked list, finding the second-to-last node requires traversing from the head in O(n) time.", "Easy"),
        ("What is the primary motivation for using a Doubly Linked List over a Singly Linked List when implementing an LRU Cache?", "O(1) deletion of an arbitrary node given only its direct pointer", ["Lower memory usage per node", "Faster cache lookups", "Simpler concurrency locks"], "An LRU cache pairs a hash map with a doubly linked list. When a key is accessed, its node can be spliced out of its current position in O(1) time because prev and next pointers are directly available.", "Medium"),
    ]

    for prompt, ans, distractors, exp, diff in dsu_trie_cases:
        q = make_question(
            id_str=f"gen-ds-concept-{q_idx}",
            topic="linked-lists",
            subtopic="data-structure-properties",
            difficulty=diff,
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=exp,
            generator_key="ds_operations.concepts",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 6. Stack Postfix Evaluation (stack.postfix_evaluation, Medium, 4 instances)
    rpn_cases = [
        ["2", "1", "+", "3", "*"],
        ["4", "13", "5", "/", "+"],
        ["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"],
        ["5", "3", "2", "*", "+", "4", "-"],
    ]
    for tokens in rpn_cases:
        ans_val = eval_rpn_oracle(tokens)
        ans = str(ans_val)
        cand = [ans_val + 3, ans_val - 3, ans_val + 5, ans_val * 2 if ans_val != 0 else 4, max(1, ans_val - 2)]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans]
        prompt = (
            f"Evaluate the arithmetic expression in Reverse Polish Notation (postfix notation) using an operand stack:\n"
            f"`{tokens}`\n\n"
            f"All operations follow standard integer arithmetic. What is the final evaluated result?"
        )
        exp = (
            f"Evaluating in postfix order using an operand stack processes operands and operators from left to right, "
            f"yielding the final result {ans_val}."
        )
        questions.append(
            make_question(
                id_str=f"gen-stack-rpn-{q_idx}",
                topic="stack",
                subtopic="postfix-evaluation",
                difficulty="Medium",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="stack.postfix_evaluation",
                rng=rng,
            )
        )
        q_idx += 1

    # 7. Stack Largest Rectangle in Histogram (stack.largest_rectangle_histogram, Hard, 4 instances)
    hist_cases = [
        [2, 1, 5, 6, 2, 3],
        [2, 4],
        [6, 2, 5, 4, 5, 1, 6],
        [3, 3, 3, 3, 3],
    ]
    for heights in hist_cases:
        ans_val = largest_rectangle_histogram_oracle(heights)
        ans = str(ans_val)
        cand = [ans_val + 2, max(1, ans_val - 2), ans_val + 4, max(1, ans_val - 4), ans_val + 6]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans]
        prompt = (
            f"Given an array of histogram bar heights `heights = {heights}` (where width of each bar is 1), "
            f"a monotonic increasing stack is used to find the maximum rectangular area in O(N) time. "
            f"What is the area of the largest rectangle in the histogram?"
        )
        exp = (
            f"Using a monotonic increasing stack to determine left and right smaller boundaries for each bar, "
            f"the maximum rectangle area formed is {ans_val}."
        )
        questions.append(
            make_question(
                id_str=f"gen-stack-hist-{q_idx}",
                topic="stack",
                subtopic="monotonic-stack-histogram",
                difficulty="Hard",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="stack.largest_rectangle_histogram",
                rng=rng,
            )
        )
        q_idx += 1

    # 8. Heap Kth Largest Element (heap.kth_largest, Medium, 4 instances)
    kth_cases = [
        ([3, 2, 1, 5, 6, 4], 2),
        ([3, 2, 3, 1, 2, 4, 5, 5, 6], 4),
        ([7, 10, 4, 3, 20, 15], 3),
        ([12, 3, 5, 7, 19], 1),
    ]
    for nums, k in kth_cases:
        ans_val = sorted(nums, reverse=True)[k - 1]
        ans = str(ans_val)
        sorted_unique = sorted(set(nums), reverse=True)
        cand = [str(x) for x in sorted_unique if x != ans_val] + [str(ans_val + 1), str(ans_val - 1)]
        distractors = [d for d in dict.fromkeys(cand) if d != ans]
        prompt = (
            f"Given the unsorted array `nums = {nums}` and `k = {k}`, "
            f"a min-heap of size `k` is maintained while scanning through the array to find the k-th largest element. "
            f"What is the value of the {k}-th largest element in `nums`?"
        )
        exp = (
            f"Maintaining a min-heap of size {k} retains the {k} largest elements seen so far; "
            f"the root of the heap gives the {k}-th largest value, which is {ans_val}."
        )
        questions.append(
            make_question(
                id_str=f"gen-heap-kth-{q_idx}",
                topic="heap",
                subtopic="kth-largest-element",
                difficulty="Medium",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="heap.kth_largest",
                rng=rng,
            )
        )
        q_idx += 1

    # 9. Heap Kth Smallest in Sorted Matrix (heap.kth_smallest_matrix, Hard, 4 instances)
    matrix_k_cases = [
        ([[1, 5, 9], [10, 11, 13], [12, 13, 15]], 8),
        ([[1, 2, 3], [4, 5, 6], [7, 8, 9]], 5),
        ([[1, 4, 7], [2, 5, 8], [3, 6, 9]], 4),
        ([[2, 6, 8], [3, 7, 10], [5, 8, 11]], 6),
    ]
    for mat, k in matrix_k_cases:
        ans_val = kth_smallest_matrix_oracle(mat, k)
        ans = str(ans_val)
        cand = [ans_val + 1, ans_val - 1, ans_val + 2, ans_val - 2, ans_val + 3]
        distractors = [str(d) for d in dict.fromkeys(cand) if str(d) != ans]
        prompt = (
            f"Given an `n x n` matrix `matrix = {mat}` where each row and column is sorted in ascending order, "
            f"a min-heap of row heads is used to extract elements in order. "
            f"What is the value of the `{k}`-th smallest element in the matrix?"
        )
        exp = (
            f"Using a min-heap initialized with the first element of each row and popping k times "
            f"(pushing the next element in the same row) finds the {k}-th smallest value {ans_val}."
        )
        questions.append(
            make_question(
                id_str=f"gen-heap-mat-{q_idx}",
                topic="heap",
                subtopic="kth-smallest-matrix",
                difficulty="Hard",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="heap.kth_smallest_matrix",
                rng=rng,
            )
        )
        q_idx += 1

    # 10. Linked List Cycle Meeting Node (linked_lists.cycle_meeting_index, Medium, 4 instances)
    cycle_cases = [
        (4, 1),
        (5, 2),
        (6, 0),
        (4, 2),
    ]
    for n_nodes, pos in cycle_cases:
        ans_val = floyd_meeting_oracle(n_nodes, pos)
        ans = str(ans_val)
        cand = [str(i) for i in range(n_nodes)]
        distractors = [d for d in dict.fromkeys(cand) if d != ans]
        prompt = (
            f"A singly linked list has {n_nodes} nodes with 0-indexed values `0, 1, ..., {n_nodes - 1}`. "
            f"The tail node (`{n_nodes - 1}`) connects back to node `{pos}`, forming a cycle. "
            f"Floyd's Tortoise and Hare algorithm starts both `slow` (speed 1) and `fast` (speed 2) at node `0`. "
            f"At which node value do `slow` and `fast` first collide?"
        )
        exp = (
            f"Simulating pointer movements step-by-step, slow and fast pointers first meet inside the cycle "
            f"at node {ans_val}."
        )
        questions.append(
            make_question(
                id_str=f"gen-ll-meet-{q_idx}",
                topic="linked-lists",
                subtopic="cycle-detection",
                difficulty="Medium",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="linked_lists.cycle_meeting_index",
                rng=rng,
            )
        )
        q_idx += 1

    # 11. Linked List Reverse Sublist (linked_lists.reverse_sublist, Hard, 4 instances)
    sublist_cases = [
        (5, 2, 4),
        (4, 1, 3),
        (6, 3, 5),
        (5, 1, 5),
    ]
    for n_nodes, left, right in sublist_cases:
        res = reverse_sublist_oracle(n_nodes, left, right)
        ans = str(res)
        cand = [
            str(list(range(1, n_nodes + 1))),  # unreversed
            str(list(reversed(range(1, n_nodes + 1)))),  # fully reversed
            str(list(range(2, n_nodes + 1)) + [1]),  # cyclic shift
            str([n_nodes] + list(range(1, n_nodes))),  # cyclic shift right
            str(reverse_sublist_oracle(n_nodes, max(1, left - 1), right)),  # off-by-one left
            str(reverse_sublist_oracle(n_nodes, left, min(n_nodes, right + 1))),  # off-by-one right
        ]
        distractors = [d for d in dict.fromkeys(cand) if d != ans]
        prompt = (
            f"Given the head of a singly linked list containing 1-indexed node values `1, 2, ..., {n_nodes}`, "
            f"the sublist from position `{left}` to `{right}` (inclusive) is reversed in-place in a single pass. "
            f"What is the resulting sequence of node values in the list?"
        )
        exp = (
            f"Reversing only nodes between position {left} and {right} reconnects the predecessor and successor, "
            f"producing the order {res}."
        )
        questions.append(
            make_question(
                id_str=f"gen-ll-revsub-{q_idx}",
                topic="linked-lists",
                subtopic="reverse-sublist",
                difficulty="Hard",
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="linked_lists.reverse_sublist",
                rng=rng,
            )
        )
        q_idx += 1

    return questions[:count]
