"""Question Authoring Framework (QAF): declarative question design system."""

from content.generators.qaf import specs
from content.generators.qaf.distractors import (
    DistractorStrategy,
    FixedDistractorStrategy,
    NumericOffsetStrategy,
    OffByOneStrategy,
    WrongComplexityStrategy,
    get_distractor_strategy,
    register_distractor_strategy,
)
from content.generators.qaf.engine import (
    generate_all_qaf,
    generate_instances_for_spec,
)
from content.generators.qaf.oracles import (
    get_oracle,
    register_oracle,
)
from content.generators.qaf.spec import (
    DesignSpec,
    get_all_specs,
    get_spec,
    register_spec,
)

__all__ = [
    "DesignSpec",
    "DistractorStrategy",
    "FixedDistractorStrategy",
    "NumericOffsetStrategy",
    "OffByOneStrategy",
    "WrongComplexityStrategy",
    "generate_all_qaf",
    "generate_instances_for_spec",
    "get_all_specs",
    "get_distractor_strategy",
    "get_oracle",
    "get_spec",
    "register_distractor_strategy",
    "register_oracle",
    "register_spec",
    "specs",
]
