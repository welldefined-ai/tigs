"""Core framework components for E2E terminal testing."""

from .terminal import TerminalApp
from .display import Display, DisplayCapture
from .utils import send_keys, wait_for_output

# Import assertions only when pytest is available
try:
    from .assertions import assert_display_matches, assert_display_contains
    __all__ = [
        "TerminalApp",
        "Display", 
        "DisplayCapture",
        "assert_display_matches",
        "assert_display_contains", 
        "send_keys",
        "wait_for_output"
    ]
except ImportError:
    # pytest not available, skip assertion imports
    __all__ = [
        "TerminalApp",
        "Display", 
        "DisplayCapture",
        "send_keys",
        "wait_for_output"
    ]