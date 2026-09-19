"""Authoring and verification script for Batch 2B: Tree problems (level-order arrays).

Trees use the bank-standard encoding (see validate-binary-search-tree):
level-order arrays with ``null`` holes, heap indexing (children of index ``i``
at ``2i+1``/``2i+2``), null entries skipped. PAF synthesizes complete-tree
cases from ``list[number]``; sparse shapes (null holes, skews, empties) are
appended per problem with judge-computed expected values. Problems whose
inputs PAF cannot synthesize validly (LCA-BST needs present p/q in a real
BST; buildTree needs consistent preorder/inorder pairs) use bespoke
judge-derived custom cases only.
"""

from __future__ import annotations

import asyncio
import json
import random
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
api_path = str(REPO_ROOT / "apps" / "api")
if api_path not in sys.path:
    sys.path.insert(0, api_path)

from content.generators.paf import (  # noqa: E402
    Algorithm,
    ProblemSpec,
    build_verified_problem,
)

BST_LINK = "https://en.wikipedia.org/wiki/Binary_search_tree"
BFS_LINK = "https://en.wikipedia.org/wiki/Breadth-first_search"
BT_LINK = "https://en.wikipedia.org/wiki/Binary_tree"
DFS_LINK = "https://en.wikipedia.org/wiki/Depth-first_search"
TRAV_LINK = "https://en.wikipedia.org/wiki/Tree_traversal"

ENCODING = (
    "The tree is given as a level-order array `root`: the children of the entry "
    "at index `i` live at indices `2i+1` (left) and `2i+2` (right). An entry "
    "holding `null` means that child is absent and is skipped while traversing."
)


async def _execute(lang: str, code: str, fn: str, cases: list[dict]) -> Any:
    from app.services.judge import execute_code

    return await execute_code(
        language=lang, code=code, function_name=fn,
        test_cases=cases, time_limit_ms=2000,
    )


async def _probe_expected(
    fn: str, code: str, lang: str, inputs: list[list[Any]], prefix: str,
) -> list[dict]:
    """Run inputs through the optimal implementation to derive expected outputs."""
    pending = [
        {"label": f"{prefix}-{i + 1:02d}", "input": values, "expected": None, "isSample": False}
        for i, values in enumerate(inputs)
    ]
    probe = await _execute(
        lang, code, fn,
        [{**c, "expected": 0} for c in pending],
    )
    if probe.compile_output or len(probe.test_results) != len(pending):
        raise ValueError(f"Optimal probe failed for {fn}: {probe.compile_output}")
    for case, result in zip(pending, probe.test_results, strict=True):
        if result.get("error") is not None or "actual" not in result:
            raise ValueError(f"Optimal probe error for {fn}: {result.get('error')}")
        case["expected"] = result["actual"]
    return pending


async def _require_ac(
    lang: str, code: str, fn: str, cases: list[dict], role: str, slug: str,
) -> float:
    check = [
        {"label": c["label"], "input": list(c["input"]),
         "expected": c["expected"], "isSample": c.get("isSample", False)}
        for c in cases
    ]
    result = await _execute(lang, code, fn, check)
    if result.verdict != "AC":
        bad = [
            f"{r.get('label')}: exp={r.get('expected')} got={r.get('actual')} err={r.get('error')}"
            for r in result.test_results if not r.get("passed")
        ]
        raise ValueError(
            f"{slug} {role} ({lang}) verdict {result.verdict}: "
            f"{result.compile_output} :: {'; '.join(bad[:6])}"
        )
    return result.runtime_ms


def _starter_js(spec: ProblemSpec) -> str:
    names = ", ".join(p.name for p in spec.parsed_signature.parameters)
    return (
        f"function {spec.function_name}({names}) {{\n"
        "  // Write your solution here\n"
        "  throw new Error('Not implemented');\n"
        "}\n"
    )


def _starter_py(spec: ProblemSpec) -> str:
    names = ", ".join(p.name for p in spec.parsed_signature.parameters)
    return (
        f"def {spec.function_name}({names}):\n"
        "    # Write your solution here\n"
        "    raise NotImplementedError\n"
    )


def _constraints(spec: ProblemSpec) -> list[str]:
    signature = spec.signature.strip().rstrip(":{").strip()
    return [
        f"Function signature: `{signature}`.",
        "Inputs are JSON-serializable values satisfying the bounds stated above.",
    ]


def _merge_cases(*groups: list[dict]) -> list[dict]:
    merged: list[dict] = []
    seen: set[str] = set()
    for group in groups:
        for case in group:
            fingerprint = json.dumps(case["input"], sort_keys=True, separators=(",", ":"))
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            merged.append(case)
    return merged


def bst_level_order(rng: random.Random, n: int, lo: int = -100, hi: int = 100) -> tuple[list, list[int]]:
    """Balanced BST serialized to a heap-indexed level-order array (may hold null holes)."""
    vals = sorted(rng.sample(range(lo, hi + 1), n))

    def build(lo_i: int, hi_i: int) -> Any:
        if lo_i > hi_i:
            return None
        mid = (lo_i + hi_i) // 2
        return (vals[mid], build(lo_i, mid - 1), build(mid + 1, hi_i))

    placed: dict[int, Any] = {}

    def serialize(node: Any, i: int) -> None:
        if node is None:
            return
        placed[i] = node[0]
        serialize(node[1], 2 * i + 1)
        serialize(node[2], 2 * i + 2)

    serialize(build(0, n - 1), 0)
    size = max(placed) + 1
    return [placed.get(i) for i in range(size)], vals


def rand_bst_pre_in(rng: random.Random) -> tuple[list[int], list[int]]:
    """Random-shape BST with unique values; returns (preorder, inorder)."""
    n = rng.randint(3, 10)
    vals = rng.sample(range(-50, 51), n)

    def insert(node: Any, v: int) -> Any:
        if node is None:
            return [v, None, None]
        if v < node[0]:
            node[1] = insert(node[1], v)
        else:
            node[2] = insert(node[2], v)
        return node

    root = None
    for v in vals:
        root = insert(root, v)
    pre: list[int] = []
    ino: list[int] = []

    def pre_walk(node: Any) -> None:
        if node is None:
            return
        pre.append(node[0])
        pre_walk(node[1])
        pre_walk(node[2])

    def in_walk(node: Any) -> None:
        if node is None:
            return
        in_walk(node[1])
        ino.append(node[0])
        in_walk(node[2])

    pre_walk(root)
    in_walk(root)
    return pre, ino


# ----------------------------------------------------------------------------
# Problem 1: lowest-common-ancestor-bst (custom cases only: needs a real BST
# with present, distinct p and q, which stock PAF synthesis cannot guarantee)
# ----------------------------------------------------------------------------

