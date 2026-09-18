"""Authoring and verification script for Batch 1C: Stack / Strings problems."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
api_path = str(REPO_ROOT / "apps" / "api")
if api_path not in sys.path:
    sys.path.insert(0, api_path)

_FIELD_ALPHABET = "abcxyz"
_NUMBERS_POOL = [str(n) for n in range(5, 301)]
_TOKENS_POOL = ["7", "12", "-4", "9", "+", "-", "*", "/"]

from content.generators.paf import (
    Algorithm,
    ProblemSpec,
    build_problem,
    build_verified_problem,
)
from content.generators.paf.inputs import generate_inputs


def _valid_baseball_ops(rng: Any, count: int) -> list[str]:
    ops: list[str] = []
    record: list[int] = []
    for _ in range(count):
        choices = ["int"]
        if record:
            choices += ["C", "int"]
            if len(record) == 1:
                choices += ["D", "+"]
            else:
                choices += ["D", "D", "+", "+"]
        kind = rng.choice(choices)
        if kind == "C":
            record.pop()
            ops.append("C")
        elif kind == "D":
            record.append(record[-1] * 2)
            ops.append("D")
        elif kind == "+":
            top = record[-1] if record else 0
            below = record[-2] if len(record) > 1 else 0
            record.append(top + below)
            ops.append("+")
        else:
            value = rng.randint(-30, 30)
            record.append(value)
            ops.append(str(value))
    return ops


def _valid_rpn_tokens(rng: Any, operand_count: int) -> list[str]:
    operands = [rng.choice(_NUMBERS_POOL) for _ in range(operand_count)]
    operators = [rng.choice(["+", "-", "*", "/"]) for _ in range(operand_count - 1)]
    tokens: list[str] = [rng.choice(operands)]
    remaining_operands = operands[1:]
    remaining_ops = operators[:]
    rng.shuffle(remaining_ops)
    depth = 1
    while remaining_operands or remaining_ops:
        use_operand = bool(remaining_operands) and (
            depth < 2 or not remaining_ops or rng.random() < 0.5
        )
        if use_operand:
            tokens.append(remaining_operands.pop(0))
            depth += 1
        else:
            tokens.append(remaining_ops.pop(0))
            depth -= 1
    return tokens


async def _execute_js(code: str, function_name: str, cases: list[dict]) -> Any:
    from app.services.judge import execute_code

    return await execute_code(
        language="javascript",
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

spec_make_good = ProblemSpec(
    signature="function makeGood(s: string)",
    statement="""# Tidy the String

Given a string `s`, repeatedly delete any adjacent pair of characters that show the same alphabet letter in opposite cases (one uppercase, the other lowercase). Each deletion may bring two new neighbours together, which must then be examined again.

Return the shortest string reachable once no such clashing pair remains anywhere in it.

Constraints: `1 <= s.length <= 100`.
""",
    brute_force=Algorithm(
        """function makeGood(s) {
  const chars = s.split('');
  let changed = true;
  while (changed) {
    changed = false;
    for (let i = 0; i < chars.length - 1; i++) {
      const a = chars[i];
      const b = chars[i + 1];
      if (a !== b && a.toLowerCase() === b.toLowerCase()) {
        chars.splice(i, 2);
        changed = true;
        break;
      }
    }
  }
  return chars.join('');
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function makeGood(s) {
  const stack = [];
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    const top = stack[stack.length - 1];
    if (stack.length > 0 && top !== ch && top.toLowerCase() === ch.toLowerCase()) {
      stack.pop();
    } else {
      stack.push(ch);
    }
  }
  return stack.join('');
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="stack",
    difficulty="Easy",
    pattern="stack / Case-cancel",
    time_limit_ms=2000,
    seed=42,
    title="Tidy the String",
    slug="make-the-string-great",
    editorial={
        "approach": 'Scan once, cancelling opposite-case neighbours on a stack.',
        "why_optimal": 'Each character is pushed and popped at most once, so the single pass is linear with a stack bounded by the input.',
        "pitfalls": 'Calling toLowerCase on non-letters is safe here, but do not treat digits as cancellable pairs.',
    },
    reading_links=['https://en.wikipedia.org/wiki/Stack_(abstract_data_type)'],
    hints=['Push characters and pop when the top and the new letter match ignoring case.', 'Only opposite cases cancel; same-case pairs stay.', 'The stack contents at the end spell the answer.'],
)

