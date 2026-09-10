"""Tree traversals and BST operations generator with programmatic tree traversal oracles."""

import random

from content.generators.base import GeneratedQuestion, make_question


class TreeNode:
    def __init__(self, val: int):
        self.val = val
        self.left: TreeNode | None = None
        self.right: TreeNode | None = None


def insert_bst(root: TreeNode | None, val: int) -> TreeNode:
    if root is None:
        return TreeNode(val)
    if val < root.val:
        root.left = insert_bst(root.left, val)
    else:
        root.right = insert_bst(root.right, val)
    return root


def inorder(root: TreeNode | None) -> list[int]:
    if not root:
        return []
    return inorder(root.left) + [root.val] + inorder(root.right)


def preorder(root: TreeNode | None) -> list[int]:
    if not root:
        return []
    return [root.val] + preorder(root.left) + preorder(root.right)


def postorder(root: TreeNode | None) -> list[int]:
    if not root:
        return []
    return postorder(root.left) + postorder(root.right) + [root.val]


def level_order(root: TreeNode | None) -> list[int]:
    if not root:
        return []
    res = []
    queue = [root]
    while queue:
        curr = queue.pop(0)
        res.append(curr.val)
        if curr.left:
            queue.append(curr.left)
        if curr.right:
            queue.append(curr.right)
    return res


def tree_height(root: TreeNode | None) -> int:
    if not root:
        return 0
    return 1 + max(tree_height(root.left), tree_height(root.right))


def count_leaves(root: TreeNode | None) -> int:
    if not root:
        return 0
    if not root.left and not root.right:
        return 1
    return count_leaves(root.left) + count_leaves(root.right)


