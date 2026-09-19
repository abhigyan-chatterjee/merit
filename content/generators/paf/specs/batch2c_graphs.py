"""Authoring and verification script for Batch 2C: Graphs + Heap problems."""

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

from content.generators.paf import Algorithm, ProblemSpec, build_verified_problem
from content.generators.paf.inputs import generate_inputs


async def _execute_js(code: str, function_name: str, cases: list[dict]) -> Any:
    from app.services.judge import execute_code

    return await execute_code(
        language="javascript",
        code=code,
        function_name=function_name,
        test_cases=cases,
        time_limit_ms=2000,
    )


async def _execute_py(code: str, function_name: str, cases: list[dict]) -> Any:
    from app.services.judge import execute_code

    return await execute_code(
        language="python",
        code=code,
        function_name=function_name,
        test_cases=cases,
        time_limit_ms=2000,
    )


async def _build_custom_cases(
    spec: ProblemSpec,
    brute_code: str,
    optimal_code: str,
    inputs: list[list[Any]],
) -> list[dict]:
    """Run bespoke valid inputs through the judge to derive expected outputs."""
    pending = [
        {"label": f"custom-{i + 1:02d}", "input": values, "expected": None, "isSample": False}
        for i, values in enumerate(inputs)
    ]
    probe = await _execute_js(optimal_code, spec.function_name, pending)
    if probe.compile_output or len(probe.test_results) != len(pending):
        raise ValueError(f"Optimal implementation failed for {spec.slug}: {probe.compile_output}")
    for case, result in zip(pending, probe.test_results, strict=True):
        if result.get("error") is not None or "actual" not in result:
            raise ValueError(f"Optimal implementation failed for {spec.slug}: {result.get('error')}")
        case["expected"] = result["actual"]
    check_pending = [
        {"label": c["label"], "input": list(c["input"]), "expected": c["expected"], "isSample": False}
        for c in pending
    ]
    brute = await _execute_js(brute_code, spec.function_name, check_pending)
    if brute.verdict != "AC":
        raise ValueError(f"Brute-force implementation failed for {spec.slug}: {brute.compile_output}")
    optimal = await _execute_js(optimal_code, spec.function_name, check_pending)
    if optimal.verdict != "AC":
        raise ValueError(f"Optimal implementation failed for {spec.slug}: {optimal.compile_output}")
    return pending


def _rng() -> random.Random:
    return random.Random(42)


