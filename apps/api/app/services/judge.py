import asyncio
import contextlib
import json
import math
import os
import pwd
import re
import secrets
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

# The harness prefixes its result block with this marker. Without it, a student
# who prints a hand-written result JSON — say from a background thread that runs
# after the harness's own final line — could be graded on output they produced
# rather than on what the harness measured. The parser prefers a marked block and
# only falls back to position-based matching for harnesses that do not emit one.
_RESULT_MARKER = "__MERIT_RESULT__"

# After the direct child exits, how long to keep draining its pipes before
# giving up on a grandchild that inherited the write end. Buffered output of a
# normal submission drains in microseconds; this only bounds the pathological
# case where a spawned helper keeps writing after its parent is gone.
_PIPE_CHUNK = 65536
#: How long a read may sit empty before the pipe is treated as stalled. An IDLE
#: bound, not a budget for the whole drain. It must stay below the minimum
#: run timeout (3 s) or a leaked grandchild turns a fast run into a TLE, and it
#: must be far longer than a live writer's gap between chunks.
_READ_IDLE_SEC = 1.0

# Submissions larger than this are refused before any process starts. Defined
# here, next to the executor that enforces it, because this file runs as both
# the API's executor and the judge service's /app/sandbox.py — the judge's HTTP
# layer imports this constant rather than declaring a second copy that could
# drift out of step.
MAX_CODE_BYTES = 64 * 1024

# Ceilings applied by the launcher before the interpreter starts.
_RLIMIT_AS_BYTES = 512 * 1024 * 1024
_RLIMIT_CPU_SEC = 5
_RLIMIT_FSIZE_BYTES = 8 * 1024 * 1024


def _address_space_limit_for(binary: str) -> int:
    """RLIMIT_AS for this binary, or 0 to leave it alone.

    Node cannot run under an address-space cap: V8 reserves a multi-gigabyte
    virtual cage for pointer compression that is never committed, so RLIMIT_AS
    makes thread creation fail at startup. Its heap is bounded through
    NODE_OPTIONS instead, and the container cgroup remains the backstop.

    The JVM has the same shape for a different reason: it reserves its max
    heap, metaspace, and code cache as virtual address space up front, so a
    512 MB RLIMIT_AS kills it before `main` runs. Java is bounded with -Xmx
    instead (see _run_compiled).
    """
    name = Path(binary).name.lower()
    if "node" in name or "java" in name:
        return 0
    return _RLIMIT_AS_BYTES


# NOTE: there is deliberately no RLIMIT_NPROC here. On Linux it caps processes
# per *real UID across the whole host*, not per process tree, so it counts the
# API worker's own threads and makes Node fail to start. Fork bombs are instead
# contained by the process-group kill on timeout (below) and by pids_limit on
# the container in docker-compose.yml.
_LAUNCHER_SRC = """\
import os, resource, sys

as_bytes, cpu, fsize, uid, gid = (int(v) for v in sys.argv[1:6])
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

# Drop privileges here, not through subprocess kwargs. asyncio's
# create_subprocess_exec does not accept Popen's user/group/extra_groups and
# raises "unexpected kwargs" before the child starts, which fails every
# submission whenever the parent is root. Order matters: groups first, because
# after setuid the process can no longer change them.
if gid:
    try:
        os.setgroups([])
    except OSError:
        pass
    os.setgid(gid)
if uid:
    os.setuid(uid)

os.execvp(sys.argv[6], sys.argv[6:])
"""


def _drop_to_unprivileged() -> tuple[int, int] | None:
    """The (uid, gid) to run submissions as, or None when not privileged.

    Only meaningful when the caller is root. In local dev and CI the tests run
    as a normal user, where dropping again is neither possible nor needed.

    `sandbox` is preferred when it exists: the judge image creates it so
    submissions run under an identity that is not the one serving requests, and
    that owns nothing. Images without it (the API) fall back to the generic
    unprivileged accounts.
    """
    if os.geteuid() != 0:
        return None
    for name in ("sandbox", "nobody", "nogroup", "daemon"):
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
        infrastructure_error: bool = False,
    ):
        self.verdict = verdict
        self.runtime_ms = runtime_ms
        self.test_results = test_results
        self.compile_output = compile_output
        # True when the run never reached a grader: the judge was unreachable,
        # the identity token could not be minted, or the deployment lacks a
        # runner for this language. The router must not persist a Submission or
        # move the user's streak for these — the handler's own message says
        # "nothing was graded", and that has to be true.
        self.infrastructure_error = infrastructure_error