spec_remove_duplicates = ProblemSpec(
    signature="function removeDuplicatesString(s: string)",
    statement="""# Collapse Adjacent Duplicates

Given a string `s`, scan it from left to right: whenever two equal characters stand side by side, delete both of them at once. Deleting a pair can join two previously separated characters into a fresh adjacent pair, which must then collapse as well.

Return the final string once no two neighbours are equal.

Constraints: `1 <= s.length <= 100`.
""",
    brute_force=Algorithm(
        """function removeDuplicatesString(s) {
  const chars = s.split('');
  let changed = true;
  while (changed) {
    changed = false;
    for (let i = 0; i < chars.length - 1; i++) {
      if (chars[i] === chars[i + 1]) {
        chars.splice(i, 2);
        changed = true;
        break;
      }
    }
  }
  return chars.join('');
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function removeDuplicatesString(s) {
  const stack = [];
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (stack.length > 0 && stack[stack.length - 1] === ch) {
      stack.pop();
    } else {
      stack.push(ch);
    }
  }
  return stack.join('');
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="stack",
    difficulty="Easy",
    pattern="stack / Collapse",
    time_limit_ms=2000,
    seed=42,
    title="Collapse Adjacent Duplicates",
    slug="remove-all-adjacent-duplicates",
    editorial={
        "approach": 'Scan once, cancelling equal neighbours on a stack.',
        "why_optimal": 'Each character is pushed and popped at most once, so the single pass is linear with a stack bounded by the input.',
        "pitfalls": 'Compare strict equality only; do not normalise case for this task.',
    },
    reading_links=['https://en.wikipedia.org/wiki/Stack_(abstract_data_type)'],
    hints=['Push characters and pop when the top equals the new character.', 'A pop can expose a fresh equal pair with the next character.', 'The stack contents at the end spell the answer.'],
)

spec_baseball = ProblemSpec(
    signature="function calPoints(operations: string[])",
    statement="""# Baseball Scorebook

You are keeping score for a baseball game with a record of round scores and four kinds of entries in `operations`:

- An integer string `x` records a new round worth `x` points.
- `"C"` voids the previous round, removing it from the record.
- `"D"` records a new round worth double the previous round's score.
- `"+"` records a new round worth the sum of the previous two rounds' scores.

Every `"C"`, `"D"`, and `"+"` entry is guaranteed a valid record to work with. Return the total of all rounds left in the record.

Constraints: `1 <= operations.length <= 100` and each integer entry satisfies `-30 <= operations[i] <= 30`.
""",
    brute_force=Algorithm(
        """function calPoints(operations) {
  const record = [];
  for (let i = 0; i < operations.length; i++) {
    const op = operations[i];
    if (op === 'C') {
      if (record.length > 0) {
        record.splice(record.length - 1, 1);
      }
    } else if (op === 'D') {
      const prev = record.length > 0 ? record[record.length - 1] : 0;
      record.push(prev * 2);
    } else if (op === '+') {
      const a = record.length > 0 ? record[record.length - 1] : 0;
      const b = record.length > 1 ? record[record.length - 2] : 0;
      record.push(a + b);
    } else {
      record.push(Number(op));
    }
  }
  let total = 0;
  for (let i = 0; i < record.length; i++) {
    total += record[i];
  }
  return total;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function calPoints(operations) {
  const stack = [];
  for (let i = 0; i < operations.length; i++) {
    const op = operations[i];
    switch (op) {
      case 'C':
        if (stack.length > 0) {
          stack.pop();
        }
        break;
      case 'D': {
        const prev = stack.length > 0 ? stack[stack.length - 1] : 0;
        stack.push(prev * 2);
        break;
      }
      case '+': {
        const a = stack.length > 0 ? stack[stack.length - 1] : 0;
        const b = stack.length > 1 ? stack[stack.length - 2] : 0;
        stack.push(a + b);
        break;
      }
      default:
        stack.push(Number(op));
        break;
    }
  }
  return stack.reduce((total, value) => total + value, 0);
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="stack",
    difficulty="Easy",
    pattern="stack / Record-ops",
    time_limit_ms=2000,
    seed=42,
    title="Baseball Scorebook",
    slug="baseball-game",
    editorial={
        "approach": 'Replay the operations on a stack of live round scores.',
        "why_optimal": 'Each operation touches only the stack top, so the replay is linear in the number of operations.',
        "pitfalls": 'Pop only when the record is non-empty; the statement guarantees valid C/D/+ entries.',
    },
    reading_links=['https://en.wikipedia.org/wiki/Stack_(abstract_data_type)'],
    hints=['Keep live round scores on a stack.', 'Translate C to pop, D to double the top, and + to sum the top two.', 'Add every surviving round at the end.'],
)

spec_next_greater = ProblemSpec(
    signature="function nextGreaterElement(nums1: number[], nums2: number[])",
    statement="""# Next Greater Element I

You are given two arrays `nums1` and `nums2` where every value of `nums1` also appears in `nums2`.

For each value `x` in `nums1`, find the first position where `x` occurs in `nums2`, then report the first value strictly greater than `x` that appears after that position. When no larger value follows, report `-1` for that entry.

Return an array holding one answer per entry of `nums1`, in order.

Constraints: `1 <= nums1.length <= 20`, `1 <= nums2.length <= 50`, `-100 <= nums1[i] <= 100`, and `-100 <= nums2[i] <= 100`.
""",
    brute_force=Algorithm(
        """function nextGreaterElement(nums1, nums2) {
  const answers = [];
  for (let i = 0; i < nums1.length; i++) {
    let found = -1;
    for (let j = 0; j < nums2.length; j++) {
      if (nums2[j] === nums1[i]) {
        for (let k = j + 1; k < nums2.length; k++) {
          if (nums2[k] > nums2[j]) {
            found = nums2[k];
            break;
          }
        }
        break;
      }
    }
    answers.push(found);
  }
  return answers;
}""",
        complexity="Time: O(n * m) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function nextGreaterElement(nums1, nums2) {
  const nextByIndex = new Array(nums2.length).fill(-1);
  const stack = [];
  for (let i = 0; i < nums2.length; i++) {
    while (stack.length > 0 && nums2[i] > nums2[stack[stack.length - 1]]) {
      nextByIndex[stack.pop()] = nums2[i];
    }
    stack.push(i);
  }
  const firstPos = new Map();
  for (let i = 0; i < nums2.length; i++) {
    if (!firstPos.has(nums2[i])) {
      firstPos.set(nums2[i], i);
    }
  }
  const answers = [];
  for (let i = 0; i < nums1.length; i++) {
    if (firstPos.has(nums1[i])) {
      answers.push(nextByIndex[firstPos.get(nums1[i])]);
    } else {
      answers.push(-1);
    }
  }
  return answers;
}""",
        complexity="Time: O(n + m) | Space: O(m)",
        language="javascript",
    ),
    topic="stack",
    difficulty="Easy",
    pattern="stack / Monotonic map",
    time_limit_ms=2000,
    seed=42,
    title="Next Greater Entry",
    slug="next-greater-element-i",
    editorial={
        "approach": 'Precompute next-greater positions in nums2 with a decreasing stack, then answer each query by lookup.',
        "why_optimal": 'The scan pushes and pops each index once, so precomputation is linear and each query is constant time.',
        "pitfalls": 'Map each query value to its first occurrence in nums2 before looking up the answer.',
    },
    reading_links=['https://en.wikipedia.org/wiki/Stack_(abstract_data_type)'],
    hints=['Scan nums2 once with a decreasing stack to map each value to its next greater entry.', 'Answer each nums1 value by table lookup, not by rescanning.', 'Write -1 when the table holds no greater value.'],
)

spec_rpn = ProblemSpec(
    signature="function evalRPN(tokens: string[])",
    statement="""# Evaluate Postfix Notation

Given an array of strings `tokens` written in postfix order, evaluate the expression it denotes and return the integer result.

Each token is either a decimal integer (possibly negative) or one of the four operators `+`, `-`, `*`, `/`. Every operator consumes its two nearest preceding values: the earlier value is the left operand and the later value is the right operand. Division between integers truncates toward zero.

Constraints: `1 <= tokens.length <= 100`.
""",
    brute_force=Algorithm(
        """function evalRPN(tokens) {
  const items = tokens.slice();
  function isOp(token) {
    return token === '+' || token === '-' || token === '*' || token === '/';
  }
  while (items.length > 1) {
    let opIdx = -1;
    for (let i = 0; i < items.length; i++) {
      if (isOp(items[i])) {
        opIdx = i;
        break;
      }
    }
    if (opIdx < 1) {
      break;
    }
    const a = Number(items[opIdx - 2]);
    const b = Number(items[opIdx - 1]);
    const op = items[opIdx];
    let value = 0;
    if (op === '+') {
      value = a + b;
    } else if (op === '-') {
      value = a - b;
    } else if (op === '*') {
      value = a * b;
    } else {
      value = Math.trunc(a / b);
    }
    items.splice(opIdx - 2, 3, String(value));
  }
  return Number(items[items.length - 1]);
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function evalRPN(tokens) {
  const stack = [];
  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i];
    if (token === '+' || token === '-' || token === '*' || token === '/') {
      const b = stack.length > 0 ? stack.pop() : 0;
      const a = stack.length > 0 ? stack.pop() : 0;
      let value = 0;
      if (token === '+') {
        value = a + b;
      } else if (token === '-') {
        value = a - b;
      } else if (token === '*') {
        value = a * b;
      } else {
        value = Math.trunc(a / b);
      }
      stack.push(value);
    } else {
      stack.push(Number(token));
    }
  }
  return stack.pop();
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="stack",
    difficulty="Medium",
    pattern="stack / Postfix eval",
    time_limit_ms=2000,
    seed=42,
    title="Evaluate Postfix Notation",
    slug="evaluate-reverse-polish-notation",
    editorial={
        "approach": 'Evaluate postfix tokens with an operand stack, applying each operator to its two topmost values.',
        "why_optimal": 'Each token is pushed and popped once, so evaluation is linear in the token count.',
        "pitfalls": 'Apply division with truncation toward zero and keep operand order as second-top operator top.',
    },
    reading_links=['https://en.wikipedia.org/wiki/Reverse_Polish_notation'],
    hints=['Push numbers and evaluate each operator against the top two stack values.', 'Subtract and divide in second-top operator top order.', 'Truncate division toward zero.'],
)

spec_daily = ProblemSpec(
    signature="function dailyTemperatures(temperatures: number[])",
    statement="""# Daily Temperatures

Given an array `temperatures` where `temperatures[i]` is the temperature of day `i`, compute for every day how many days pass before a strictly warmer temperature occurs. When no future day is warmer, record `0` for that day.

Return an array of the same length holding one waiting time per day.

Constraints: `1 <= temperatures.length <= 100` and `30 <= temperatures[i] <= 100`.
""",
    brute_force=Algorithm(
        """function dailyTemperatures(temperatures) {
  const n = temperatures.length;
  const waits = new Array(n).fill(0);
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      if (temperatures[j] > temperatures[i]) {
        waits[i] = j - i;
        break;
      }
    }
  }
  return waits;
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function dailyTemperatures(temperatures) {
  const n = temperatures.length;
  const waits = new Array(n).fill(0);
  const stack = [];
  for (let i = 0; i < n; i++) {
    while (stack.length > 0 && temperatures[i] > temperatures[stack[stack.length - 1]]) {
      const prev = stack.pop();
      waits[prev] = i - prev;
    }
    stack.push(i);
  }
  return waits;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="stack",
    difficulty="Medium",
    pattern="stack / Next greater",
    time_limit_ms=2000,
    seed=42,
    title="Waiting for Warmer Days",
    slug="daily-temperatures",
    editorial={
        "approach": 'Walk days forward, keeping indices with unanswered waits on a decreasing stack.',
        "why_optimal": 'Each index is pushed and popped at most once, so the scan is linear with a stack bounded by the input.',
        "pitfalls": 'Record zero for days with no warmer future day; never default to the end of the array.',
    },
    reading_links=['https://en.wikipedia.org/wiki/Stack_(abstract_data_type)'],
    hints=['Keep unresolved day indices on a decreasing stack.', 'When a warmer day arrives, pop every cooler day it resolves.', 'Leave unanswered days at zero.'],
)

spec_asteroid = ProblemSpec(
    signature="function asteroidCollision(asteroids: number[])",
    statement="""# Asteroid Collision

You are given an array `asteroids` of non-zero integers tracing rocks on a single line. The absolute value of an entry is the rock's size: a positive rock drifts right and a negative rock drifts left, each at the same speed.

Rocks moving in the same direction never meet. When a right-drifting rock meets a left-drifting one, the smaller rock explodes; when both share the same size, both explode. Survivors keep drifting and may collide further.

Return the left-to-right state of the rocks that survive every collision. A zero entry, if present, simply passes through without colliding.

Constraints: `1 <= asteroids.length <= 100` and `-1000 <= asteroids[i] <= 1000`.
""",
    brute_force=Algorithm(
        """function asteroidCollision(asteroids) {
  const rocks = asteroids.slice();
  let collided = true;
  while (collided) {
    collided = false;
    for (let i = 0; i < rocks.length - 1; i++) {
      if (rocks[i] > 0 && rocks[i + 1] < 0) {
        const rightSize = rocks[i];
        const leftSize = -rocks[i + 1];
        if (rightSize === leftSize) {
          rocks.splice(i, 2);
        } else if (rightSize > leftSize) {
          rocks.splice(i + 1, 1);
        } else {
          rocks.splice(i, 1);
        }
        collided = true;
        break;
      }
    }
  }
  return rocks;
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function asteroidCollision(asteroids) {
  const stack = [];
  for (let i = 0; i < asteroids.length; i++) {
    const rock = asteroids[i];
    let alive = true;
    while (alive && rock < 0 && stack.length > 0 && stack[stack.length - 1] > 0) {
      const top = stack[stack.length - 1];
      if (top < -rock) {
        stack.pop();
      } else if (top === -rock) {
        stack.pop();
        alive = false;
      } else {
        alive = false;
      }
    }
    if (alive) {
      stack.push(rock);
    }
  }
  return stack;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="stack",
    difficulty="Medium",
    pattern="stack / Simulate",
    time_limit_ms=2000,
    seed=42,
    title="Colliding Asteroids",
    slug="asteroid-collision",
    editorial={
        "approach": 'Sweep left to right, letting each left-moving rock duel the stack of right-moving survivors.',
        "why_optimal": 'Each rock is pushed and popped at most once, so the sweep is linear with a stack bounded by the input.',
        "pitfalls": 'Equal sizes destroy both rocks; same-direction neighbours never collide.',
    },
    reading_links=['https://en.wikipedia.org/wiki/Stack_(abstract_data_type)'],
    hints=['Push right-moving rocks and duel each left-moving rock against the stack top.', 'Equal sizes remove both rocks; larger survivors stay.', 'Never collide same-direction neighbours.'],
)

spec_simplify = ProblemSpec(
    signature="function simplifyPath(path: string)",
    statement="""# Simplify Path

Given an absolute Unix-style path string `path`, reduce it to its canonical form: a single leading slash, directory names joined by exactly one slash each, with no trailing slash.

Resolve every `.` segment (stay in place) and every `..` segment (step to the parent directory, staying at the root when already there). Treat repeated slashes as one separator and drop empty segments.

Constraints: `1 <= path.length <= 100`.
""",
    brute_force=Algorithm(
        """function simplifyPath(path) {
  const parts = path.split('/');
  let idx = parts.indexOf('..');
  while (idx !== -1) {
    parts.splice(idx, 1);
    for (let j = idx - 1; j >= 0; j--) {
      if (parts[j] !== '' && parts[j] !== '.' && parts[j] !== '..') {
        parts.splice(j, 1);
        break;
      }
    }
    idx = parts.indexOf('..');
  }
  const names = [];
  for (let i = 0; i < parts.length; i++) {
    if (parts[i] !== '' && parts[i] !== '.' && parts[i] !== '..') {
      names.push(parts[i]);
    }
  }
  return '/' + names.join('/');
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function simplifyPath(path) {
  const stack = [];
  const parts = path.split('/');
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    if (part === '' || part === '.') {
      continue;
    } else if (part === '..') {
      if (stack.length > 0) {
        stack.pop();
      }
    } else {
      stack.push(part);
    }
  }
  return '/' + stack.join('/');
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="stack",
    difficulty="Medium",
    pattern="stack / Token parse",
    time_limit_ms=2000,
    seed=42,
    title="Canonical Unix Path",
    slug="simplify-path",
    editorial={
        "approach": 'Split on slashes and keep real directory names on a stack, skipping dots and popping on double dots.',
        "why_optimal": 'One pass over the segments is linear in the path length with a stack bounded by the depth.',
        "pitfalls": 'Ignore empty segments from repeated slashes and never pop past the root.',
    },
    reading_links=['https://en.wikipedia.org/wiki/Path_(computing)'],
    hints=['Split the path on slashes and skip empty or single-dot segments.', 'Pop the stack on double dots when it is non-empty.', 'Join survivors with single slashes behind one leading slash.'],
)

spec_calculator = ProblemSpec(
    signature="function calculate(s: string)",
    statement="""# Basic Calculator II

Given a string `s` holding an arithmetic expression with non-negative integers, the binary operators `+`, `-`, `*`, `/`, and optional spaces, evaluate it and return the integer result.

Multiplication and division bind tighter than addition and subtraction; operators sharing a precedence level apply left to right. There are no parentheses. Division between integers truncates toward zero.

Constraints: `1 <= s.length <= 100`.
""",
    brute_force=Algorithm(
        """function calculate(s) {
  const nums = [];
  const ops = [];
  let current = 0;
  let building = false;
  function flush() {
    if (building) {
      nums.push(current);
      current = 0;
      building = false;
    }
  }
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (ch >= '0' && ch <= '9') {
      current = current * 10 + (ch.charCodeAt(0) - 48);
      building = true;
    } else if (ch === '+' || ch === '-' || ch === '*' || ch === '/') {
      flush();
      ops.push(ch);
    }
  }
  flush();
  if (nums.length === 0) {
    return 0;
  }
  const values = nums.slice();
  const operators = ops.slice();
  if (operators.length === values.length) {
    values.unshift(0);
  }
  let pos = 0;
  while (pos < operators.length) {
    if (operators[pos] === '*' || operators[pos] === '/') {
      const a = values[pos];
      const b = values[pos + 1] !== undefined ? values[pos + 1] : 0;
      const result = operators[pos] === '*' ? a * b : Math.trunc(a / b);
      values.splice(pos, 2, result);
      operators.splice(pos, 1);
    } else {
      pos++;
    }
  }
  let total = values[0];
  for (let i = 0; i < operators.length; i++) {
    const next = values[i + 1] !== undefined ? values[i + 1] : 0;
    total = operators[i] === '+' ? total + next : total - next;
  }
  return total;
}""",
        complexity="Time: O(n²) | Space: O(n)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function calculate(s) {
  const stack = [];
  let current = 0;
  let building = false;
  let op = '+';
  function apply() {
    if (!building) {
      return;
    }
    if (op === '+') {
      stack.push(current);
    } else if (op === '-') {
      stack.push(-current);
    } else if (op === '*') {
      const prev = stack.length > 0 ? stack.pop() : 0;
      stack.push(prev * current);
    } else {
      const prev = stack.length > 0 ? stack.pop() : 0;
      stack.push(Math.trunc(prev / current));
    }
    current = 0;
    building = false;
  }
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (ch >= '0' && ch <= '9') {
      current = current * 10 + (ch.charCodeAt(0) - 48);
      building = true;
    } else if (ch === '+' || ch === '-' || ch === '*' || ch === '/') {
      apply();
      op = ch;
    }
  }
  apply();
  let total = 0;
  for (let i = 0; i < stack.length; i++) {
    total += stack[i];
  }
  return total;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="stack",
    difficulty="Medium",
    pattern="stack / Deferred ops",
    time_limit_ms=2000,
    seed=42,
    title="Arithmetic Without Parentheses",
    slug="basic-calculator-ii",
    editorial={
        "approach": 'Parse numbers left to right, pushing signed terms and resolving multiply/divide immediately.',
        "why_optimal": 'One pass with constant stack depth per term keeps evaluation linear in the string length.',
        "pitfalls": 'Apply truncation toward zero on division and flush the final pending number.',
    },
    reading_links=['https://en.wikipedia.org/wiki/Shunting-yard_algorithm'],
    hints=['Track the pending plus/minus sign while scanning numbers.', 'Resolve multiply and divide against the stack top immediately.', 'Sum the signed stack terms for the result.'],
)

spec_histogram = ProblemSpec(
    signature="function largestRectangleArea(heights: number[])",
    statement="""# Largest Rectangle in Histogram

Given an array `heights` where `heights[i]` is the height of bar `i` and every bar shares width `1`, find the largest rectangular area that fits entirely inside the union of the bars.

Any group of consecutive bars supports a rectangle whose height cannot exceed the shortest bar of the group; multiply that height by the group's width to obtain its area.

Constraints: `1 <= heights.length <= 100` and `0 <= heights[i] <= 100`.
""",
    brute_force=Algorithm(
        """function largestRectangleArea(heights) {
  let best = 0;
  const n = heights.length;
  for (let i = 0; i < n; i++) {
    let minHeight = heights[i];
    for (let j = i; j < n; j++) {
      if (heights[j] < minHeight) {
        minHeight = heights[j];
      }
      const area = minHeight * (j - i + 1);
      if (area > best) {
        best = area;
      }
    }
  }
  return best;
}""",
        complexity="Time: O(n²) | Space: O(1)",
        language="javascript",
    ),
    optimal=Algorithm(
        """function largestRectangleArea(heights) {
  const extended = heights.concat([0]);
  const stack = [];
  let best = 0;
  for (let i = 0; i < extended.length; i++) {
    while (stack.length > 0 && extended[i] < extended[stack[stack.length - 1]]) {
      const top = stack.pop();
      const height = extended[top];
      const width = stack.length === 0 ? i : i - stack[stack.length - 1] - 1;
      const area = height * width;
      if (area > best) {
        best = area;
      }
    }
    stack.push(i);
  }
  return best;
}""",
        complexity="Time: O(n) | Space: O(n)",
        language="javascript",
    ),
    topic="stack",
    difficulty="Hard",
    pattern="stack / Monotonic increasing",
    time_limit_ms=2000,
    seed=42,
    title="Widest Bar Rectangle",
    slug="largest-rectangle-in-histogram",
    editorial={
        "approach": 'Extend the bars with a zero sentinel and pop a rising stack to close out each maximal width.',
        "why_optimal": 'Each bar is pushed and popped once, so the scan is linear with a stack bounded by the bar count.',
        "pitfalls": 'Compute width from the new stack top after each pop; bars of height zero contribute no area.',
    },
    reading_links=['https://en.wikipedia.org/wiki/Stack_(abstract_data_type)'],
    hints=['Push rising bar indices and pop whenever a lower bar arrives.', 'Measure each popped bar across the span since the new stack top.', 'Append a zero-height sentinel to flush every bar.'],
)

SPECS: list[ProblemSpec] = [
    spec_make_good,
    spec_remove_duplicates,
    spec_baseball,
    spec_next_greater,
    spec_rpn,
    spec_daily,
    spec_asteroid,
    spec_simplify,
    spec_calculator,
    spec_histogram,
]


def _paf_report_total_ms(report: Any) -> tuple[float, float]:
    return report.brute_force_runtime_ms, report.optimal_runtime_ms


async def _build_paf_problem(spec: ProblemSpec) -> Any:
    """Run stock PAF verification, then swap in bespoke valid inputs where needed."""
    problem = await build_verified_problem(spec)
    needs_custom = spec.slug in {
        "baseball-game",
        "evaluate-reverse-polish-notation",
        "next-greater-element-i",
        "simplify-path",
        "basic-calculator-ii",
    }
    if not needs_custom:
        return problem
    import random

    rng = random.Random(spec.seed)
    custom_inputs: list[list[Any]] = []
    if spec.slug == "baseball-game":
        custom_inputs = [
            [["5", "2", "C", "D", "+"]],
            [["5", "-2", "4", "C", "D", "9", "+", "+"]],
            [["5"]],
            [["3", "C"]],
            [["10", "20", "30"]],
            [["1", "C", "2", "D", "+"]],
            [_valid_baseball_ops(rng, 12)],
            [_valid_baseball_ops(rng, 8)],
            [_valid_baseball_ops(rng, 20)],
            [_valid_baseball_ops(rng, 5)],
            [_valid_baseball_ops(rng, 16)],
            [_valid_baseball_ops(rng, 24)],
        ]
    elif spec.slug == "evaluate-reverse-polish-notation":
        custom_inputs = [
            [["2", "1", "+", "3", "*"]],
            [["4", "13", "5", "/", "+"]],
            [["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]],
            [["18"]],
            [["-7", "3", "/"]],
            [["4", "-2", "/", "2", "*"]],
            [_valid_rpn_tokens(rng, 4)],
            [_valid_rpn_tokens(rng, 6)],
            [_valid_rpn_tokens(rng, 8)],
            [_valid_rpn_tokens(rng, 3)],
            [_valid_rpn_tokens(rng, 10)],
            [_valid_rpn_tokens(rng, 5)],
        ]
    elif spec.slug == "next-greater-element-i":
        universe = [-3, -1, 0, 2, 5, 9]
        custom_inputs = [
            [[4, 1, 2], [1, 3, 4, 2]],
            [[2, 4], [1, 2, 3, 4]],
            [[4, 3, 2, 1], [4, 3, 2, 1]],
            [[1], [1]],
            [[5, 9, 2], [9, 2, 5, 7, 1]],
        ]
        extra: list[list[Any]] = []
        for _ in range(17):
            m = rng.randint(2, 6)
            pool = rng.sample(universe, m)
            n = rng.randint(1, min(4, m))
            picks = rng.sample(pool, n)
            extra.append([picks, pool])
        custom_inputs.extend(extra)
    elif spec.slug == "simplify-path":
        custom_inputs = [
            ["/home/"],
            ["/../"],
            ["/home//foo/"],
            ["/a/./b/../../c/"],
            ["/"],
            ["/abcxyz/012/"],
            ["/abcxyz/def/"],
        ]
        for _ in range(15):
            depth = rng.randint(1, 5)
            segments: list[str] = []
            for _ in range(depth):
                pick = rng.random()
                if pick < 0.15:
                    segments.append("..")
                elif pick < 0.3:
                    segments.append(".")
                else:
                    word = "".join(rng.choice(_FIELD_ALPHABET + "012") for _ in range(rng.randint(1, 4)))
                    segments.append(word)
            raw = "/" + "/".join(segments) + ("/" if rng.random() < 0.5 else "")
            if rng.random() < 0.2:
                raw = raw.replace("/", "//", 1)
            custom_inputs.append([raw])
    elif spec.slug == "basic-calculator-ii":
        custom_inputs = [
            ["3+2*2"],
            [" 3/2 "],
            [" 3+5 / 2 "],
            ["7"],
            ["  14-3/2"],
            ["100+200*3-50/2"],
            ["0"],
        ]
        ops = ["+", "-", "*", "/"]
        for _ in range(15):
            parts: list[str] = [str(rng.randint(0, 99))]
            for _ in range(rng.randint(1, 4)):
                parts.append(rng.choice(ops))
                parts.append(str(rng.randint(1, 99)))
            expr = "".join(parts)
            if rng.random() < 0.5:
                expr = " " + expr + " "
            expr = expr.replace("*", " * ").replace("/", " / ") if rng.random() < 0.3 else expr
            custom_inputs.append([expr])

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


def main() -> None:
    import asyncio as _asyncio

    output_dir = REPO_ROOT / "content" / "problems"
    print(f"Authoring and verifying {len(SPECS)} Batch-1C problems with PAF...")
    for idx, spec in enumerate(SPECS, 1):
        print(f"[{idx}/{len(SPECS)}] Generating {spec.slug} ({spec.difficulty})...")
        problem = _asyncio.run(_build_paf_problem(spec))
        out_file = problem.write_to(output_dir)
        print(
            f"  ✓ {problem.data['slug']}: {problem.report.total_cases} cases verified | "
            f"Brute: {problem.report.brute_force_runtime_ms:.2f}ms | "
            f"Optimal: {problem.report.optimal_runtime_ms:.2f}ms -> {out_file.name}"
        )
    print("\nAll 10 Batch-1C problems generated and PAF-verified successfully.")


if __name__ == "__main__":
    main()
