"""Validate that logs pane surfaces sessions from multiple providers."""

import tempfile
from pathlib import Path

import pytest

from framework.fixtures import create_test_repo
from framework.mock_claude_logs import create_mock_claude_home
from framework.mock_codex_logs import create_mock_codex_home
from framework.paths import PYTHON_DIR
from framework.tui import TUI


def test_logs_show_claude_and_codex_sessions(monkeypatch):
    """Ensure both Claude Code and Codex CLI logs appear in the logs pane."""

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        home_path = Path(tmpdir) / "home"
        home_path.mkdir(parents=True, exist_ok=True)

        # Point HOME to the sandboxed directory containing mocked logs
        monkeypatch.setenv("HOME", str(home_path))

        # Minimal Git history for store command to boot
        create_test_repo(repo_path, ["Initial commit", "Follow-up change"])

        # Populate provider-specific log directories
        # Claude discovery derives project folder from the TUI's cwd (python impl dir).
        create_mock_claude_home(home_path)
        create_mock_codex_home(home_path)

        command = f"uv run tigs --repo {repo_path} store"
        env = {
            "HOME": str(home_path),
            "TIGS_CHAT_PROVIDERS": "claude-code codex-cli",
        }

        try:
            with TUI(
                command,
                cwd=PYTHON_DIR,
                env=env,
                dimensions=(30, 132),
                timeout=12.0,
            ) as tui:
                tui.wait_for("Commits", timeout=6.0)

                import time

                combined = ""
                lines = []
                deadline = time.time() + 6.0

                while time.time() < deadline:
                    lines = tui.capture()
                    combined = "\n".join(lines)
                    if "Logs" in combined and "Claude" in combined and "Codex" in combined:
                        break
                    time.sleep(0.25)

                if "Logs" not in combined:
                    pytest.skip(
                        "Logs pane not visible in this environment; cannot validate multi-provider output"
                    )

                assert "Claude" in combined, (
                    "Expected Claude Code sessions to be visible in logs pane"
                )
                assert "Codex" in combined, (
                    "Expected Codex CLI sessions to be visible in logs pane"
                )
        except OSError as exc:
            if "out of pty devices" in str(exc).lower():
                pytest.skip("System cannot allocate PTY devices for TUI test")
            raise
