"""Shared fixtures for tigs testing."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Generator
from typing import List
from typing import Optional

import pytest


def set_file_time(file_path: Path, timestamp: float):
    """Set file modification time (cross-platform)."""
    file_path.touch()
    os.utime(file_path, times=(timestamp, timestamp))


def create_test_repo(repo_path: Path, commits: Optional[List[str]] = None) -> None:
    """Create a test Git repository with optional commits.

    Args:
        repo_path: Path where to create the repository
        commits: List of commit messages to create
    """
    repo_path.mkdir(parents=True, exist_ok=True)

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
    )

    if commits:
        for i, commit_msg in enumerate(commits):
            # Create a test file for each commit
            test_file = repo_path / f"file_{i}.txt"
            test_file.write_text(f"Content for commit: {commit_msg}\n")

            subprocess.run(["git", "add", test_file.name], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", commit_msg], cwd=repo_path, check=True
            )


@pytest.fixture
def multiline_repo() -> Generator[Path, None, None]:
    """Create a repository with varied multi-line commit messages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "multiline_repo"

        # Create repository with varied commit message lengths
        commits = []
        for i in range(50):
            if i % 5 == 0:
                # Every 5th commit: Very long message that will wrap to 2-3 lines
                commits.append(
                    f"Change {i + 1}: This is a very long commit message that will definitely wrap to multiple lines when displayed in the narrow commits pane. It contains enough text to thoroughly test the multi-line display behavior of tigs terminal interface and should cause issues with cursor navigation if not handled properly."
                )
            elif i % 7 == 0:
                # Every 7th commit: Medium length that might wrap
                commits.append(
                    f"Change {i + 1}: Implement feature with moderately long description that may wrap depending on terminal width and column layout configuration"
                )
            elif i % 3 == 0:
                # Every 3rd commit: Multi-line with actual newlines
                commits.append(
                    f"Change {i + 1}: Feature implementation\n\nThis commit adds the following important changes:\n- Feature A implementation\n- Feature B with error handling\n- Bug fixes and improvements\n- Documentation updates"
                )
            else:
                # Regular short commits
                commits.append(f"Change {i + 1}")

        create_test_repo(repo_path, commits)
        yield repo_path


@pytest.fixture
def simple_repo() -> Generator[Path, None, None]:
    """Create a repository with simple commit messages for reliable navigation testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "simple_repo"

        # Create simple commits for reliable navigation testing
        commits = [f"Nav {i + 1}" for i in range(30)]
        create_test_repo(repo_path, commits)
        yield repo_path


@pytest.fixture
def extreme_repo() -> Generator[Path, None, None]:
    """Create a repository with extremely challenging commit messages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "extreme_repo"
        repo_path.mkdir(parents=True, exist_ok=True)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
        )

        # Create commits with extremely problematic messages
        extreme_commits = [
            # Commit 1: Extremely long single line
            "Commit 1: "
            + "x" * 500
            + " This commit has an extremely long single line that should definitely cause wrapping issues and potentially break terminal display parsing in ways that reveal cursor navigation bugs",
            # Commit 2: Many newlines
            "Commit 2: Multiple newlines\n\n\n\n\n\n\nThis has many blank lines that might cause issues",
            # Commit 3: Unicode and special characters
            "Commit 3: Unicode test 🚀🔥💯 with émojis and spëcial characters that might break parsing: ñoñó",
            # Commit 4: Very long with newlines
            "Commit 4: "
            + "Very long line " * 50
            + "\n\nSecond paragraph is also very long "
            + "repeated text " * 30,
            # Commit 5: Empty commit message (just title)
            "Commit 5",
            # Commit 6: Only newlines
            "Commit 6: Title\n\n\n\n",
            # Commit 7: Tab and control characters
            "Commit 7: Tab\tcharacters\nand\rcontrol\bcharacters",
            # Commit 8: Another extremely long line
            "Commit 8: "
            + "This is another extremely long commit message designed to wrap multiple lines and potentially cause issues with terminal display parsing when the text extends beyond normal boundaries "
            * 3,
            # Commit 9: Mixed content
            "Commit 9: Mixed\n\nBullet points:\n• Item 1 with very long text "
            + "x" * 100
            + "\n• Item 2\n• Item 3 with more text "
            + "y" * 80,
            # Commit 10: Normal commit for comparison
            "Commit 10: Normal commit message",
        ]

        for i, commit_msg in enumerate(extreme_commits):
            # Create a test file for each commit
            test_file = repo_path / f"extreme_file_{i}.txt"
            test_file.write_text(f"Content for extreme commit {i + 1}\n")

            subprocess.run(["git", "add", test_file.name], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", commit_msg], cwd=repo_path, check=True
            )

        yield repo_path
