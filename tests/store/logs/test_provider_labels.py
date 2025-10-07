#!/usr/bin/env python3
"""Validate that provider labels appear in the logs pane."""

import tempfile
from pathlib import Path

import pytest

from framework.fixtures import create_test_repo
from framework.mock_claude_logs import create_mock_claude_home
from framework.paths import PYTHON_DIR
from framework.tui import TUI


@pytest.fixture
def repo_with_provider(monkeypatch):
    """Repository with a single Claude log for provider label testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        mock_home = Path(tmpdir) / "mock_home"
        mock_home.mkdir()

        monkeypatch.setenv("HOME", str(mock_home))

        create_test_repo(repo_path, ["Initial commit"])

        create_mock_claude_home(
            mock_home,
            sessions_data=[[("user", "Show provider"), ("assistant", "Sure")]],
            cwd=repo_path,
        )

        yield repo_path, mock_home


class TestLogProviderLabels:
    """Ensure the logs pane shows provider information."""

    def test_provider_name_visible(self, repo_with_provider):
        repo_path, mock_home = repo_with_provider
        command = f"uv run tigs --repo {repo_path} store"

        with TUI(
            command,
            cwd=PYTHON_DIR,
            dimensions=(30, 80),
            env={"HOME": str(mock_home)},
        ) as tui:
            tui.wait_for("Logs", timeout=5.0)
            lines = tui.capture()

            combined = " ".join(line.strip() for line in lines)
            assert "Claude" in combined, "Logs pane should display provider label"
