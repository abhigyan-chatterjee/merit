"""Guard against dependencies that work locally and vanish in the image.

The deployable image installs only what `pyproject.toml` declares. A dev venv
accumulates more: transitive dependencies, hand-installed packages, dev extras.
So `import starlette` works perfectly for months, then the image is rebuilt from
a clean cache and the import is gone.

This asserts every third-party module the application imports is declared. It
cannot catch a *dependency's own* optional sub-dependency — the failure that
caused the judge outage (`google-auth` importing `requests` lazily) is invisible
to any static scan, because the name never appears in our source. That class can
only be caught by exercising the real code path, which is what
`test_judge_backend.py::test_minting_reaches_the_network_instead_of_failing_to_import`
does.
"""

from __future__ import annotations

import ast
import sys
import tomllib
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = API_ROOT / "pyproject.toml"
APP_ROOT = API_ROOT / "app"

# Import name -> distribution name, where the two differ.
IMPORT_TO_DISTRIBUTION = {
    "jwt": "pyjwt",
    "google": "google-auth",
    "multipart": "python-multipart",
}


def _normalise(name: str) -> str:
    """PEP 503 normalisation, so `pydantic_settings` matches `pydantic-settings`."""
    return name.lower().replace("-", "_").replace(".", "_")


def _declared_distributions() -> set[str]:
    data = tomllib.loads(PYPROJECT.read_text())
    declared = set()
    for dep in data["project"]["dependencies"]:
        # Strip version specifiers and extras: "google-auth[requests]>=2.35" ->
        # "google_auth"
        name = dep.split(">")[0].split("=")[0].split("<")[0].split("~")[0].split("!")[0]
        name = name.split("[")[0].strip()
        declared.add(_normalise(name))
    return declared


def _imported_third_party_modules() -> dict[str, str]:
    """Every third-party module imported under app/, mapped to where it appeared.

    Walks the AST rather than importing the app, so a module that fails to
    import is still reported instead of taking the test down with it.
    """
    stdlib = set(sys.stdlib_module_names)
    found: dict[str, str] = {}

    for path in sorted(APP_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            roots: list[str] = []
            if isinstance(node, ast.Import):
                roots = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                roots = [node.module.split(".")[0]]

            for root in roots:
                if root in stdlib or root == "app":
                    continue
                location = f"{path.relative_to(API_ROOT)}:{node.lineno}"
                found.setdefault(root, location)

    return found


def test_every_imported_module_is_a_declared_dependency():
    declared = _declared_distributions()
    imported = _imported_third_party_modules()

    assert imported, "expected to find third-party imports under app/"

    undeclared = {}
    for module, location in sorted(imported.items()):
        distribution = _normalise(IMPORT_TO_DISTRIBUTION.get(module, module))
        if distribution not in declared:
            undeclared[module] = location

    assert not undeclared, (
        "these modules are imported by the application but not declared in "
        "pyproject.toml, so they will be missing from a clean image build:\n"
        + "\n".join(f"  {mod}  (first used at {loc})" for mod, loc in undeclared.items())
    )


def test_declared_dependencies_are_installed():
    """The other direction: what we declare must actually be present.

    Catches a dependency edited out of the environment without being removed
    from pyproject, which would otherwise only surface on a fresh install.
    """
    import importlib.util

    missing = []
    for distribution in sorted(_declared_distributions()):
        # Only check the ones we know how to name; the import-name mapping is
        # incomplete by nature, and a false failure here is worse than a miss.
        candidates = [distribution]
        for import_name, dist in IMPORT_TO_DISTRIBUTION.items():
            if _normalise(dist) == distribution:
                candidates.append(import_name)

        if not any(importlib.util.find_spec(c) is not None for c in candidates):
            missing.append(distribution)

    assert not missing, (
        "declared in pyproject.toml but not importable in this environment:\n"
        + "\n".join(f"  {m}" for m in missing)
    )