spec_lca = ProblemSpec(
    signature="function lowestCommonAncestor(root: number[], p: number, q: number)",
    statement=f"""# Ancestor Query in a Search Tree

A binary search tree is handed to you as a level-order array `root`. {ENCODING} Every present value obeys the search-tree order: all values in a left subtree are smaller than their parent, and all values in a right subtree are larger.

Given two distinct values `p` and `q` that both occur somewhere in the tree, return the value of their lowest common ancestor: the deepest node whose subtree contains both values. Either target may itself be the ancestor of the other, and the root may be the answer.

Constraints: `0 <= root.length <= 30`, `-100 <= root[i] <= 100`, `-100 <= p <= 100`, `-100 <= q <= 100`, `p != q`, and both `p` and `q` are present in a valid search tree.
""",
    brute_force=Algorithm(
        """function lowestCommonAncestor(root, p, q) {
  function findPath(i, target, path) {
    if (i >= root.length || root[i] === null) return false;
    path.push(root[i]);
    if (root[i] === target) return true;
    if (findPath(2 * i + 1, target, path) || findPath(2 * i + 2, target, path)) return true;
    path.pop();
    return false;
  }
  const pathP = [];
  const pathQ = [];
  findPath(0, p, pathP);
  findPath(0, q, pathQ);
  let lca = pathP[0];
  const shared = Math.min(pathP.length, pathQ.length);
  for (let k = 0; k < shared; k++) {
    if (pathP[k] === pathQ[k]) {
      lca = pathP[k];
    } else {
      break;
    }
  }
  return lca;
}""",
        complexity="Time: O(n) | Space: O(h)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function lowestCommonAncestor(root, p, q) {
  let i = 0;
  while (i < root.length && root[i] !== null) {
    if (p < root[i] && q < root[i]) {
      i = 2 * i + 1;
    } else if (p > root[i] && q > root[i]) {
      i = 2 * i + 2;
    } else {
      return root[i];
    }
  }
  return null;
}""",
        complexity="Time: O(h) | Space: O(1)",
        language="javascript",
    ),
    topic="trees",
    difficulty="Medium",
    pattern="trees / BST descend",
    time_limit_ms=2000,
    seed=42,
    title="Ancestor Query in a Search Tree",
    slug="lowest-common-ancestor-bst",
    editorial={
        "approach": "Walk down from the root, steering left when both targets are smaller and right when both are larger; the first node that splits them (or equals one of them) is the answer.",
        "why_optimal": "Each step discards a whole subtree, so the walk costs time proportional to the height with constant extra space.",
        "pitfalls": "When one target is an ancestor of the other, that ancestor itself is the answer — do not descend past it.",
    },
    reading_links=[BST_LINK],
    hints=[
        "At each node, compare both targets against the node value.",
        "Both smaller means the answer hides in the left subtree; both larger means the right.",
        "A split — or a direct hit on p or q — stops the descent.",
    ],
)

PY_LCA_BRUTE = """def lowestCommonAncestor(root: list, p: int, q: int):
    def find_path(i, target, path):
        if i >= len(root) or root[i] is None:
            return False
        path.append(root[i])
        if root[i] == target:
            return True
        if find_path(2 * i + 1, target, path) or find_path(2 * i + 2, target, path):
            return True
        path.pop()
        return False
    path_p, path_q = [], []
    find_path(0, p, path_p)
    find_path(0, q, path_q)
    lca = path_p[0] if path_p else None
    for a, b in zip(path_p, path_q):
        if a == b:
            lca = a
        else:
            break
    return lca
"""

PY_LCA_OPTIMAL = """def lowestCommonAncestor(root: list, p: int, q: int):
    i = 0
    while i < len(root) and root[i] is not None:
        if p < root[i] and q < root[i]:
            i = 2 * i + 1
        elif p > root[i] and q > root[i]:
            i = 2 * i + 2
        else:
            return root[i]
    return None
"""

LCA_MAIN_TREE = [6, 2, 8, 0, 4, 7, 9, None, None, 3, 5]
LCA_LEFT_CHAIN = [5, 4, None, 3, None, None, None, 2, None, None, None, None, None, None, None, 1]
LCA_RIGHT_CHAIN = [1, None, 2, None, None, None, 3, None, None, None, None, None, None, None, 4]
LCA_EXAMPLES = [
    {
        "input": f"root = {json.dumps(LCA_MAIN_TREE)}, p = 2, q = 8",
        "output": "6",
        "explanation": "2 lives in the left subtree of 6 and 8 lives in the right subtree, so the paths split at the root itself.",
    },
    {
        "input": f"root = {json.dumps(LCA_MAIN_TREE)}, p = 2, q = 4",
        "output": "2",
        "explanation": "4 sits inside the subtree rooted at 2, so 2 is an ancestor of the other target and is the answer.",
    },
    {
        "input": f"root = {json.dumps(LCA_MAIN_TREE)}, p = 3, q = 5",
        "output": "4",
        "explanation": "3 is the left child of 4 and 5 is the right child of 4, making 4 the deepest node covering both.",
    },
]
LCA_EXAMPLE_IO = [
    ([LCA_MAIN_TREE, 2, 8], 6),
    ([LCA_MAIN_TREE, 2, 4], 2),
    ([LCA_MAIN_TREE, 3, 5], 4),
]
LCA_SPARSE_IO = [
    ([LCA_LEFT_CHAIN, 1, 3], 3),
    ([LCA_RIGHT_CHAIN, 2, 4], 2),
    ([LCA_MAIN_TREE, 0, 9], 6),
    ([LCA_MAIN_TREE, 3, 4], 4),
]

# ----------------------------------------------------------------------------
# Problem 2: binary-tree-level-order-traversal
# ----------------------------------------------------------------------------

spec_level = ProblemSpec(
    signature="function levelOrder(root: number[])",
    statement=f"""# Level Order Listing

{ENCODING}

Return an array with one entry per depth level, where each entry lists that level's values from left to right. `null` holes are skipped and never appear in the output. An empty tree yields `[]`.

Constraints: `0 <= root.length <= 30` and `-100 <= root[i] <= 100`.
""",
    brute_force=Algorithm(
        """function levelOrder(root) {
  const pairs = [];
  (function dfs(i, d) {
    if (i >= root.length || root[i] === null) return;
    pairs.push([d, root[i]]);
    dfs(2 * i + 1, d + 1);
    dfs(2 * i + 2, d + 1);
  })(0, 0);
  pairs.sort((a, b) => a[0] - b[0]);
  const levels = [];
  for (const [d, v] of pairs) {
    if (!levels[d]) levels[d] = [];
    levels[d].push(v);
  }
  return levels.filter((lv) => lv !== undefined);
}""",
        complexity="Time: O(n log n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function levelOrder(root) {
  const levels = [];
  if (root.length === 0 || root[0] === null) return levels;
  let current = [0];
  while (current.length > 0) {
    const next = [];
    const vals = [];
    for (const i of current) {
      vals.push(root[i]);
      const l = 2 * i + 1;
      const r = 2 * i + 2;
      if (l < root.length && root[l] !== null) next.push(l);
      if (r < root.length && root[r] !== null) next.push(r);
    }
    levels.push(vals);
    current = next;
  }
  return levels;
}""",
        complexity="Time: O(n) | Space: O(w)",
        language="javascript",
    ),
    topic="trees",
    difficulty="Medium",
    pattern="trees / BFS levels",
    time_limit_ms=2000,
    seed=42,
    title="Level Order Listing",
    slug="binary-tree-level-order-traversal",
    editorial={
        "approach": "Breadth-first sweep: process one depth level at a time, queuing each node's present children for the next round.",
        "why_optimal": "Every present node is enqueued and dequeued once, giving linear time with a queue bounded by the widest level.",
        "pitfalls": "Skip null holes without emitting placeholders, and return an empty array for an empty tree.",
    },
    reading_links=[BFS_LINK],
    hints=[
        "Handle levels one at a time, not nodes one at a time.",
        "Only enqueue children that are actually present.",
        "Collect each level's values before moving deeper.",
    ],
)

PY_LEVEL_BRUTE = """def levelOrder(root: list) -> list:
    pairs = []
    def dfs(i, d):
        if i >= len(root) or root[i] is None:
            return
        pairs.append((d, root[i]))
        dfs(2 * i + 1, d + 1)
        dfs(2 * i + 2, d + 1)
    dfs(0, 0)
    pairs.sort(key=lambda item: item[0])
    levels = []
    for d, v in pairs:
        while len(levels) <= d:
            levels.append([])
        levels[d].append(v)
    return [lv for lv in levels if lv]
"""

PY_LEVEL_OPTIMAL = """def levelOrder(root: list) -> list:
    levels = []
    if len(root) == 0 or root[0] is None:
        return levels
    current = [0]
    while current:
        nxt, vals = [], []
        for i in current:
            vals.append(root[i])
            l, r = 2 * i + 1, 2 * i + 2
            if l < len(root) and root[l] is not None:
                nxt.append(l)
            if r < len(root) and root[r] is not None:
                nxt.append(r)
        levels.append(vals)
        current = nxt
    return levels
"""

LEVEL_EXAMPLES = [
    {
        "input": "root = [3,9,20,null,null,15,7]",
        "output": "[[3],[9,20],[15,7]]",
        "explanation": "Depth 0 holds 3; depth 1 holds 9 and 20 left to right; depth 2 holds 15 and 7 under node 20.",
    },
    {
        "input": "root = [1]",
        "output": "[[1]]",
        "explanation": "A single node forms one level containing just itself.",
    },
    {
        "input": "root = [1,null,2]",
        "output": "[[1],[2]]",
        "explanation": "The null left hole is skipped, so 2 (the right child) stands alone on depth 1.",
    },
]
LEVEL_EXAMPLE_IO = [
    ([[3, 9, 20, None, None, 15, 7]], [[3], [9, 20], [15, 7]]),
    ([[1]], [[1]]),
    ([[1, None, 2]], [[1], [2]]),
]
LEVEL_SPARSE_IO = [
    ([[]], []),
    ([[None]], []),
    ([[7]], [[7]]),
    ([[1, 2, None, 3, None, None, None, 4]], [[1], [2], [3], [4]]),
    ([[1, None, 2, None, None, None, 3]], [[1], [2], [3]]),
]

