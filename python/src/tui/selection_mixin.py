"""Shared visual selection functionality for TUI views."""

import curses
from typing import Set, Optional, Tuple


class VisualSelectionMixin:
    """Mixin class providing visual selection functionality for TUI views.
    
    This mixin provides common visual selection behavior including:
    - Visual mode toggling
    - Range selection
    - Individual item selection
    - Selection clearing
    
    Classes using this mixin must have:
    - self.cursor_idx: int - Current cursor position
    - self.selected_items: Set[int] - Set of selected item indices
    - self.items: list - List of items being displayed
    """
    
    def __init__(self):
        """Initialize visual selection state."""
        self.visual_mode: bool = False
        self.visual_start_idx: Optional[int] = None
        self.selected_items: Set[int] = set()
    
    def is_item_selected(self, index: int) -> bool:
        """Check if an item at the given index is selected.
        
        Args:
            index: Index of the item to check
            
        Returns:
            True if the item is selected
        """
        # Check explicit selection
        if index in self.selected_items:
            return True
        
        # Check visual mode range
        if self.visual_mode and self.visual_start_idx is not None:
            visual_min = min(self.visual_start_idx, self.cursor_idx)
            visual_max = max(self.visual_start_idx, self.cursor_idx)
            if visual_min <= index <= visual_max:
                return True
        
        return False
    
    def toggle_item_selection(self, index: Optional[int] = None) -> bool:
        """Toggle selection of an item.
        
        Args:
            index: Index to toggle, or None to use cursor position
            
        Returns:
            True if selection changed
        """
        if index is None:
            index = self.cursor_idx
        
        if index in self.selected_items:
            self.selected_items.remove(index)
        else:
            self.selected_items.add(index)
        
        # Exit visual mode when toggling individual selection
        self.visual_mode = False
        self.visual_start_idx = None
        
        return True
    
    def enter_visual_mode(self) -> None:
        """Enter visual selection mode."""
        if not self.visual_mode:
            self.visual_mode = True
            self.visual_start_idx = self.cursor_idx
    
    def exit_visual_mode(self, confirm_selection: bool = False) -> bool:
        """Exit visual selection mode.
        
        Args:
            confirm_selection: If True, add visual range to selection
            
        Returns:
            True if selection changed
        """
        selection_changed = False
        
        if self.visual_mode and confirm_selection and self.visual_start_idx is not None:
            # Add visual range to selection
            visual_min = min(self.visual_start_idx, self.cursor_idx)
            visual_max = max(self.visual_start_idx, self.cursor_idx)
            
            for i in range(visual_min, visual_max + 1):
                if i < len(self.items):
                    self.selected_items.add(i)
            
            selection_changed = True
        
        self.visual_mode = False
        self.visual_start_idx = None
        
        return selection_changed
    
    def toggle_visual_mode(self) -> bool:
        """Toggle visual selection mode.
        
        Returns:
            True if selection changed
        """
        if not self.visual_mode:
            self.enter_visual_mode()
            return False
        else:
            return self.exit_visual_mode(confirm_selection=True)
    
    def clear_selection(self) -> bool:
        """Clear all selections and exit visual mode.
        
        Returns:
            True if there were selections to clear
        """
        had_selections = bool(self.selected_items)
        self.selected_items.clear()
        self.visual_mode = False
        self.visual_start_idx = None
        return had_selections
    
    def select_all(self) -> bool:
        """Select all items.
        
        Returns:
            True if selection changed
        """
        old_size = len(self.selected_items)
        for i in range(len(self.items)):
            self.selected_items.add(i)
        
        self.visual_mode = False
        self.visual_start_idx = None
        
        return len(self.selected_items) != old_size
    
    def handle_selection_input(self, key: int) -> bool:
        """Handle selection-related keyboard input.
        
        Args:
            key: The key pressed
            
        Returns:
            True if selection changed
        """
        selection_changed = False
        
        if key == ord(' '):  # Space - toggle selection at cursor
            selection_changed = self.toggle_item_selection()
        
        elif key == ord('v'):  # Visual mode
            selection_changed = self.toggle_visual_mode()
        
        elif key == ord('c'):  # Clear all selections
            selection_changed = self.clear_selection()
        
        elif key == ord('a'):  # Select all
            selection_changed = self.select_all()
        
        elif key == 27:  # Escape - cancel visual mode
            self.exit_visual_mode(confirm_selection=False)
        
        return selection_changed
    
    def get_visual_mode_indicator(self) -> str:
        """Get the visual mode indicator string.
        
        Returns:
            Visual mode indicator or empty string
        """
        if self.visual_mode:
            return "-- VISUAL --"
        return ""
    
    def get_selection_range(self) -> Tuple[Optional[int], Optional[int]]:
        """Get the current visual selection range.
        
        Returns:
            Tuple of (start_index, end_index) or (None, None) if not in visual mode
        """
        if self.visual_mode and self.visual_start_idx is not None:
            visual_min = min(self.visual_start_idx, self.cursor_idx)
            visual_max = max(self.visual_start_idx, self.cursor_idx)
            return visual_min, visual_max
        return None, None