import asyncio
import contextlib
import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

# Mirrors the router-level check: harnesses interpolate function_name into
# generated code, so anything beyond a plain identifier must never reach it.
_FUNCTION_NAME_RE = re.compile(r"^[A-Za-z_$][\w$]*$")


class JudgeResult:
    def __init__(
        self,
        verdict: str,  # AC | WA | TLE | RE | CE
        runtime_ms: float,
        test_results: list[dict[str, Any]],
        compile_output: str = "",
    ):
        self.verdict = verdict
        self.runtime_ms = runtime_ms
        self.test_results = test_results
        self.compile_output = compile_output


async def run_in_sandbox(
    cmd: list[str],
    cwd: str,
    timeout_sec: float = 4.0,
) -> tuple[int, str, str, bool]:
    """Runs command with strict timeout and captures stdout/stderr."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout_b, stderr_b = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout_sec,
        )
        return (
            proc.returncode or 0,
            stdout_b.decode("utf-8", errors="replace"),
            stderr_b.decode("utf-8", errors="replace"),
            False,
        )
    except TimeoutError:
        with contextlib.suppress(Exception):
            proc.kill()
        return (-1, "", "Time Limit Exceeded", True)
    except Exception as err:
        return (-1, "", str(err), False)


async def execute_code(
    language: str,
    code: str,
    function_name: str,
    test_cases: list[dict[str, Any]],
    time_limit_ms: int = 2000,
) -> JudgeResult:
    """Executes code against test cases in an isolated sandbox."""
    if len(code.encode("utf-8")) > 64 * 1024:
        return JudgeResult(
            verdict="CE",
            runtime_ms=0,
            test_results=[],
            compile_output="Code size exceeds maximum limit of 64 KB",
        )

    if not _FUNCTION_NAME_RE.match(function_name):
        return JudgeResult(
            verdict="CE",
            runtime_ms=0,
            test_results=[],
            compile_output=(
                f"Invalid function name {function_name!r}: expected a plain identifier"
            ),
        )

    tmpdir = tempfile.mkdtemp(prefix="merit_judge_")
    try:
        tmp_path = Path(tmpdir)
        timeout_sec = max(3.0, (time_limit_ms / 1000.0) * 1.5)

        if language == "javascript":
            harness = f"""
{code}

const cases = {json.dumps(test_cases)};

// Deterministic key order so comparison parity matches the Python judge's
// json.dumps(..., sort_keys=True).
const stableStringify = (value) => {{
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return '[' + value.map(stableStringify).join(',') + ']';
  const entries = Object.keys(value)
    .sort()
    .map((k) => JSON.stringify(k) + ':' + stableStringify(value[k]));
  return '{{' + entries.join(',') + '}}';
}};

const results = [];
let totalRuntime = 0;

for (let i = 0; i < cases.length; i++) {{
  const tc = cases[i];
  const start = performance.now();
  try {{
    if (typeof {function_name} !== 'function') {{
      throw new TypeError("{function_name} is not defined as a function");
    }}
    const out = {function_name}(...tc.input);
    const runtime = performance.now() - start;
    totalRuntime += runtime;

    // Strict comparison
    const expectedStr = stableStringify(tc.expected);
    const actualStr = stableStringify(out);
    const passed = expectedStr === actualStr;

    results.push({{
      label: tc.label || `Case ${{i + 1}}`,
      passed,
      input: tc.input,
      expected: tc.expected,
      actual: out,
      runtime_ms: Math.round(runtime * 100) / 100,
      error: null
    }});
  }} catch (err) {{
    results.push({{
      label: tc.label || `Case ${{i + 1}}`,
      passed: false,
      input: tc.input,
      expected: tc.expected,
      actual: null,
      runtime_ms: 0,
      error: err.message || String(err)
    }});
  }}
}}

