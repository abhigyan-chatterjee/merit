import asyncio
import contextlib
import json
import os
import pwd
import re
import shutil
import signal
import sys
import tempfile
from pathlib import Path
from typing import Any

# Mirrors the router-level check: harnesses interpolate function_name into
# generated code, so anything beyond a plain identifier must never reach it.
_FUNCTION_NAME_RE = re.compile(r"^[A-Za-z_$][\w$]*\Z")
_DUNDER_NAME_RE = re.compile(r"^__.*__\Z")

# ---------------------------------------------------------------------------
# Sandbox isolation
#
# User code is untrusted. Without these the child inherits the API's whole
# environment (SECRET_KEY, DATABASE_URL, GITHUB_TOKEN), runs with the API's
# privileges, and can read or write the database — one submission could forge
# any user's session. Everything below narrows the child to "run this file
# and print its output".
# ---------------------------------------------------------------------------

# An explicit allowlist. The child gets a PATH and nothing else: no secrets,
# no database URL, no tokens, no proxy settings.
JUDGE_ENV: dict[str, str] = {
    "PATH": "/usr/local/bin:/usr/bin:/bin",
    "HOME": "/tmp",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "PYTHONDONTWRITEBYTECODE": "1",
    "NODE_OPTIONS": "--max-old-space-size=256",
}

# stdout/stderr beyond this is discarded and the run is failed as overflow.
# A `while (true) console.log(1)` would otherwise buffer unbounded into the
# API's own memory and OOM the container.
MAX_OUTPUT_BYTES = 256 * 1024

# Ceilings applied by the launcher before the interpreter starts.
_RLIMIT_AS_BYTES = 512 * 1024 * 1024
_RLIMIT_CPU_SEC = 5
_RLIMIT_FSIZE_BYTES = 8 * 1024 * 1024


def _address_space_limit_for(binary: str) -> int:
    """RLIMIT_AS for this interpreter, or 0 to leave it alone.

    Node cannot run under an address-space cap: V8 reserves a multi-gigabyte
    virtual cage for pointer compression that is never committed, so RLIMIT_AS
    makes thread creation fail at startup. Its heap is bounded through
    NODE_OPTIONS instead, and the container cgroup remains the backstop.
    """
    if "node" in Path(binary).name.lower():
        return 0
    return _RLIMIT_AS_BYTES


# NOTE: there is deliberately no RLIMIT_NPROC here. On Linux it caps processes
# per *real UID across the whole host*, not per process tree, so it counts the
# API worker's own threads and makes Node fail to start. Fork bombs are instead
# contained by the process-group kill on timeout (below) and by pids_limit on
# the container in docker-compose.yml.
_LAUNCHER_SRC = """\
import os, resource, sys

as_bytes, cpu, fsize = (int(v) for v in sys.argv[1:4])
for res, lim in (
    (resource.RLIMIT_CPU, cpu),
    (resource.RLIMIT_FSIZE, fsize),
    (resource.RLIMIT_CORE, 0),
):
    try:
        resource.setrlimit(res, (lim, lim))
    except (ValueError, OSError):
        pass

# 0 means "no address-space cap" (Node reserves a large virtual cage).
if as_bytes:
    try:
        resource.setrlimit(resource.RLIMIT_AS, (as_bytes, as_bytes))
    except (ValueError, OSError):
        pass

os.execvp(sys.argv[4], sys.argv[4:])
"""


def _drop_to_unprivileged() -> tuple[int, int] | None:
    """The (uid, gid) to run submissions as, or None when not privileged.

    Only meaningful when the API itself is root. In local dev and CI the tests
    run as a normal user, where dropping again is neither possible nor needed.
    """
    if os.geteuid() != 0:
        return None
    for name in ("nobody", "nogroup", "daemon"):
        try:
            entry = pwd.getpwnam(name)
        except KeyError:
            continue
        if entry.pw_uid != 0:
            return (entry.pw_uid, entry.pw_gid)
    return None


def _launcher_path(tmp_path: Path) -> Path:
    launcher = tmp_path / "_launch.py"
    launcher.write_text(_LAUNCHER_SRC, encoding="utf-8")
    return launcher


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