def generate_tree_questions(count: int = 120, seed: int = 43) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    q_idx = 1

    # Pre-defined BST insertion sequences to yield rich trees
    sequences = [
        [50, 30, 70, 20, 40, 60, 80],
        [45, 25, 65, 15, 35, 55, 75],
        [10, 5, 15, 2, 7, 12, 18],
        [100, 50, 150, 25, 75, 125, 175],
        [40, 20, 60, 10, 30, 50, 70],
        [8, 3, 10, 1, 6, 14, 4, 7, 13],
        [20, 10, 30, 5, 15, 25, 35],
        [55, 33, 77, 22, 44, 66, 88],
        [60, 40, 80, 30, 50, 70, 90, 20],
        [15, 9, 23, 3, 12, 17, 28, 8],
        [50, 20, 80, 10, 30, 70, 90, 5, 15],
        [32, 16, 48, 8, 24, 40, 56],
        [25, 12, 37, 6, 18, 31, 43],
        [70, 50, 90, 40, 60, 80, 100],
        [50, 25, 75, 10, 40, 60, 90, 30],
        [65, 35, 85, 20, 45, 75, 95],
        [80, 40, 120, 20, 60, 100, 140],
        [42, 21, 63, 14, 28, 56, 70],
        [90, 60, 120, 40, 70, 110, 130],
        [30, 15, 45, 10, 20, 40, 50, 5],
        [16, 8, 24, 4, 12, 20, 28, 2],
        [88, 44, 132, 22, 66, 110, 154],
        [52, 26, 78, 13, 39, 65, 91],
        [64, 32, 96, 16, 48, 80, 112],
        [12, 6, 18, 3, 9, 15, 21],
        [96, 48, 144, 24, 72, 120, 168],
        [48, 24, 72, 12, 36, 60, 84],
        [75, 50, 100, 25, 60, 85, 115],
        [36, 18, 54, 9, 27, 45, 63],
        [28, 14, 42, 7, 21, 35, 49],
        [84, 42, 126, 21, 63, 105, 147],
        [22, 11, 33, 5, 17, 27, 39],
        [72, 36, 108, 18, 54, 90, 126],
        [68, 34, 102, 17, 51, 85, 119],
        [56, 28, 84, 14, 42, 70, 98],
        [44, 22, 66, 11, 33, 55, 77],
        [38, 19, 57, 10, 29, 47, 67],
        [92, 46, 138, 23, 69, 115, 161],
        [82, 41, 123, 20, 61, 102, 143],
        [74, 37, 111, 19, 55, 93, 129],
        [62, 31, 93, 15, 46, 77, 108],
        [58, 29, 87, 14, 43, 72, 101],
        [46, 23, 69, 12, 34, 58, 80],
        [105, 55, 155, 30, 80, 130, 180],
        [110, 60, 160, 35, 85, 135, 185],
        [115, 65, 165, 40, 90, 140, 190],
        [120, 70, 170, 45, 95, 145, 195],
        [125, 75, 175, 50, 100, 150, 200],
        [130, 80, 180, 55, 105, 155, 205],
        [135, 85, 185, 60, 110, 160, 210],
        [140, 90, 190, 65, 115, 165, 215],
        [145, 95, 195, 70, 120, 170, 220],
        [150, 100, 200, 75, 125, 175, 225],
        [155, 105, 205, 80, 130, 180, 230],
        [160, 110, 210, 85, 135, 185, 235],
        [165, 115, 215, 90, 140, 190, 240],
        [170, 120, 220, 95, 145, 195, 245],
        [175, 125, 225, 100, 150, 200, 250],
        [180, 130, 230, 105, 155, 205, 255],
        [185, 135, 235, 110, 160, 210, 260],
        [190, 140, 240, 115, 165, 215, 265],
        [195, 145, 245, 120, 170, 220, 270],
        [200, 150, 250, 125, 175, 225, 275],
        [205, 155, 255, 130, 180, 230, 280],
        [210, 160, 260, 135, 185, 235, 285],
        [215, 165, 265, 140, 190, 240, 290],
    ]

    traversal_types = ["Inorder", "Preorder", "Postorder", "Level-order"]

    for seq in sequences:
        root: TreeNode | None = None
        for val in seq:
            root = insert_bst(root, val)

        in_res = inorder(root)
        pre_res = preorder(root)
        post_res = postorder(root)
        lvl_res = level_order(root)
        height = tree_height(root)
        leaves = count_leaves(root)

        # 1. Traversal questions
        for ttype in traversal_types:
            if ttype == "Inorder":
                ans_list = in_res
                distractor_lists = [pre_res, post_res, lvl_res]
                explanation = (
                    f"Inorder traversal visits Left Subtree -> Root -> Right Subtree. "
                    f"For any valid BST, an Inorder traversal always yields the keys in ascending sorted order: {ans_list}."
                )
                diff = "Easy"
            elif ttype == "Preorder":
                ans_list = pre_res
                distractor_lists = [in_res, post_res, lvl_res]
                explanation = (
                    f"Preorder traversal visits Root -> Left Subtree -> Right Subtree. "
                    f"Root {seq[0]} is visited first, recursively followed by its left and right descendants: {ans_list}."
                )
                diff = "Medium"
            elif ttype == "Postorder":
                ans_list = post_res
                distractor_lists = [in_res, pre_res, lvl_res]
                explanation = (
                    f"Postorder traversal visits Left Subtree -> Right Subtree -> Root. "
                    f"Root {seq[0]} is processed last after all its children: {ans_list}."
                )
                diff = "Medium"
            else:  # Level-order
                ans_list = lvl_res
                distractor_lists = [in_res, pre_res, post_res]
                explanation = (
                    f"Level-order traversal (BFS) processes nodes level-by-level from top to bottom, left to right: {ans_list}."
                )
                diff = "Easy"

            ans_str = ", ".join(map(str, ans_list))
            distractors_str = [", ".join(map(str, d)) for d in distractor_lists]

            prompt = (
                f"A Binary Search Tree (BST) is constructed by sequentially inserting the following keys into an initially empty tree:\n"
                f"`{seq}`\n\n"
                f"What is the exact **{ttype}** traversal sequence of this tree?"
            )

            q = make_question(
                id_str=f"gen-tree-trav-{q_idx}",
                topic="trees",
                subtopic=f"{ttype.lower()}-traversal",
                difficulty=diff,
                prompt=prompt,
                correct_answer=ans_str,
                distractors=distractors_str,
                explanation=explanation,
                generator_key="tree_traversals.sequence",
                rng=rng,
            )
            questions.append(q)
            q_idx += 1

        # 2. Height and Leaf questions
        height_ans = str(height)
        cand_h = [height + 1, height + 2, height + 3]
        if height > 1:
            cand_h.append(height - 1)
        height_distractors = [str(d) for d in cand_h if d != height]

        prompt_h = (
            f"Keys `{seq}` are inserted into an initially empty Binary Search Tree. "
            f"What is the height (maximum number of levels / depth from root to deepest node) of this tree?"
        )
        q_h = make_question(
            id_str=f"gen-tree-height-{q_idx}",
            topic="trees",
            subtopic="tree-properties",
            difficulty="Hard",
            prompt=prompt_h,
            correct_answer=height_ans,
            distractors=height_distractors,
            explanation=f"By following BST insertion rules for `{seq}`, the deepest path spans {height} levels.",
            generator_key="tree_traversals.height",
            rng=rng,
        )
        questions.append(q_h)
        q_idx += 1

        leaves_ans = str(leaves)
        cand_l = [leaves + 1, leaves + 2, leaves + 3]
        if leaves > 1:
            cand_l.append(leaves - 1)
        leaves_distractors = [str(d) for d in cand_l if d != leaves]

        prompt_l = (
            f"Keys `{seq}` are inserted into an initially empty Binary Search Tree. "
            f"How many leaf nodes (nodes with no left or right children) exist in the resulting tree?"
        )
        q_l = make_question(
            id_str=f"gen-tree-leaf-{q_idx}",
            topic="trees",
            subtopic="tree-properties",
            difficulty="Easy",
            prompt=prompt_l,
            correct_answer=leaves_ans,
            distractors=leaves_distractors,
            explanation=f"A leaf node has both left and right pointers equal to null. In the resulting tree, exactly {leaves} such nodes are formed.",
            generator_key="tree_traversals.leaves",
            rng=rng,
        )
        questions.append(q_l)
        q_idx += 1

        internal = len(seq) - leaves
        internal_ans = str(internal)
        cand_in = [internal + 1, internal + 2, internal + 3]
        if internal > 1:
            cand_in.append(internal - 1)
        internal_distractors = [str(d) for d in cand_in if d != internal]

        prompt_in = (
            f"Keys `{seq}` are inserted into an initially empty Binary Search Tree. "
            f"How many internal nodes (non-leaf nodes with at least one child) exist in the resulting tree?"
        )
        q_in = make_question(
            id_str=f"gen-tree-internal-{q_idx}",
            topic="trees",
            subtopic="tree-properties",
            difficulty="Medium",
            prompt=prompt_in,
            correct_answer=internal_ans,
            distractors=internal_distractors,
            explanation=f"With {len(seq)} total nodes and {leaves} leaves, the number of internal nodes is {len(seq)} - {leaves} = {internal}.",
            generator_key="tree_traversals.internal_nodes",
            rng=rng,
        )
        questions.append(q_in)
        q_idx += 1

    return questions[:count]
