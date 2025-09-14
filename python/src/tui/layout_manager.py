"""Layout management for dynamic column widths."""

from typing import Tuple, List, Optional
import curses


class LayoutManager:
    """Manages dynamic column width calculations."""
    
    # Constants for short datetime format approach  
    # Format: "MM-DD HH:MM author_name title..."
    # Short datetime (11 chars) + space + author + space + title
    MIN_COMMIT_WIDTH = 27   # Minimum for short datetime + reasonable author name
    MAX_COMMIT_WIDTH = 48   # Cap to leave more space for messages
    MIN_MESSAGE_WIDTH = 25
    MIN_LOG_WIDTH = 17  # Space for "• MM-DD HH:MM" (13 chars) + borders + padding
    MAX_LOG_WIDTH = 17  # Keep minimal to avoid padding
    
    # Indicators for scrollable content
    SCROLL_LEFT = "◀"
    SCROLL_RIGHT = "▶"
    SCROLL_BOTH = "◀▶"
    
    def __init__(self):
        """Initialize layout manager."""
        self.cached_widths: Optional[Tuple[int, int, int]] = None
        self.last_screen_width: int = 0
        self.commit_title_scroll: dict = {}  # {commit_idx: scroll_offset}
    
    def calculate_column_widths(
        self, 
        screen_width: int, 
        commit_titles: List[str],
        log_count: int = 0,
        read_only_mode: bool = False
    ) -> Tuple[int, int, int]:
        """Calculate optimal column widths.
        
        Args:
            screen_width: Total screen width available
            commit_titles: List of commit titles for width calculation
            log_count: Number of log entries (0 if no logs)
            read_only_mode: If True, use shorter prefix (tigs view), else use checkbox prefix (tigs store)
        
        Returns:
            Tuple of (commit_width, message_width, log_width)
        """
        # Determine log column width
        if log_count == 0:
            log_width = 0
        else:
            log_width = self.MAX_LOG_WIDTH  # Use max width for logs to fit timestamp format
        
        # Simplified width calculation for soft-wrap approach
        # Use a reasonable fixed width that allows for author names and dates
        # Titles will wrap naturally, so we don't need to calculate based on title length
        available_for_commits = screen_width - log_width
        
        # Use a smaller proportion since short datetime saves space
        ideal_commit_width = min(
            int(available_for_commits * 0.4),  # 40% since short datetime is more compact
            self.MAX_COMMIT_WIDTH
        )
        
        commit_width = max(self.MIN_COMMIT_WIDTH, ideal_commit_width)
        
        # In read-only mode (tigs view), we can save 6 characters from shorter prefix
        # Store prefix: ">[ ] * " (6 chars), View prefix: ">• " (3 chars)
        # But add 1 extra char to store width so metadata display matches view
        if read_only_mode:
            commit_width = max(self.MIN_COMMIT_WIDTH - 6, commit_width - 6)
        else:
            # Store mode gets +1 char to match metadata display with view (but cap at MAX)
            commit_width = min(self.MAX_COMMIT_WIDTH, commit_width + 1)
        
        # Calculate message width with remaining space
        message_width = screen_width - commit_width - log_width
        
        # Ensure message width is reasonable (no max limit, just ensure it's positive)
        if message_width < self.MIN_MESSAGE_WIDTH:
            # Shrink commit column if needed to give messages minimum space
            available = screen_width - log_width - self.MIN_MESSAGE_WIDTH
            commit_width = max(self.MIN_COMMIT_WIDTH, available)
            message_width = screen_width - commit_width - log_width
        
        # Cache for resize detection
        self.cached_widths = (commit_width, message_width, log_width)
        self.last_screen_width = screen_width
        
        return commit_width, message_width, log_width
    
    def needs_recalculation(self, screen_width: int) -> bool:
        """Check if widths need recalculation after resize.
        
        Args:
            screen_width: Current screen width
            
        Returns:
            True if recalculation is needed
        """
        return (
            self.cached_widths is None or 
            self.last_screen_width != screen_width
        )
    
    def format_scrollable_text(
        self, 
        text: str, 
        max_width: int, 
        scroll_offset: int = 0,
        show_indicators: bool = True
    ) -> Tuple[str, bool, bool]:
        """Format text with horizontal scrolling.
        
        Args:
            text: The text to format
            max_width: Maximum width available
            scroll_offset: Current horizontal scroll position
            show_indicators: Whether to show scroll indicators
        
        Returns:
            Tuple of (formatted_text, can_scroll_left, can_scroll_right)
        """
        if len(text) <= max_width:
            return text, False, False
        
        # Calculate visible portion
        visible_start = scroll_offset
        visible_end = scroll_offset + max_width
        
        can_scroll_left = visible_start > 0
        can_scroll_right = visible_end < len(text)
        
        # Reserve space for indicators
        if show_indicators:
            indicator_space = 2  # For "◀ " or " ▶" or "◀▶"
            content_width = max_width - indicator_space
        else:
            content_width = max_width
        
        # Extract visible text
        visible_text = text[visible_start:visible_start + content_width]
        
        # Add indicators if needed
        if show_indicators:
            if can_scroll_left and can_scroll_right:
                formatted = f"{self.SCROLL_BOTH}{visible_text[2:]}"
            elif can_scroll_left:
                formatted = f"{self.SCROLL_LEFT} {visible_text[2:]}"
            elif can_scroll_right:
                formatted = f"{visible_text[:-2]} {self.SCROLL_RIGHT}"
            else:
                formatted = visible_text
        else:
            formatted = visible_text
        
        return formatted, can_scroll_left, can_scroll_right