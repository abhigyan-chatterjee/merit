"""Per-problem type signatures, used to generate compiled-language harnesses.

Authored and gated in content/ (see content/validators/verify_signatures.py);
the API only reads the result. Java and C++ need the parameter and return types
to emit typed source, which is what makes a type error a compile error.
"""

import json
from functools import lru_cache
from typing import Any

from app.seed import resolve_content_dir


@lru_cache(maxsize=1)
def _load() -> dict[str, dict[str, Any]]:
    """Reads signatures.json once. A missing file disables compiled languages
    rather than failing startup: the interpreted languages keep working."""
    path = resolve_content_dir("problems").parent / "signatures.json"
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def get_signature(slug: str) -> dict[str, Any] | None:
    """The recorded signature for a problem, or None when it has none."""
    entry = _load().get(slug)
    return entry if isinstance(entry, dict) else None