# ----------------------------------------------------------------------------
# Problem 3: binary-tree-right-side-view
# ----------------------------------------------------------------------------

spec_right = ProblemSpec(
    signature="function rightSideView(root: number[])",
    statement=f"""# Right Side View

{ENCODING}

Imagine standing to the right of the tree and looking left: at each depth only the rightmost present node stays visible. Return those visible values from top to bottom. An empty tree shows nothing, so return `[]`.

Constraints: `0 <= root.length <= 30` and `-100 <= root[i] <= 100`.
""",
    brute_force=Algorithm(
        """function rightSideView(root) {
  const levels = [];
  (function dfs(i, d) {
    if (i >= root.length || root[i] === null) return;
    if (!levels[d]) levels[d] = [];
    levels[d].push(root[i]);
    dfs(2 * i + 1, d + 1);
    dfs(2 * i + 2, d + 1);
  })(0, 0);
  return levels.map((lv) => lv[lv.length - 1]);
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function rightSideView(root) {
  const view = [];
  (function dfs(i, d) {
    if (i >= root.length || root[i] === null) return;
    if (d === view.length) view.push(root[i]);
    dfs(2 * i + 2, d + 1);
    dfs(2 * i + 1, d + 1);
  })(0, 0);
  return view;
}""",
        complexity="Time: O(n) | Space: O(h)",
        language="javascript",
    ),
    topic="trees",
    difficulty="Medium",
    pattern="trees / Level last",
    time_limit_ms=2000,
    seed=42,
    title="Right Side View",
    slug="binary-tree-right-side-view",
    editorial={
        "approach": "Depth-first walk that always visits the right child before the left, recording the first node seen at each depth.",
        "why_optimal": "Each node is visited once and only one value per depth is stored, so time is linear and extra space follows the height.",
        "pitfalls": "Record a depth only the first time you reach it; later left-side arrivals at the same depth stay hidden.",
    },
    reading_links=[BFS_LINK],
    hints=[
        "The visible node at each depth is the rightmost one.",
        "Visit right children before left children.",
        "Keep the first value you meet at every new depth.",
    ],
)

PY_RIGHT_BRUTE = """def rightSideView(root: list) -> list:
    levels = []
    def dfs(i, d):
        if i >= len(root) or root[i] is None:
            return
        while len(levels) <= d:
            levels.append([])
        levels[d].append(root[i])
        dfs(2 * i + 1, d + 1)
        dfs(2 * i + 2, d + 1)
    dfs(0, 0)
    return [lv[-1] for lv in levels]
"""

PY_RIGHT_OPTIMAL = """def rightSideView(root: list) -> list:
    view = []
    def dfs(i, d):
        if i >= len(root) or root[i] is None:
            return
        if d == len(view):
            view.append(root[i])
        dfs(2 * i + 2, d + 1)
        dfs(2 * i + 1, d + 1)
    dfs(0, 0)
    return view
"""

RIGHT_EXAMPLES = [
    {
        "input": "root = [1,2,3,null,5,null,4]",
        "output": "[1,3,4]",
        "explanation": "Depth 0 shows 1; at depth 1 the rightmost node is 3; at depth 2 the candidates are 5 and 4, so 4 wins.",
    },
    {
        "input": "root = [1,null,3]",
        "output": "[1,3]",
        "explanation": "The missing left child changes nothing on the right: 1 then 3 are visible.",
    },
    {
        "input": "root = [1,2,null,3]",
        "output": "[1,2,3]",
        "explanation": "A left-leaning chain hides nothing from the right, so every level's single node is visible.",
    },
]
RIGHT_EXAMPLE_IO = [
    ([[1, 2, 3, None, 5, None, 4]], [1, 3, 4]),
    ([[1, None, 3]], [1, 3]),
    ([[1, 2, None, 3]], [1, 2, 3]),
]
RIGHT_SPARSE_IO = [
    ([[]], []),
    ([[None]], []),
    ([[5]], [5]),
    ([[3, 2, None, 1]], [3, 2, 1]),
    ([[1, None, 2, None, None, None, 3]], [1, 2, 3]),
]

# ----------------------------------------------------------------------------
# Problem 4: count-good-nodes
# ----------------------------------------------------------------------------