async def run_in_sandbox(
    cmd: list[str],
    cwd: str,
    timeout_sec: float = 4.0,
    cpu_sec: int = _RLIMIT_CPU_SEC,
    address_space_bytes: int | None = None,
    stdin_data: bytes | None = None,
) -> tuple[int, str, str, bool]:
    """Runs command with strict timeout, scrubbed env, and captured output.

    The child is denied the API's environment, dropped to an unprivileged uid
    when the parent is root, hard-limited by rlimits, and killed as a process
    group so nothing outlives the timeout.

    `address_space_bytes` replaces the per-binary default for compilation. It
    only applies where there already is a limit: a binary that runs uncapped (the
    JVM and Node reserve multi-gigabyte virtual address space and are bounded by
    other means) must stay uncapped, or it fails to start at all.
    """
    identity = _drop_to_unprivileged()
    uid, gid = identity if identity else (0, 0)
    # The submission's working directory must be reachable by the unprivileged
    # child; mkdtemp creates it 0700 owned by the caller.
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
        # asyncio pauses a subprocess pipe's transport once its StreamReader
        # buffer passes 2x its limit (128 KB by default). A child writing a
        # large result then blocks mid-write, and the drain stalls after exactly
        # two 64 KB reads — which graded every >128 KB harness result as RE.
        # The output budget is 256 KB, so a 1 MB stream limit never pauses.
        "limit": 1 << 20,
    }
    if stdin_data is not None:
        kwargs["stdin"] = asyncio.subprocess.PIPE

    # rlimits and the privilege drop are applied by a launcher that execs the
    # real interpreter. It runs on the same interpreter as the API so it is
    # present in every image.
    launcher = _launcher_path(Path(cwd))
    # 0 means "run uncapped" and must stay that way: giving the JVM an
    # address-space limit stops it before main runs.
    address_space = _address_space_limit_for(cmd[0])
    if address_space and address_space_bytes is not None:
        address_space = address_space_bytes
    launcher_cmd = [
        sys.executable,
        str(launcher),
        str(address_space),
        str(cpu_sec),
        str(_RLIMIT_FSIZE_BYTES),
        str(uid),
        str(gid),
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
        if stdin_data is not None:
            try:
                proc.stdin.write(stdin_data)
                await proc.stdin.drain()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                proc.stdin.close()
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

    await _kill_tree(proc)

    if proc.returncode in (-signal.SIGXCPU, 128 + signal.SIGXCPU):
        return (
            -1,
            "",
            "Time Limit Exceeded (CPU limit exceeded)",
            True,
        )

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
    """Drains both pipes until the child exits, not until EOF.

    EOF is the obvious stopping condition and it is the wrong one: a submission
    that spawns a helper (`subprocess.Popen`, `child_process.spawn`) hands the
    pipe's write end to a process that outlives the direct child, so EOF never
    arrives and the caller's wall-clock wait_for fires. A program that finished
    in milliseconds was graded TLE.

    So: wait for the direct child, then drain while reads keep producing. Each
    read is bounded by an idle window rather than the drain being bounded as a
    whole, which is what lets a legitimate multi-chunk result through. Output is
    accumulated into shared buffers rather than returned from the reader, so
    cancelling a still-blocked reader keeps everything received up to that
    point.

    Output past `budget` is counted, discarded, and drained rather than
    abandoned. Leaving data in the pipe blocks the child on a full buffer, which
    turns an oversized-output run into a timeout and hides the real cause.
    """
    out_buf = bytearray()
    err_buf = bytearray()
    state = {"overflowed": False}

    async def pump(stream: asyncio.StreamReader | None, buf: bytearray) -> None:
        if stream is None:
            return
        while True:
            # Bound each read, not the whole drain. A fixed budget for the
            # entire drain truncated any output larger than one pipe buffer:
            # the reader was cancelled after the first 64 KB while the child
            # still had bytes queued, so a legitimate 65 KB result arrived
            # cut in half and was graded RE. A read that has data returns at
            # once, so this only costs time when the pipe has genuinely stalled
            # — which is the grandchild case it exists for.
            try:
                chunk = await asyncio.wait_for(
                    stream.read(_PIPE_CHUNK), timeout=_READ_IDLE_SEC
                )
            except asyncio.CancelledError:
                # The caller gave up; keep what was already accumulated.
                return
            except Exception:
                # Includes the idle timeout, a pipe error, and EOF races.
                return
            if not chunk:
                return
            room = budget - len(buf)
            if room > 0:
                buf.extend(chunk[:room])
            if len(chunk) > room:
                state["overflowed"] = True

    readers = [
        asyncio.ensure_future(pump(proc.stdout, out_buf)),
        asyncio.ensure_future(pump(proc.stderr, err_buf)),
    ]
    try:
        await proc.wait()
        # Each read is individually bounded above, so this settles: it ends at
        # EOF, or one idle grace window after the pipe stops producing. No
        # outer timeout, because that is what cut large results in half.
        await asyncio.gather(*readers, return_exceptions=True)
    finally:
        for reader in readers:
            if not reader.done():
                reader.cancel()
        await asyncio.gather(*readers, return_exceptions=True)

    return bytes(out_buf), bytes(err_buf), state["overflowed"]


async def _kill_tree(proc: asyncio.subprocess.Process) -> None:
    """SIGKILLs the child's whole process group.

    The group is killed even when the direct child has already exited, because
    that is exactly the case where grandchildren survive: with
    `start_new_session=True` the child is a session leader, so its pid is also
    the process-group id, which stays valid after the child is reaped. The old
    early return on `proc.returncode is not None` skipped the kill in precisely
    the leftover-child scenario, and orphans accumulated for the life of the
    instance.
    """
    with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
        os.killpg(proc.pid, signal.SIGKILL)
    with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
        proc.kill()
    # Reaping prevents a zombie lingering for the worker's lifetime.
    with contextlib.suppress(Exception):
        await asyncio.wait_for(proc.wait(), timeout=5.0)


# Compilation is far heavier than a single test run, so it gets its own budget.
# The heaviest harness in the bank (permutations) compiles in ~14s at -O1 and
# ~51s at -O2; -O1 keeps optimisation while making the compile 3.7x cheaper, and
# these caps sit well above it.
_COMPILE_TIMEOUT_SEC = 120.0
_COMPILE_CPU_SEC = 60

# Compilers get far more address space than a submission does. `g++` peaks
# around 540 MB on the largest harness here, so the 512 MB a run is held to
# turns a valid submission into "cc1plus: out of memory allocating ..." — a
# Compile Error for code that is correct. The container's own memory limit is
# the real ceiling; this only has to avoid being the binding constraint.
_COMPILE_AS_BYTES = 1536 * 1024 * 1024


def _summarise_compile_error(stdout: str, stderr: str) -> str:
    """First handful of compiler diagnostics, which is where the cause is."""
    text = (stderr or stdout or "").strip()
    if not text:
        return "Compilation failed."
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:20])


# V8 reports heap exhaustion as a fatal native crash: a GC log, a FATAL ERROR
# line, and a native stack trace naming the node binary and its shared objects.
# None of that tells a learner anything about their own code, and it leaks
# container paths into the response. Recognise it and say what happened, the way
# a timeout is already reported in plain words.
_NODE_MEMORY_MARKERS = (
    "JavaScript heap out of memory",
    "Ineffective mark-compacts near heap limit",
)


def _summarise_runtime_error(stdout: str, stderr: str) -> str:
    """A readable reason for a non-zero exit, without the runtime's internals."""
    text = (stderr or stdout or "").strip()
    if any(marker in text for marker in _NODE_MEMORY_MARKERS):
        return (
            "Memory limit exceeded: your solution used more memory than the "
            "sandbox allows. Reduce what it stores, or avoid materialising the "
            "whole input."
        )
    if not text:
        # A SIGKILL leaves nothing on stderr. The overwhelming cause here is the
        # CPU rlimit firing, so say that instead of returning an empty message
        # the UI renders as a bare "Runtime Error" with no explanation.
        return (
            "Your solution was stopped before finishing: it exceeded the "
            "per-run CPU budget. Look for an accidental infinite loop or work "
            "that repeats per element."
        )
    return text