spec_rotting_oranges = ProblemSpec(
    signature="function orangesRotting(grid: number[][])",
    statement="""# Rotting Oranges

A crate of oranges is arranged in a rectangular grid `grid`. Each cell holds `0` for an empty slot, `1` for a fresh orange, or `2` for a rotten orange.

Every minute, each rotten orange spoils its four orthogonal neighbours (up, down, left, right) that currently hold a fresh orange. Empty slots never change and never transmit rot.

Return the number of minutes until no fresh orange remains. Return `-1` when at least one fresh orange can never rot, and `0` when there is nothing fresh to begin with.

Constraints: `1 <= grid.length <= 8` and `0 <= grid[i] <= 2`.
""",
    brute_force=Algorithm(
        """function orangesRotting(grid) {
  const g = grid.map((row) => row.slice());
  if (g.length === 0) return 0;
  function freshCount() {
    let total = 0;
    for (let r = 0; r < g.length; r++) {
      for (let c = 0; c < g[r].length; c++) {
        if (g[r][c] === 1) total++;
      }
    }
    return total;
  }
  if (freshCount() === 0) return 0;
  let minutes = 0;
  while (true) {
    const toRot = [];
    for (let r = 0; r < g.length; r++) {
      for (let c = 0; c < g[r].length; c++) {
        if (g[r][c] !== 1) continue;
        const near =
          (r > 0 && g[r - 1][c] === 2) ||
          (r + 1 < g.length && g[r + 1][c] === 2) ||
          (c > 0 && g[r][c - 1] === 2) ||
          (c + 1 < g[r].length && g[r][c + 1] === 2);
        if (near) toRot.push([r, c]);
      }
    }
    if (toRot.length === 0) return -1;
    for (const pair of toRot) g[pair[0]][pair[1]] = 2;
    minutes++;
    if (freshCount() === 0) return minutes;
  }
}""",
        complexity="Time: O((R * C)²) | Space: O(R * C)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function orangesRotting(grid) {
  const g = grid.map((row) => row.slice());
  if (g.length === 0) return 0;
  const queue = [];
  let fresh = 0;
  for (let r = 0; r < g.length; r++) {
    for (let c = 0; c < g[r].length; c++) {
      if (g[r][c] === 2) queue.push([r, c]);
      else if (g[r][c] === 1) fresh++;
    }
  }
  if (fresh === 0) return 0;
  let minutes = 0;
  let head = 0;
  const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  while (head < queue.length && fresh > 0) {
    const size = queue.length - head;
    let rotted = false;
    for (let i = 0; i < size; i++) {
      const cell = queue[head++];
      for (const d of dirs) {
        const nr = cell[0] + d[0];
        const nc = cell[1] + d[1];
        if (nr >= 0 && nc >= 0 && nr < g.length && nc < g[nr].length && g[nr][nc] === 1) {
          g[nr][nc] = 2;
          fresh--;
          queue.push([nr, nc]);
          rotted = true;
        }
      }
    }
    if (rotted) minutes++;
  }
  return fresh === 0 ? minutes : -1;
}""",
        complexity="Time: O(R * C) | Space: O(R * C)",
        language="javascript",
    ),
    topic="graphs",
    difficulty="Medium",
    pattern="graphs / Multi-source BFS",
    time_limit_ms=2000,
    seed=42,
    title="Rotting Oranges",
    slug="rotting-oranges",
    editorial={
        "approach": "Seed a queue with every rotten orange and expand level by level, spoiling fresh neighbours. Track the remaining fresh count and the number of levels processed.",
        "why_optimal": "Multi-source BFS visits each cell once, dropping the repeated full-grid scans of the minute-by-minute simulation. __RUNTIMES__",
        "pitfalls": "Return 0 immediately when no fresh orange exists, even if no rotten orange is present. Only count a minute when at least one orange actually rotted, and return -1 when fresh oranges remain but the queue is exhausted.",
    },
    reading_links=["https://en.wikipedia.org/wiki/Breadth-first_search"],
    hints=[
        "All rotten oranges spread simultaneously, so seed the queue with every one of them at time zero.",
        "Process the queue one level per minute and count a minute only when fresh oranges rot during that level.",
        "If fresh oranges remain after the queue drains, those oranges are unreachable: answer -1.",
    ],
)

spec_surrounded_regions = ProblemSpec(
    signature="function solve(board: string[][])",
    statement="""# Surrounded Regions

A rectangular board `board` holds the strings `'X'` and `'O'`. Any `'O'` cell that is not connected to the border of the board through a chain of orthogonally adjacent `'O'` cells is captured and flipped to `'X'`.

An `'O'` region survives exactly when at least one of its cells touches the border, or reaches the border through neighbouring `'O'` cells. Every other `'O'` becomes `'X'`.

Return the board after all captures are applied.

Constraints: `1 <= board.length <= 8`. Every row holds only `'X'` and `'O'` strings.
""",
    brute_force=Algorithm(
        """function solve(board) {
  if (board.length === 0) return [];
  const orig = board.map((row) => row.slice());
  const g = board.map((row) => row.slice());
  const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  function reachesBorder(sr, sc) {
    const seen = new Set([sr + ',' + sc]);
    const queue = [[sr, sc]];
    let head = 0;
    while (head < queue.length) {
      const cell = queue[head++];
      const r = cell[0];
      const c = cell[1];
      if (r === 0 || c === 0 || r === orig.length - 1 || c === orig[r].length - 1) return true;
      for (const d of dirs) {
        const nr = r + d[0];
        const nc = c + d[1];
        if (nr >= 0 && nc >= 0 && nr < orig.length && nc < orig[nr].length && orig[nr][nc] === 'O') {
          const key = nr + ',' + nc;
          if (!seen.has(key)) {
            seen.add(key);
            queue.push([nr, nc]);
          }
        }
      }
    }
    return false;
  }
  for (let r = 0; r < orig.length; r++) {
    for (let c = 0; c < orig[r].length; c++) {
      if (orig[r][c] === 'O' && !reachesBorder(r, c)) g[r][c] = 'X';
    }
  }
  for (let r = 0; r < g.length; r++) {
    for (let c = 0; c < g[r].length; c++) {
      if (g[r][c] !== 'O') g[r][c] = 'X';
    }
  }
  return g;
}""",
        complexity="Time: O((R * C)²) | Space: O(R * C)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function solve(board) {
  if (board.length === 0) return [];
  const g = board.map((row) => row.slice());
  const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  const stack = [];
  for (let r = 0; r < g.length; r++) {
    for (let c = 0; c < g[r].length; c++) {
      const onBorder = r === 0 || c === 0 || r === g.length - 1 || c === g[r].length - 1;
      if (onBorder && g[r][c] === 'O') {
        g[r][c] = 'S';
        stack.push([r, c]);
      }
    }
  }
  while (stack.length > 0) {
    const cell = stack.pop();
    for (const d of dirs) {
      const nr = cell[0] + d[0];
      const nc = cell[1] + d[1];
      if (nr >= 0 && nc >= 0 && nr < g.length && nc < g[nr].length && g[nr][nc] === 'O') {
        g[nr][nc] = 'S';
        stack.push([nr, nc]);
      }
    }
  }
  for (let r = 0; r < g.length; r++) {
    for (let c = 0; c < g[r].length; c++) {
      g[r][c] = g[r][c] === 'S' ? 'O' : 'X';
    }
  }
  return g;
}""",
        complexity="Time: O(R * C) | Space: O(R * C)",
        language="javascript",
    ),
    topic="graphs",
    difficulty="Medium",
    pattern="graphs / Border DFS",
    time_limit_ms=2000,
    seed=42,
    title="Surrounded Regions",
    slug="surrounded-regions",
    editorial={
        "approach": "Mark every border-connected 'O' as safe with a flood fill starting from all border 'O' cells, then flip every remaining 'O' to 'X' and restore the safe marks.",
        "why_optimal": "One flood fill from the border classifies every cell in linear time instead of searching for a border path from each 'O' separately. __RUNTIMES__",
        "pitfalls": "Diagonal neighbours do not connect regions; only orthogonal adjacency counts. A region survives when any single cell reaches the border, not when most of it does.",
    },
    reading_links=["https://en.wikipedia.org/wiki/Depth-first_search"],
    hints=[
        "It is easier to find the survivors than the captured: start from the border, not the interior.",
        "Flood fill from every border 'O' and mark everything reachable as safe.",
        "Flip every unmarked 'O' to 'X' and restore the safe marks back to 'O'.",
    ],
)

