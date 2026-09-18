"""Tests for PAF editorial/reading-links/hints gates (Ticket 1.1)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from content.validators.verify_problems import check_paf_gates


def _complete_paf_dict() -> dict:
    return {
        "slug": "paf-sample",
        "pafVerification": {"seed": 42, "generatedCaseCount": 5},
        "editorial": {
            "approach": "Scan once with a hash map.",
            "why_optimal": "Each lookup is O(1) so the pass is linear.",
            "pitfalls": "Watch for duplicate values overwriting indices.",
        },
        "reading_links": ["https://example.com/hash-map-guide"],
        "hints": ["Try brute force first.", "Cache complements.", "Check duplicates."],
    }


def test_paf_shaped_dict_missing_editorial_fails():
    data = _complete_paf_dict()
    del data["editorial"]
    errors = check_paf_gates(data, "paf-sample.json")
    assert errors, "PAF-shaped dict without editorial must fail"
    assert any("editorial" in err for err in errors)


def test_paf_shaped_dict_missing_links_fails():
    data = _complete_paf_dict()
    del data["reading_links"]
    errors = check_paf_gates(data, "paf-sample.json")
    assert errors, "PAF-shaped dict without reading_links must fail"
    assert any("reading_links" in err for err in errors)


def test_paf_shaped_dict_too_few_hints_fails():
    data = _complete_paf_dict()
    data["hints"] = ["Only one hint.", "Only one hint."]
    errors = check_paf_gates(data, "paf-sample.json")
    assert errors, "PAF-shaped dict with <3 distinct hints must fail"
    assert any("hints" in err for err in errors)


def test_complete_paf_shaped_dict_passes():
    assert check_paf_gates(_complete_paf_dict(), "paf-sample.json") == []


def test_legacy_dict_without_paf_verification_passes(capsys):
    data = {"slug": "two-sum", "hints": ["One hint."]}
    assert check_paf_gates(data, "two-sum.json") == []
    captured = capsys.readouterr()
    assert "legacy" in captured.out.lower()
