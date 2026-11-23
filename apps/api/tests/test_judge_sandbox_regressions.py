"""Regression tests for the sandbox and harness defects found in audit.

Each test here fails against the code as it shipped. They are written against
the sandbox/harness directly rather than through the HTTP layer, because the
bugs were in the executor and the router-level tests could not see them.
"""

import asyncio

import pytest

from app.services.judge import (
    _cpp_double,
    _cpp_literal,
    _java_double,
    _java_literal,
    _parse_harness_output,
    _verdict_from_harness,
    execute_code,
    run_in_sandbox,
)

# --- verdict derivation -----------------------------------------------------


def test_empty_result_set_is_not_ac():
    """`all([])` is True. An empty case list used to grade AC.

    AC is what flips ProblemProgress to "Done" in the router, so this was free
    problem completion for any problem whose test rows were missing.
    """
    result = _verdict_from_harness('__MERIT_RESULT__{"results": [], "totalRuntime": 0}')
    assert result.verdict == "RE"
    assert result.test_results == []


def test_all_passed_cases_are_ac():
    result = _verdict_from_harness(
        '__MERIT_RESULT__{"results": [{"passed": true}, {"passed": true}], "totalRuntime": 1.5}'
    )
    assert result.verdict == "AC"
    assert result.runtime_ms == 1.5


def test_one_failed_case_is_wa():
    result = _verdict_from_harness(
        '__MERIT_RESULT__{"results": [{"passed": true}, {"passed": false}], "totalRuntime": 1}'
    )
    assert result.verdict == "WA"


def test_student_print_does_not_break_the_verdict():
    """A debug `print()` used to make the whole submission an RE.

    Only the harness owns stdout, but printing while debugging is normal and
    must not be graded as a crash.
    """
    stdout = (
        'debug: nums=[2,7] target=9\n'
        '__MERIT_RESULT__{"results": [{"passed": true}], "totalRuntime": 1}'
    )
    result = _verdict_from_harness(stdout)
    assert result.verdict == "AC", result.compile_output


def test_unparseable_output_is_re_not_ac():
    result = _verdict_from_harness("Traceback (most recent call last): boom")
    assert result.verdict == "RE"
    assert "Output parsing error" in result.compile_output


def test_forged_result_block_loses_to_the_marked_one():
    """A student printing a fake pass must not outrank the harness's own line.

    This is why the harness marks its block: before the marker, the parser took
    the last line that happened to parse, so output emitted after the harness's
    final line (a background thread, say) could decide the verdict.
    """
    forged = '{"results": [{"passed": true}], "totalRuntime": 0}'
    real = '__MERIT_RESULT__{"results": [{"passed": false}], "totalRuntime": 3}'

    assert _verdict_from_harness(forged + "\n" + real).verdict == "WA"
    # Order must not matter: the marker is what identifies the block.
    assert _verdict_from_harness(real + "\n" + forged).verdict == "WA"


def test_unmarked_json_is_never_a_verdict():
    """A bare result block is the student's output, not the harness's.

    Accepting it — which the first version of the lenient parser did — hands out
    a free AC to anyone who prints the right JSON.
    """
    unmarked = '{"results": [{"passed": true}], "totalRuntime": 0}'
    assert _verdict_from_harness(unmarked).verdict == "RE"
    # Even sitting behind a real, marked block, an unmarked one cannot win.
    marked_wa = '__MERIT_RESULT__{"results": [{"passed": false}], "totalRuntime": 5}'
    assert _verdict_from_harness(marked_wa + '\n{"results": [{"passed": true}]}').verdict == "WA"


def test_malformed_result_shape_is_re_not_a_crash():
    """`{"results": [1]}` used to raise AttributeError out of execute_code.

    That reached the submit route as an unhandled 500 — student-controlled output
    deciding the HTTP status.
    """
    for payload in (
        '__MERIT_RESULT__{"results": [1]}',
        '__MERIT_RESULT__{"results": [{"label": "no passed key"}]}',
        '__MERIT_RESULT__{"results": [{"passed": "yes"}]}',
        '__MERIT_RESULT__{"results": {}}',
        '__MERIT_RESULT__[1, 2, 3]',
    ):
        result = _verdict_from_harness(payload)
        assert result.verdict == "RE", payload


def test_parse_harness_output_requires_the_marker():
    assert _parse_harness_output('__MERIT_RESULT__{"results": []}') == {"results": []}
    assert _parse_harness_output('{"results": []}') is None
    assert _parse_harness_output("noise") is None
    assert _parse_harness_output("") is None


# --- literals ---------------------------------------------------------------