spec_pacific_atlantic = ProblemSpec(
    signature="function pacificAtlantic(heights: number[][])",
    statement="""# Pacific Atlantic Water Flow

A rectangular island is described by `heights`, where `heights[r][c]` is the elevation of cell `(r, c)`. Rain falling on a cell flows to each orthogonal neighbour whose height is less than or equal to the current cell.

The Pacific ocean touches the top and left edges of the island; the Atlantic ocean touches the bottom and right edges. A cell drains to an ocean when a non-increasing path of heights leads from the cell to that ocean edge.

Return every `[row, col]` coordinate whose rain reaches both oceans, sorted lexicographically by row then column.

Constraints: `1 <= heights.length <= 8` and `0 <= heights[i] <= 20`.
""",
    brute_force=Algorithm(
        """function pacificAtlantic(heights) {
  if (heights.length === 0) return [];
  if (heights[0].length === 0) return [];
  const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  function reaches(sr, sc, ocean) {
    const seen = new Set([sr + ',' + sc]);
    const stack = [[sr, sc]];
    while (stack.length > 0) {
      const cell = stack.pop();
      const r = cell[0];
      const c = cell[1];
      const onOcean =
        ocean === 'pacific'
          ? r === 0 || c === 0
          : r === heights.length - 1 || c === heights[r].length - 1;
      if (onOcean) return true;
      for (const d of dirs) {
        const nr = r + d[0];
        const nc = c + d[1];
        if (nr >= 0 && nc >= 0 && nr < heights.length && nc < heights[nr].length) {
          const key = nr + ',' + nc;
          if (!seen.has(key) && heights[nr][nc] <= heights[r][c]) {
            seen.add(key);
            stack.push([nr, nc]);
          }
        }
      }
    }
    return false;
  }
  const res = [];
  for (let r = 0; r < heights.length; r++) {
    for (let c = 0; c < heights[r].length; c++) {
      if (reaches(r, c, 'pacific') && reaches(r, c, 'atlantic')) res.push([r, c]);
    }
  }
  res.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  return res;
}""",
        complexity="Time: O((R * C)²) | Space: O(R * C)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function pacificAtlantic(heights) {
  if (heights.length === 0) return [];
  if (heights[0].length === 0) return [];
  const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  function flowFrom(starts) {
    const seen = new Set(starts.map((p) => p[0] + ',' + p[1]));
    const stack = starts.slice();
    while (stack.length > 0) {
      const cell = stack.pop();
      const r = cell[0];
      const c = cell[1];
      for (const d of dirs) {
        const nr = r + d[0];
        const nc = c + d[1];
        if (nr >= 0 && nc >= 0 && nr < heights.length && nc < heights[nr].length) {
          const key = nr + ',' + nc;
          if (!seen.has(key) && heights[nr][nc] >= heights[r][c]) {
            seen.add(key);
            stack.push([nr, nc]);
          }
        }
      }
    }
    return seen;
  }
  const pacStarts = [];
  const atlStarts = [];
  for (let r = 0; r < heights.length; r++) {
    pacStarts.push([r, 0]);
    atlStarts.push([r, heights[r].length - 1]);
  }
  for (let c = 0; c < heights[0].length; c++) {
    pacStarts.push([0, c]);
    atlStarts.push([heights.length - 1, c]);
  }
  const pac = flowFrom(pacStarts);
  const atl = flowFrom(atlStarts);
  const res = [];
  for (let r = 0; r < heights.length; r++) {
    for (let c = 0; c < heights[r].length; c++) {
      if (pac.has(r + ',' + c) && atl.has(r + ',' + c)) res.push([r, c]);
    }
  }
  res.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  return res;
}""",
        complexity="Time: O(R * C) | Space: O(R * C)",
        language="javascript",
    ),
    topic="graphs",
    difficulty="Medium",
    pattern="graphs / Dual DFS",
    time_limit_ms=2000,
    seed=42,
    title="Pacific Atlantic Water Flow",
    slug="pacific-atlantic-water-flow",
    editorial={
        "approach": "Reverse the flow: start one flood fill from the Pacific border and one from the Atlantic border, climbing to neighbours of equal or greater height. Cells reached by both fills drain to both oceans.",
        "why_optimal": "Two border fills classify the whole island in linear time, replacing a downhill search from every cell. __RUNTIMES__",
        "pitfalls": "Water flows to neighbours of equal height, so both directions use non-strict comparisons. Sort the answer lexicographically; ocean order or discovery order is not deterministic output.",
    },
    reading_links=["https://en.wikipedia.org/wiki/Depth-first_search"],
    hints=[
        "Searching downhill from every cell repeats the same slopes; try searching uphill from the oceans instead.",
        "Reverse the rule: from an ocean cell you may climb to neighbours of equal or greater height.",
        "Intersect the two reachable sets and sort the shared coordinates lexicographically.",
    ],
)

spec_word_ladder = ProblemSpec(
    signature="function ladderLength(beginWord: string, endWord: string, wordList: string[])",
    statement="""# Word Ladder

A start word `beginWord`, a target word `endWord`, and a dictionary `wordList` are given. Every entry is a lowercase English word; only words sharing the start word's length can take part in a ladder.

One step replaces exactly one letter of the current word, and every intermediate word must appear in `wordList`. The ladder begins at `beginWord` and each visited word counts toward its length, so a direct one-letter change scores `2`.

Return the length of the shortest such ladder from `beginWord` to `endWord`. Return `0` when `endWord` is absent from `wordList` or when no chain of valid steps connects them.

Constraints: `1 <= wordList.length <= 20`. Each word holds lowercase English letters.
""",
    brute_force=Algorithm(
        """function ladderLength(beginWord, endWord, wordList) {
  const dict = new Set(wordList);
  if (!dict.has(endWord)) return 0;
  if (beginWord === endWord) return 1;
  function differsByOne(a, b) {
    if (a.length !== b.length) return false;
    let diff = 0;
    for (let i = 0; i < a.length; i++) {
      if (a[i] !== b[i]) {
        diff++;
        if (diff > 1) return false;
      }
    }
    return diff === 1;
  }
  const queue = [beginWord];
  const seen = new Set([beginWord]);
  let steps = 1;
  let head = 0;
  while (head < queue.length) {
    const size = queue.length - head;
    for (let i = 0; i < size; i++) {
      const word = queue[head++];
      if (word === endWord) return steps;
      for (const cand of wordList) {
        if (!seen.has(cand) && differsByOne(word, cand)) {
          seen.add(cand);
          queue.push(cand);
        }
      }
    }
    steps++;
  }
  return 0;
}""",
        complexity="Time: O(N² * L) | Space: O(N * L)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function ladderLength(beginWord, endWord, wordList) {
  const dict = new Set(wordList);
  if (!dict.has(endWord)) return 0;
  if (beginWord === endWord) return 1;
  const buckets = new Map();
  for (const word of dict) {
    if (word.length !== beginWord.length) continue;
    for (let i = 0; i < word.length; i++) {
      const key = word.slice(0, i) + '*' + word.slice(i + 1);
      if (!buckets.has(key)) buckets.set(key, []);
      buckets.get(key).push(word);
    }
  }
  const queue = [beginWord];
  const seen = new Set([beginWord]);
  let steps = 1;
  let head = 0;
  while (head < queue.length) {
    const size = queue.length - head;
    for (let i = 0; i < size; i++) {
      const word = queue[head++];
      if (word === endWord) return steps;
      for (let j = 0; j < word.length; j++) {
        const key = word.slice(0, j) + '*' + word.slice(j + 1);
        const group = buckets.get(key) || [];
        for (const next of group) {
          if (!seen.has(next)) {
            seen.add(next);
            queue.push(next);
          }
        }
      }
    }
    steps++;
  }
  return 0;
}""",
        complexity="Time: O(N * L) | Space: O(N * L)",
        language="javascript",
    ),
    topic="graphs",
    difficulty="Hard",
    pattern="graphs / BFS shortest",
    time_limit_ms=2000,
    seed=42,
    title="Word Ladder",
    slug="word-ladder",
    editorial={
        "approach": "Treat each dictionary word as a graph node with edges between words differing by one letter, then run BFS from the start word. The first visit to the target word gives the shortest ladder length.",
        "why_optimal": "Grouping words by wildcard pattern finds every neighbour in constant time instead of comparing each word against the whole dictionary. __RUNTIMES__",
        "pitfalls": "Return 0 before searching when the target word is missing from the dictionary. Words of a different length than the start word can never join the ladder and must be skipped.",
    },
    reading_links=["https://en.wikipedia.org/wiki/Breadth-first_search"],
    hints=[
        "Each word is a node; draw an edge between words that differ in exactly one position.",
        "BFS from the start word reaches words in order of ladder length, so the first arrival at the target is optimal.",
        "Wildcard patterns like h*t group mutual neighbours without pairwise comparisons.",
    ],
)

