"""Protocol definitions for TUI mixin requirements."""

from typing import Protocol, List, Set, Optional


class ScrollableView(Protocol):
    """Protocol defining requirements for using ScrollableMixin."""
    
    cursor_idx: int
    scroll_offset: int
    items: List
    

class SelectableView(Protocol):
    """Protocol defining requirements for using VisualSelectionMixin."""
    
    cursor_idx: int
    selected_items: Set[int]
    items: List
    visual_mode: bool
    visual_start_idx: Optional[int]


class ScrollableSelectableView(ScrollableView, SelectableView):
    """Combined protocol for views using both mixins."""
    pass