async def _read_capped(stream: asyncio.StreamReader, budget: int) -> tuple[bytes, bool]:
    """Reads a stream but stops at `budget`, reporting whether it overflowed."""
    chunks: list[bytes] = []
    total = 0
    overflowed = False
    while True:
        chunk = await stream.read(65536)
        if not chunk:
            break
        total += len(chunk)
        if total > budget:
            chunks.append(chunk[: max(0, budget - (total - len(chunk)))])
            overflowed = True
            break
        chunks.append(chunk)
    return b"".join(chunks), overflowed


async def run_in_sandbox(
    cmd: list[str],
    cwd: str,
    timeout_sec: float = 4.0,
) -> tuple[int, str, str, bool]:
    """Runs command with strict timeout, scrubbed env, and captured output.

    The child is denied the API's environment, dropped to an unprivileged uid
    when the parent is root, hard-limited by rlimits, and killed as a process
    group so nothing outlives the timeout.
    """
    identity = _drop_to_unprivileged()
    # The submission's working directory must be reachable by the unprivileged
    # child; mkdtemp creates it 0700 owned by root.
    if identity:
        with contextlib.suppress(OSError):
            os.chmod(cwd, 0o777)

    kwargs: dict[str, Any] = {
        "stdout": asyncio.subprocess.PIPE,
        "stderr": asyncio.subprocess.PIPE,
        "cwd": cwd,
        "env": JUDGE_ENV,
        # Its own session means the whole tree shares one process group, so a
        # timeout can kill grandchildren too — a fork bomb cannot outlive it.
        "start_new_session": True,
    }
    if identity:
        kwargs["user"] = identity[0]
        kwargs["group"] = identity[1]
        kwargs["extra_groups"] = []

    # rlimits are applied by a launcher that execs the real interpreter. It
    # runs on the same interpreter as the API so it is present in every image.
    launcher = _launcher_path(Path(cwd))
    launcher_cmd = [
        sys.executable,
        str(launcher),
        str(_address_space_limit_for(cmd[0])),
        str(_RLIMIT_CPU_SEC),
        str(_RLIMIT_FSIZE_BYTES),
        *cmd,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(*launcher_cmd, **kwargs)
    except (OSError, ValueError) as err:
        # Falling back is better than a dead judge, but the limits are the
        # point — surface it rather than silently running unprotected.
        return (-1, "", f"Sandbox launch failed: {err}", False)

    overflowed = False
    timed_out = False
    try:
        stdout_b, stderr_b, overflowed = await asyncio.wait_for(
            _collect(proc, MAX_OUTPUT_BYTES), timeout=timeout_sec
        )
    except TimeoutError:
        timed_out = True
        await _kill_tree(proc)
        stdout_b, stderr_b = b"", b""
    except Exception as err:
        await _kill_tree(proc)
        return (-1, "", str(err), False)

    if timed_out:
        return (-1, "", "Time Limit Exceeded", True)

    if overflowed:
        return (
            -1,
            "",
            f"Output limit exceeded ({MAX_OUTPUT_BYTES // 1024} KB). "
            "Reduce what the solution prints.",
            False,
        )

    return (
        proc.returncode or 0,
        stdout_b.decode("utf-8", errors="replace"),
        stderr_b.decode("utf-8", errors="replace"),
        False,
    )


async def _collect(
    proc: asyncio.subprocess.Process, budget: int
) -> tuple[bytes, bytes, bool]:
    out, out_over = await _read_capped(proc.stdout, budget)
    err, err_over = await _read_capped(proc.stderr, budget)
    await proc.wait()
    return out, err, (out_over or err_over)


async def _kill_tree(proc: asyncio.subprocess.Process) -> None:
    """SIGKILLs the child's whole process group, then reaps it."""
    if proc.returncode is not None:
        return
    with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    with contextlib.suppress(Exception):
        proc.kill()
    # Reaping prevents a zombie lingering for the worker's lifetime.
    with contextlib.suppress(Exception):
        await asyncio.wait_for(proc.wait(), timeout=5.0)


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

    if (
        not _FUNCTION_NAME_RE.match(function_name)
        or _DUNDER_NAME_RE.match(function_name)
    ):
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