spec_good = ProblemSpec(
    signature="function goodNodes(root: number[])",
    statement=f"""# Record Nodes on Root Paths

{ENCODING}

A node earns the title of record node when its value is greater than or equal to every value on the path from the root down to (but excluding) itself. The root has no ancestors above it, so it always qualifies.

Return how many present nodes are record nodes.

Constraints: `0 <= root.length <= 30` and `-100 <= root[i] <= 100`.
""",
    brute_force=Algorithm(
        """function goodNodes(root) {
  const present = [];
  (function collect(i) {
    if (i >= root.length || root[i] === null) return;
    present.push(i);
    collect(2 * i + 1);
    collect(2 * i + 2);
  })(0);
  function pathTo(target) {
    const path = [];
    function dfs(i) {
      if (i >= root.length || root[i] === null) return false;
      path.push(root[i]);
      if (i === target) return true;
      if (dfs(2 * i + 1) || dfs(2 * i + 2)) return true;
      path.pop();
      return false;
    }
    dfs(0);
    return path;
  }
  let count = 0;
  for (const t of present) {
    const path = pathTo(t);
    const val = path[path.length - 1];
    let ok = true;
    for (let k = 0; k < path.length - 1; k++) {
      if (path[k] > val) {
        ok = false;
        break;
      }
    }
    if (ok) count++;
  }
  return count;
}""",
        complexity="Time: O(n²) | Space: O(h)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function goodNodes(root) {
  let count = 0;
  (function dfs(i, best) {
    if (i >= root.length || root[i] === null) return;
    if (root[i] >= best) count++;
    const next = Math.max(best, root[i]);
    dfs(2 * i + 1, next);
    dfs(2 * i + 2, next);
  })(0, -Infinity);
  return count;
}""",
        complexity="Time: O(n) | Space: O(h)",
        language="javascript",
    ),
    topic="trees",
    difficulty="Medium",
    pattern="trees / Max-path",
    time_limit_ms=2000,
    seed=42,
    title="Record Nodes on Root Paths",
    slug="count-good-nodes",
    editorial={
        "approach": "Walk down from the root carrying the largest value met so far; count a node when it matches or beats that record, then extend the record into its children.",
        "why_optimal": "Each node is visited once with constant extra work, so the walk is linear in time with stack space bounded by the height.",
        "pitfalls": "Ties still count — only strictly smaller values fail. Skip null holes without counting them, and remember the root always qualifies.",
    },
    reading_links=[BT_LINK],
    hints=[
        "Compare each node against the best value seen above it.",
        "The root has no ancestors, so it always qualifies.",
        "Carry the running maximum downward instead of recomputing each path.",
    ],
)

PY_GOOD_BRUTE = """def goodNodes(root: list) -> int:
    present = []
    def collect(i):
        if i >= len(root) or root[i] is None:
            return
        present.append(i)
        collect(2 * i + 1)
        collect(2 * i + 2)
    collect(0)
    def path_to(target):
        path = []
        def dfs(i):
            if i >= len(root) or root[i] is None:
                return False
            path.append(root[i])
            if i == target:
                return True
            if dfs(2 * i + 1) or dfs(2 * i + 2):
                return True
            path.pop()
            return False
        dfs(0)
        return path
    count = 0
    for t in present:
        path = path_to(t)
        if all(a <= path[-1] for a in path[:-1]):
            count += 1
    return count
"""

PY_GOOD_OPTIMAL = """def goodNodes(root: list) -> int:
    count = 0
    def dfs(i, best):
        nonlocal count
        if i >= len(root) or root[i] is None:
            return
        if root[i] >= best:
            count += 1
        nxt = max(best, root[i])
        dfs(2 * i + 1, nxt)
        dfs(2 * i + 2, nxt)
    dfs(0, float('-inf'))
    return count
"""

GOOD_EXAMPLES = [
    {
        "input": "root = [3,1,4,3,null,1,5]",
        "output": "4",
        "explanation": "3 starts the record; 1 falls short of it; 4 sets a new record; the lower 3 ties the root's record and counts; 1 stays below 4; 5 tops everything.",
    },
    {
        "input": "root = [3,3,null,3]",
        "output": "3",
        "explanation": "Every node ties the ancestral best of 3, and ties qualify, so all three present nodes count.",
    },
    {
        "input": "root = [5,4,3]",
        "output": "1",
        "explanation": "Values shrink along every root path, so only the root itself ever leads.",
    },
]
GOOD_EXAMPLE_IO = [
    ([[3, 1, 4, 3, None, 1, 5]], 4),
    ([[3, 3, None, 3]], 3),
    ([[5, 4, 3]], 1),
]
GOOD_SPARSE_IO = [
    ([[]], 0),
    ([[None]], 0),
    ([[7]], 1),
    ([[5, 4, None, 3]], 1),
    ([[2, 2, 2, 2]], 4),
]

# ----------------------------------------------------------------------------
# Problem 5: symmetric-tree
# ----------------------------------------------------------------------------

spec_sym = ProblemSpec(
    signature="function isSymmetric(root: number[])",
    statement=f"""# Mirror Check

{ENCODING}

A tree mirrors itself when its left and right subtrees are reflections of each other: the two child values must match, the outer grandchildren must mirror each other, and so must the inner grandchildren, all the way down. A `null` hole only mirrors another `null` hole in the facing position. An empty tree (or a `null` root) mirrors itself, so answer `true`.

Return `true` when the tree is a mirror image of itself, otherwise `false`.

Constraints: `0 <= root.length <= 30` and `-100 <= root[i] <= 100`.
""",
    brute_force=Algorithm(
        """function isSymmetric(root) {
  function build(i) {
    if (i >= root.length || root[i] === null) return null;
    return { v: root[i], l: build(2 * i + 1), r: build(2 * i + 2) };
  }
  const tree = build(0);
  if (tree === null) return true;
  const stack = [[tree.l, tree.r]];
  while (stack.length > 0) {
    const pair = stack.pop();
    const a = pair[0];
    const b = pair[1];
    if (a === null && b === null) continue;
    if (a === null || b === null || a.v !== b.v) return false;
    stack.push([a.l, b.r]);
    stack.push([a.r, b.l]);
  }
  return true;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function isSymmetric(root) {
  function mirror(l, r) {
    const lv = l < root.length ? root[l] : null;
    const rv = r < root.length ? root[r] : null;
    if (lv === null && rv === null) return true;
    if (lv === null || rv === null || lv !== rv) return false;
    return mirror(2 * l + 1, 2 * r + 2) && mirror(2 * l + 2, 2 * r + 1);
  }
  if (root.length === 0 || root[0] === null) return true;
  return mirror(1, 2);
}""",
        complexity="Time: O(n) | Space: O(h)",
        language="javascript",
    ),
    topic="trees",
    difficulty="Easy",
    pattern="trees / Mirror compare",
    time_limit_ms=2000,
    seed=42,
    title="Mirror Check",
    slug="symmetric-tree",
    editorial={
        "approach": "Check the two subtrees as mirror images: values must match, outer index pairs recurse together and inner index pairs recurse together.",
        "why_optimal": "Each index pair is visited once, so the check is linear in the array size with recursion depth bounded by the height.",
        "pitfalls": "Missing children are significant — a value facing a hole breaks symmetry just as surely as two different values.",
    },
    reading_links=[BT_LINK],
    hints=[
        "Compare the left and right subtrees as mirror images.",
        "Pair the outer children together and the inner children together.",
        "A hole must face a hole; a value facing a hole breaks symmetry.",
    ],
)

PY_SYM_BRUTE = """def isSymmetric(root: list) -> bool:
    def build(i):
        if i >= len(root) or root[i] is None:
            return None
        return (root[i], build(2 * i + 1), build(2 * i + 2))
    tree = build(0)
    if tree is None:
        return True
    stack = [(tree[1], tree[2])]
    while stack:
        a, b = stack.pop()
        if a is None and b is None:
            continue
        if a is None or b is None or a[0] != b[0]:
            return False
        stack.append((a[1], b[2]))
        stack.append((a[2], b[1]))
    return True
"""

PY_SYM_OPTIMAL = """def isSymmetric(root: list) -> bool:
    def mirror(l, r):
        lv = root[l] if l < len(root) else None
        rv = root[r] if r < len(root) else None
        if lv is None and rv is None:
            return True
        if lv is None or rv is None or lv != rv:
            return False
        return mirror(2 * l + 1, 2 * r + 2) and mirror(2 * l + 2, 2 * r + 1)
    if len(root) == 0 or root[0] is None:
        return True
    return mirror(1, 2)
"""

SYM_EXAMPLES = [
    {
        "input": "root = [1,2,2,3,4,4,3]",
        "output": "true",
        "explanation": "The two 2s match, the outer 3s match each other, and the inner 4s match each other.",
    },
    {
        "input": "root = [1,2,2,null,3,null,3]",
        "output": "false",
        "explanation": "The inner pair pits 3 against a hole: the left 2 has a right child while the right 2 has no left child.",
    },
    {
        "input": "root = [1,2,2,3,null,null,3]",
        "output": "true",
        "explanation": "The holes face each other on the inside while the two 3s face each other on the outside.",
    },
]
SYM_EXAMPLE_IO = [
    ([[1, 2, 2, 3, 4, 4, 3]], True),
    ([[1, 2, 2, None, 3, None, 3]], False),
    ([[1, 2, 2, 3, None, None, 3]], True),
]
SYM_SPARSE_IO = [
    ([[]], True),
    ([[None]], True),
    ([[1]], True),
    ([[1, 2, None, 3]], False),
    ([[1, None, 2, None, None, None, 3]], False),
]

# ----------------------------------------------------------------------------
# Problem 6: balanced-binary-tree
# ----------------------------------------------------------------------------

spec_bal = ProblemSpec(
    signature="function isBalanced(root: number[])",
    statement=f"""# Height-Balanced Check

{ENCODING}

A tree is height-balanced when, at every present node, the heights of its left and right subtrees differ by at most one. Height counts nodes along the longest downward path: a leaf has height 1 and an absent child has height 0. An empty tree counts as balanced.

Return `true` when every node passes this test, otherwise `false`.

Constraints: `0 <= root.length <= 30` and `-100 <= root[i] <= 100`.
""",
    brute_force=Algorithm(
        """function isBalanced(root) {
  function height(i) {
    if (i >= root.length || root[i] === null) return 0;
    return 1 + Math.max(height(2 * i + 1), height(2 * i + 2));
  }
  function check(i) {
    if (i >= root.length || root[i] === null) return true;
    const l = height(2 * i + 1);
    const r = height(2 * i + 2);
    if (Math.abs(l - r) > 1) return false;
    return check(2 * i + 1) && check(2 * i + 2);
  }
  return check(0);
}""",
        complexity="Time: O(n·h) | Space: O(h)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function isBalanced(root) {
  function probe(i) {
    if (i >= root.length || root[i] === null) return 0;
    const l = probe(2 * i + 1);
    if (l === -1) return -1;
    const r = probe(2 * i + 2);
    if (r === -1) return -1;
    if (Math.abs(l - r) > 1) return -1;
    return 1 + Math.max(l, r);
  }
  return probe(0) !== -1;
}""",
        complexity="Time: O(n) | Space: O(h)",
        language="javascript",
    ),
    topic="trees",
    difficulty="Medium",
    pattern="trees / Height diff",
    time_limit_ms=2000,
    seed=42,
    title="Height-Balanced Check",
    slug="balanced-binary-tree",
    editorial={
        "approach": "One post-order pass returns each subtree's height, carrying a failure flag upward the moment two sibling heights differ by more than one.",
        "why_optimal": "Each node is measured once, so the pass is linear in time with recursion depth bounded by the height.",
        "pitfalls": "A tall chain hidden deep inside still unbalances the tree — test every node, not just the root, and treat absent children as height zero.",
    },
    reading_links=[BT_LINK],
    hints=[
        "The height of an absent child is zero.",
        "Every node must pass the at-most-one test, not just the root.",
        "Bubble a failure upward immediately instead of measuring the rest.",
    ],
)

