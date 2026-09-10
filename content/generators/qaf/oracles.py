"""Oracle registry and algorithmic oracles for question generation."""

from collections import Counter
from collections.abc import Callable
from typing import Any

OracleFunc = Callable[..., Any]
_ORACLE_REGISTRY: dict[str, OracleFunc] = {}


def register_oracle(name: str | None = None) -> Callable[[OracleFunc], OracleFunc]:
    """Decorator to register an oracle function by name."""

    def decorator(fn: OracleFunc) -> OracleFunc:
        oracle_name = name or fn.__name__
        _ORACLE_REGISTRY[oracle_name] = fn
        return fn

    return decorator


def get_oracle(name_or_callable: str | OracleFunc) -> OracleFunc:
    """Get an oracle function by name or return the callable directly."""
    if callable(name_or_callable):
        return name_or_callable
    if name_or_callable in _ORACLE_REGISTRY:
        return _ORACLE_REGISTRY[name_or_callable]
    raise KeyError(
        f"Oracle '{name_or_callable}' not found in registry. "
        f"Available: {sorted(_ORACLE_REGISTRY.keys())}"
    )


@register_oracle("kadane")
@register_oracle("kadane_oracle")
@register_oracle("arrays_strings.kadane")
def kadane_oracle(nums: list[int] | None = None, arr: list[int] | None = None) -> int:
    """Kadane's algorithm maximum contiguous subarray sum."""
    target = nums if nums is not None else arr
    if target is None:
        raise ValueError("Kadane oracle requires 'nums' or 'arr'")
    max_so_far = target[0]
    curr_max = target[0]
    for x in target[1:]:
        curr_max = max(x, curr_max + x)
        max_so_far = max(max_so_far, curr_max)
    return max_so_far


@register_oracle("prefix_sum")
@register_oracle("prefix_sum_oracle")
@register_oracle("arrays_strings.prefix_sum")
def prefix_sum_oracle(
    nums: list[int] | None = None,
    arr: list[int] | None = None,
    left: int | None = None,
    right: int | None = None,
    L: int | None = None,
    R: int | None = None,
) -> int:
    """Prefix sum range query sum(nums[L..R])."""
    target = nums if nums is not None else arr
    l_val = left if left is not None else L
    r_val = right if right is not None else R
    if target is None or l_val is None or r_val is None:
        raise ValueError("prefix_sum oracle requires nums/arr and left/L, right/R")
    return sum(target[l_val : r_val + 1])


@register_oracle("max_sum_fixed")
@register_oracle("max_sum_fixed_oracle")
@register_oracle("sliding_windows.max_sum_fixed")
@register_oracle("arrays_strings.sliding_window")
def max_sum_fixed_oracle(
    nums: list[int] | None = None,
    arr: list[int] | None = None,
    k: int = 1,
) -> int:
    """Maximum sum of contiguous subarray of fixed length k."""
    target = nums if nums is not None else arr
    if target is None:
        raise ValueError("max_sum_fixed oracle requires 'nums' or 'arr'")
    curr = sum(target[:k])
    max_s = curr
    for i in range(k, len(target)):
        curr += target[i] - target[i - k]
        max_s = max(max_s, curr)
    return max_s


@register_oracle("min_window_substring")
@register_oracle("min_window_substring_oracle")
@register_oracle("sliding_windows.min_window_substring")
def min_window_substring_oracle(
    s: str | None = None,
    t: str | None = None,
    s_str: str | None = None,
    t_str: str | None = None,
) -> int:
    """Minimum window substring length containing all characters of t, or 0."""
    target_s = s if s is not None else s_str
    target_t = t if t is not None else t_str
    if target_s is None or target_t is None or not target_s or not target_t:
        return 0
    t_count = Counter(target_t)
    required = len(t_count)
    left_ptr = 0
    formed = 0
    window_counts: dict[str, int] = {}
    min_len = float("inf")
    for right_ptr in range(len(target_s)):
        char = target_s[right_ptr]
        window_counts[char] = window_counts.get(char, 0) + 1
        if char in t_count and window_counts[char] == t_count[char]:
            formed += 1
        while left_ptr <= right_ptr and formed == required:
            min_len = min(min_len, right_ptr - left_ptr + 1)
            left_char = target_s[left_ptr]
            window_counts[left_char] -= 1
            if left_char in t_count and window_counts[left_char] < t_count[left_char]:
                formed -= 1
            left_ptr += 1
    return 0 if min_len == float("inf") else int(min_len)


@register_oracle("identity")
@register_oracle("conceptual")
@register_oracle("arrays_strings.concepts")
def identity_oracle(answer: Any = None, ans: Any = None, **_kwargs: Any) -> Any:
    """Return the specified answer directly (used for conceptual designs)."""
    return answer if answer is not None else ans