spec_kth_largest = ProblemSpec(
    signature="function findKthLargest(nums: number[], k: number)",
    statement="""# Kth Largest Element in an Array

An unsorted integer array `nums` and an integer `k` are given. Order the values from largest to smallest; the element in position `k` (1-based) is the kth largest, counting duplicates separately rather than collapsing them.

For `k = 1` this is the maximum of the array, and for `k = nums.length` it is the minimum.

Constraints: `1 <= nums.length <= 50`, `-100 <= nums[i] <= 100`, and `1 <= k <= nums.length`.
""",
    brute_force=Algorithm(
        """function findKthLargest(nums, k) {
  const sorted = nums.slice().sort((a, b) => a - b);
  return sorted[sorted.length - k];
}""",
        complexity="Time: O(n log n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function findKthLargest(nums, k) {
  const arr = nums.slice();
  const target = arr.length - k;
  function swap(i, j) {
    const t = arr[i];
    arr[i] = arr[j];
    arr[j] = t;
  }
  let lo = 0;
  let hi = arr.length - 1;
  while (lo < hi) {
    const pivot = arr[(lo + hi) >> 1];
    let i = lo;
    let lt = lo;
    let gt = hi;
    while (i <= gt) {
      if (arr[i] < pivot) {
        swap(i, lt);
        i++;
        lt++;
      } else if (arr[i] > pivot) {
        swap(i, gt);
        gt--;
      } else {
        i++;
      }
    }
    if (target < lt) hi = lt - 1;
    else if (target > gt) lo = gt + 1;
    else return pivot;
  }
  return arr[lo];
}""",
        complexity="Time: O(n) average | Space: O(1)",
        language="javascript",
    ),
    topic="heap",
    difficulty="Medium",
    pattern="heap / Quickselect",
    time_limit_ms=2000,
    seed=42,
    title="Kth Largest Element in an Array",
    slug="kth-largest-element-in-an-array",
    editorial={
        "approach": "The kth largest is the element at sorted index n - k. Quickselect partitions around a pivot and recurses only into the side holding that index, using a three-way split so duplicate values settle together.",
        "why_optimal": "Partitioning discards a fraction of the array per round for linear average time with constant extra space, instead of sorting everything. __RUNTIMES__",
        "pitfalls": "Translate k to the ascending index n - k before partitioning. A two-way partition degrades on heavy duplicates; the three-way split keeps equal values out of further rounds.",
    },
    reading_links=["https://en.wikipedia.org/wiki/Quickselect"],
    hints=[
        "Sorting answers the query; ask which ranked index the kth largest occupies.",
        "A partition around a pivot tells you exactly which ranks fall left and right of it.",
        "Recurse only into the side containing rank n - k and stop when the pivot settles there.",
    ],
)

spec_last_stone = ProblemSpec(
    signature="function lastStoneWeight(stones: number[])",
    statement="""# Last Stone Weight

A row of stones is given, where `stones[i]` is the weight of stone `i`. The game repeats the following round while more than one stone remains: pick the two heaviest stones `x <= y`, smash them together, and if `x < y` put a new stone of weight `y - x` back into the row. Equal stones destroy each other completely.

A single surviving stone keeps its weight; when every stone is destroyed the result is `0`.

Constraints: `1 <= stones.length <= 30` and `1 <= stones[i] <= 100`.
""",
    brute_force=Algorithm(
        """function lastStoneWeight(stones) {
  let piles = stones.slice();
  while (piles.length > 1) {
    piles.sort((a, b) => a - b);
    const y = piles.pop();
    const x = piles.pop();
    if (y !== x) piles.push(y - x);
  }
  return piles.length === 0 ? 0 : piles[0];
}""",
        complexity="Time: O(n² log n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function lastStoneWeight(stones) {
  const heap = [];
  function push(v) {
    heap.push(v);
    let i = heap.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (heap[p] >= heap[i]) break;
      const t = heap[p];
      heap[p] = heap[i];
      heap[i] = t;
      i = p;
    }
  }
  function pop() {
    const top = heap[0];
    const last = heap.pop();
    if (heap.length > 0) {
      heap[0] = last;
      let i = 0;
      while (true) {
        const l = 2 * i + 1;
        const r = 2 * i + 2;
        let s = i;
        if (l < heap.length && heap[l] > heap[s]) s = l;
        if (r < heap.length && heap[r] > heap[s]) s = r;
        if (s === i) break;
        const t = heap[s];
        heap[s] = heap[i];
        heap[i] = t;
        i = s;
      }
    }
    return top;
  }
  for (const s of stones) push(s);
  while (heap.length > 1) {
    const y = pop();
    const x = pop();
    if (y !== x) push(y - x);
  }
  return heap.length === 0 ? 0 : heap[0];
}""",
        complexity="Time: O(n log n) | Space: O(n)",
        language="javascript",
    ),
    topic="heap",
    difficulty="Easy",
    pattern="heap / Max simulate",
    time_limit_ms=2000,
    seed=42,
    title="Last Stone Weight",
    slug="last-stone-weight",
    editorial={
        "approach": "Repeatedly smash the two heaviest stones, returning any remainder to the row. A max-heap always exposes the two heaviest in logarithmic time.",
        "why_optimal": "Heap extraction replaces the full re-sort of every round, cutting each round from linearithmic to logarithmic time. __RUNTIMES__",
        "pitfalls": "Equal stones vanish without a remainder; only push y - x back when the weights differ. A single starting stone is already the answer.",
    },
    reading_links=["https://en.wikipedia.org/wiki/Binary_heap"],
    hints=[
        "Every round needs the two current maximums; the rest of the row is irrelevant.",
        "A max-heap delivers the two heaviest stones without re-sorting the row.",
        "Push the difference back only when the two weights differ.",
    ],
)

