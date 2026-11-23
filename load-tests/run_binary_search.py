#!/usr/bin/env python3
"""Binary Search Load Simulator via k6.

Tests realistic user traffic (70% read-heavy, 30% Cloud Run judge submissions)
and searches for the server's stable concurrent VU limit.
Logs all steps and results to load-tests/vu_search.log.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOAD_TESTS_DIR = REPO_ROOT / "load-tests"
LOG_FILE = LOAD_TESTS_DIR / "vu_search.log"
SCRIPT_PATH = "/load-tests/realistic_simulation.js"
TARGET_URL = os.environ.get("TARGET_URL", "http://127.0.0.1:8000")

DURATION_PER_STEP = "25s"
MAX_ERROR_RATE = 10.0  # percent
MAX_P95_MS = 2500.0   # milliseconds
MIN_CHECKS_PASS = 95.0 # percent


def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def parse_duration_to_ms(val_str: str) -> float:
    val_str = val_str.strip()
    if val_str.endswith("ms"):
        return float(val_str[:-2])
    elif val_str.endswith("s"):
        return float(val_str[:-1]) * 1000.0
    elif val_str.endswith("m"):
        return float(val_str[:-1]) * 60000.0
    return float(val_str)


def run_k6_step(vus: int) -> dict:
    log(f"--- Running load step with {vus} VUs for {DURATION_PER_STEP} ---")
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{LOAD_TESTS_DIR}:/load-tests:ro",
        "-e", f"TARGET_URL={TARGET_URL}",
        "-e", f"VUS={vus}",
        "-e", f"DURATION={DURATION_PER_STEP}",
        "grafana/k6", "run", SCRIPT_PATH,
    ]

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output = proc.stdout

    if proc.returncode != 0:
        raise RuntimeError(
            f"k6 run failed with exit code {proc.returncode}:\n{output[-2000:]}"
        )

    # Parse metrics from k6 output
    # Checks: checks_succeeded...: 100.00% 13 out of 13
    checks_match = re.search(r"checks_succeeded\.\.\.:\s*([\d\.]+)%", output)
    if not checks_match:
        raise ValueError("missing checks_succeeded metric in k6 output")
    checks_pct = float(checks_match.group(1))

    # HTTP failed rate: http_req_failed................: 2.48% 65 out of 2615
    failed_match = re.search(r"http_req_failed\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.:\s*([\d\.]+)%", output)
    if not failed_match:
        raise ValueError("missing http_req_failed metric in k6 output")
    failed_pct = float(failed_match.group(1))

    # Total HTTP requests: http_reqs......................: 2615
    reqs_match = re.search(r"http_reqs\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.:\s*(\d+)", output)
    if not reqs_match:
        raise ValueError("missing http_reqs metric in k6 output")
    total_reqs = int(reqs_match.group(1))

    # Duration p95: http_req_duration..............: avg=... min=... med=... max=... p(90)=... p(95)=13.24s
    p95_match = re.search(r"http_req_duration\.\.\.\.\.\.\.\.\.\.\.\.\.\.:[^\n]*p\(95\)=([\d\.]+(?:ms|s|m))", output)
    if not p95_match:
        raise ValueError("missing p95 metric in k6 output")
    p95_ms = parse_duration_to_ms(p95_match.group(1))

    # Median duration: med=...
    med_match = re.search(r"http_req_duration\.\.\.\.\.\.\.\.\.\.\.\.\.\.:[^\n]*med=([\d\.]+(?:ms|s|m))", output)
    if not med_match:
        raise ValueError("missing median metric in k6 output")
    med_ms = parse_duration_to_ms(med_match.group(1))

    passed = (failed_pct <= MAX_ERROR_RATE) and (p95_ms <= MAX_P95_MS) and (checks_pct >= MIN_CHECKS_PASS)

    result = {
        "vus": vus,
        "passed": passed,
        "failed_pct": failed_pct,
        "p95_ms": p95_ms,
        "med_ms": med_ms,
        "checks_pct": checks_pct,
        "total_reqs": total_reqs,
    }

    status_str = "PASS" if passed else "FAIL"
    log(
        f"Result for {vus} VUs -> {status_str} | "
        f"Reqs: {total_reqs} | Error Rate: {failed_pct:.2f}% | "
        f"p95: {p95_ms:.1f}ms | Median: {med_ms:.1f}ms | Checks: {checks_pct:.1f}%"
    )
    return result


def binary_search_vus(low: int = 5, high: int = 150, initial_probe: int = 50):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"=== Starting VU Binary Search Load Simulation at {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        f.write(f"Target: {TARGET_URL}\n")
        f.write(f"Parameters: 70% Read-heavy / 30% Judge Submissions, step duration {DURATION_PER_STEP}\n")
        f.write(f"Thresholds: Error Rate <= {MAX_ERROR_RATE}%, p95 <= {MAX_P95_MS}ms, Checks >= {MIN_CHECKS_PASS}%\n\n")

    log(f"Starting Binary Search. Bounds: [{low}, {high}], Initial Probe: {initial_probe}")

    history = []
    current = initial_probe
    max_stable_vus = 0

    iteration = 1
    max_iterations = 7

    while iteration <= max_iterations and low <= high:
        log(f"=== Iteration {iteration}: Testing target VU={current} (Range: [{low}, {high}]) ===")
        res = run_k6_step(current)
        history.append(res)

        if res["passed"]:
            max_stable_vus = max(max_stable_vus, current)
            log(f"VU={current} PASSED. Raising lower bound from {low} to {current + 1}.")
            low = current + 1
        else:
            log(f"VU={current} FAILED thresholds. Lowering upper bound from {high} to {current - 1}.")
            high = current - 1

        if low > high:
            log("Search bounds converged.")
            break

        # Cooldown sleep between steps to let queues drain
        log("Cooling down 5s before next step...")
        time.sleep(5)

        next_vu = (low + high) // 2
        if next_vu == current:
            break
        current = next_vu
        iteration += 1

    log("=" * 60)
    log(f"BINARY SEARCH COMPLETE. Maximum Stable Capacity: {max_stable_vus} VUs")
    log("=" * 60)
    return max_stable_vus, history


if __name__ == "__main__":
    binary_search_vus()