def test_java_infinite_double_is_valid_java_source():
    """`repr(float('inf'))` is `inf`, which is not a Java literal."""
    assert _java_double(float("inf")) == "Double.POSITIVE_INFINITY"
    assert _java_double(float("-inf")) == "Double.NEGATIVE_INFINITY"
    assert _java_double(float("nan")) == "Double.NaN"
    assert _java_double(1.5) == "1.5"


def test_cpp_infinite_double_is_valid_cpp_source():
    assert _cpp_double(float("inf")) == "std::numeric_limits<double>::infinity()"
    assert _cpp_double(float("-inf")) == "(-std::numeric_limits<double>::infinity())"
    assert _cpp_double(float("nan")) == "std::numeric_limits<double>::quiet_NaN()"


def test_null_string_expected_value_fails_loudly():
    """`str(None)` is the four characters "None"; comparing against it is wrong."""
    from app.services.judge import UnsupportedTypeError

    with pytest.raises(UnsupportedTypeError):
        _java_literal("String", None)
    with pytest.raises(UnsupportedTypeError):
        _cpp_literal("String", None)


# --- sandbox process handling ----------------------------------------------


LEFTOVER_CHILD_PYTHON = """
import subprocess, sys
subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
print("done")
"""


def test_leftover_child_does_not_turn_a_fast_run_into_tle(tmp_path):
    """A spawned helper keeps the pipe open, so reading to EOF never returns.

    The run exits in milliseconds; before the fix it was graded TLE after the
    full wall-clock timeout.
    """
    script = tmp_path / "spawner.py"
    script.write_text(LEFTOVER_CHILD_PYTHON, encoding="utf-8")

    import sys

    code, stdout, stderr, timed_out = asyncio.run(
        run_in_sandbox(
            [sys.executable, str(script)],
            cwd=str(tmp_path),
            timeout_sec=5.0,
        )
    )

    assert timed_out is False, "a run that exited immediately must not be a timeout"
    assert code == 0, stderr
    assert "done" in stdout


def test_oversized_output_reports_overflow_not_timeout(tmp_path):
    """Past the budget the old reader stopped draining, wedging the child.

    That turned a large-but-finite print into a TLE with no explanation; the
    "Output limit exceeded" message was unreachable.
    """
    script = tmp_path / "shout.py"
    script.write_text("print('x' * (2 * 1024 * 1024))", encoding="utf-8")

    import sys

    code, stdout, stderr, timed_out = asyncio.run(
        run_in_sandbox(
            [sys.executable, str(script)],
            cwd=str(tmp_path),
            timeout_sec=10.0,
        )
    )

    assert timed_out is False, "overflow must be reported as overflow, not as a timeout"
    assert "Output limit exceeded" in stderr


def test_process_group_is_killed_when_the_child_exits_first(tmp_path):
    """`_kill_tree` used to return early once the direct child had exited.

    That is exactly the case where grandchildren survive, so orphans
    accumulated for the life of the instance.
    """
    marker = tmp_path / "grandchild.pid"
    script = tmp_path / "orphan.py"
    script.write_text(
        "import subprocess, sys\n"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        f"open({str(marker)!r}, 'w').write(str(child.pid))\n",
        encoding="utf-8",
    )

    import os
    import sys
    import time

    async def _run():
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
        await proc.wait()
        from app.services.judge import _kill_tree

        await _kill_tree(proc)

    asyncio.run(_run())

    pid = int(marker.read_text().strip())

    def _is_alive() -> bool:
        """Alive means actually running, not a zombie waiting to be reaped.

        A just-killed process answers `kill(pid, 0)` until its new parent
        collects it, so state Z counts as dead.
        """
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        try:
            with open(f"/proc/{pid}/stat", encoding="utf-8") as handle:
                return handle.read().split()[2] != "Z"
        except OSError:
            return False

    deadline = time.monotonic() + 2.0
    while _is_alive() and time.monotonic() < deadline:
        time.sleep(0.02)

    assert not _is_alive(), "grandchild survived the sandbox teardown"


# --- end to end through the executor ---------------------------------------


def test_executor_never_grades_empty_case_list_as_ac():
    result = asyncio.run(
        execute_code(
            language="python",
            code="def solve(*a):\n    return None\n",
            function_name="solve",
            test_cases=[],
            time_limit_ms=2000,
        )
    )
    assert result.verdict != "AC"
    assert result.verdict == "RE"