PY_BAL_BRUTE = """def isBalanced(root: list) -> bool:
    def height(i):
        if i >= len(root) or root[i] is None:
            return 0
        return 1 + max(height(2 * i + 1), height(2 * i + 2))
    def check(i):
        if i >= len(root) or root[i] is None:
            return True
        if abs(height(2 * i + 1) - height(2 * i + 2)) > 1:
            return False
        return check(2 * i + 1) and check(2 * i + 2)
    return check(0)
"""

PY_BAL_OPTIMAL = """def isBalanced(root: list) -> bool:
    def probe(i):
        if i >= len(root) or root[i] is None:
            return 0
        l = probe(2 * i + 1)
        if l == -1:
            return -1
        r = probe(2 * i + 2)
        if r == -1:
            return -1
        if abs(l - r) > 1:
            return -1
        return 1 + max(l, r)
    return probe(0) != -1
"""

BAL_EXAMPLES = [
    {
        "input": "root = [3,9,20,null,null,15,7]",
        "output": "true",
        "explanation": "The left subtree has height 1 and the right has height 2, and every smaller subtree is even tighter.",
    },
    {
        "input": "root = [1,2,2,3,3,null,null,4,4]",
        "output": "false",
        "explanation": "The left subtree reaches height 3 through its double chain while the right subtree has height 1.",
    },
    {
        "input": "root = [2,1,3]",
        "output": "true",
        "explanation": "Both children are leaves, so every balance check passes with a difference of zero.",
    },
]
BAL_EXAMPLE_IO = [
    ([[3, 9, 20, None, None, 15, 7]], True),
    ([[1, 2, 2, 3, 3, None, None, 4, 4]], False),
    ([[2, 1, 3]], True),
]
BAL_SPARSE_IO = [
    ([[]], True),
    ([[None]], True),
    ([[1]], True),
    ([[3, 2, None, 1]], False),
    ([[1, None, 2, None, None, None, 3]], False),
]

# ----------------------------------------------------------------------------
# Problem 7: binary-tree-maximum-path-sum
# ----------------------------------------------------------------------------

spec_maxpath = ProblemSpec(
    signature="function maxPathSum(root: number[])",
    statement=f"""# Best Downward Chain

{ENCODING}

A path is any non-empty sequence of present nodes linked parent-to-child, travelled in either direction; it may bend once at its highest node but never branches. Negative values are allowed, and a single node alone qualifies as a path.

Return the largest achievable sum of values along any such path. Because paths must be non-empty, an all-negative tree answers with its least-negative value.

Constraints: `1 <= root.length <= 30` and `-100 <= root[i] <= 100`, with `root[0]` present.
""",
    brute_force=Algorithm(
        """function maxPathSum(root) {
  const present = [];
  (function collect(i) {
    if (i >= root.length || root[i] === null) return;
    present.push(i);
    collect(2 * i + 1);
    collect(2 * i + 2);
  })(0);
  function bestDown(i) {
    if (i >= root.length || root[i] === null) return -Infinity;
    return root[i] + Math.max(0, bestDown(2 * i + 1), bestDown(2 * i + 2));
  }
  let best = -Infinity;
  for (const t of present) {
    const l = bestDown(2 * t + 1);
    const r = bestDown(2 * t + 2);
    const through = root[t] + Math.max(0, l) + Math.max(0, r);
    if (through > best) best = through;
  }
  return best;
}""",
        complexity="Time: O(n·h) | Space: O(h)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function maxPathSum(root) {
  let best = -Infinity;
  function gain(i) {
    if (i >= root.length || root[i] === null) return 0;
    const l = Math.max(0, gain(2 * i + 1));
    const r = Math.max(0, gain(2 * i + 2));
    const through = root[i] + l + r;
    if (through > best) best = through;
    return root[i] + Math.max(l, r);
  }
  gain(0);
  return best;
}""",
        complexity="Time: O(n) | Space: O(h)",
        language="javascript",
    ),
    topic="trees",
    difficulty="Hard",
    pattern="trees / Gain clamp",
    time_limit_ms=2000,
    seed=42,
    title="Best Downward Chain",
    slug="binary-tree-maximum-path-sum",
    editorial={
        "approach": "Post-order pass: each subtree reports the best downward gain it can offer its parent (negative gains clamped to zero), while a global best tracks the top bent path seen anywhere.",
        "why_optimal": "Each node is processed once with constant work, giving linear time and recursion depth bounded by the height.",
        "pitfalls": "Clamp negative child gains to zero when extending, but never force the global answer down to zero — an all-negative tree still returns its least-negative node.",
    },
    reading_links=[DFS_LINK],
    hints=[
        "Let every subtree report the best downward sum it can hand upward.",
        "Drop negative child gains; a bent path never benefits from a losing branch.",
        "Track the best path seen anywhere, not just paths through the root.",
    ],
)

PY_MAXPATH_BRUTE = """def maxPathSum(root: list) -> int:
    present = []
    def collect(i):
        if i >= len(root) or root[i] is None:
            return
        present.append(i)
        collect(2 * i + 1)
        collect(2 * i + 2)
    collect(0)
    def best_down(i):
        if i >= len(root) or root[i] is None:
            return float('-inf')
        return root[i] + max(0, best_down(2 * i + 1), best_down(2 * i + 2))
    best = float('-inf')
    for t in present:
        l, r = best_down(2 * t + 1), best_down(2 * t + 2)
        through = root[t] + max(0, l) + max(0, r)
        best = max(best, through)
    return best
"""

PY_MAXPATH_OPTIMAL = """def maxPathSum(root: list) -> int:
    best = float('-inf')
    def gain(i):
        nonlocal best
        if i >= len(root) or root[i] is None:
            return 0
        l = max(0, gain(2 * i + 1))
        r = max(0, gain(2 * i + 2))
        best = max(best, root[i] + l + r)
        return root[i] + max(l, r)
    gain(0)
    return best
"""

MAXPATH_EXAMPLES = [
    {
        "input": "root = [1,2,3]",
        "output": "6",
        "explanation": "The bent path 2 -> 1 -> 3 collects all three values, beating any single-side chain.",
    },
    {
        "input": "root = [-10,9,20,null,null,15,7]",
        "output": "42",
        "explanation": "The clamped gains from 15 and 7 lift 20 to 42; routing through the -10 root would only lose value.",
    },
    {
        "input": "root = [-3,-2,-5]",
        "output": "-2",
        "explanation": "Every multi-node path adds more negativity, so the least-negative single node wins.",
    },
]
MAXPATH_EXAMPLE_IO = [
    ([[1, 2, 3]], 6),
    ([[-10, 9, 20, None, None, 15, 7]], 42),
    ([[-3, -2, -5]], -2),
]
MAXPATH_SPARSE_IO = [
    ([[7]], 7),
    ([[-8]], -8),
    ([[-10, -20, None, -30]], -10),
    ([[2, None, -1, None, None, None, 3]], 4),
]

# ----------------------------------------------------------------------------
# Problem 8: sum-root-to-leaf-numbers
# ----------------------------------------------------------------------------

spec_sum = ProblemSpec(
    signature="function sumNumbers(root: number[])",
    statement=f"""# Root-to-Leaf Numbers

{ENCODING}

Every present node holds a single decimal digit (`0` to `9`). Each root-to-leaf path spells a decimal number: starting from `0` at the root's parent, each step updates `value = value * 10 + digit`. A lone root is itself a leaf, contributing its own digit.

Return the sum of the numbers spelled by all root-to-leaf paths.

Constraints: `1 <= root.length <= 30`, `0 <= root[i] <= 9`, and `root[0]` is present.
""",
    brute_force=Algorithm(
        """function sumNumbers(root) {
  const paths = [];
  (function build(i, cur) {
    if (i >= root.length || root[i] === null) return;
    const next = cur.concat([root[i]]);
    const l = 2 * i + 1;
    const r = 2 * i + 2;
    const hasL = l < root.length && root[l] !== null;
    const hasR = r < root.length && root[r] !== null;
    if (!hasL && !hasR) {
      paths.push(next);
      return;
    }
    build(l, next);
    build(r, next);
  })(0, []);
  let total = 0;
  for (const digits of paths) {
    let value = 0;
    for (const d of digits) value = value * 10 + d;
    total += value;
  }
  return total;
}""",
        complexity="Time: O(n·h) | Space: O(n·h)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function sumNumbers(root) {
  let total = 0;
  (function dfs(i, cur) {
    if (i >= root.length || root[i] === null) return;
    const next = cur * 10 + root[i];
    const l = 2 * i + 1;
    const r = 2 * i + 2;
    const hasL = l < root.length && root[l] !== null;
    const hasR = r < root.length && root[r] !== null;
    if (!hasL && !hasR) {
      total += next;
      return;
    }
    dfs(l, next);
    dfs(r, next);
  })(0, 0);
  return total;
}""",
        complexity="Time: O(n) | Space: O(h)",
        language="javascript",
    ),
    topic="trees",
    difficulty="Medium",
    pattern="trees / Path accumulate",
    time_limit_ms=2000,
    seed=42,
    title="Root-to-Leaf Numbers",
    slug="sum-root-to-leaf-numbers",
    editorial={
        "approach": "Depth-first walk carrying the number built so far; each step multiplies by ten and adds the digit, adding the total at every leaf.",
        "why_optimal": "Each node is visited once with constant extra work, so time is linear and stack space follows the height.",
        "pitfalls": "Zeros are real digits that shift place values; a missing child ends a path but a zero child extends it.",
    },
    reading_links=[TRAV_LINK],
    hints=[
        "Carry the prefix number downward, not upward.",
        "Each step multiplies the prefix by 10 before adding the digit.",
        "Add to the total only at leaves — nodes with no present children.",
    ],
)