console.log(JSON.stringify({{ results, totalRuntime }}));
"""
            script_file = tmp_path / "solution.mjs"
            script_file.write_text(harness, encoding="utf-8")

            node_bin = shutil.which("node") or "node"
            code_ret, stdout, stderr, timed_out = await run_in_sandbox(
                [node_bin, str(script_file)],
                cwd=str(tmp_path),
                timeout_sec=timeout_sec,
            )

            if timed_out:
                return JudgeResult(
                    verdict="TLE",
                    runtime_ms=time_limit_ms,
                    test_results=[],
                    compile_output="Time Limit Exceeded",
                )

            if code_ret != 0:
                return JudgeResult(
                    verdict="RE",
                    runtime_ms=0,
                    test_results=[],
                    compile_output=stderr or stdout,
                )

            try:
                # Find JSON output
                parsed = json.loads(stdout.strip())
                results = parsed["results"]
                total_runtime = parsed.get("totalRuntime", 0.0)

                all_passed = all(r["passed"] for r in results)
                verdict = "AC" if all_passed else "WA"
                return JudgeResult(
                    verdict=verdict,
                    runtime_ms=total_runtime,
                    test_results=results,
                )
            except Exception as err:
                return JudgeResult(
                    verdict="RE",
                    runtime_ms=0,
                    test_results=[],
                    compile_output=f"Output parsing error: {err}\nOutput was: {stdout}",
                )

        elif language == "python":
            cases_json_literal = json.dumps(test_cases)
            harness = f"""
import json, time, sys

{code}

cases = json.loads({json.dumps(cases_json_literal)})
results = []
total_runtime = 0.0

if '{function_name}' not in globals() or not callable(globals()['{function_name}']):
    sys.stderr.write("Function '{function_name}' is not defined")
    sys.exit(1)

fn = globals()['{function_name}']

for i, tc in enumerate(cases):
    start = time.perf_counter()
    try:
        out = fn(*tc['input'])
        runtime = (time.perf_counter() - start) * 1000.0
        total_runtime += runtime

        # Exact JSON equality comparison
        expected_str = json.dumps(tc['expected'], sort_keys=True)
        actual_str = json.dumps(out, sort_keys=True)
        passed = expected_str == actual_str

        results.append({{
            'label': tc.get('label', f"Case {{i + 1}}"),
            'passed': passed,
            'input': tc['input'],
            'expected': tc['expected'],
            'actual': out,
            'runtime_ms': round(runtime, 2),
            'error': None
        }})
    except Exception as err:
        results.append({{
            'label': tc.get('label', f"Case {{i + 1}}"),
            'passed': False,
            'input': tc['input'],
            'expected': tc['expected'],
            'actual': None,
            'runtime_ms': 0.0,
            'error': str(err)
        }})

print(json.dumps({{'results': results, 'totalRuntime': total_runtime}}))
"""
            script_file = tmp_path / "solution.py"
            script_file.write_text(harness, encoding="utf-8")

            py_bin = shutil.which("python3") or shutil.which("python") or "python3"
            code_ret, stdout, stderr, timed_out = await run_in_sandbox(
                [py_bin, str(script_file)],
                cwd=str(tmp_path),
                timeout_sec=timeout_sec,
            )

            if timed_out:
                return JudgeResult(
                    verdict="TLE",
                    runtime_ms=time_limit_ms,
                    test_results=[],
                    compile_output="Time Limit Exceeded",
                )

            if code_ret != 0:
                return JudgeResult(
                    verdict="RE",
                    runtime_ms=0,
                    test_results=[],
                    compile_output=stderr or stdout,
                )

            try:
                parsed = json.loads(stdout.strip())
                results = parsed["results"]
                total_runtime = parsed.get("totalRuntime", 0.0)

                all_passed = all(r["passed"] for r in results)
                verdict = "AC" if all_passed else "WA"
                return JudgeResult(
                    verdict=verdict,
                    runtime_ms=total_runtime,
                    test_results=results,
                )
            except Exception as err:
                return JudgeResult(
                    verdict="RE",
                    runtime_ms=0,
                    test_results=[],
                    compile_output=f"Output parsing error: {err}\nOutput was: {stdout}",
                )

        else:
            return JudgeResult(
                verdict="CE",
                runtime_ms=0,
                test_results=[],
                compile_output=(
                    f"Language '{language}' is not yet configured on this execution runner."
                ),
            )

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
