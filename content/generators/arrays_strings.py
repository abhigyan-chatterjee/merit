"""Arrays & Strings question generator ported to Question Authoring Framework (QAF)."""

from content.generators.base import GeneratedQuestion
from content.generators.qaf.engine import generate_all_qaf
from content.generators.qaf.oracles import (
    kadane_oracle,
    max_sum_fixed_oracle,
    min_window_substring_oracle,
    prefix_sum_oracle,
)
from content.generators.qaf.specs.arrays_strings import ARRAY_STRING_SPECS


def generate_array_string_questions(
    count: int = 150,
    seed: int = 49,
) -> list[GeneratedQuestion]:
    """Generate verified questions for Arrays & Strings designs via QAF."""
    questions = generate_all_qaf(specs=ARRAY_STRING_SPECS, instance_cap=4)
    return questions[:count]


__all__ = [
    "ARRAY_STRING_SPECS",
    "generate_array_string_questions",
    "kadane_oracle",
    "max_sum_fixed_oracle",
    "min_window_substring_oracle",
    "prefix_sum_oracle",
]
