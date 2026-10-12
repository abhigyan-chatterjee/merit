"""Tests for the QAF design registry.

`clear_specs` exists for test isolation and had no caller anywhere in the repo,
which is the same as not existing. These exercise it against the registry it
clears, so a change that silently stops clearing is caught.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from content.generators.qaf.spec import (  # noqa: E402
    DesignSpec,
    clear_specs,
    get_all_specs,
    get_spec,
    register_spec,
)


def _spec(key: str) -> DesignSpec:
    return DesignSpec(
        key=key,
        topic="arrays-hashing",
        subtopic="basics",
        oracle="kadane",
        sample=lambda rng: {"n": rng.randint(1, 5)},
        prompt="{n}",
        explanation="{answer}",
        difficulty="Easy",
        distractors="numeric_offsets",
    )


@pytest.fixture(autouse=True)
def isolated_registry():
    """Every test starts and ends with an empty registry."""
    clear_specs()
    yield
    clear_specs()


def test_register_then_get_returns_the_same_spec():
    spec = _spec("qaf-registry-probe")
    register_spec(spec)
    assert get_spec("qaf-registry-probe") is spec
    assert get_all_specs() == [spec]


def test_clear_specs_empties_the_registry():
    register_spec(_spec("qaf-registry-a"))
    register_spec(_spec("qaf-registry-b"))
    assert len(get_all_specs()) == 2

    clear_specs()

    assert get_all_specs() == []
    with pytest.raises(KeyError):
        get_spec("qaf-registry-a")


def test_registry_is_isolated_between_tests():
    """The autouse fixture is what makes the previous test's keys absent."""
    assert get_all_specs() == []
    with pytest.raises(KeyError):
        get_spec("qaf-registry-a")


def test_sample_is_deterministic_for_a_seed():
    spec = _spec("qaf-registry-sample")
    assert spec.sample(random.Random(7)) == spec.sample(random.Random(7))
