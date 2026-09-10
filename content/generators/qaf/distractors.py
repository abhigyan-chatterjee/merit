"""Reusable distractor strategies for question generation."""

import random
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from typing import Any, ClassVar


def ensure_distinct_distractors(
    answer: str,
    candidates: Iterable[Any],
    min_count: int = 3,
    fallback_generator: Callable[[str, int], list[Any]] | None = None,
) -> list[str]:
    """Ensure at least min_count distinct, non-empty options distinct from answer."""
    clean_ans = str(answer).strip()
    seen = {clean_ans}
    result: list[str] = []

    for cand in candidates:
        c_str = str(cand).strip()
        if c_str and c_str not in seen:
            seen.add(c_str)
            result.append(c_str)

    if len(result) < min_count and fallback_generator:
        extra = fallback_generator(clean_ans, min_count - len(result))
        for cand in extra:
            c_str = str(cand).strip()
            if c_str and c_str not in seen:
                seen.add(c_str)
                result.append(c_str)

    if len(result) < min_count:
        raise ValueError(
            f"Distractor strategy yielded only {len(result)} options distinct from answer '{clean_ans}'. "
            f"Required at least {min_count}. Options: {result}"
        )

    return result


class DistractorStrategy(ABC):
    """Base abstract class for all distractor strategies."""

    @abstractmethod
    def build(
        self,
        answer: str,
        params: dict[str, Any],
        rng: random.Random | None = None,
    ) -> list[str]:
        """Return at least 3 distinct distractors distinct from answer."""

    def __call__(
        self,
        answer: str,
        params: dict[str, Any],
        rng: random.Random | None = None,
    ) -> list[str]:
        return self.build(answer, params, rng)


class NumericOffsetStrategy(DistractorStrategy):
    """Generates numeric distractors by applying relative offsets to the answer."""

    def __init__(
        self,
        offsets: list[int],
        min_val: int | None = None,
        max_val: int | None = None,
        clamp_min: bool = False,
    ):
        self.offsets = offsets
        self.min_val = min_val
        self.max_val = max_val
        self.clamp_min = clamp_min

    def build(
        self,
        answer: str,
        params: dict[str, Any],
        rng: random.Random | None = None,
    ) -> list[str]:
        val = int(answer)
        cands: list[int] = []
        for off in self.offsets:
            cand = val + off
            if self.clamp_min and self.min_val is not None:
                cand = max(self.min_val, cand)
            elif self.min_val is not None and cand < self.min_val:
                continue
            if self.max_val is not None and cand > self.max_val:
                continue
            cands.append(cand)

        def fallback(ans_str: str, needed: int) -> list[int]:
            ans_v = int(ans_str)
            extra: list[int] = []
            step = 1
            while len(extra) < needed * 4:
                for delta in [step, -step, step + 2, -(step + 2), step + 5]:
                    c = ans_v + delta
                    if self.min_val is not None and c < self.min_val:
                        continue
                    if self.max_val is not None and c > self.max_val:
                        continue
                    extra.append(c)
                step += 1
            return extra

        return ensure_distinct_distractors(
            answer, cands, min_count=3, fallback_generator=fallback
        )


class OffByOneStrategy(NumericOffsetStrategy):
    """Specialized numeric offset strategy generating small step variants."""

    def __init__(self, min_val: int | None = 0):
        super().__init__(offsets=[1, -1, 2, -2, 3, -3], min_val=min_val)


class WrongComplexityStrategy(DistractorStrategy):
    """Generates time or space complexity distractors from standard complexity classes."""

    DEFAULT_COMPLEXITIES: ClassVar[list[str]] = [
        "O(1)",
        "O(log N)",
        "O(N)",
        "O(N log N)",
        "O(N + M)",
        "O(N * M)",
        "O(N²)",
        "O(2^N)",
    ]

    def __init__(self, pool: list[str] | None = None):
        self.pool = pool or self.DEFAULT_COMPLEXITIES

    def build(
        self,
        answer: str,
        params: dict[str, Any],
        rng: random.Random | None = None,
    ) -> list[str]:
        clean_ans = str(answer).strip()
        cands = [c for c in self.pool if c != clean_ans]
        if rng:
            rng.shuffle(cands)
        return ensure_distinct_distractors(answer, cands, min_count=3)


class FixedDistractorStrategy(DistractorStrategy):
    """Extracts fixed distractors from the strategy config or sampled parameters."""

    def __init__(self, distractors: list[str] | None = None):
        self.distractors = distractors

    def build(
        self,
        answer: str,
        params: dict[str, Any],
        rng: random.Random | None = None,
    ) -> list[str]:
        opts = self.distractors or params.get("distractors", [])
        return ensure_distinct_distractors(answer, opts, min_count=3)


_STRATEGY_REGISTRY: dict[str, DistractorStrategy | Callable[..., list[str]]] = {
    "off_by_one": OffByOneStrategy(),
    "wrong_complexity": WrongComplexityStrategy(),
}


def register_distractor_strategy(
    name: str,
    strategy: DistractorStrategy | Callable[..., list[str]],
) -> None:
    """Register a reusable distractor strategy by name."""
    _STRATEGY_REGISTRY[name] = strategy


def get_distractor_strategy(
    name_or_strat: str | DistractorStrategy | Callable[..., list[str]],
) -> DistractorStrategy | Callable[..., list[str]]:
    """Resolve a distractor strategy by name or pass through instance/callable."""
    if isinstance(name_or_strat, str):
        if name_or_strat in _STRATEGY_REGISTRY:
            return _STRATEGY_REGISTRY[name_or_strat]
        raise KeyError(
            f"Distractor strategy '{name_or_strat}' not found. "
            f"Available: {sorted(_STRATEGY_REGISTRY.keys())}"
        )
    return name_or_strat
