"""Terminal User Interface for Tigs store command."""

try:
    import curses
    CURSES_AVAILABLE = True
except ImportError:
    CURSES_AVAILABLE = False

from .store_app import TigsStoreApp
from .log_app import TigsLogApp

__all__ = ['TigsStoreApp', 'TigsLogApp', 'CURSES_AVAILABLE']