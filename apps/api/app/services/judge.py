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
    cpu_sec: int = _RLIMIT_CPU_SEC,
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
        str(cpu_sec),
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


# Compilation is far heavier than a single test run, so it gets its own budget.
_COMPILE_TIMEOUT_SEC = 90.0
_COMPILE_CPU_SEC = 30


def _summarise_compile_error(stdout: str, stderr: str) -> str:
    """First handful of compiler diagnostics, which is where the cause is."""
    text = (stderr or stdout or "").strip()
    if not text:
        return "Compilation failed."
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:20])


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

    try:
        if language == "java":
            solution_src, driver_src = java_sources(
                code, function_name, params, return_type, test_cases
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
            source = cpp_source(code, function_name, params, return_type, test_cases)
            (tmp_path / "solution.cpp").write_text(source, encoding="utf-8")
            compiler = shutil.which("g++")
            if not compiler:
                return JudgeResult(
                    verdict="CE",
                    runtime_ms=0,
                    test_results=[],
                    compile_output="g++ is not installed on this runner.",
                )
            compile_cmd = [compiler, "-std=c++17", "-O2", "-o", "solution", "solution.cpp"]
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

    build_ret, build_out, build_err, build_timed_out = await run_in_sandbox(
        compile_cmd,
        cwd=str(tmp_path),
        timeout_sec=_COMPILE_TIMEOUT_SEC,
        cpu_sec=_COMPILE_CPU_SEC,
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

    code_ret, stdout, stderr, timed_out = await run_in_sandbox(
        run_cmd, cwd=str(tmp_path), timeout_sec=timeout_sec
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
        return JudgeResult(
            verdict="AC" if all_passed else "WA",
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
    "double": {"java": "double", "cpp": "double"},
    "boolean": {"java": "boolean", "cpp": "bool"},
    "String": {"java": "String", "cpp": "std::string"},
    "List<Integer>": {"java": "int[]", "cpp": "std::vector<int>"},
    "List<String>": {"java": "String[]", "cpp": "std::vector<std::string>"},
    "List<List<Integer>>": {"java": "int[][]", "cpp": "std::vector<std::vector<int>>"},
    "List<List<String>>": {"java": "String[][]", "cpp": "std::vector<std::vector<std::string>>"},
}

SUPPORTED_TYPES = set(_TYPES)

# Java serializer method names, one per type.
_JAVA_SER = {
    "int": "serInt",
    "double": "serDbl",
    "boolean": "serBool",
    "String": "serStr",
    "List<Integer>": "serInts",
    "List<String>": "serStrs",
    "List<List<Integer>>": "serIntGrid",
    "List<List<String>>": "serStrGrid",
}

# C++ serializer function names, one per type.
_CPP_SER = {
    "int": "serInt",
    "double": "serDbl",
    "boolean": "serBool",
    "String": "serStr",
    "List<Integer>": "serInts",
    "List<String>": "serStrs",
    "List<List<Integer>>": "serIntGrid",
    "List<List<String>>": "serStrGrid",
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


def _java_literal(type_name: str, value: Any) -> str:
    _check(type_name)
    if type_name == "int":
        return str(int(value))
    if type_name == "double":
        return repr(float(value))
    if type_name == "boolean":
        return "true" if value else "false"
    if type_name == "String":
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
    raise UnsupportedTypeError(type_name)


_JAVA_HELPERS = """
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
  static String serDbl(double v) { return Double.toString(v); }
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
            f"""    {{
{chr(10).join(declarations)}
      {java_return} expected = {_java_literal(return_type, tc.get("expected"))};
      long started = System.nanoTime();
      String actualJson = "null";
      String error = null;
      boolean passed = false;
      try {{
        {java_return} actual = sol.{function_name}({", ".join(call_args)});
        actualJson = {serialize_return}(actual);
        passed = actualJson.equals({serialize_return}(expected));
      }} catch (Throwable thrown) {{
        error = thrown.getClass().getSimpleName() + ": " + String.valueOf(thrown.getMessage());
      }}
      double runtimeMs = (System.nanoTime() - started) / 1e6;
      total += runtimeMs;
      if (caseIndex++ > 0) sb.append(",");
      sb.append("{{\\"label\\":").append(quoted({json.dumps(label)}))
        .append(",\\"passed\\":").append(passed)
        .append(",\\"input\\":").append({args_json})
        .append(",\\"expected\\":").append({serialize_return}(expected))
        .append(",\\"actual\\":").append(actualJson)
        .append(",\\"runtime_ms\\":").append(serRuntime(runtimeMs))
        .append(",\\"error\\":").append(error == null ? "null" : quoted(error))
        .append("}}");
    }}"""
        )

    driver = f"""import java.util.*;

public class Main {{
{_JAVA_HELPERS}
  public static void main(String[] args) {{
    Solution sol = new Solution();
    StringBuilder sb = new StringBuilder("{{\\"results\\":[");
    double total = 0.0;
    int caseIndex = 0;
{chr(10).join(blocks)}
    sb.append("],\\"totalRuntime\\":").append(serRuntime(total)).append("}}");
    System.out.println(sb);
  }}
}}
"""
    return solution, driver


# --- C++ --------------------------------------------------------------------


def _cpp_literal(type_name: str, value: Any) -> str:
    _check(type_name)
    if type_name == "int":
        return str(int(value))
    if type_name == "double":
        return repr(float(value))
    if type_name == "boolean":
        return "true" if value else "false"
    if type_name == "String":
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
    raise UnsupportedTypeError(type_name)


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
static std::string serDbl(double v) {
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
    {cpp_return} expected = {_cpp_literal(return_type, tc.get("expected"))};
    auto started = std::chrono::steady_clock::now();
    std::string actualJson = "null";
    std::string error;
    bool passed = false;
    try {{
      {cpp_return} actual = sol.{function_name}({", ".join(call_args)});
      actualJson = {serialize_return}(actual);
      passed = (actualJson == {serialize_return}(expected));
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
        + ",\\"passed\\":" + std::string(passed ? "true" : "false")
        + ",\\"input\\":" + {args_json}
        + ",\\"expected\\":" + {serialize_return}(expected)
        + ",\\"actual\\":" + actualJson
        + ",\\"runtime_ms\\":" + std::to_string(runtimeMs)
        + ",\\"error\\":" + (error.empty() ? std::string("null") : jsonStr(error))
        + "}}";
  }}"""
        )

    return f"""#include <bits/stdc++.h>
using namespace std;

{code}

{_CPP_HELPERS}

int main() {{
  Solution sol;
  string sb = "{{\\"results\\":[";
  int caseIndex = 0;
  double totalRuntime = 0.0;
{chr(10).join(blocks)}
  sb += "],\\"totalRuntime\\":" + std::to_string(totalRuntime) + "}}";
  cout << sb << endl;
  return 0;
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
