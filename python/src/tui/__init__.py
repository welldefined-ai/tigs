"""Terminal User Interface for Tigs store command."""

try:
    import curses

    # Verify curses is usable by checking for required functionality
    curses.KEY_UP  # Basic key constant check
    CURSES_AVAILABLE = True
except (ImportError, AttributeError):
    CURSES_AVAILABLE = False

from .store_app import TigsStoreApp
from .view_app import TigsViewApp

__all__ = ["TigsStoreApp", "TigsViewApp", "CURSES_AVAILABLE"]
