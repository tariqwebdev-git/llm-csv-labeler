"""Checks that the app runs from the project's own Python environment.

If the app is started from another environment (for example conda's "base"),
other versions of packages can be picked up and cause confusing errors.
"""
import sys
from pathlib import Path

from labeler import config


def running_in_project_env() -> bool:
    """True if Python runs from an environment inside the project folder (.venv or venv)."""
    prefix = Path(sys.prefix).resolve()
    return prefix.is_relative_to(config.PROJECT_ROOT.resolve())