def _parse_harness_output(
    stdout: str, marker: str = _RESULT_MARKER
) -> dict[str, Any] | None:
    """Finds the harness result block in stdout.

    The block MUST be marked and MUST be shape-valid. Both requirements are
    load-bearing:

    * Unmarked JSON is not accepted at all. Every harness emits the marker, so a
      bare `{"results": ...}` line is output the student printed — treating it as
      a verdict hands them a free AC.
    * Each result must be an object with a boolean `passed`. A block like
      `{"results": [1]}` used to reach `r.get("passed")` and raise out of
      `execute_code`, surfacing as an unhandled 500 on the submit route.

    The last marked line wins, which is correct because the harness prints after
    the student's code has run; the harnesses then hard-exit so nothing the
    student registered can print afterwards.
    """
    text = (stdout or "").strip()
    if not text:
        return None

    for line in reversed(text.splitlines()):
        stripped = line.strip()
        index = stripped.find(marker)
        if index == -1:
            continue
        try:
            parsed = json.loads(stripped[index + len(marker) :].strip())
        except (ValueError, TypeError):
            continue
        if not _is_well_formed_result(
            parsed, require_passed=(marker == _RESULT_MARKER)
        ):
            continue
        return parsed
    return None


def _is_well_formed_result(
    parsed: Any, require_passed: bool = True
) -> bool:
    """True when `parsed` has the exact shape a verdict needs."""
    if not isinstance(parsed, dict):
        return False
    results = parsed.get("results")
    if not isinstance(results, list):
        return False
    for entry in results:
        if not isinstance(entry, dict):
            return False
        if require_passed and not isinstance(entry.get("passed"), bool):
            return False
    return True


def _grade_harness_output(
    stdout: str,
    test_cases: list[dict[str, Any]],
    *,
    marker: str,
    compiled_language: bool = False,
    return_type: str | None = None,
) -> JudgeResult:
    parsed = _parse_harness_output(stdout, marker)
    if parsed is None:
        return JudgeResult(
            verdict="RE",
            runtime_ms=0,
            test_results=[],
            compile_output="Output parsing error: the harness produced no result block.",
        )

    results = parsed.get("results")
    if not isinstance(results, list) or not results or len(results) != len(test_cases):
        return JudgeResult(
            verdict="RE",
            runtime_ms=0,
            test_results=[],
            compile_output="No test cases ran or the harness returned an invalid result count.",
        )

    graded: list[dict[str, Any]] = []
    for index, (tc, raw) in enumerate(zip(test_cases, results, strict=True)):
        if not isinstance(raw, dict):
            return JudgeResult(
                verdict="RE",
                runtime_ms=0,
                test_results=[],
                compile_output="The harness returned a malformed result.",
            )
        error = str(raw.get("error")) if raw.get("error") else None
        actual = raw.get("actual")
        passed = False
        if error:
            actual = None
        elif compiled_language:
            expected = tc.get("expected")
            if return_type == "double":
                special = {
                    "Infinity": float("inf"),
                    "-Infinity": float("-inf"),
                    "NaN": float("nan"),
                    "inf": float("inf"),
                    "-inf": float("-inf"),
                    "nan": float("nan"),
                }
                if isinstance(actual, str) and actual in special:
                    actual_value = special[actual]
                else:
                    try:
                        actual_value = float(actual)
                    except (TypeError, ValueError):
                        actual_value = actual
                if isinstance(expected, (int, float)) and not isinstance(expected, bool):
                    if isinstance(actual_value, float) and isinstance(expected, float):
                        passed = (
                            (math.isnan(actual_value) and math.isnan(expected))
                            or (
                                math.isinf(actual_value)
                                and math.isinf(expected)
                                and (actual_value > 0) == (expected > 0)
                            )
                            or actual_value == expected
                        )
                    else:
                        passed = actual_value == expected
                else:
                    passed = actual_value == expected
            elif return_type == "TreeNode":
                trimmed = list(expected) if isinstance(expected, list) else expected
                if isinstance(trimmed, list):
                    while trimmed and trimmed[-1] is None:
                        trimmed.pop()
                passed = actual == trimmed
            else:
                passed = actual == expected
        else:
            try:
                passed = json.dumps(tc.get("expected"), sort_keys=True) == json.dumps(
                    actual, sort_keys=True
                )
            except (TypeError, ValueError):
                passed = False

        try:
            runtime_ms = round(float(raw.get("runtime_ms") or 0.0), 2)
        except (TypeError, ValueError):
            runtime_ms = 0.0
        graded.append(
            {
                "label": tc.get("label", f"Case {index + 1}"),
                "passed": passed,
                "input": tc.get("input"),
                "expected": tc.get("expected"),
                "actual": actual,
                "runtime_ms": runtime_ms,
                "error": error,
            }
        )

    try:
        runtime_ms = round(float(parsed.get("totalRuntime") or 0.0), 2)
    except (TypeError, ValueError):
        runtime_ms = 0.0
    return JudgeResult(
        verdict="AC" if all(row["passed"] for row in graded) else "WA",
        runtime_ms=runtime_ms,
        test_results=graded,
    )


