"""HTTP status constants that resolve on every Starlette version we pin.

Starlette renamed two codes: `HTTP_413_REQUEST_ENTITY_TOO_LARGE` became
`HTTP_413_CONTENT_TOO_LARGE`, and `HTTP_422_UNPROCESSABLE_ENTITY` became
`HTTP_422_UNPROCESSABLE_CONTENT`. The new spellings do not exist before the
rename and the old ones are deprecated after it, so referencing either name
directly couples this code to one major version. Because those references sit
inside exception handlers, getting it wrong replaces the intended status with an
AttributeError, which surfaces as a 500.

Resolve at import time against whatever Starlette is actually installed.
"""

from starlette import status

_PAIRS: dict[str, tuple[str, str]] = {
    "HTTP_413": ("HTTP_413_CONTENT_TOO_LARGE", "HTTP_413_REQUEST_ENTITY_TOO_LARGE"),
    "HTTP_422": ("HTTP_422_UNPROCESSABLE_CONTENT", "HTTP_422_UNPROCESSABLE_ENTITY"),
}


def _resolve(new_name: str, old_name: str) -> int:
    """The renamed code where the installed Starlette has it, else the old one."""
    return getattr(status, new_name, None) or getattr(status, old_name)


#: 413 Request Entity Too Large
HTTP_413 = _resolve(*_PAIRS["HTTP_413"])

#: 422 Unprocessable Entity / Content
HTTP_422 = _resolve(*_PAIRS["HTTP_422"])
