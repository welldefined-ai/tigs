"""Terminal User Interface for Tigs store command."""

try:
    import curses
    CURSES_AVAILABLE = True
except ImportError:
    CURSES_AVAILABLE = False

from .app import TigsStoreApp

__all__ = ['TigsStoreApp', 'CURSES_AVAILABLE']