async def _run_compiled(
    language: str,
    code: str,
    function_name: str,
    test_cases: list[dict[str, Any]],
    signature: dict[str, Any] | None,
    tmp_path: Path,
    time_limit_ms: int,
    timeout_sec: float,
) -> JudgeResult:
    """Java and C++: compile first, then run.

    The compile step is the point of these languages. A solution whose types
    disagree with the problem's signature does not build, so it comes back as
    a Compile Error with the compiler's own message — never a Wrong Answer.
    """
    if not signature:
        return JudgeResult(
            verdict="CE",
            runtime_ms=0,
            test_results=[],
            compile_output=(
                f"{language} needs a recorded signature (parameter and return types) "
                "and this problem does not have one yet."
            ),
        )

    params = list(signature.get("params") or [])
    return_type = signature.get("returnType")
    run_marker = f"__MERIT_RESULT_{secrets.token_hex(16)}__"

    try:
        if language == "java":
            solution_src, driver_src = java_sources(
                code, function_name, params, return_type, test_cases, run_marker
            )
            (tmp_path / "Solution.java").write_text(solution_src, encoding="utf-8")
            (tmp_path / "Main.java").write_text(driver_src, encoding="utf-8")
            compiler = shutil.which("javac")
            if not compiler:
                return JudgeResult(
                    verdict="CE",
                    runtime_ms=0,
                    test_results=[],
                    compile_output="javac is not installed on this runner.",
                )
            compile_cmd = [compiler, "-encoding", "UTF-8", "Main.java", "Solution.java"]
            # -Xmx bounds the heap because RLIMIT_AS cannot (see
            # _address_space_limit_for); -Xss keeps deep recursion alive.
            run_cmd = [
                shutil.which("java") or "java",
                "-Xmx256m",
                "-Xss16m",
                "-XX:+UseSerialGC",
                "-cp",
                str(tmp_path),
                "Main",
            ]
        else:
            source = cpp_source(
                code, function_name, params, return_type, test_cases, run_marker
            )
            (tmp_path / "solution.cpp").write_text(source, encoding="utf-8")
            compiler = shutil.which("g++")
            if not compiler:
                return JudgeResult(
                    verdict="CE",
                    runtime_ms=0,
                    test_results=[],
                    compile_output="g++ is not installed on this runner.",
                )
            compile_cmd = [compiler, "-std=c++17", "-O1", "-o", "solution", "solution.cpp"]
            run_cmd = [str(tmp_path / "solution")]
    except UnsupportedTypeError as err:
        return JudgeResult(
            verdict="CE",
            runtime_ms=0,
            test_results=[],
            compile_output=(
                f"This problem cannot be generated for {language} yet: {err}"
            ),
        )
    except (TypeError, ValueError, KeyError, IndexError, AttributeError) as err:
        # Test data the signature allows but the author got wrong — a null where
        # an int belongs, a shape that does not match. This used to propagate
        # out of execute_code as an unhandled 500 against the submitter. Bad
        # content is a compile-class failure for this run, not a server error.
        return JudgeResult(
            verdict="CE",
            runtime_ms=0,
            test_results=[],
            compile_output=(
                f"This problem's test data could not be converted to {language}: {err}. "
                "Please report this problem."
            ),
        )

    build_ret, build_out, build_err, build_timed_out = await run_in_sandbox(
        compile_cmd,
        cwd=str(tmp_path),
        timeout_sec=_COMPILE_TIMEOUT_SEC,
        cpu_sec=_COMPILE_CPU_SEC,
        address_space_bytes=_COMPILE_AS_BYTES,
    )
    if build_timed_out:
        return JudgeResult(
            verdict="CE",
            runtime_ms=0,
            test_results=[],
            compile_output="Compilation timed out.",
        )
    if build_ret != 0:
        return JudgeResult(
            verdict="CE",
            runtime_ms=0,
            test_results=[],
            compile_output=_summarise_compile_error(build_out, build_err),
        )

    stdin_payload = (
        run_marker
        + "\n"
        + json.dumps({"inputs": [tc.get("input") or [] for tc in test_cases]})
        + "\n"
    ).encode("utf-8")
    code_ret, stdout, stderr, timed_out = await run_in_sandbox(
        run_cmd,
        cwd=str(tmp_path),
        timeout_sec=timeout_sec,
        stdin_data=stdin_payload,
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
            compile_output=_summarise_runtime_error(stderr, stdout),
        )

    return _grade_harness_output(
        stdout,
        test_cases,
        marker=run_marker,
        compiled_language=True,
        return_type=return_type,
    )


# ---------------------------------------------------------------------------
# Java and C++ harness generation
#
# Kept in this file rather than a sibling module: judge.py is copied into the
# judge image on its own as sandbox.py, so anything it imports would have to
# be copied and imported a second way too.
# ---------------------------------------------------------------------------
# signatures.json type -> per-language spellings.
_TYPES: dict[str, dict[str, str]] = {
    "int": {"java": "int", "cpp": "int"},
    "long": {"java": "long", "cpp": "long long"},
    "double": {"java": "double", "cpp": "double"},
    "boolean": {"java": "boolean", "cpp": "bool"},
    "String": {"java": "String", "cpp": "std::string"},
    "List<Integer>": {"java": "int[]", "cpp": "std::vector<int>"},
    "List<String>": {"java": "String[]", "cpp": "std::vector<std::string>"},
    "List<List<Integer>>": {"java": "int[][]", "cpp": "std::vector<std::vector<int>>"},
    "List<List<String>>": {"java": "String[][]", "cpp": "std::vector<std::vector<std::string>>"},
    "TreeNode": {"java": "TreeNode", "cpp": "TreeNode*"},
}

SUPPORTED_TYPES = set(_TYPES)

# Java serializer method names, one per type.
_JAVA_SER = {
    "int": "serInt",
    "long": "serLong",
    "double": "serDbl",
    "boolean": "serBool",
    "String": "serStr",
    "List<Integer>": "serInts",
    "List<String>": "serStrs",
    "List<List<Integer>>": "serIntGrid",
    "List<List<String>>": "serStrGrid",
    "TreeNode": "serTree",
}

# C++ serializer function names, one per type. The tree helpers are prefixed
# because the learner's code sits in the same translation unit and `buildTree`
# is a plausible name for them to pick — in Java the same helpers are members of
# Main and cannot collide with a method on Solution.
_CPP_SER = {
    "int": "serInt",
    "long": "serLong",
    "double": "serDbl",
    "boolean": "serBool",
    "String": "serStr",
    "List<Integer>": "serInts",
    "List<String>": "serStrs",
    "List<List<Integer>>": "serIntGrid",
    "List<List<String>>": "serStrGrid",
    "TreeNode": "meritSerTree",
}


class UnsupportedTypeError(Exception):
    """The signature declares something the harness cannot emit yet."""


def _check(type_name: str) -> str:
    if type_name not in _TYPES:
        raise UnsupportedTypeError(type_name)
    return type_name


def _has_null(value: list[Any]) -> bool:
    return any(item is None for item in value)


# --- Java -------------------------------------------------------------------


_JAVA_FLOAT_SPECIAL = {
    "inf": "Double.POSITIVE_INFINITY",
    "-inf": "Double.NEGATIVE_INFINITY",
    "nan": "Double.NaN",
}


def _java_double(value: Any) -> str:
    """A Java double literal, including the values `repr` does not spell.

    `repr(float('inf'))` is `inf`, which is not Java source, so a legitimate
    infinite expected value used to compile-error the whole submission.
    """
    number = float(value)
    special = _JAVA_FLOAT_SPECIAL.get(repr(number))
    if special:
        return special
    return repr(number)


