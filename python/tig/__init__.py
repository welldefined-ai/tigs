"""Tig - Talk in Git.

A Git-based system for storing and managing text objects in Git repositories.
"""

__version__ = "0.1.0"

from .store import TigStore

__all__ = ["TigStore"]