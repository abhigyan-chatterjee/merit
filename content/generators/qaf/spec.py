"""Declarative design record specification for QAF."""

import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from content.generators.qaf.distractors import (
    DistractorStrategy,
    get_distractor_strategy,
)
from content.generators.qaf.oracles import get_oracle

DifficultyType = Literal["Easy", "Medium", "Hard"]
DifficultyRule = DifficultyType | Callable[[dict[str, Any]], DifficultyType]


@dataclass
class DesignSpec:
    """A declarative question design record."""

    key: str
    topic: str
    subtopic: str
    oracle: str | Callable[..., Any]
    sample: Callable[[random.Random], dict[str, Any]]
    prompt: str | Callable[[dict[str, Any]], str]
    explanation: str | Callable[[dict[str, Any]], str]
    difficulty: DifficultyRule
    distractors: str | Callable[..., list[str]] | DistractorStrategy
    id_prefix: str | None = None
    instance_ids: list[str] | None = None
    seed: int = 42

    def resolve_oracle(self) -> Callable[..., Any]:
        """Resolve the oracle callable for this design."""
        return get_oracle(self.oracle)

    def resolve_distractors(
        self,
        answer: str,
        params: dict[str, Any],
        rng: random.Random | None = None,
    ) -> list[str]:
        """Generate at least 3 distinct distractors using the configured strategy."""
        strat = get_distractor_strategy(self.distractors)
        if isinstance(strat, DistractorStrategy):
            return strat.build(answer, params, rng)
        if callable(strat):
            return strat(answer, params, rng)
        raise TypeError(f"Invalid distractor strategy configuration: {strat}")

    def render_prompt(self, params: dict[str, Any]) -> str:
        """Render the question prompt template with sampled params."""
        if callable(self.prompt):
            return self.prompt(params)
        return self.prompt.format(**params)

    def render_explanation(self, params: dict[str, Any], answer: Any) -> str:
        """Render the question explanation template with params and computed answer."""
        ctx = {**params, "answer": answer}
        if callable(self.explanation):
            return self.explanation(ctx)
        return self.explanation.format(**ctx)

    def resolve_difficulty(self, params: dict[str, Any]) -> DifficultyType:
        """Determine question difficulty (either fixed string or rule over params)."""
        if callable(self.difficulty):
            return self.difficulty(params)
        return self.difficulty


_SPEC_REGISTRY: dict[str, DesignSpec] = {}


def register_spec(spec: DesignSpec) -> DesignSpec:
    """Register a DesignSpec into the global QAF registry."""
    _SPEC_REGISTRY[spec.key] = spec
    return spec


def get_spec(key: str) -> DesignSpec:
    """Retrieve a registered DesignSpec by its generator key."""
    if key in _SPEC_REGISTRY:
        return _SPEC_REGISTRY[key]
    raise KeyError(
        f"DesignSpec '{key}' not registered. "
        f"Registered designs: {sorted(_SPEC_REGISTRY.keys())}"
    )


def get_all_specs() -> list[DesignSpec]:
    """Retrieve all registered DesignSpecs."""
    return list(_SPEC_REGISTRY.values())


def clear_specs() -> None:
    """Clear all registered DesignSpecs (mainly for test isolation)."""
    _SPEC_REGISTRY.clear()
