"""Checks that Python is new enough before the rest of the app is imported.

Written without newer syntax, so even an old Python (e.g. 3.8) can run it
and show a clear message instead of a confusing error.
"""
import sys

from labeler import config


def python_too_old(version_info=None) -> bool:
    """True if this Python is older than config.MIN_PYTHON."""
    version = tuple(version_info or sys.version_info)[:2]
    return version < tuple(config.MIN_PYTHON)


def python_version_message(version_info=None) -> str:
    """Plain message saying which Python is running and which one is needed."""
    version = tuple(version_info or sys.version_info)[:3]
    found = ".".join(str(part) for part in version)
    needed = ".".join(str(part) for part in config.MIN_PYTHON)
    return ("This app needs Python {needed} or newer, but it was started with Python {found}. "
            "Start it with: .venv/bin/python -m streamlit run app.py "
            "(see INSTALL-MAC.md).").format(needed=needed, found=found)
