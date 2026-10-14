"""Verify model-authored net-new problem bundles through the real judge and publish.

The mechanical half of the two-model pipeline. It takes authored bundles
(produced by the author subagent) and for each one:

  1. generates test inputs from the signature + statement bounds (JS spec),
  2. derives expected values from the JS optimal implementation,
  3. requires JS brute-force, JS optimal, Python brute-force and Python optimal
     to all agree with those expected values through the production judge,
  4. assembles the bilingual problem JSON and runs the schema + PAF gates,
  5. writes ``content/problems/<slug>.json`` only when every case is AC.

Anything that fails is recorded, never written. This is the oracle the author
cannot argue with; what it *cannot* catch (a statement that passes but tests the
wrong intent) is what the independent reviewer subagent exists for.

Usage:
    python3 content/generators/build_netnew_problem.py [--authored-dir DIR] [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from app.services.judge import execute_code  # noqa: E402
from content.generators.paf.inputs import generate_inputs  # noqa: E402
from content.generators.paf.spec import Algorithm, ProblemSpec  # noqa: E402
from content.taxonomy import CATEGORY_SLUGS  # noqa: E402
from content.validators.schema import ProblemSchema  # noqa: E402
from content.validators.verify_problems import check_paf_gates  # noqa: E402

NETNEW_DIR = REPO_ROOT / ".netnew"
PROBLEMS_DIR = REPO_ROOT / "content" / "problems"

# Held back on purpose, with the reason. The gate verified the repaired bundle,
# but by then the repair had replaced the problem with a different one: the
# authored "Single Element in a Sorted Array" needs an input premise (sorted,
# every value twice except one) that the generator cannot synthesise, and the
# replacement solution is the XOR single-number the live bank already ships
# under the same title. Publishing it would add a duplicate, not coverage.
EXCLUDED_SLUGS = {"single-element-in-a-sorted-array"}

REQUIRED_FIELDS = (
    "slug",
    "title",
    "topic",
    "difficulty",
    "pattern",
    "statement",
    "function_name",
    "signature_js",
    "signature_py",
    "js_brute",
    "js_optimal",
    "py_brute",
    "py_optimal",
    "editorial",
    "hints",
    "reading_links",
)


def _strip_title_header(statement: str) -> str:
    """Match the normalized bank: no leading `# Title` (the page renders it)."""
    text = statement.strip()
    if text.startswith("#"):
        lines = text.split("\n")
        if lines and lines[0].lstrip().startswith("#"):
            text = "\n".join(lines[1:]).strip()
    return text


def _display_input(parameters, values) -> str:
    return ", ".join(
        f"{p.name} = {json.dumps(v, ensure_ascii=False)}"
        for p, v in zip(parameters, values)
    )


def _fail(label: str, result) -> str:
    detail = (result.compile_output or "").strip()
    failures = [
        f"{row.get('label')}: {row.get('error') or 'mismatch'}"
        for row in result.test_results
        if not row.get("passed")
    ]
    return f"{label} {result.verdict}" + (
        f" :: {detail or '; '.join(failures[:3])}" if (detail or failures) else ""
    )


def normalize_js_signature(signature: str) -> str:
    """Drop a JavaScript *return* annotation, leaving parameter types intact.

    The test generator derives its input types from `signature_js`, so parameter
    annotations are load-bearing: a bare `function solve(nums)` is rejected with
    "needs a TypeScript-style type annotation for test generation". A return
    annotation is the opposite failure — the parser matches `function name(args)`
    and refuses the trailing `: Type`. Only that trailing annotation is removed.
    """
    text = (signature or "").strip()
    close = text.rfind(")")
    if "(" not in text or close == -1:
        return text
    if text[close + 1 :].strip().startswith(":"):
        text = text[: close + 1]
    return text.strip()


async def verify_bundle(bundle: dict) -> tuple[dict | None, list[str]]:
    """Return (verified_problem_data, errors). data is None when anything fails."""
    errors: list[str] = []
    missing = [f for f in REQUIRED_FIELDS if not bundle.get(f)]
    if missing:
        return None, [f"missing fields: {', '.join(missing)}"]

    slug = bundle["slug"]
    topic = bundle["topic"]
    if topic not in CATEGORY_SLUGS:
        return None, [f"unknown topic '{topic}'"]

    try:
        alphabets = bundle.get("string_alphabets") or {}
        js_spec = ProblemSpec(
            signature=normalize_js_signature(bundle["signature_js"]),
            statement=bundle["statement"],
            brute_force=Algorithm(bundle["js_brute"], bundle.get("js_brute_complexity", ""), "javascript"),
            optimal=Algorithm(bundle["js_optimal"], bundle.get("js_optimal_complexity", ""), "javascript"),
            topic=topic,
            difficulty=bundle["difficulty"],
            pattern=bundle["pattern"],
            title=bundle["title"],
            slug=slug,
            string_alphabets=alphabets,
        )
        py_spec = ProblemSpec(
            signature=bundle["signature_py"],
            statement=bundle["statement"],
            brute_force=Algorithm(bundle["py_brute"], bundle.get("py_brute_complexity", ""), "python"),
            optimal=Algorithm(bundle["py_optimal"], bundle.get("py_optimal_complexity", ""), "python"),
            topic=topic,
            difficulty=bundle["difficulty"],
            pattern=bundle["pattern"],
            title=bundle["title"],
            slug=slug,
            string_alphabets=alphabets,
        )
    except Exception as err:  # noqa: BLE001 - author input, report verbatim
        return None, [f"spec build failed: {err}"]
    if js_spec.function_name != py_spec.function_name:
        return None, [
            f"function name mismatch: js '{js_spec.function_name}' vs py '{py_spec.function_name}'"
        ]
    fn = js_spec.function_name

    try:
        cases = generate_inputs(js_spec, random_cases=16, stress_cases=4)
    except Exception as err:  # noqa: BLE001
        return None, [f"input generation failed: {err}"]

    limit = bundle.get("time_limit_ms", 2000)

    async def run(code: str, language: str, use_cases):
        return await execute_code(
            language=language,
            code=code,
            function_name=fn,
            test_cases=copy.deepcopy(use_cases),
            time_limit_ms=limit,
        )

    # 1. JS optimal produces the expected values.
    js_opt = await run(bundle["js_optimal"], "javascript", cases)
    if js_opt.compile_output or len(js_opt.test_results) != len(cases):
        return None, [_fail("js-optimal", js_opt)]
    for case, row in zip(cases, js_opt.test_results, strict=True):
        if row.get("error") is not None or "actual" not in row:
            return None, [_fail("js-optimal", js_opt)]
        case["expected"] = row["actual"]

    # 2. All four implementations must reproduce those expected values.
    js_brute, py_opt, py_brute = await asyncio.gather(
        run(bundle["js_brute"], "javascript", cases),
        run(bundle["py_optimal"], "python", cases),
        run(bundle["py_brute"], "python", cases),
    )
    for label, result in (("js-brute", js_brute), ("py-optimal", py_opt), ("py-brute", py_brute)):
        if result.verdict != "AC":
            errors.append(_fail(label, result))
    if errors:
        return None, errors

    constraints = [
        f"Function signature: `{bundle['signature_js'].strip().rstrip(':').rstrip('{').strip()}`.",
        "Inputs are JSON-serializable values satisfying the bounds stated above.",
    ]
    examples = [
        {
            "input": _display_input(js_spec.parsed_signature.parameters, case["input"]),
            "output": json.dumps(case["expected"], ensure_ascii=False),
            "explanation": "Generated from the verified optimal implementation.",
        }
        for case in cases[:2]
    ]

    def starter(fn_name: str, names: str, language: str) -> str:
        if language == "python":
            return f"def {fn_name}({names}):\n    # Write your solution here\n    raise NotImplementedError\n"
        return f"function {fn_name}({names}) {{\n  // Write your solution here\n  throw new Error('Not implemented');\n}}\n"

    names = ", ".join(p.name for p in js_spec.parsed_signature.parameters)

    data = {
        "slug": slug,
        "title": bundle["title"],
        "topic": topic,
        "difficulty": bundle["difficulty"],
        "pattern": bundle["pattern"],
        "statement": _strip_title_header(bundle["statement"]) + "\n",
        "examples": examples,
        "constraints": constraints,
        "hints": list(bundle["hints"])[:4],
        "editorial": {
            "approach": bundle["editorial"]["approach"],
            "why_optimal": bundle["editorial"]["why_optimal"],
            "pitfalls": bundle["editorial"]["pitfalls"],
        },
        "reading_links": list(bundle["reading_links"])[:3],
        "starterCode": {
            "javascript": starter(fn, names, "javascript"),
            "python": starter(fn, names, "python"),
        },
        "functionName": fn,
        "timeLimitMs": limit,
        "reviewStatus": "verified",
        "pafVerification": {
            "seed": 42,
            "generatedCaseCount": len(cases),
            "bruteForceRuntimeMs": js_brute.runtime_ms,
            "optimalRuntimeMs": js_opt.runtime_ms,
            "crossLanguage": True,
        },
        "testCases": [
            {
                "label": case["label"],
                "input": case["input"],
                "expected": case["expected"],
                "isSample": idx < 2,
            }
            for idx, case in enumerate(cases)
        ],
        "solutions": [
            {
                "title": "Brute Force",
                "complexity": bundle.get("js_brute_complexity", "Complexity profiled by PAF"),
                "language": "javascript",
                "code": bundle["js_brute"],
                "isReference": False,
            },
            {
                "title": "Optimal",
                "complexity": bundle.get("js_optimal_complexity", "Complexity profiled by PAF"),
                "language": "javascript",
                "code": bundle["js_optimal"],
                "isReference": True,
            },
        ],
    }

    gate_errors = check_paf_gates(data, f"{slug}.json")
    if gate_errors:
        return None, gate_errors

    # Java/C++ starters and the signatures.json entry are derived from the test
    # data. A shape with no compiled equivalent cannot ship: the bundle sync
    # refuses a problem the editor cannot run in all four languages, so it is a
    # gate failure that goes back to the author, not a silent omission.
    from content.generators.derive_compiled_types import derive_compiled

    param_names = [p.name for p in js_spec.parsed_signature.parameters]
    starters, signature_entry, warnings = derive_compiled(data, param_names)
    if warnings:
        return None, [f"compiled types: {w}" for w in warnings]

    # Compile-only check on the heavy tier. The derived starter must build against
    # the harness the judge generates from the same signature, otherwise the
    # editor hands the learner Java/C++ that cannot compile. The starter throws
    # "Not implemented", so a clean build surfaces as RE/WA, never as AC — only a
    # CE means the signature, the harness and the starter disagree.
    for lang, starter in (("java", starters["java"]), ("cpp", starters["cpp"])):
        probe = await execute_code(
            language=lang,
            code=starter,
            function_name=fn,
            test_cases=copy.deepcopy(cases[:1]),
            time_limit_ms=limit,
            signature=signature_entry,
        )
        if probe.verdict == "CE":
            return None, [
                f"{lang} starter does not compile against its harness: "
                f"{(probe.compile_output or '').strip()[:200]}"
            ]

    data["starterCode"].update(starters)

    try:
        ProblemSchema(**data)
    except Exception as err:  # noqa: BLE001
        return None, [f"schema: {err}"]

    data["_signature_entry"] = signature_entry
    return data, []


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authored-dir", default=str(NETNEW_DIR))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    authored_dir = Path(args.authored_dir)
    bundles: dict[str, dict] = {}
    for pattern in ("authored_*.json", "repaired_*.json"):
        for path in sorted(authored_dir.glob(pattern)):
            payload = json.loads(path.read_text(encoding="utf-8"))
            entries = payload.get("problems") if isinstance(payload, dict) else payload
            for entry in entries or []:
                if entry.get("slug"):
                    bundles[entry["slug"]] = entry

    print(f"authored bundles: {len(bundles)}")
    passed: list[str] = []
    failed: dict[str, list[str]] = {}
    excluded: list[str] = []
    signature_entries: dict[str, dict] = {}

    for slug, bundle in sorted(bundles.items()):
        if slug in EXCLUDED_SLUGS:
            print(f"  SKIP {slug}: excluded on purpose (see EXCLUDED_SLUGS)")
            excluded.append(slug)
            continue
        data, errors = await verify_bundle(bundle)
        if errors or data is None:
            failed[slug] = errors
            print(f"  FAIL {slug}: {errors[0] if errors else 'unknown'}")
            continue
        passed.append(slug)
        signature_entries[slug] = data.pop("_signature_entry")
        out = PROBLEMS_DIR / f"{slug}.json"
        if not args.dry_run:
            out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        n = data["pafVerification"]["generatedCaseCount"]
        print(f"  PASS {slug}: {n} cases, 4 solutions AC, java+cpp derived")

    report = {"passed": passed, "failed": failed, "excluded": excluded}
    (NETNEW_DIR / "gate_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    (NETNEW_DIR / "signatures_new.json").write_text(
        json.dumps(signature_entries, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nverified {len(passed)} / {len(bundles)}  (failures: {len(failed)})")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
