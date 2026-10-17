"""Compute the package version at build time.

Hatchling runs this file as its version source and reads ``__version__`` from it.
"""

import os
import subprocess
from pathlib import Path

_ROOT = Path(__file__).parent

# Set by the Nix build, whose sandbox has no .git to ask.
_GIT_REF_VARIABLE = "ANANKE_GIT_REF"


def _git_ref() -> str | None:
    """Find the git reference to append to the base version.

    Returns:
        The reference from the environment if set, otherwise the short hash of HEAD, or None when neither is available.
    """
    ref = os.environ.get(_GIT_REF_VARIABLE)
    if ref is not None:
        return ref
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            cwd=_ROOT,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _version() -> str:
    """Combine the base version with the git reference.

    Returns:
        ``<base>+<ref>`` when a reference is available, otherwise the base version alone.
    """
    base = (_ROOT / "VERSION").read_text().strip()
    ref = _git_ref()
    return f"{base}+{ref}" if ref else base


__version__ = _version()