spec_task_scheduler = ProblemSpec(
    signature="function leastInterval(tasks: string[], n: number)",
    statement="""# Task Scheduler

A list of tasks is given, where each entry is an uppercase letter naming the task type, alongside a cooldown `n`. Each task occupies one unit of time, and two tasks of the same type must be separated by at least `n` units containing other tasks or idle waiting.

Tasks may run in any order. Return the smallest total time units, including idle slots, needed to finish every task. With `n = 0` no waiting is ever required.

Constraints: `1 <= tasks.length <= 50` and `0 <= n <= 20`. Each task is an uppercase letter.
""",
    brute_force=Algorithm(
        """function leastInterval(tasks, n) {
  const freq = new Map();
  for (const t of tasks) freq.set(t, (freq.get(t) || 0) + 1);
  const nextFree = new Map();
  let time = 0;
  let remaining = tasks.length;
  while (remaining > 0) {
    let best = null;
    let bestCount = 0;
    for (const entry of freq.entries()) {
      const task = entry[0];
      const count = entry[1];
      if (count > 0 && (nextFree.get(task) || 0) <= time && count > bestCount) {
        best = task;
        bestCount = count;
      }
    }
    if (best === null) {
      time++;
    } else {
      freq.set(best, freq.get(best) - 1);
      nextFree.set(best, time + n + 1);
      remaining--;
      time++;
    }
  }
  return time;
}""",
        complexity="Time: O(T * U) | Space: O(U)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function leastInterval(tasks, n) {
  if (tasks.length === 0) return 0;
  const freq = new Map();
  for (const t of tasks) freq.set(t, (freq.get(t) || 0) + 1);
  let maxFreq = 0;
  let maxCount = 0;
  for (const c of freq.values()) {
    if (c > maxFreq) {
      maxFreq = c;
      maxCount = 1;
    } else if (c === maxFreq) {
      maxCount++;
    }
  }
  const slots = (maxFreq - 1) * (n + 1) + maxCount;
  return slots > tasks.length ? slots : tasks.length;
}""",
        complexity="Time: O(T) | Space: O(U)",
        language="javascript",
    ),
    topic="heap",
    difficulty="Medium",
    pattern="heap / Frequency math",
    time_limit_ms=2000,
    seed=42,
    title="Task Scheduler",
    slug="task-scheduler",
    editorial={
        "approach": "Count each task type. The most frequent type dictates the frame: maxFreq - 1 full blocks of width n + 1, plus one slot per type tied at maxFreq. The answer is that frame size or the task count, whichever is larger.",
        "why_optimal": "Frequency counting answers in one pass instead of simulating every time unit and scanning all types per tick. __RUNTIMES__",
        "pitfalls": "Every type tied at the maximum frequency contributes a final slot, not just one of them. When tasks are plentiful the frame fills completely and the answer is simply the task count.",
    },
    reading_links=["https://en.wikipedia.org/wiki/Greedy_algorithm"],
    hints=[
        "The most frequent task type determines the minimum possible schedule length.",
        "Picture maxFreq - 1 blocks of width n + 1, each opened by one copy of the busiest task.",
        "Types tied at the maximum each claim one extra slot in the final partial block.",
    ],
)

spec_keys_rooms = ProblemSpec(
    signature="function canVisitAllRooms(rooms: number[][])",
    statement="""# Keys and Rooms

There are `n` rooms numbered `0` to `n - 1`, described by `rooms` where `rooms[i]` lists the keys found inside room `i`. Every key is a room number that its door opens.

Starting with room `0` unlocked and all other rooms locked, a key collected from any visited room may be used to open its room. Return `true` when every room becomes reachable this way, else `false`.

A single room is trivially fully visitable.

Constraints: `1 <= rooms.length <= 20` and `0 <= rooms[i] <= 19`.
""",
    brute_force=Algorithm(
        """function canVisitAllRooms(rooms) {
  const n = rooms.length;
  const visited = new Set([0]);
  let changed = true;
  while (changed) {
    changed = false;
    for (let r = 0; r < n; r++) {
      if (!visited.has(r)) continue;
      const keys = rooms[r] || [];
      for (let k = 0; k < keys.length; k++) {
        const dest = keys[k];
        if (dest >= 0 && dest < n && !visited.has(dest)) {
          visited.add(dest);
          changed = true;
        }
      }
    }
  }
  return visited.size === n;
}""",
        complexity="Time: O(n * (n + E)) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function canVisitAllRooms(rooms) {
  const n = rooms.length;
  const seen = new Set([0]);
  const stack = [0];
  while (stack.length > 0) {
    const room = stack.pop();
    const keys = rooms[room] || [];
    for (let k = 0; k < keys.length; k++) {
      const dest = keys[k];
      if (dest >= 0 && dest < n && !seen.has(dest)) {
        seen.add(dest);
        stack.push(dest);
      }
    }
  }
  return seen.size === n;
}""",
        complexity="Time: O(n + E) | Space: O(n)",
        language="javascript",
    ),
    topic="graphs",
    difficulty="Easy",
    pattern="graphs / DFS reachability",
    time_limit_ms=2000,
    seed=42,
    title="Keys and Rooms",
    slug="keys-and-rooms",
    editorial={
        "approach": "Walk outward from room 0 along collected keys with a stack, marking each newly opened room. When the walk ends, every room is reachable exactly when all marks are set.",
        "why_optimal": "One DFS follows each key once instead of re-scanning every visited room until no change remains. __RUNTIMES__",
        "pitfalls": "Keys outside 0..n-1 are invalid doors and must be ignored. Duplicate keys and the starting room's self-keys must not cause revisits or infinite loops.",
    },
    reading_links=["https://en.wikipedia.org/wiki/Depth-first_search"],
    hints=[
        "Room 0 is the only entry point; every other room must be reached through collected keys.",
        "Treat rooms as graph nodes and keys as directed edges from room 0 outward.",
        "One DFS from room 0 visits exactly the reachable rooms; compare its count with n.",
    ],
)