PY_SUM_BRUTE = """def sumNumbers(root: list) -> int:
    paths = []
    def build(i, cur):
        if i >= len(root) or root[i] is None:
            return
        nxt = cur + [root[i]]
        l, r = 2 * i + 1, 2 * i + 2
        has_l = l < len(root) and root[l] is not None
        has_r = r < len(root) and root[r] is not None
        if not has_l and not has_r:
            paths.append(nxt)
            return
        build(l, nxt)
        build(r, nxt)
    build(0, [])
    total = 0
    for digits in paths:
        value = 0
        for d in digits:
            value = value * 10 + d
        total += value
    return total
"""

PY_SUM_OPTIMAL = """def sumNumbers(root: list) -> int:
    total = 0
    def dfs(i, cur):
        nonlocal total
        if i >= len(root) or root[i] is None:
            return
        nxt = cur * 10 + root[i]
        l, r = 2 * i + 1, 2 * i + 2
        has_l = l < len(root) and root[l] is not None
        has_r = r < len(root) and root[r] is not None
        if not has_l and not has_r:
            total += nxt
            return
        dfs(l, nxt)
        dfs(r, nxt)
    dfs(0, 0)
    return total
"""

SUM_EXAMPLES = [
    {
        "input": "root = [1,2,3]",
        "output": "25",
        "explanation": "The paths spell 12 and 13, which sum to 25.",
    },
    {
        "input": "root = [4,9,0,5,1]",
        "output": "1026",
        "explanation": "The paths spell 495, 491, and 40; together they total 1026.",
    },
    {
        "input": "root = [1,0]",
        "output": "10",
        "explanation": "A single zero child still extends the path, spelling 10.",
    },
]
SUM_EXAMPLE_IO = [
    ([[1, 2, 3]], 25),
    ([[4, 9, 0, 5, 1]], 1026),
    ([[1, 0]], 10),
]
SUM_SPARSE_IO = [
    ([[5]], 5),
    ([[0]], 0),
    ([[1, None, 0]], 10),
    ([[9, 0, None, 0]], 900),
]

# ----------------------------------------------------------------------------
# Problem 9: flatten-binary-tree-preorder
# ----------------------------------------------------------------------------

spec_flat = ProblemSpec(
    signature="function flatten(root: number[])",
    statement=f"""# Preorder Flatten Order

{ENCODING}

Flattening rewires the tree into a right-leaning chain that visits every present node exactly once in preorder (node, then left subtree, then right subtree). Because the judge compares returned values rather than pointer surgery, this task asks for the flattened order directly.

Return the preorder traversal of the present nodes as a flat array.

Constraints: `0 <= root.length <= 30` and `-100 <= root[i] <= 100`.
""",
    brute_force=Algorithm(
        """function flatten(root) {
  function pre(i) {
    if (i >= root.length || root[i] === null) return [];
    return [root[i]].concat(pre(2 * i + 1), pre(2 * i + 2));
  }
  return pre(0);
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function flatten(root) {
  const order = [];
  const stack = [];
  if (root.length > 0 && root[0] !== null) stack.push(0);
  while (stack.length > 0) {
    const i = stack.pop();
    order.push(root[i]);
    const l = 2 * i + 1;
    const r = 2 * i + 2;
    if (r < root.length && root[r] !== null) stack.push(r);
    if (l < root.length && root[l] !== null) stack.push(l);
  }
  return order;
}""",
        complexity="Time: O(n) | Space: O(h)",
        language="javascript",
    ),
    topic="trees",
    difficulty="Medium",
    pattern="trees / Preorder sequence",
    time_limit_ms=2000,
    seed=42,
    title="Preorder Flatten Order",
    slug="flatten-binary-tree-preorder",
    editorial={
        "approach": "Iterative preorder with an explicit stack: emit each node, then stack its right child below its left child so the left subtree always comes first.",
        "why_optimal": "Each present node is pushed and popped once, giving linear time with a stack bounded by the height.",
        "pitfalls": "Push the right child before the left so the left pops first; skip null holes entirely instead of emitting placeholders.",
    },
    reading_links=[TRAV_LINK],
    hints=[
        "Preorder means node first, then the whole left subtree, then the right.",
        "A stack can replay the recursion: push right, then left.",
        "Null holes contribute nothing to the order.",
    ],
)

PY_FLAT_BRUTE = """def flatten(root: list) -> list:
    def pre(i):
        if i >= len(root) or root[i] is None:
            return []
        return [root[i]] + pre(2 * i + 1) + pre(2 * i + 2)
    return pre(0)
"""

PY_FLAT_OPTIMAL = """def flatten(root: list) -> list:
    order = []
    stack = []
    if len(root) > 0 and root[0] is not None:
        stack.append(0)
    while stack:
        i = stack.pop()
        order.append(root[i])
        l, r = 2 * i + 1, 2 * i + 2
        if r < len(root) and root[r] is not None:
            stack.append(r)
        if l < len(root) and root[l] is not None:
            stack.append(l)
    return order
"""

FLAT_EXAMPLES = [
    {
        "input": "root = [1,2,5,3,4,null,6]",
        "output": "[1,2,3,4,5,6]",
        "explanation": "Preorder visits 1, then the left subtree as 2, 3, 4, then the right subtree as 5, 6.",
    },
    {
        "input": "root = [1,null,2]",
        "output": "[1,2]",
        "explanation": "The missing left child is skipped, leaving the node followed by its right child.",
    },
    {
        "input": "root = [3,1,null,2]",
        "output": "[3,1,2]",
        "explanation": "Node 3 comes first, then 1, then 1's left child 2 — even though 2 sits two levels down.",
    },
]
FLAT_EXAMPLE_IO = [
    ([[1, 2, 5, 3, 4, None, 6]], [1, 2, 3, 4, 5, 6]),
    ([[1, None, 2]], [1, 2]),
    ([[3, 1, None, 2]], [3, 1, 2]),
]
FLAT_SPARSE_IO = [
    ([[]], []),
    ([[None]], []),
    ([[9]], [9]),
    ([[1, 2, None, 3, None, None, None, 4]], [1, 2, 3, 4]),
    ([[1, None, 2, None, None, None, 3]], [1, 2, 3]),
]

# ----------------------------------------------------------------------------
# Problem 10: construct-from-preorder-inorder (custom cases only: preorder and
# inorder must be a consistent pair over unique values)
# ----------------------------------------------------------------------------

