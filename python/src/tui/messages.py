"""Message view management for TUI."""

import curses
from typing import List, Tuple, Optional, Set
from datetime import datetime

from cligent import Role


class MessageView:
    """Manages message display and interaction."""
    
    def __init__(self, chat_parser):
        """Initialize message view.
        
        Args:
            chat_parser: ChatParser instance for loading messages
        """
        self.chat_parser = chat_parser
        self.messages = []
        self.message_cursor_idx = 0
        self.message_scroll_offset = 0
        self.selected_messages: Set[int] = set()
        self.visual_mode = False
        self.visual_start_idx: Optional[int] = None
        self._needs_message_view_init = True
    
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
            self.message_scroll_offset = 0
            self.selected_messages.clear()
            self.visual_mode = False
            self.visual_start_idx = None
            
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
            
            # Check if selected
            is_selected = i in self.selected_messages
            
            # In visual mode, check if in range
            if self.visual_mode and self.visual_start_idx is not None:
                visual_min = min(self.visual_start_idx, self.message_cursor_idx)
                visual_max = max(self.visual_start_idx, self.message_cursor_idx)
                if visual_min <= i <= visual_max:
                    is_selected = True
            
            # Format selection indicator
            if is_selected:
                selection_indicator = "[x]"
            else:
                selection_indicator = "[ ]"
            
            # Format cursor indicator
            if i == self.message_cursor_idx:
                cursor_indicator = "▶"
            else:
                cursor_indicator = " "
            
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
            lines.append("-- VISUAL MODE --")
        
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
                # If cursor moved above visible area, scroll up
                if self.message_cursor_idx < self.message_scroll_offset:
                    self.message_scroll_offset = self.message_cursor_idx
                    
        elif key == curses.KEY_DOWN:
            if self.message_cursor_idx < len(self.messages) - 1:
                self.message_cursor_idx += 1
                # If cursor moved below visible area, scroll down to keep cursor visible
                if self.message_cursor_idx >= self.message_scroll_offset + visible_items:
                    # Calculate new scroll to keep cursor visible
                    # The cursor should remain at its new position, we just adjust scroll
                    self.message_scroll_offset = self.message_cursor_idx - visible_items + 1
                    
                    # Ensure scroll doesn't go beyond the last page
                    max_scroll = max(0, len(self.messages) - visible_items)
                    self.message_scroll_offset = min(self.message_scroll_offset, max_scroll)
        
        # Selection operations
        elif key == ord(' '):  # Space - toggle selection at cursor position
            if self.message_cursor_idx in self.selected_messages:
                self.selected_messages.remove(self.message_cursor_idx)
            else:
                self.selected_messages.add(self.message_cursor_idx)
            # Exit visual mode when using space
            self.visual_mode = False
            self.visual_start_idx = None
        
        elif key == ord('v'):  # Start visual selection mode
            if not self.visual_mode:
                self.visual_mode = True
                self.visual_start_idx = self.message_cursor_idx
            else:
                # Exit visual mode and confirm selection
                if self.visual_start_idx is not None:
                    visual_min = min(self.visual_start_idx, self.message_cursor_idx)
                    visual_max = max(self.visual_start_idx, self.message_cursor_idx)
                    for i in range(visual_min, visual_max + 1):
                        if i < len(self.messages):
                            self.selected_messages.add(i)
                self.visual_mode = False
                self.visual_start_idx = None
        
        elif key == ord('c'):  # Clear all selections
            self.selected_messages.clear()
            self.visual_mode = False
            self.visual_start_idx = None
        
        elif key == ord('a'):  # Select all messages
            for i in range(len(self.messages)):
                self.selected_messages.add(i)
            self.visual_mode = False
            self.visual_start_idx = None
        
        elif key == 27:  # Escape - cancel visual mode
            self.visual_mode = False
            self.visual_start_idx = None
    
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