spec_all_paths = ProblemSpec(
    signature="function allPathsSourceTarget(graph: number[][])",
    statement="""# All Paths from Source to Target

A directed acyclic graph with `n` nodes is given as an adjacency list `graph`, where `graph[i]` lists the neighbours of node `i` in ascending order and every edge points from a smaller node to a larger one.

Enumerate every directed path from node `0` to node `n - 1`. Each path is written as the sequence of visited node ids. Return the full list of paths sorted lexicographically.

A single direct edge yields exactly one path `[[0, 1]]`.

Constraints: `2 <= graph.length <= 6` and `0 <= graph[i] <= 5`.
""",
    brute_force=Algorithm(
        """function allPathsSourceTarget(graph) {
  const target = graph.length - 1;
  const res = [];
  const queue = [[0]];
  while (queue.length > 0) {
    const path = queue.shift();
    const node = path[path.length - 1];
    if (node === target) {
      res.push(path.slice());
      continue;
    }
    const nexts = (graph[node] || []).slice().sort((a, b) => a - b);
    for (let i = 0; i < nexts.length; i++) {
      if (path.indexOf(nexts[i]) === -1) queue.push(path.concat([nexts[i]]));
    }
  }
  res.sort((a, b) => {
    const m = Math.min(a.length, b.length);
    for (let i = 0; i < m; i++) {
      if (a[i] !== b[i]) return a[i] - b[i];
    }
    return a.length - b.length;
  });
  return res;
}""",
        complexity="Time: O(2^n * n) | Space: O(2^n * n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function allPathsSourceTarget(graph) {
  const target = graph.length - 1;
  const res = [];
  const path = [0];
  function dfs(node) {
    if (node === target) {
      res.push(path.slice());
      return;
    }
    const nexts = (graph[node] || []).slice().sort((a, b) => a - b);
    for (let i = 0; i < nexts.length; i++) {
      if (path.indexOf(nexts[i]) !== -1) continue;
      path.push(nexts[i]);
      dfs(nexts[i]);
      path.pop();
    }
  }
  dfs(0);
  res.sort((a, b) => {
    const m = Math.min(a.length, b.length);
    for (let i = 0; i < m; i++) {
      if (a[i] !== b[i]) return a[i] - b[i];
    }
    return a.length - b.length;
  });
  return res;
}""",
        complexity="Time: O(2^n * n) | Space: O(n + P * n)",
        language="javascript",
    ),
    topic="graphs",
    difficulty="Medium",
    pattern="graphs / DAG DFS",
    time_limit_ms=2000,
    seed=42,
    title="All Paths from Source to Target",
    slug="all-paths-from-source-to-target",
    editorial={
        "approach": "Backtrack from node 0, extending the current path along each neighbour in order and recording a copy whenever the target is reached. Sort the collected paths lexicographically.",
        "why_optimal": "DFS reuses one path buffer with push and pop instead of copying a prefix for every queue entry, cutting queue memory while enumerating the same paths. __RUNTIMES__",
        "pitfalls": "Record a copy of the path on arrival, not a reference to the live buffer. Sort neighbours during traversal and sort the final list so output order is deterministic.",
    },
    reading_links=["https://en.wikipedia.org/wiki/Depth-first_search"],
    hints=[
        "Grow paths forward from node 0, one neighbour at a time.",
        "Keep a single current path: push before recursing and pop when returning.",
        "Copy the path when it reaches the target, then sort all paths lexicographically.",
    ],
)

spec_redundant = ProblemSpec(
    signature="function findRedundantConnection(edges: number[][])",
    statement="""# Redundant Connection

A connected undirected graph with `n` labelled nodes `1..n` began as a tree with `n - 1` edges; one extra edge was then appended, creating exactly one cycle. The input `edges` lists all `n` edges in the order they were added.

Return the extra edge `[u, v]` whose removal restores a tree. Because exactly one cycle exists, this is the last edge in input order whose endpoints are already connected by the earlier edges.

Constraints: `3 <= edges.length <= 15` and `1 <= edges[i] <= 8`. Each edge joins two distinct node labels.
""",
    brute_force=Algorithm(
        """function findRedundantConnection(edges) {
  const adj = new Map();
  function addEdge(u, v) {
    if (!adj.has(u)) adj.set(u, []);
    if (!adj.has(v)) adj.set(v, []);
    adj.get(u).push(v);
    adj.get(v).push(u);
  }
  function connected(u, v) {
    const seen = new Set([u]);
    const queue = [u];
    let head = 0;
    while (head < queue.length) {
      const node = queue[head++];
      if (node === v) return true;
      const nexts = adj.get(node) || [];
      for (let i = 0; i < nexts.length; i++) {
        if (!seen.has(nexts[i])) {
          seen.add(nexts[i]);
          queue.push(nexts[i]);
        }
      }
    }
    return false;
  }
  for (let i = 0; i < edges.length; i++) {
    const u = edges[i][0];
    const v = edges[i][1];
    if (connected(u, v)) return [u, v];
    addEdge(u, v);
  }
  return [];
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function findRedundantConnection(edges) {
  let maxNode = 0;
  for (let i = 0; i < edges.length; i++) {
    if (edges[i][0] > maxNode) maxNode = edges[i][0];
    if (edges[i][1] > maxNode) maxNode = edges[i][1];
  }
  const parent = [];
  for (let i = 0; i <= maxNode; i++) parent[i] = i;
  function find(x) {
    while (parent[x] !== x) {
      parent[x] = parent[parent[x]];
      x = parent[x];
    }
    return x;
  }
  for (let i = 0; i < edges.length; i++) {
    const u = edges[i][0];
    const v = edges[i][1];
    const ru = find(u);
    const rv = find(v);
    if (ru === rv) return [u, v];
    parent[ru] = rv;
  }
  return [];
}""",
        complexity="Time: O(n α(n)) | Space: O(n)",
        language="javascript",
    ),
    topic="graphs",
    difficulty="Medium",
    pattern="graphs / Union-find",
    time_limit_ms=2000,
    seed=42,
    title="Redundant Connection",
    slug="redundant-connection",
    editorial={
        "approach": "Scan edges in input order while maintaining disjoint sets. The first edge joining two vertices already in the same set closes the single cycle and is the redundant one.",
        "why_optimal": "Union-find with path halving answers each connectivity query in amortized constant time instead of re-running BFS over the growing graph. __RUNTIMES__",
        "pitfalls": "Process edges strictly in input order: the answer is the last cycle-closing edge, not the first cycle found under another order. Union by attaching one root to the other keeps all vertices in a consistent set.",
    },
    reading_links=["https://en.wikipedia.org/wiki/Disjoint-set_data_structure"],
    hints=[
        "Add edges one at a time in the given order and watch for the edge that first closes a cycle.",
        "Two vertices are already connected exactly when they share the same set representative.",
        "Union the endpoints of every non-cycle edge so later checks see the growing components.",
    ],
)


def _valid_word(rng: random.Random, length: int) -> str:
    return "".join(rng.choice("abcde") for _ in range(length))


def _valid_ladder_inputs(rng: random.Random) -> list[list[Any]]:
    out: list[list[Any]] = [
        [["hit", "cog"], "hit", "cog"],
        [["hit", "hot", "dot", "dog", "cog"], "hit", "cog"],
        [["hot", "dot", "dog", "cog"], "hit", "cog"],
        [["a", "b", "c"], "a", "c"],
        [["hot", "dot", "dog"], "hot", "hot"],
    ]
    for _ in range(17):
        length = rng.randint(1, 4)
        begin = _valid_word(rng, length)
        words = {_valid_word(rng, length) for _ in range(rng.randint(1, 6))}
        words.add(begin)
        if rng.random() < 0.6:
            end = _valid_word(rng, length)
            words.add(end)
        else:
            end = rng.choice(sorted(words))
        word_list = sorted(words)
        if len(word_list) > 20:
            word_list = word_list[:20]
            if end not in word_list:
                word_list[-1] = end
        out.append([word_list, begin, end])
    # Reorder to (beginWord, endWord, wordList) to match signatures.
    return [[b, e, w] for [w, b, e] in out]


def _valid_grid(rng: random.Random, rows: int, cols: int, lo: int, hi: int) -> list[list[int]]:
    return [[rng.randint(lo, hi) for _ in range(cols)] for _ in range(rows)]


def _valid_board(rng: random.Random, rows: int, cols: int) -> list[list[str]]:
    return [[rng.choice(["X", "O"]) for _ in range(cols)] for _ in range(rows)]


_CELEBS = ["A", "B", "C", "D", "E", "F", "G"]


def _valid_tasks(rng: random.Random, count: int, n: int) -> tuple[list[str], int]:
    pool = _CELEBS[: rng.randint(1, 4)]
    tasks = [rng.choice(pool) for _ in range(count)]
    return tasks, n


def _valid_rooms(rng: random.Random, n: int) -> list[list[int]]:
    rooms: list[list[int]] = []
    for i in range(n):
        keys = []
        for _ in range(rng.randint(0, 3)):
            keys.append(rng.randint(0, n - 1))
        rooms.append(sorted(set(keys)))
    return rooms


def _valid_dag(rng: random.Random, n: int) -> list[list[int]]:
    graph = [[] for _ in range(n)]
    for i in range(n - 1):
        for j in range(i + 1, n):
            if rng.random() < 0.4:
                graph[i].append(j)
    if not any(n - 1 in row for row in graph):
        src = rng.randint(0, n - 2)
        graph[src].append(n - 1)
    for row in graph:
        row[:] = sorted(set(row))
    return graph


def _valid_tree_plus_one(rng: random.Random, n: int) -> list[list[int]]:
    parent = list(range(n + 1))
    edges: list[list[int]] = []
    for node in range(2, n + 1):
        other = rng.randint(1, node - 1)
        edges.append([other, node])
    a = rng.randint(1, n)
    b = rng.randint(1, n)
    while b == a:
        b = rng.randint(1, n)
    edges.append([a, b] if rng.random() < 0.5 else [b, a])
    rng.shuffle(edges)
    return edges


async def _build_paf_problem(spec: ProblemSpec) -> Any:
    """Run stock PAF verification, then swap in bespoke valid inputs where needed."""
    problem = await build_verified_problem(spec)
    needs_custom = spec.slug in {
        "rotting-oranges",
        "surrounded-regions",
        "pacific-atlantic-water-flow",
        "word-ladder",
        "kth-largest-element-in-an-array",
        "last-stone-weight",
        "task-scheduler",
        "keys-and-rooms",
        "all-paths-from-source-to-target",
        "redundant-connection",
    }
    if not needs_custom:
        return problem
    rng = _rng()
    custom_inputs: list[list[Any]] = []
    if spec.slug == "rotting-oranges":
        custom_inputs = [
            [[[2, 1, 1], [1, 1, 0], [0, 1, 1]]],
            [[[2, 1, 1], [0, 1, 1], [1, 0, 1]]],
            [[[0, 2]]],
            [[[1, 1, 1], [1, 1, 1]]],
            [[[2, 2], [2, 2]]],
            [[[0, 0], [0, 0]]],
            [[_valid_grid(rng, 3, 3, 0, 2)]],
            [[_valid_grid(rng, 2, 4, 0, 2)]],
            [[_valid_grid(rng, 4, 2, 0, 2)]],
            [[_valid_grid(rng, 1, 5, 0, 2)]],
            [[_valid_grid(rng, 5, 1, 0, 2)]],
            [[_valid_grid(rng, 4, 4, 0, 2)]],
            [[_valid_grid(rng, 2, 2, 0, 2)]],
            [[_valid_grid(rng, 3, 5, 0, 2)]],
        ]
    elif spec.slug == "surrounded-regions":
        custom_inputs = [
            [[["X", "X", "X", "X"], ["X", "O", "O", "X"], ["X", "X", "O", "X"], ["X", "O", "X", "X"]]],
            [[["X", "X", "X"], ["X", "O", "X"], ["X", "X", "X"]]],
            [[["O"]]],
            [[["X"]]],
            [[["O", "O", "O"], ["O", "O", "O"], ["O", "O", "O"]]],
            [[["X", "O"], ["O", "X"]]],
            [[_valid_board(rng, 3, 3)]],
            [[_valid_board(rng, 2, 4)]],
            [[_valid_board(rng, 4, 4)]],
            [[_valid_board(rng, 1, 4)]],
            [[_valid_board(rng, 4, 1)]],
            [[_valid_board(rng, 5, 5)]],
        ]
    elif spec.slug == "pacific-atlantic-water-flow":
        custom_inputs = [
            [[[1, 2, 2, 3, 5], [3, 2, 3, 4, 4], [2, 4, 5, 3, 1], [6, 7, 1, 4, 5], [5, 1, 1, 2, 4]]],
            [[[5]]],
            [[[2, 2], [2, 2]]],
            [[[1, 2], [3, 4]]],
            [[[4, 3], [2, 1]]],
            [[_valid_grid(rng, 3, 3, 0, 5)]],
            [[_valid_grid(rng, 2, 4, 0, 5)]],
            [[_valid_grid(rng, 4, 4, 0, 5)]],
            [[_valid_grid(rng, 1, 4, 0, 5)]],
            [[_valid_grid(rng, 5, 5, 0, 5)]],
            [[_valid_grid(rng, 3, 5, 0, 5)]],
            [[_valid_grid(rng, 2, 2, 0, 5)]],
        ]
    elif spec.slug == "word-ladder":
        custom_inputs = _valid_ladder_inputs(rng)
    elif spec.slug == "kth-largest-element-in-an-array":
        custom_inputs = [
            [[3, 2, 1, 5, 6, 4], 2],
            [[3, 2, 3, 1, 2, 4, 5, 5, 6], 4],
            [[1], 1],
            [[2, 2, 2], 2],
            [[5, 5, 4, 4, 3], 5],
            [[7, 7, 7, 7], 1],
        ]
        for _ in range(16):
            count = rng.randint(1, 12)
            nums = [rng.randint(-10, 10) for _ in range(count)]
            k = rng.randint(1, count)
            custom_inputs.append([nums, k])
    elif spec.slug == "last-stone-weight":
        custom_inputs = [
            [[2, 7, 4, 1, 8, 1]],
            [[1]],
            [[2, 2]],
            [[5, 5, 5]],
            [[10, 10, 10, 10]],
            [[1, 2, 3, 4, 5]],
        ]
        for _ in range(16):
            count = rng.randint(1, 10)
            stones = [rng.randint(1, 20) for _ in range(count)]
            custom_inputs.append([stones])
    elif spec.slug == "task-scheduler":
        params = [("A", 3), ("B", 1), ("C", 2), ("D", 1), ("E", 2), ("F", 3)]
        custom_inputs = [
            [["A", "A", "A", "B", "B", "B"], 2],
            [["A", "A", "A", "B", "B", "B"], 0],
            [["A", "A", "A", "A", "A", "A", "B", "C", "D", "E", "F", "G"], 2],
            [["A"], 3],
            [["A", "B", "C"], 5],
            [["A", "A", "B", "B"], 1],
        ]
        for letter, n in params:
            for _ in range(2):
                tasks, cool = _valid_tasks(rng, rng.randint(1, 12), n)
                custom_inputs.append([tasks, cool])
        tasks, cool = _valid_tasks(rng, 6, 2)
        custom_inputs.append([tasks, cool])
        tasks, cool = _valid_tasks(rng, 9, 0)
        custom_inputs.append([tasks, cool])
    elif spec.slug == "keys-and-rooms":
        custom_inputs = [
            [[[1], [2], [3], []]],
            [[[1, 3], [3, 0, 1], [2], [0]]],
            [[[]]],
            [[[], [0]]],
            [[[1], [], [0]]],
            [[[1], [0], [3], []]],
        ]
        for _ in range(16):
            custom_inputs.append([_valid_rooms(rng, rng.randint(1, 6))])
    elif spec.slug == "all-paths-from-source-to-target":
        custom_inputs = [
            [[[1], []]],
            [[[1, 2], [3], [3], []]],
            [[[4, 3, 1], [3], [4], [4], []]],
            [[[1], [2], [3], []]],
            [[[1, 2, 3], [], [], []]],
        ]
        for _ in range(17):
            custom_inputs.append([_valid_dag(rng, rng.randint(2, 6))])
    elif spec.slug == "redundant-connection":
        custom_inputs = [
            [[[1, 2], [1, 3], [2, 3]]],
            [[[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]]],
            [[[1, 2], [1, 3], [3, 4], [4, 5], [2, 5]]],
            [[[3, 4], [1, 2], [2, 4], [1, 3]]],
        ]
        for _ in range(18):
            custom_inputs.append([_valid_tree_plus_one(rng, rng.randint(3, 8))])

    bespoke = await _build_custom_cases(
        spec, spec.brute_force.code, spec.optimal.code, custom_inputs
    )
    stock_inputs = generate_inputs(spec, random_cases=16, stress_cases=4)
    generated = await build_verified_problem(spec)
    problem.report.test_cases = bespoke + generated.report.test_cases
    problem.report.brute_force_case_runtimes_ms = []
    problem.report.optimal_case_runtimes_ms = []
    merged: list[dict] = []
    seen: set[str] = set()
    for case in problem.report.test_cases:
        fingerprint = json.dumps(case["input"], sort_keys=True, separators=(",", ":"))
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        merged.append(case)
    merged[0]["isSample"] = True
    merged[1]["isSample"] = True
    for case in merged[2:]:
        case["isSample"] = False
    problem.report.test_cases = merged
    problem.data["testCases"] = merged
    problem.data["pafVerification"]["generatedCaseCount"] = len(merged)
    examples = [
        {
            "input": ", ".join(
                f"{parameter.name} = {json.dumps(value, ensure_ascii=False)}"
                for parameter, value in zip(
                    spec.parsed_signature.parameters, case["input"], strict=True
                )
            ),
            "output": json.dumps(case["expected"], ensure_ascii=False),
            "explanation": "Generated from the verified optimal implementation.",
        }
        for case in merged[:2]
    ]
    problem.data["examples"] = examples
    return problem


SPECS: list[ProblemSpec] = [
    spec_rotting_oranges,
    spec_surrounded_regions,
    spec_pacific_atlantic,
    spec_word_ladder,
    spec_kth_largest,
    spec_last_stone,
    spec_task_scheduler,
    spec_keys_rooms,
    spec_all_paths,
    spec_redundant,
]


def main() -> None:
    output_dir = REPO_ROOT / "content" / "problems"
    print(f"Authoring and verifying {len(SPECS)} Batch-2C problems with PAF...")
    for idx, spec in enumerate(SPECS, 1):
        print(f"[{idx}/{len(SPECS)}] Generating {spec.slug} ({spec.difficulty})...")
        problem = asyncio.run(_build_paf_problem(spec))
        out_file = problem.write_to(output_dir)
        print(
            f"  ✓ {problem.data['slug']}: {problem.report.total_cases} cases verified | "
            f"Brute: {problem.report.brute_force_runtime_ms:.2f}ms | "
            f"Optimal: {problem.report.optimal_runtime_ms:.2f}ms -> {out_file.name}"
        )
    print("\nAll 10 Batch-2C problems generated and PAF-verified successfully.")


if __name__ == "__main__":
    main()