def _java_literal(type_name: str, value: Any) -> str:
    _check(type_name)
    if type_name == "int":
        return str(int(value))
    if type_name == "long":
        return f"{int(value)}L"
    if type_name == "double":
        return _java_double(value)
    if type_name == "boolean":
        return "true" if value else "false"
    if type_name == "String":
        if value is None:
            raise UnsupportedTypeError("String expected value is null")
        return json.dumps(str(value))
    if type_name == "List<Integer>":
        # A null inside the list means a tree/linked-list encoding, which is a
        # node type — refuse it loudly rather than emit code that cannot compile.
        if _has_null(value):
            raise UnsupportedTypeError("List<Integer> containing null (node encoding)")
        return "new int[]{" + ", ".join(str(int(x)) for x in value) + "}"
    if type_name == "List<String>":
        return "new String[]{" + ", ".join(json.dumps(str(x)) for x in value) + "}"
    if type_name == "List<List<Integer>>":
        rows = ", ".join("new int[]{" + ", ".join(str(int(x)) for x in row) + "}" for row in value)
        return f"new int[][]{{{rows}}}"
    if type_name == "List<List<String>>":
        rows = ", ".join(
            "new String[]{" + ", ".join(json.dumps(str(x)) for x in row) + "}"
            for row in value
        )
        return f"new String[][]{{{rows}}}"
    if type_name == "TreeNode":
        # The level-order encoding, nulls included: a null marks an absent
        # child, which is exactly what a node type can express and a plain
        # int[] cannot.
        items = ", ".join("null" if x is None else str(int(x)) for x in value)
        return f"buildTree(new Integer[]{{{items}}})"
    raise UnsupportedTypeError(type_name)


# Declared at the top level of Main.java, not nested inside Main, because the
# learner's file is compiled separately: `javac Main.java Solution.java` shares
# one package, so a nested Main.TreeNode would not resolve from Solution.java.
_JAVA_NODE_DECL = """
class TreeNode {
  int val;
  TreeNode left, right;
  TreeNode(int val) { this.val = val; }
}
"""

_JAVA_HELPERS = """
  static TreeNode buildTree(Integer[] a) {
    if (a.length == 0 || a[0] == null) return null;
    // Index-addressed, not a BFS queue: the stored encoding places index i's
    // children at 2i+1 and 2i+2, and every reference solution reads it that
    // way. A queue that skips nulls decodes a different tree whenever the gaps
    // are interior, e.g. [1, null, 2, null, null, 3].
    TreeNode[] nodes = new TreeNode[a.length];
    for (int i = 0; i < a.length; i++) {
      if (a[i] != null) nodes[i] = new TreeNode(a[i]);
    }
    for (int i = 0; i < a.length; i++) {
      if (nodes[i] == null) continue;
      int left = 2 * i + 1, right = 2 * i + 2;
      if (left < a.length) nodes[i].left = nodes[left];
      if (right < a.length) nodes[i].right = nodes[right];
    }
    return nodes[0];
  }
  static String serTree(TreeNode root) {
    if (root == null) return "null";
    java.util.List<String> parts = new java.util.ArrayList<>();
    java.util.Deque<Object[]> frontier = new java.util.LinkedList<>();
    frontier.add(new Object[]{root, 0});
    while (!frontier.isEmpty()) {
      Object[] item = frontier.poll();
      TreeNode node = (TreeNode) item[0];
      int i = (Integer) item[1];
      while (parts.size() <= i) parts.add("null");
      parts.set(i, String.valueOf(node.val));
      if (node.left != null) frontier.add(new Object[]{node.left, 2 * i + 1});
      if (node.right != null) frontier.add(new Object[]{node.right, 2 * i + 2});
    }
    // Trailing nulls describe positions past the last real node, and the stored
    // expectations trim exactly those.
    int end = parts.size();
    while (end > 0 && parts.get(end - 1).equals("null")) end--;
    return "[" + String.join(",", parts.subList(0, end)) + "]";
  }
  static String esc(String s) {
    StringBuilder b = new StringBuilder();
    for (int i = 0; i < s.length(); i++) {
      char c = s.charAt(i);
      switch (c) {
        case '"': b.append("\\\\\\""); break;
        case '\\\\': b.append("\\\\\\\\"); break;
        case '\\n': b.append("\\\\n"); break;
        case '\\r': b.append("\\\\r"); break;
        case '\\t': b.append("\\\\t"); break;
        default:
          if (c < 0x20) b.append(String.format("\\\\u%04x", (int) c));
          else b.append(c);
      }
    }
    return b.toString();
  }
  static String quoted(String s) { return "\\"" + esc(s) + "\\""; }
  static String serInt(int v) { return String.valueOf(v); }
  static String serLong(long v) { return Long.toString(v); }
  static String serDbl(double v) {
    if (Double.isInfinite(v)) return v > 0 ? "\\"Infinity\\"" : "\\"-Infinity\\"";
    if (Double.isNaN(v)) return "\\"NaN\\"";
    return Double.toString(v);
  }
  static String serBool(boolean v) { return v ? "true" : "false"; }
  static String serStr(String v) { return v == null ? "null" : quoted(v); }
  static String serInts(int[] a) {
    StringBuilder b = new StringBuilder("[");
    for (int i = 0; i < a.length; i++) { if (i > 0) b.append(","); b.append(a[i]); }
    return b.append("]").toString();
  }
  static String serStrs(String[] a) {
    StringBuilder b = new StringBuilder("[");
    for (int i = 0; i < a.length; i++) { if (i > 0) b.append(","); b.append(serStr(a[i])); }
    return b.append("]").toString();
  }
  static String serIntGrid(int[][] a) {
    StringBuilder b = new StringBuilder("[");
    for (int i = 0; i < a.length; i++) { if (i > 0) b.append(","); b.append(serInts(a[i])); }
    return b.append("]").toString();
  }
  static String serStrGrid(String[][] a) {
    StringBuilder b = new StringBuilder("[");
    for (int i = 0; i < a.length; i++) { if (i > 0) b.append(","); b.append(serStrs(a[i])); }
    return b.append("]").toString();
  }
  static String serRuntime(double v) {
    return String.format(java.util.Locale.ROOT, "%.3f", v);
  }
"""


def _check_arity(params: list[str], args: list[Any]) -> None:
    """A signature that disagrees with the test data must not generate code.

    Signatures are authored separately from the test cases, so a drift between
    the two is a real failure mode. Without this the generated call would
    silently drop arguments and grade the result as if it were correct.
    """
    if len(args) != len(params):
        raise UnsupportedTypeError(
            f"test case supplies {len(args)} argument(s) but the signature "
            f"declares {len(params)}"
        )


