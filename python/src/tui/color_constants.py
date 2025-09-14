"""Color constants for TUI views following tig's color scheme.

These color pair numbers are defined consistently across all TUI apps
(store_app.py and view_app.py) and match tig's default color scheme.
"""

# Standard tig-inspired color pairs
# These must match the curses.init_pair() calls in the app files
COLOR_DEFAULT = 0       # Default terminal colors
COLOR_NORMAL = 1        # Normal text (white on black or default)
COLOR_CYAN = 2          # Author, Assistant role, focused border
COLOR_GREEN = 3         # Commit SHA, additions, success
COLOR_YELLOW = 4        # Date headers, System role, warnings
COLOR_MAGENTA = 5       # Refs (branches/tags), special markers
COLOR_RED = 6           # Deletions, errors
COLOR_BLUE = 7          # Timestamps, metadata, filenames

# Semantic aliases for specific uses
COLOR_AUTHOR = COLOR_CYAN
COLOR_COMMIT = COLOR_GREEN
COLOR_DATE = COLOR_YELLOW
COLOR_REFS = COLOR_MAGENTA
COLOR_DELETE = COLOR_RED
COLOR_METADATA = COLOR_BLUE

# Message role colors
ROLE_COLORS = {
    'user': COLOR_DEFAULT,      # User messages in default color
    'assistant': COLOR_CYAN,     # Assistant like commit author
    'system': COLOR_YELLOW,      # System messages like headers
}

def get_role_color(role: str) -> int:
    """Get color pair for a message role.
    
    Args:
        role: Message role ('user', 'assistant', 'system')
        
    Returns:
        Color pair number for the role
    """
    return ROLE_COLORS.get(role.lower(), COLOR_DEFAULT)