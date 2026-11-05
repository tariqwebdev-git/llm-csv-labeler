import sys

from labeler import config
from labeler.environment_check import running_in_project_env


def test_project_env_is_recognised(monkeypatch):
    monkeypatch.setattr(sys, "prefix", str(config.PROJECT_ROOT / ".venv"))
    assert running_in_project_env()


def test_outside_env_is_flagged(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "prefix", str(tmp_path / "miniconda" / "base"))
    assert not running_in_project_env()