def java_sources(
    code: str,
    function_name: str,
    params: list[str],
    return_type: str,
    test_cases: list[dict[str, Any]],
    marker: str = _RESULT_MARKER,
) -> tuple[str, str]:
    """Returns (solution_source, driver_source). The driver is Main.java."""
    _check(return_type)
    for param in params:
        _check(param)

    # Learners are not expected to write imports, and a duplicate import is
    # legal in Java, so the common ones are prepended unconditionally.
    solution = "import java.util.*;\nimport java.io.*;\n\n" + code

    java_return = _TYPES[return_type]["java"]
    serialize_return = _JAVA_SER[return_type]

    blocks: list[str] = []
    for index, tc in enumerate(test_cases):
        args = tc.get("input") or []
        label = tc.get("label") or f"Case {index + 1}"
        _check_arity(params, args)

        declarations = []
        call_args = []
        for position, (type_name, value) in enumerate(zip(params, args, strict=True)):
            var = f"arg{position}"
            declarations.append(
                f"      {_TYPES[type_name]['java']} {var} = {_java_literal(type_name, value)};"
            )
            call_args.append(var)

        if params:
            serialised = ' + "," + '.join(
                f"{_JAVA_SER[p]}(arg{i})" for i, p in enumerate(params)
            )
            args_json = f'"[" + {serialised} + "]"'
        else:
            args_json = '"[]"'

        blocks.append(
            f"""  static String runCase{index}() {{
    Solution sol = new Solution();
{chr(10).join(declarations)}
    long started = System.nanoTime();
    String actualJson = "null";
    String error = null;
    try {{
      {java_return} actual = sol.{function_name}({", ".join(call_args)});
      actualJson = {serialize_return}(actual);
    }} catch (Throwable thrown) {{
      error = thrown.getClass().getSimpleName() + ": " + String.valueOf(thrown.getMessage());
    }}
    double runtimeMs = (System.nanoTime() - started) / 1e6;
    totalRuntime += runtimeMs;
    StringBuilder sb = new StringBuilder();
    sb.append("{{\\"label\\":").append(quoted({json.dumps(label)}))
      .append(",\\"input\\":").append({args_json})
      .append(",\\"actual\\":").append(actualJson)
      .append(",\\"runtime_ms\\":").append(serRuntime(runtimeMs))
      .append(",\\"error\\":").append(error == null ? "null" : quoted(error))
      .append("}}");
    return sb.toString();
  }}"""
        )

    # One method per case, not one run of blocks inside main. A problem whose
    # expected answers are large (every permutation, every subset) overflows the
    # JVM's 64 KB limit on a single method, and the class fails to compile no
    # matter what the learner wrote. Each case fits comfortably on its own.
    if test_cases:
        appends = ["    sb.append(runCase0());"]
        appends += [
            f'    sb.append(",").append(runCase{i}());' for i in range(1, len(test_cases))
        ]
    else:
        appends = []

    driver = f"""import java.util.*;

{_JAVA_NODE_DECL}

public class Main {{
{_JAVA_HELPERS}
  static double totalRuntime = 0.0;

{chr(10).join(blocks)}

  public static void main(String[] args) {{
    try {{
      java.io.BufferedReader reader = new java.io.BufferedReader(
        new java.io.InputStreamReader(System.in, java.nio.charset.StandardCharsets.UTF_8)
      );
      reader.readLine();
      reader.close();
    }} catch (Exception err) {{
      System.err.println("Failed to read judge marker");
      Runtime.getRuntime().halt(1);
    }}
    StringBuilder sb = new StringBuilder("{{\\"results\\":[");
{chr(10).join(appends)}
    sb.append("],\\"totalRuntime\\":").append(serRuntime(totalRuntime)).append("}}");
    System.out.println({json.dumps(marker)} + sb);
    // halt(), not exit(): exit runs registered shutdown hooks first, and a
    // student can register one that prints a forged result block after this
    // line. halt() terminates immediately and runs none of them.
    Runtime.getRuntime().halt(0);
  }}
}}
"""
    return solution, driver


# --- C++ --------------------------------------------------------------------


_CPP_FLOAT_SPECIAL = {
    "inf": "std::numeric_limits<double>::infinity()",
    "-inf": "(-std::numeric_limits<double>::infinity())",
    "nan": "std::numeric_limits<double>::quiet_NaN()",
}


def _cpp_double(value: Any) -> str:
    """A C++ double literal, including the values `repr` does not spell."""
    number = float(value)
    special = _CPP_FLOAT_SPECIAL.get(repr(number))
    if special:
        return special
    return repr(number)


def _cpp_literal(type_name: str, value: Any) -> str:
    _check(type_name)
    if type_name == "int":
        return str(int(value))
    if type_name == "long":
        return f"{int(value)}LL"
    if type_name == "double":
        return _cpp_double(value)
    if type_name == "boolean":
        return "true" if value else "false"
    if type_name == "String":
        if value is None:
            raise UnsupportedTypeError("String expected value is null")
        return json.dumps(str(value))
    if type_name == "List<Integer>":
        if _has_null(value):
            raise UnsupportedTypeError("List<Integer> containing null (node encoding)")
        return "std::vector<int>{" + ", ".join(str(int(x)) for x in value) + "}"
    if type_name == "List<String>":
        return "std::vector<std::string>{" + ", ".join(json.dumps(str(x)) for x in value) + "}"
    if type_name == "List<List<Integer>>":
        rows = ", ".join(
            "std::vector<int>{" + ", ".join(str(int(x)) for x in row) + "}" for row in value
        )
        return f"std::vector<std::vector<int>>{{{rows}}}"
    if type_name == "List<List<String>>":
        rows = ", ".join(
            "std::vector<std::string>{" + ", ".join(json.dumps(str(x)) for x in row) + "}"
            for row in value
        )
        return f"std::vector<std::vector<std::string>>{{{rows}}}"
    if type_name == "TreeNode":
        items = ", ".join("std::nullopt" if x is None else str(int(x)) for x in value)
        return f"meritBuildTree({{{items}}})"
    raise UnsupportedTypeError(type_name)


# Emitted before the learner's code, because their signature names TreeNode and
# C++ needs the declaration above the use.
_CPP_NODE_DECL = """
struct TreeNode {
  int val;
  TreeNode* left = nullptr;
  TreeNode* right = nullptr;
  TreeNode(int v) : val(v) {}
};

static TreeNode* meritBuildTree(std::initializer_list<std::optional<int>> a) {
  std::vector<std::optional<int>> v(a);
  if (v.empty() || !v[0].has_value()) return nullptr;
  // Index-addressed, matching the stored encoding and every reference solution:
  // index i's children are at 2i+1 and 2i+2. A BFS queue that skips nulls
  // decodes a different tree whenever the gaps are interior.
  std::vector<TreeNode*> nodes(v.size(), nullptr);
  for (size_t i = 0; i < v.size(); i++) {
    if (v[i].has_value()) nodes[i] = new TreeNode(*v[i]);
  }
  for (size_t i = 0; i < v.size(); i++) {
    if (!nodes[i]) continue;
    size_t left = 2 * i + 1, right = 2 * i + 2;
    if (left < v.size()) nodes[i]->left = nodes[left];
    if (right < v.size()) nodes[i]->right = nodes[right];
  }
  return nodes[0];
}

static std::string meritSerTree(TreeNode* root) {
  if (!root) return "null";
  std::vector<std::string> parts;
  std::deque<std::pair<TreeNode*, size_t>> frontier;
  frontier.push_back({root, 0});
  while (!frontier.empty()) {
    auto [node, i] = frontier.front();
    frontier.pop_front();
    while (parts.size() <= i) parts.push_back("null");
    parts[i] = std::to_string(node->val);
    if (node->left) frontier.push_back({node->left, 2 * i + 1});
    if (node->right) frontier.push_back({node->right, 2 * i + 2});
  }
  // Trailing nulls describe positions past the last real node, and the stored
  // expectations trim exactly those.
  while (!parts.empty() && parts.back() == "null") parts.pop_back();
  std::string out = "[";
  for (size_t k = 0; k < parts.size(); k++) { if (k) out += ","; out += parts[k]; }
  return out + "]";
}
"""

