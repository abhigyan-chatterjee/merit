import pytest
from pydantic import ValidationError

from content.validators.schema import LearningPathSchema


def _path(summary: str = "A useful beginner summary.") -> dict:
    return {
        "slug": "sample",
        "title": "Sample",
        "blurb": "A sample learning path.",
        "icon": "LayoutGrid",
        "track": "foundational",
        "ordinal": 1,
        "steps": [
            {
                "ordinal": 1,
                "step_type": "mock",
                "ref_id": "mixed",
                "title": "Sample mock",
                "summary": summary,
                "reading_links": [],
            }
        ],
    }


def test_path_schema_requires_step_summaries():
    data = _path()
    data["steps"][0]["summary"] = None
    with pytest.raises(ValidationError):
        LearningPathSchema(**data)


def test_path_schema_caps_summary_length():
    with pytest.raises(ValidationError):
        LearningPathSchema(**_path("x" * 161))
