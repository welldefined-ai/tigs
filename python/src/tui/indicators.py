"""Common UI indicators and formatting for TUI components."""

from typing import Optional


class SelectionIndicators:
    """Constants and methods for selection indicators."""
    
    # Selection box indicators
    SELECTED = "[x]"
    UNSELECTED = "[ ]"
    
    # Cursor indicators
    CURSOR_ARROW = ">"
    CURSOR_TRIANGLE = "▶"
    CURSOR_BULLET = "•"
    CURSOR_NONE = " "
    
    # Visual mode indicators
    VISUAL_MODE = "-- VISUAL --"
    
    @staticmethod
    def format_selection_box(is_selected: bool) -> str:
        """Format a selection checkbox indicator.
        
        Args:
            is_selected: Whether the item is selected
            
        Returns:
            Selection indicator string
        """
        return SelectionIndicators.SELECTED if is_selected else SelectionIndicators.UNSELECTED
    
    @staticmethod
    def format_cursor(is_current: bool, 
                     style: str = "arrow",
                     pad: bool = True) -> str:
        """Format a cursor indicator.
        
        Args:
            is_current: Whether this is the current cursor position
            style: Style of cursor ("arrow", "triangle", "bullet")
            pad: Whether to pad with space when no cursor
            
        Returns:
            Cursor indicator string
        """
        if not is_current:
            return SelectionIndicators.CURSOR_NONE if pad else ""
        
        styles = {
            "arrow": SelectionIndicators.CURSOR_ARROW,
            "triangle": SelectionIndicators.CURSOR_TRIANGLE,
            "bullet": SelectionIndicators.CURSOR_BULLET,
        }
        return styles.get(style, SelectionIndicators.CURSOR_ARROW)
    
    @staticmethod
    def format_list_item(index: int,
                        cursor_idx: int,
                        is_selected: bool,
                        text: str,
                        cursor_style: str = "arrow",
                        show_selection: bool = True) -> str:
        """Format a complete list item with cursor and selection.
        
        Args:
            index: Index of the current item
            cursor_idx: Index of the cursor position
            is_selected: Whether the item is selected
            text: The item text
            cursor_style: Style of cursor indicator
            show_selection: Whether to show selection box
            
        Returns:
            Formatted line string
        """
        cursor = SelectionIndicators.format_cursor(
            index == cursor_idx, 
            style=cursor_style
        )
        
        if show_selection:
            selection = SelectionIndicators.format_selection_box(is_selected)
            return f"{cursor}{selection} {text}"
        else:
            return f"{cursor} {text}"