_CPP_HELPERS = """
static std::string esc(const std::string& s) {
  std::string out;
  for (unsigned char c : s) {
    switch (c) {
      case '"': out += "\\\\\\""; break;
      case '\\\\': out += "\\\\\\\\"; break;
      case '\\n': out += "\\\\n"; break;
      case '\\r': out += "\\\\r"; break;
      case '\\t': out += "\\\\t"; break;
      default:
        if (c < 0x20) { char buf[8]; std::snprintf(buf, sizeof(buf), "\\\\u%04x", c); out += buf; }
        else out += static_cast<char>(c);
    }
  }
  return out;
}
static std::string jsonStr(const std::string& s) { return "\\"" + esc(s) + "\\""; }
static std::string serInt(int v) { return std::to_string(v); }
static std::string serLong(long long v) { return std::to_string(v); }
static std::string serDbl(double v) {
  if (std::isinf(v)) return v > 0 ? "\\\"Infinity\\\"" : "\\\"-Infinity\\\"";
  if (std::isnan(v)) return "\\\"NaN\\\"";
  std::ostringstream o;
  o << std::setprecision(17) << v;
  return o.str();
}
static std::string serBool(bool v) { return v ? "true" : "false"; }
static std::string serStr(const std::string& v) { return jsonStr(v); }
static std::string serInts(const std::vector<int>& a) {
  std::string out = "[";
  for (size_t i = 0; i < a.size(); i++) { if (i) out += ","; out += std::to_string(a[i]); }
  return out + "]";
}
static std::string serStrs(const std::vector<std::string>& a) {
  std::string out = "[";
  for (size_t i = 0; i < a.size(); i++) { if (i) out += ","; out += jsonStr(a[i]); }
  return out + "]";
}
static std::string serIntGrid(const std::vector<std::vector<int>>& a) {
  std::string out = "[";
  for (size_t i = 0; i < a.size(); i++) { if (i) out += ","; out += serInts(a[i]); }
  return out + "]";
}
static std::string serStrGrid(const std::vector<std::vector<std::string>>& a) {
  std::string out = "[";
  for (size_t i = 0; i < a.size(); i++) { if (i) out += ","; out += serStrs(a[i]); }
  return out + "]";
}
"""


def cpp_source(
    code: str,
    function_name: str,
    params: list[str],
    return_type: str,
    test_cases: list[dict[str, Any]],
    marker: str = _RESULT_MARKER,
) -> str:
    """Returns one translation unit: includes, user code, helpers, driver."""
    _check(return_type)
    for param in params:
        _check(param)

    cpp_return = _TYPES[return_type]["cpp"]
    serialize_return = _CPP_SER[return_type]

    blocks: list[str] = []
    for index, tc in enumerate(test_cases):
        args = tc.get("input") or []
        label = tc.get("label") or f"Case {index + 1}"
        _check_arity(params, args)

        declarations = []
        call_args = []
        for position, (type_name, value) in enumerate(zip(params, args, strict=True)):
            var = f"arg{position}"
            declarations.append(
                f"    {_TYPES[type_name]['cpp']} {var} = {_cpp_literal(type_name, value)};"
            )
            call_args.append(var)

        if params:
            args_json = " + \",\" + ".join(f"{_CPP_SER[p]}(arg{i})" for i, p in enumerate(params))
            args_json = f'"[" + {args_json} + "]"'
        else:
            args_json = '"[]"'

        blocks.append(
            f"""  {{
{chr(10).join(declarations)}
    auto started = std::chrono::steady_clock::now();
    std::string actualJson = "null";
    std::string error;
    try {{
      {cpp_return} actual = sol.{function_name}({", ".join(call_args)});
      actualJson = {serialize_return}(actual);
    }} catch (const std::exception& thrown) {{
      error = thrown.what();
    }} catch (...) {{
      error = "unknown error";
    }}
    double runtimeMs = std::chrono::duration<double, std::milli>(
        std::chrono::steady_clock::now() - started).count();
    totalRuntime += runtimeMs;
    if (caseIndex++ > 0) sb += ",";
    sb += "{{\\"label\\":" + jsonStr({json.dumps(label)})
        + ",\\"input\\":" + {args_json}
        + ",\\"actual\\":" + actualJson
        + ",\\"runtime_ms\\":" + std::to_string(runtimeMs)
        + ",\\"error\\":" + (error.empty() ? std::string("null") : jsonStr(error))
        + "}}";
  }}"""
        )

    return f"""#include <bits/stdc++.h>
#include <cstdlib>
#include <unistd.h>
using namespace std;

__attribute__((constructor(101))) static void merit_read_marker() {{
  char c;
  while (read(0, &c, 1) == 1) {{
    if (c == '\\n') break;
  }}
  close(0);
}}

{_CPP_NODE_DECL}

{code}

{_CPP_HELPERS}

int main() {{
  Solution sol;
  string sb = "{{\\"results\\":[";
  int caseIndex = 0;
  double totalRuntime = 0.0;
{chr(10).join(blocks)}
  sb += "],\\"totalRuntime\\":" + std::to_string(totalRuntime) + "}}";
  cout << {json.dumps(marker)} << sb << endl;
  // _Exit(), not return: returning runs static destructors and any atexit
  // handler, which a student could use to print a forged result afterwards.
  std::_Exit(0);
}}
"""