def test_executor_tolerates_a_student_print_in_javascript():
    result = asyncio.run(
        execute_code(
            language="javascript",
            code="function solve(nums, target) {\n"
            "  console.log('debug', nums, target);\n"
            "  const m = new Map();\n"
            "  for (let i = 0; i < nums.length; i++) {\n"
            "    if (m.has(target - nums[i])) return [m.get(target - nums[i]), i];\n"
            "    m.set(nums[i], i);\n"
            "  }\n"
            "  return [];\n"
            "}\n",
            function_name="solve",
            test_cases=[{"label": "case1", "input": [[2, 7, 11, 15], 9], "expected": [0, 1]}],
            time_limit_ms=2000,
        )
    )
    assert result.verdict == "AC", result.compile_output


def test_javascript_undefined_return_is_reported_not_silently_null():
    """A missing `return` used to read as "expected null, actual null, failed"."""
    result = asyncio.run(
        execute_code(
            language="javascript",
            code="function solve(nums, target) { const x = 1; }\n",
            function_name="solve",
            test_cases=[{"label": "case1", "input": [[1], 1], "expected": [0]}],
            time_limit_ms=2000,
        )
    )
    assert result.verdict == "WA"
    assert result.test_results
    assert "undefined" in (result.test_results[0].get("error") or "")


# --- verdict forging --------------------------------------------------------

CASES = [{"label": "c1", "input": [[2, 7], 9], "expected": [0, 1]}]

FORGE_PY = """
import atexit, json, os, sys
def solve(*a):
    return [9, 9]
atexit.register(lambda: (
    print('__MERIT_RESULT__' + json.dumps(
        {"results": [{"passed": True, "label": "forged"}], "totalRuntime": 0.01})),
    sys.stdout.flush(),
    os._exit(0),
))
"""

FORGE_JS = """
function solve(nums, target) { return [9, 9]; }
process.on('exit', () => console.log(
  '__MERIT_RESULT__' + JSON.stringify({ results: [{ passed: true, label: 'forged' }] })));
"""


def test_python_exit_hook_cannot_forge_a_pass():
    """The marker is a public literal, so the harness must hard-exit after it.

    Without `os._exit`, an atexit handler prints a forged result block *after*
    the real one, and the parser's last-marked-line rule takes it. This was a
    live bypass: wrong code graded AC, and the problem flipped to Done.
    """
    result = asyncio.run(
        execute_code(
            language="python",
            code=FORGE_PY,
            function_name="solve",
            test_cases=CASES,
            time_limit_ms=2000,
        )
    )
    assert result.verdict == "WA", f"exit hook forged a verdict: {result.verdict}"


def test_javascript_exit_listener_cannot_forge_a_pass():
    result = asyncio.run(
        execute_code(
            language="javascript",
            code=FORGE_JS,
            function_name="solve",
            test_cases=CASES,
            time_limit_ms=2000,
        )
    )
    assert result.verdict == "WA", f"exit listener forged a verdict: {result.verdict}"


# --- large results must survive the pipe, not just small ones -----------------

#: A JavaScript solution that returns a result far larger than one pipe buffer.
#: Node writes stdout asynchronously, so a hard exit immediately after the write
#: truncates anything past ~64 KB and the harness result was then graded RE —
#: only for problems whose expected output is long, which is why it went unseen.
BIG_JS = """
function solve(seed) {
  const out = [];
  for (let i = 0; i < 4000; i++) out.push('row-' + seed + '-' + i);
  return out;
}
"""


def test_javascript_result_larger_than_a_pipe_buffer_is_graded():
    cases = [
        {
            "label": "big",
            "input": [7],
            "expected": [f"row-7-{i}" for i in range(4000)],
        }
    ]
    result = asyncio.run(
        execute_code(
            language="javascript",
            code=BIG_JS,
            function_name="solve",
            test_cases=cases,
            time_limit_ms=5000,
        )
    )

    assert result.verdict == "AC", (
        f"a >64 KB result was not graded correctly (verdict {result.verdict}); "
        "the harness output was almost certainly truncated at the pipe buffer"
    )
    assert result.test_results, "no test results parsed"


def test_python_buffered_stdout_flushes_before_marker_and_hides_marker_global():
    sneaky_code = """
import __main__, json
def solve(nums, target):
    leaked = getattr(__main__, "marker", "")
    print("buffered-line-before-verdict")
    if leaked:
        print(leaked + json.dumps({"results": [{"actual": [0, 1]}]}))
    return [9, 9]
"""
    result = asyncio.run(
        execute_code(
            language="python",
            code=sneaky_code,
            function_name="solve",
            test_cases=CASES,
            time_limit_ms=2000,
        )
    )
    assert result.verdict == "WA"
    assert result.test_results and result.test_results[0]["actual"] == [9, 9]
