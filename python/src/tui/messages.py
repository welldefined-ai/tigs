"""Message view management for TUI."""

import curses
from typing import List, Tuple, Optional, Set
from datetime import datetime

from cligent import Role
from .selection import VisualSelectionMixin
from .scrollable import ScrollableMixin
from .indicators import SelectionIndicators


class MessageView(VisualSelectionMixin, ScrollableMixin):
    """Manages message display and interaction."""
    
    def __init__(self, chat_parser):
        """Initialize message view.
        
        Args:
            chat_parser: ChatParser instance for loading messages
        """
        VisualSelectionMixin.__init__(self)  # Initialize selection mixin
        ScrollableMixin.__init__(self)  # Initialize scrollable mixin
        self.chat_parser = chat_parser
        self.messages = []
        self.items = self.messages  # Alias for mixin compatibility
        self.message_cursor_idx = 0
        self.cursor_idx = 0  # Alias for mixin compatibility
        self.message_scroll_offset = 0  # Legacy alias
        self.selected_messages: Set[int] = set()  # Legacy alias
        self.selected_items = self.selected_messages  # Point to same set for mixin
        self._needs_message_view_init = True
    
    def get_selected_messages_content(self) -> str:
        """Get the exported chat content from cligent.
        
        Returns:
            The exported chat content from cligent
        """
        if not self.chat_parser or not hasattr(self, 'current_session_id'):
            raise ValueError("No chat loaded")
        
        # Clear any previous selections
        self.chat_parser.clear_selection()
        
        # Select the messages we want
        selected_indices = sorted(self.selected_messages)
        self.chat_parser.select(self.current_session_id, selected_indices)
        
        # Compose returns the exported text directly
        return self.chat_parser.compose()
    
    def load_messages(self, session_id: str) -> None:
        """Load messages for a specific session.
        
        Args:
            session_id: ID of the session to load messages from
        """
        if not self.chat_parser:
            self.messages = []
            return
            
        try:
            chat = self.chat_parser.parse(session_id)
            self.current_session_id = session_id  # Store session ID for compose()
            
            # Extract messages from the chat
            self.messages = []
            for msg in chat.messages:
                # Handle cligent Role enum or string
                if hasattr(msg, 'role'):
                    role = msg.role
                    # Convert Role enum to string if needed
                    if hasattr(role, 'value'):
                        role = role.value
                    elif role == Role.USER:
                        role = 'user'
                    elif role == Role.ASSISTANT:
                        role = 'assistant'
                    else:
                        role = str(role).lower()
                else:
                    role = 'unknown'
                    
                content = msg.content if hasattr(msg, 'content') else str(msg)
                self.messages.append((role, content))
            
            # Reset cursor and scroll position for new messages
            self.message_cursor_idx = 0
            self.cursor_idx = 0  # Keep mixin alias in sync
            self.message_scroll_offset = 0
            self.selected_messages.clear()
            # Update items reference for mixin
            self.items = self.messages
            
            # Defer cursor positioning until first draw when we have screen height
            self._needs_message_view_init = True
        except Exception:
            self.messages = []
    
    def get_display_lines(self, height: int) -> List[str]:
        """Get display lines for messages pane with bottom-anchored display.
        
        Args:
            height: Available height for content
            
        Returns:
            List of formatted message lines
        """
        lines = []
        
        if not self.messages:
            lines.append("(No messages to display)")
            return lines
        
        # Initialize message view on first draw when we have screen height
        if self._needs_message_view_init:
            self._init_message_view(height)
            self._needs_message_view_init = False
        
        # Get message view parameters (single source of truth)
        visible_items, start_idx, end_idx = self._message_view(height)

        # Build display lines
        for i in range(start_idx, end_idx):
            role, content = self.messages[i]
            
            # Check if selected using mixin method
            is_selected = self.is_item_selected(i)
            
            # Format selection and cursor indicators using the indicators module
            selection_indicator = SelectionIndicators.format_selection_box(is_selected)
            cursor_indicator = SelectionIndicators.format_cursor(
                i == self.message_cursor_idx, style="triangle"
            )
            
            # Format message header
            if role == 'user':
                header = f"{cursor_indicator}{selection_indicator} User:"
            else:
                header = f"{cursor_indicator}{selection_indicator} Assistant:"
            
            lines.append(header)
            
            # Add first line of content (truncated if needed)
            content_lines = content.split('\n')
            if content_lines:
                first_line = content_lines[0][:37] + "..." if len(content_lines[0]) > 37 else content_lines[0]
                lines.append(f"    {first_line}")
        
        # Add status line if in visual mode
        if self.visual_mode:
            lines.append("")
            lines.append(SelectionIndicators.VISUAL_MODE)
        
        return lines
    
    def handle_input(self, stdscr, key: int, pane_height: int) -> None:
        """Handle input when messages pane is focused.
        
        Args:
            stdscr: The curses screen (unused but kept for consistency)
            key: The key pressed
            pane_height: Height of the messages pane
        """
        if not self.messages:
            return
            
        # Use pane height for scrolling calculations, not full screen height
        visible_items = self._visible_message_items(pane_height)
        
        # Navigation with Up/Down arrows - move cursor and adjust scroll immediately
        if key == curses.KEY_UP:
            if self.message_cursor_idx > 0:
                self.message_cursor_idx -= 1
                self.cursor_idx = self.message_cursor_idx  # Keep mixin alias in sync
                # If cursor moved above visible area, scroll up
                if self.message_cursor_idx < self.message_scroll_offset:
                    self.message_scroll_offset = self.message_cursor_idx
                    
        elif key == curses.KEY_DOWN:
            if self.message_cursor_idx < len(self.messages) - 1:
                self.message_cursor_idx += 1
                self.cursor_idx = self.message_cursor_idx  # Keep mixin alias in sync
                # If cursor moved below visible area, scroll down to keep cursor visible
                if self.message_cursor_idx >= self.message_scroll_offset + visible_items:
                    # Calculate new scroll to keep cursor visible
                    # The cursor should remain at its new position, we just adjust scroll
                    self.message_scroll_offset = self.message_cursor_idx - visible_items + 1
                    
                    # Ensure scroll doesn't go beyond the last page
                    max_scroll = max(0, len(self.messages) - visible_items)
                    self.message_scroll_offset = min(self.message_scroll_offset, max_scroll)
        
        # Delegate selection operations to mixin
        else:
            self.handle_selection_input(key)
    
    def _visible_message_items(self, height: int) -> int:
        """Calculate how many message items can fit in the given height.
        
        Args:
            height: Screen height
            
        Returns:
            Number of message items that can be displayed
        """
        # Rows available for content between borders
        rows = max(0, height - 2)
        
        # Reserve rows for any status footer we append
        if self.visual_mode:
            rows = max(0, rows - 2)  # One blank + "-- VISUAL MODE --"
        
        LINES_PER_MESSAGE = 2  # Header + first content line
        return max(1, rows // LINES_PER_MESSAGE)
    
    def _message_view(self, height: int) -> Tuple[int, int, int]:
        """Get message view parameters - single source of truth.
        
        Args:
            height: Screen height
            
        Returns:
            Tuple of (visible_items, start_idx, end_idx)
        """
        visible_items = self._visible_message_items(height)
        start_idx = self.message_scroll_offset
        end_idx = min(start_idx + visible_items, len(self.messages))
        return visible_items, start_idx, end_idx
    
    def _init_message_view(self, height: int) -> None:
        """Initialize cursor and scroll position based on actual screen height.
        
        Args:
            height: Screen height
        """
        if not self.messages:
            self.message_cursor_idx = 0
            self.message_scroll_offset = 0
            return
        
        visible_items = self._visible_message_items(height)
        
        # Show last visible_items messages, with cursor at bottom of visible area
        self.message_scroll_offset = max(0, len(self.messages) - visible_items)
        # Position cursor at bottom of visible area, ensuring room to scroll down
        self.message_cursor_idx = min(
            len(self.messages) - 1,
            self.message_scroll_offset + visible_items - 1
        )
        self.cursor_idx = self.message_cursor_idx  # Keep mixin alias in sync