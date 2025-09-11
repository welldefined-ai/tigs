"""Shared pane rendering functionality for TUI applications."""

import curses
from typing import List, Union, Tuple


class PaneRenderer:
    """Handles drawing of bordered panes with titles and content."""
    
    @staticmethod
    def draw_pane(stdscr, y: int, x: int, height: int, width: int,
                  title: str, focused: bool, content: List[Union[str, Tuple, List]],
                  colors_enabled: bool = False) -> None:
        """Draw a bordered pane with title and content.
        
        When focused, only the borders and title are bold, not the content.
        
        Args:
            stdscr: The curses screen
            y: Top position
            x: Left position  
            height: Pane height
            width: Pane width
            title: Pane title
            focused: Whether this pane has focus
            content: Lines of content to display (strings, tuples, or lists of tuples)
            colors_enabled: Whether colors are available
        """
        if width < 2 or height < 2:
            return
        
        # Box drawing characters
        tl = curses.ACS_ULCORNER  # Top-left
        tr = curses.ACS_URCORNER  # Top-right
        bl = curses.ACS_LLCORNER  # Bottom-left
        br = curses.ACS_LRCORNER  # Bottom-right
        hz = curses.ACS_HLINE     # Horizontal
        vt = curses.ACS_VLINE     # Vertical
        
        try:
            # Apply styling for borders and title if focused
            if focused:
                stdscr.attron(curses.A_BOLD)
                if colors_enabled:
                    # Optional: use a color for focused borders (cyan)
                    stdscr.attron(curses.color_pair(2))
            
            # Draw corners
            stdscr.addch(y, x, tl)
            stdscr.addch(y, x + width - 1, tr)
            stdscr.addch(y + height - 1, x, bl)
            stdscr.addch(y + height - 1, x + width - 1, br)
            
            # Draw horizontal lines
            for i in range(1, width - 1):
                stdscr.addch(y, x + i, hz)
                stdscr.addch(y + height - 1, x + i, hz)
            
            # Draw vertical lines
            for i in range(1, height - 1):
                stdscr.addch(y + i, x, vt)
                stdscr.addch(y + i, x + width - 1, vt)
            
            # Draw title (still with bold if focused)
            if title and len(title) + 4 < width:
                title_text = f" {title} "
                title_x = x + (width - len(title_text)) // 2
                stdscr.addstr(y, title_x, title_text)
            
            # Turn off bold/color before drawing content
            if focused:
                stdscr.attroff(curses.A_BOLD)
                if colors_enabled:
                    stdscr.attroff(curses.color_pair(2))
            
            # Draw content (without bold)
            for i, item in enumerate(content):
                if i + 1 < height - 1:  # Leave room for border
                    PaneRenderer._draw_content_line(
                        stdscr, y + i + 1, x + 2, width - 4, 
                        item, colors_enabled
                    )
                    
        except curses.error:
            pass  # Ignore errors from drawing outside screen
    
    @staticmethod
    def _draw_content_line(stdscr, y: int, x: int, max_width: int,
                           item: Union[str, Tuple, List], 
                           colors_enabled: bool) -> None:
        """Draw a single line of content.
        
        Args:
            stdscr: The curses screen
            y: Y position
            x: X position
            max_width: Maximum width for the line
            item: Content item (string, tuple, or list of tuples)
            colors_enabled: Whether colors are available
        """
        if isinstance(item, list):
            # Multi-colored line (list of tuples)
            x_offset = x
            remaining_width = max_width
            for part_text, part_color in item:
                if remaining_width <= 0:
                    break
                if len(part_text) > remaining_width:
                    part_text = part_text[:remaining_width]
                if colors_enabled and part_color > 0:
                    stdscr.attron(curses.color_pair(part_color))
                stdscr.addstr(y, x_offset, part_text)
                if colors_enabled and part_color > 0:
                    stdscr.attroff(curses.color_pair(part_color))
                x_offset += len(part_text)
                remaining_width -= len(part_text)
                
        elif isinstance(item, tuple):
            # Single-colored line (text, color_pair)
            text, color_pair = item
            if len(text) > max_width:
                text = text[:max_width]
            if colors_enabled and color_pair > 0:
                stdscr.attron(curses.color_pair(color_pair))
            stdscr.addstr(y, x, text)
            if colors_enabled and color_pair > 0:
                stdscr.attroff(curses.color_pair(color_pair))
                
        else:
            # Plain string
            line = str(item)
            if len(line) > max_width:
                line = line[:max_width]
            stdscr.addstr(y, x, line)