async def execute_code(
    language: str,
    code: str,
    function_name: str,
    test_cases: list[dict[str, Any]],
    time_limit_ms: int = 2000,
    signature: dict[str, Any] | None = None,
) -> JudgeResult:
    """Executes code against test cases in an isolated sandbox."""
    if not test_cases:
        return JudgeResult(
            verdict="RE",
            runtime_ms=0,
            test_results=[],
            compile_output="No test cases ran. Nothing was graded.",
        )

    if len(code.encode("utf-8")) > MAX_CODE_BYTES:
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
        run_marker = f"__MERIT_RESULT_{secrets.token_hex(16)}__"
        stdin_payload = json.dumps(
            {
                "marker": run_marker,
                "inputs": [tc.get("input") or [] for tc in test_cases],
            },
            separators=(",", ":"),
        ).encode("utf-8")

        if language == "javascript":
            (tmp_path / "user_code.js").write_text(code, encoding="utf-8")
            harness = r"""
import fs from 'node:fs';
import vm from 'node:vm';
import { performance } from 'node:perf_hooks';
const _payload = JSON.parse(fs.readFileSync(0, 'utf8'));
const marker = _payload.marker;
const inputs = _payload.inputs;
const _write = process.stdout.write.bind(process.stdout);
const _exit = process.reallyExit.bind(process);
const _JSON = JSON;
const _now = performance.now.bind(performance);
const userSrc = fs.readFileSync('user_code.js', 'utf8');
const ctx = vm.createContext({
  console, Math, Date, JSON, Array, Object, String, Number, Boolean,
  Map, Set, RegExp, Error, TypeError, RangeError, SyntaxError,
  parseInt, parseFloat, isNaN, isFinite, Infinity, NaN, undefined, BigInt
});
let fn = null;
let loadErr = null;
try { vm.runInContext(userSrc, ctx); } catch (err) { loadErr = err; }
try {
  fn = vm.runInContext(
    "typeof __FUNCTION_NAME__ === 'function' ? __FUNCTION_NAME__ : null",
    ctx
  );
} catch (_) {}
if (typeof fn !== 'function') {
  const msg = loadErr !== null
    ? String((loadErr && (loadErr.stack || loadErr.message)) || loadErr)
    : "Function __FUNCTION_NAME__ is not defined";
  process.stderr.write(msg);
  _exit(1);
}
const results = [];
let totalRuntime = 0;
for (let i = 0; i < inputs.length; i++) {
  const start = _now();
  try {
    const out = fn(...inputs[i]);
    const runtime = _now() - start;
    totalRuntime += runtime;
    if (out === undefined) {
      throw new TypeError("Your function returned undefined here. Every path needs a return.");
    }
    let serialised;
    try {
      serialised = _JSON.stringify(out);
      if (serialised === undefined) throw new TypeError("Result is not JSON serializable");
    } catch (serialiseErr) {
      throw new TypeError(String(serialiseErr.message || serialiseErr));
    }
    results.push({
      label: "Case " + (i + 1),
      actual: _JSON.parse(serialised),
      runtime_ms: Math.round(runtime * 100) / 100,
      error: null
    });
  } catch (err) {
    results.push({
      label: "Case " + (i + 1),
      actual: null,
      runtime_ms: 0,
      error: err.message || String(err)
    });
  }
}
_write(marker + _JSON.stringify({ results, totalRuntime }) + "\n", () => _exit(0));
setTimeout(() => _exit(0), 5000).unref();
"""
            harness = harness.replace("__FUNCTION_NAME__", function_name)
            (tmp_path / "runner.mjs").write_text(harness, encoding="utf-8")

            node_bin = shutil.which("node") or "node"
            code_ret, stdout, stderr, timed_out = await run_in_sandbox(
                [node_bin, str(tmp_path / "runner.mjs")],
                cwd=str(tmp_path),
                timeout_sec=timeout_sec,
                stdin_data=stdin_payload,
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
                    compile_output=_summarise_runtime_error(stderr, stdout),
                )

            return _grade_harness_output(stdout, test_cases, marker=run_marker)

        elif language == "python":
            (tmp_path / "user_code.py").write_text(code, encoding="utf-8")
            harness = r"""
def _merit_run():
    import importlib
    import json
    import os
    import sys
    import time

    payload = json.loads(sys.stdin.read())
    marker = payload["marker"]
    inputs = payload["inputs"]
    _write = os.write
    _exit = os._exit
    _dumps = json.dumps
    _perf = time.perf_counter
    _stdout_flush = sys.stdout.flush
    _stderr_flush = sys.stderr.flush
    try:
        user_code = importlib.import_module("user_code")
    except Exception as err:
        sys.stderr.write(str(err))
        _stderr_flush()
        _exit(1)
    fn = getattr(user_code, __FUNCTION_NAME__, None)
    if not callable(fn):
        sys.stderr.write("Function __FUNCTION_NAME__ is not defined")
        _stderr_flush()
        _exit(1)
    results = []
    total_runtime = 0.0
    for index, args in enumerate(inputs):
        start = _perf()
        try:
            out = fn(*args)
            runtime = (_perf() - start) * 1000.0
            total_runtime += runtime
            try:
                _dumps(out)
            except (TypeError, ValueError) as err:
                raise TypeError(str(err)) from err
            results.append({
                "label": "Case " + str(index + 1),
                "actual": out,
                "runtime_ms": round(runtime, 2),
                "error": None,
            })
        except Exception as err:
            results.append({
                "label": "Case " + str(index + 1),
                "actual": None,
                "runtime_ms": 0.0,
                "error": str(err),
            })
    _stdout_flush()
    _stderr_flush()
    payload_json = _dumps({"results": results, "totalRuntime": total_runtime})
    data = (marker + payload_json + "\n").encode("utf-8")
    view = memoryview(data)
    while view:
        written = _write(1, view)
        if written <= 0:
            break
        view = view[written:]
    _exit(0)


_merit_run()
"""
            harness = harness.replace("__FUNCTION_NAME__", repr(function_name))
            (tmp_path / "runner.py").write_text(harness, encoding="utf-8")

            py_bin = shutil.which("python3") or shutil.which("python") or "python3"
            code_ret, stdout, stderr, timed_out = await run_in_sandbox(
                [py_bin, str(tmp_path / "runner.py")],
                cwd=str(tmp_path),
                timeout_sec=timeout_sec,
                stdin_data=stdin_payload,
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
                    compile_output=_summarise_runtime_error(stderr, stdout),
                )

            return _grade_harness_output(stdout, test_cases, marker=run_marker)

        elif language in ("java", "cpp"):
            return await _run_compiled(
                language=language,
                code=code,
                function_name=function_name,
                test_cases=test_cases,
                signature=signature,
                tmp_path=tmp_path,
                time_limit_ms=time_limit_ms,
                timeout_sec=timeout_sec,
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