spec_build = ProblemSpec(
    signature="function buildTree(preorder: number[], inorder: number[])",
    statement="""# Rebuild from Two Traversals

You are given the preorder and inorder traversals of one binary tree whose values are all distinct. In preorder the root of every subtree comes first, followed by its left subtree then its right subtree; in inorder the left subtree comes first, then the root, then the right subtree.

Rebuild the original tree and return it as a level-order array using the bank-standard heap encoding: the children of the entry at index `i` live at `2i+1` and `2i+2`, absent children are written as `null`, and trailing `null` entries are trimmed. Both inputs are non-empty and describe the same set of values.

Constraints: `1 <= preorder.length <= 20`, `1 <= inorder.length <= 20`, `preorder.length == inorder.length`, `-100 <= preorder[i] <= 100`, and all values are unique.
""",
    brute_force=Algorithm(
        """function buildTree(preorder, inorder) {
  function build(preL, preR, inL, inR) {
    if (preL > preR) return null;
    const value = preorder[preL];
    let k = inL;
    while (inorder[k] !== value) k++;
    const leftSize = k - inL;
    return {
      v: value,
      l: build(preL + 1, preL + leftSize, inL, k - 1),
      r: build(preL + leftSize + 1, preR, k + 1, inR),
    };
  }
  const tree = build(0, preorder.length - 1, 0, inorder.length - 1);
  if (tree === null) return [];
  const out = [];
  const queue = [{ node: tree, i: 0 }];
  while (queue.length > 0) {
    const cur = queue.shift();
    while (out.length <= cur.i) out.push(null);
    out[cur.i] = cur.node.v;
    if (cur.node.l !== null) queue.push({ node: cur.node.l, i: 2 * cur.i + 1 });
    if (cur.node.r !== null) queue.push({ node: cur.node.r, i: 2 * cur.i + 2 });
  }
  while (out.length > 0 && out[out.length - 1] === null) out.pop();
  return out;
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function buildTree(preorder, inorder) {
  const pos = new Map();
  for (let k = 0; k < inorder.length; k++) pos.set(inorder[k], k);
  let cursor = 0;
  function build(inL, inR) {
    if (inL > inR) return null;
    const value = preorder[cursor];
    cursor++;
    const k = pos.get(value);
    const left = build(inL, k - 1);
    const right = build(k + 1, inR);
    return { v: value, l: left, r: right };
  }
  const tree = build(0, inorder.length - 1);
  if (tree === null) return [];
  const out = [];
  const queue = [{ node: tree, i: 0 }];
  while (queue.length > 0) {
    const cur = queue.shift();
    while (out.length <= cur.i) out.push(null);
    out[cur.i] = cur.node.v;
    if (cur.node.l !== null) queue.push({ node: cur.node.l, i: 2 * cur.i + 1 });
    if (cur.node.r !== null) queue.push({ node: cur.node.r, i: 2 * cur.i + 2 });
  }
  while (out.length > 0 && out[out.length - 1] === null) out.pop();
  return out;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="trees",
    difficulty="Medium",
    pattern="trees / Partition",
    time_limit_ms=2000,
    seed=42,
    title="Rebuild from Two Traversals",
    slug="construct-from-preorder-inorder",
    editorial={
        "approach": "Take the next preorder value as the subtree root, split inorder at its position into left and right ranges, and recurse — with a value-to-index map for constant splits.",
        "why_optimal": "Each node is placed once and each inorder lookup is constant, so the rebuild is linear with stack space bounded by the height.",
        "pitfalls": "Consume preorder in strict order across the recursion; trim trailing nulls from the level-order output so equivalent trees serialize identically.",
    },
    reading_links=[TRAV_LINK],
    hints=[
        "The first unconsumed preorder value is always the current subtree root.",
        "That root's inorder position splits the range into left and right parts.",
        "A map from value to inorder index keeps every split constant time.",
    ],
)

PY_BUILD_BRUTE = """def buildTree(preorder: list, inorder: list) -> list:
    def build(pre_l, pre_r, in_l, in_r):
        if pre_l > pre_r:
            return None
        value = preorder[pre_l]
        k = in_l
        while inorder[k] != value:
            k += 1
        left_size = k - in_l
        return (
            value,
            build(pre_l + 1, pre_l + left_size, in_l, k - 1),
            build(pre_l + left_size + 1, pre_r, k + 1, in_r),
        )
    def emit(tree):
        if tree is None:
            return []
        out, queue = [], [(tree, 0)]
        while queue:
            node, i = queue.pop(0)
            while len(out) <= i:
                out.append(None)
            out[i] = node[0]
            if node[1] is not None:
                queue.append((node[1], 2 * i + 1))
            if node[2] is not None:
                queue.append((node[2], 2 * i + 2))
        while out and out[-1] is None:
            out.pop()
        return out
    return emit(build(0, len(preorder) - 1, 0, len(inorder) - 1))
"""

PY_BUILD_OPTIMAL = """def buildTree(preorder: list, inorder: list) -> list:
    pos = {v: k for k, v in enumerate(inorder)}
    cursor = 0
    def build(in_l, in_r):
        nonlocal cursor
        if in_l > in_r:
            return None
        value = preorder[cursor]
        cursor += 1
        k = pos[value]
        return (value, build(in_l, k - 1), build(k + 1, in_r))
    def emit(tree):
        if tree is None:
            return []
        out, queue = [], [(tree, 0)]
        while queue:
            node, i = queue.pop(0)
            while len(out) <= i:
                out.append(None)
            out[i] = node[0]
            if node[1] is not None:
                queue.append((node[1], 2 * i + 1))
            if node[2] is not None:
                queue.append((node[2], 2 * i + 2))
        while out and out[-1] is None:
            out.pop()
        return out
    return emit(build(0, len(inorder) - 1))
"""

BUILD_EXAMPLES = [
    {
        "input": "preorder = [3,9,20,15,7], inorder = [9,3,15,20,7]",
        "output": "[3,9,20,null,null,15,7]",
        "explanation": "3 is the root; 9 forms the left subtree; in the right subtree 20 is the root with 15 left and 7 right.",
    },
    {
        "input": "preorder = [1,2], inorder = [2,1]",
        "output": "[1,2]",
        "explanation": "The root 1 sits after 2 in inorder, so 2 is its left child.",
    },
    {
        "input": "preorder = [1,2,3], inorder = [3,2,1]",
        "output": "[1,2,null,3]",
        "explanation": "1 is the root, 2 is its left child, and 3 hangs left of 2 — a pure left chain.",
    },
]
BUILD_EXAMPLE_IO = [
    ([[3, 9, 20, 15, 7], [9, 3, 15, 20, 7]], [3, 9, 20, None, None, 15, 7]),
    ([[1, 2], [2, 1]], [1, 2]),
    ([[1, 2, 3], [3, 2, 1]], [1, 2, None, 3]),
]
BUILD_SPARSE_IO = [
    ([[7], [7]], [7]),
    ([[1, 2], [2, 1]], [1, 2]),
    ([[5, 4, 3], [3, 4, 5]], [5, 4, None, 3]),
    ([[1, 2, 3], [1, 2, 3]], [1, None, 2, None, None, None, 3]),
]

def _lca_random_inputs(rng: random.Random) -> list[list[Any]]:
    inputs: list[list[Any]] = []
    for _ in range(8):
        arr, vals = bst_level_order(rng, rng.randint(5, 12))
        a, b = rng.sample(vals, 2)
        inputs.append([list(arr), a, b])
        other = rng.choice([v for v in vals if v != arr[0]])
        inputs.append([list(arr), arr[0], other])
    return inputs


def _build_random_inputs(rng: random.Random) -> list[list[Any]]:
    inputs: list[list[Any]] = []
    for _ in range(14):
        pre, ino = rand_bst_pre_in(rng)
        inputs.append([pre, ino])
    inputs.append([[5, 4, 3, 2, 1], [1, 2, 3, 4, 5]])
    inputs.append([[1, 2, 3, 4, 5], [1, 2, 3, 4, 5]])
    inputs.append([[10, 5], [5, 10]])
    inputs.append([[10, 5], [10, 5]])
    return inputs


ENTRIES: list[dict[str, Any]] = [
    {"spec": spec_lca, "py_brute": PY_LCA_BRUTE, "py_opt": PY_LCA_OPTIMAL,
     "examples": LCA_EXAMPLES, "example_io": LCA_EXAMPLE_IO, "sparse_io": LCA_SPARSE_IO,
     "mode": "custom", "random_inputs": _lca_random_inputs},
    {"spec": spec_level, "py_brute": PY_LEVEL_BRUTE, "py_opt": PY_LEVEL_OPTIMAL,
     "examples": LEVEL_EXAMPLES, "example_io": LEVEL_EXAMPLE_IO, "sparse_io": LEVEL_SPARSE_IO,
     "mode": "paf"},
    {"spec": spec_right, "py_brute": PY_RIGHT_BRUTE, "py_opt": PY_RIGHT_OPTIMAL,
     "examples": RIGHT_EXAMPLES, "example_io": RIGHT_EXAMPLE_IO, "sparse_io": RIGHT_SPARSE_IO,
     "mode": "paf"},
    {"spec": spec_good, "py_brute": PY_GOOD_BRUTE, "py_opt": PY_GOOD_OPTIMAL,
     "examples": GOOD_EXAMPLES, "example_io": GOOD_EXAMPLE_IO, "sparse_io": GOOD_SPARSE_IO,
     "mode": "paf"},
    {"spec": spec_sym, "py_brute": PY_SYM_BRUTE, "py_opt": PY_SYM_OPTIMAL,
     "examples": SYM_EXAMPLES, "example_io": SYM_EXAMPLE_IO, "sparse_io": SYM_SPARSE_IO,
     "mode": "paf"},
    {"spec": spec_bal, "py_brute": PY_BAL_BRUTE, "py_opt": PY_BAL_OPTIMAL,
     "examples": BAL_EXAMPLES, "example_io": BAL_EXAMPLE_IO, "sparse_io": BAL_SPARSE_IO,
     "mode": "paf"},
    {"spec": spec_maxpath, "py_brute": PY_MAXPATH_BRUTE, "py_opt": PY_MAXPATH_OPTIMAL,
     "examples": MAXPATH_EXAMPLES, "example_io": MAXPATH_EXAMPLE_IO, "sparse_io": MAXPATH_SPARSE_IO,
     "mode": "paf"},
    {"spec": spec_sum, "py_brute": PY_SUM_BRUTE, "py_opt": PY_SUM_OPTIMAL,
     "examples": SUM_EXAMPLES, "example_io": SUM_EXAMPLE_IO, "sparse_io": SUM_SPARSE_IO,
     "mode": "paf"},
    {"spec": spec_flat, "py_brute": PY_FLAT_BRUTE, "py_opt": PY_FLAT_OPTIMAL,
     "examples": FLAT_EXAMPLES, "example_io": FLAT_EXAMPLE_IO, "sparse_io": FLAT_SPARSE_IO,
     "mode": "paf"},
    {"spec": spec_build, "py_brute": PY_BUILD_BRUTE, "py_opt": PY_BUILD_OPTIMAL,
     "examples": BUILD_EXAMPLES, "example_io": BUILD_EXAMPLE_IO, "sparse_io": BUILD_SPARSE_IO,
     "mode": "custom", "random_inputs": _build_random_inputs},
]


def _assemble_data(
    spec: ProblemSpec, merged: list[dict], examples: list[dict],
    brute_rt: float, opt_rt: float, py_brute: str, py_opt: str,
) -> dict[str, Any]:
    return {
        "slug": spec.resolved_slug,
        "title": spec.resolved_title,
        "topic": spec.topic,
        "difficulty": spec.difficulty,
        "pattern": spec.pattern,
        "statement": spec.statement,
        "examples": examples,
        "constraints": _constraints(spec),
        "hints": list(spec.hints or []),
        "editorial": dict(spec.editorial or {}),
        "reading_links": list(spec.reading_links),
        "starterCode": {"javascript": _starter_js(spec), "python": _starter_py(spec)},
        "functionName": spec.function_name,
        "timeLimitMs": spec.time_limit_ms,
        "reviewStatus": "verified",
        "pafVerification": {
            "seed": spec.seed,
            "generatedCaseCount": len(merged),
            "bruteForceRuntimeMs": brute_rt,
            "optimalRuntimeMs": opt_rt,
        },
        "testCases": merged,
        "solutions": [
            {"title": "Brute Force", "complexity": spec.brute_force.complexity,
             "language": "javascript", "code": spec.brute_force.code, "isReference": False},
            {"title": "Optimal", "complexity": spec.optimal.complexity,
             "language": "javascript", "code": spec.optimal.code, "isReference": True},
            {"title": "Brute Force", "complexity": spec.brute_force.complexity,
             "language": "python", "code": py_brute, "isReference": False},
            {"title": "Optimal", "complexity": spec.optimal.complexity,
             "language": "python", "code": py_opt, "isReference": True},
        ],
    }


async def _finalize(entry: dict[str, Any], rng: random.Random) -> tuple[dict[str, Any], float, float]:
    spec: ProblemSpec = entry["spec"]
    slug = spec.slug or spec.resolved_slug

    if entry["mode"] == "paf":
        problem = await build_verified_problem(spec)
        stock = problem.report.test_cases
        brute_rt = problem.report.brute_force_runtime_ms
        opt_rt = problem.report.optimal_runtime_ms
        data = problem.data
    else:
        rand_inputs = entry["random_inputs"](rng)
        stock = await _probe_expected(
            spec.function_name, spec.optimal.code, "javascript", rand_inputs, "custom-rand")
        await _require_ac("javascript", spec.brute_force.code,
                           spec.function_name, stock, "brute-force", slug)
        brute_rt = opt_rt = 0.0
        data = None

    fixed_inputs = [list(io) for io, _ in entry["example_io"]] + \
                   [list(io) for io, _ in entry["sparse_io"]]
    hand = [exp for _, exp in entry["example_io"]] + [exp for _, exp in entry["sparse_io"]]
    fixed = await _probe_expected(
        spec.function_name, spec.optimal.code, "javascript", fixed_inputs, "edge-fixed")
    for case, h in zip(fixed, hand, strict=True):
        if json.dumps(case["expected"], sort_keys=True) != json.dumps(h, sort_keys=True):
            raise ValueError(
                f"{slug} hand/judge mismatch on {case['input']}: hand={h} judge={case['expected']}")
    n_examples = len(entry["example_io"])
    for i, case in enumerate(fixed):
        case["isSample"] = i < 2
        case["label"] = f"example-{i + 1:02d}" if i < n_examples else f"edge-sparse-{i - n_examples + 1:02d}"

    merged = _merge_cases(fixed, stock)
    merged[0]["isSample"] = True
    merged[1]["isSample"] = True
    for case in merged[2:]:
        case["isSample"] = False

    await _require_ac("javascript", spec.brute_force.code,
                       spec.function_name, merged, "brute-force", slug)
    js_opt_rt = await _require_ac("javascript", spec.optimal.code,
                                  spec.function_name, merged, "optimal", slug)
    py_brute_rt = await _require_ac("python", entry["py_brute"],
                                    spec.function_name, merged, "brute-force", slug)
    py_opt_rt = await _require_ac("python", entry["py_opt"],
                                  spec.function_name, merged, "optimal", slug)
    if entry["mode"] == "custom":
        brute_rt = await _require_ac("javascript", spec.brute_force.code,
                                     spec.function_name, merged, "brute-force", slug)
        opt_rt = js_opt_rt

    if data is None:
        data = _assemble_data(spec, merged, entry["examples"],
                              brute_rt, opt_rt, entry["py_brute"], entry["py_opt"])
    else:
        data["examples"] = entry["examples"]
        data["constraints"] = _constraints(spec)
        data["testCases"] = merged
        data["pafVerification"]["generatedCaseCount"] = len(merged)
        data["solutions"] = data["solutions"] + [
            {"title": "Brute Force", "complexity": spec.brute_force.complexity,
             "language": "python", "code": entry["py_brute"], "isReference": False},
            {"title": "Optimal", "complexity": spec.optimal.complexity,
             "language": "python", "code": entry["py_opt"], "isReference": True},
        ]
    return data, py_brute_rt, py_opt_rt


async def _run_all() -> None:
    output_dir = REPO_ROOT / "content" / "problems"
    rng = random.Random(42)
    print(f"Authoring and verifying {len(ENTRIES)} Batch-2B tree problems...")
    for idx, entry in enumerate(ENTRIES, 1):
        spec: ProblemSpec = entry["spec"]
        print(f"[{idx}/{len(ENTRIES)}] Generating {spec.slug} ({spec.difficulty})...")
        data, py_brute_rt, py_opt_rt = await _finalize(entry, rng)
        out_file = output_dir / f"{data['slug']}.json"
        out_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        pv = data["pafVerification"]
        print(
            f"  ok {data['slug']}: {len(data['testCases'])} cases verified | "
            f"JS brute: {pv['bruteForceRuntimeMs']:.2f}ms | "
            f"JS optimal: {pv['optimalRuntimeMs']:.2f}ms | "
            f"PY brute: {py_brute_rt:.2f}ms | PY optimal: {py_opt_rt:.2f}ms -> {out_file.name}"
        )
    print("\nAll 10 Batch-2B problems generated and verified successfully.")


def main() -> None:
    asyncio.run(_run_all())


if __name__ == "__main__":
    main()
