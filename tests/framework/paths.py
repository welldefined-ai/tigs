"""Path utilities for test framework."""

from pathlib import Path

# Project root is 2 levels up from this file
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Current implementation directory
PYTHON_DIR = PROJECT_ROOT / "python"


def get_impl_dir(language: str) -> Path:
    """Get implementation directory for a given language."""
    return PROJECT_ROOT / language
