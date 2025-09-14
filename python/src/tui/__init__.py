"""Terminal User Interface for Tigs store command."""

try:
    import curses
    CURSES_AVAILABLE = True
except ImportError:
    CURSES_AVAILABLE = False

from .store_app import TigsStoreApp
from .view_app import TigsViewApp

__all__ = ['TigsStoreApp', 'TigsViewApp', 'CURSES_AVAILABLE']