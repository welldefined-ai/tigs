"""Message view management for TUI."""

import curses
from typing import List, Tuple, Optional, Set, Union
from datetime import datetime

from cligent import Role
from .selection_mixin import VisualSelectionMixin
from .scrollable_mixin import ScrollableMixin
from .indicators import SelectionIndicators
from .text_utils import word_wrap
from .color_constants import get_role_color, COLOR_METADATA, COLOR_DEFAULT


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
        self.cursor_idx = 0  # Primary cursor index
        self.message_cursor_idx = self.cursor_idx  # Legacy alias for backward compatibility
        self.message_scroll_offset = 0  # Will be replaced with scroll_offset gradually
        self.selected_messages: Set[int] = set()  # Legacy alias
        self.selected_items = self.selected_messages  # Point to same set for mixin
        self._needs_message_view_init = True
        self._internal_scroll_offset = 0  # Internal scroll within a long message
        self.read_only = False  # Flag for read-only mode
    
    def get_selected_messages_content(self) -> str:
        """Get the exported chat content from cligent.
        
        Returns:
            The exported chat content from cligent
        """
        if not self.chat_parser or not hasattr(self, 'current_log_id'):
            raise ValueError("No chat loaded")
        
        # Clear any previous selections
        self.chat_parser.clear_selection()
        
        # Select the messages we want
        selected_indices = sorted(self.selected_messages)
        self.chat_parser.select(self.current_log_id, selected_indices)
        
        # Compose returns the exported text directly
        return self.chat_parser.compose()
    
    def load_messages(self, log_id: str) -> None:
        """Load messages for a specific log.

        Args:
            log_id: ID of the log to load messages from
        """
        if not self.chat_parser:
            self.messages = []
            return
            
        try:
            chat = self.chat_parser.parse(log_id)
            self.current_log_id = log_id  # Store log ID for compose()
            
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
                timestamp = msg.timestamp if hasattr(msg, 'timestamp') else None
                self.messages.append((role, content, timestamp))
            
            # Reset cursor and scroll position for new messages
            self.cursor_idx = 0
            self.message_cursor_idx = self.cursor_idx  # Keep legacy alias in sync
            self.message_scroll_offset = 0
            self._internal_scroll_offset = 0  # Reset internal scroll
            self.selected_messages.clear()
            # Update items reference for mixin
            self.items = self.messages

            # Defer cursor positioning until first draw when we have screen height
            self._needs_message_view_init = True
        except Exception:
            self.messages = []
    
    def _format_timestamp(self, timestamp) -> str:
        """Format timestamp with space separator for readability.
        
        Args:
            timestamp: Optional datetime object
            
        Returns:
            Formatted string like " 09-08 03:05" or empty string
        """
        if not timestamp:
            return ""
        try:
            return f" {timestamp.strftime('%m-%d %H:%M')}"
        except:
            return ""
    
    def get_display_lines(self, height: int, width: int = 40, colors_enabled: bool = False) -> List[Union[str, List[Tuple[str, int]]]]:
        """Get display lines for messages pane with bottom-anchored display.

        Args:
            height: Available height for content
            width: Available width for content
            colors_enabled: Whether to return colored output

        Returns:
            List of formatted message lines (strings or color tuple lists)
        """
        lines = []

        if not self.messages:
            if colors_enabled:
                lines.append([("(No messages to display)", COLOR_DEFAULT)])
            else:
                lines.append("(No messages to display)")
            return lines

        # Initialize message view on first draw when we have screen height
        if self._needs_message_view_init:
            self._init_message_view(height)
            self._needs_message_view_init = False

        # Calculate message heights with current width
        message_heights = self._calculate_message_heights(self.messages, width)

        # Get visible messages using variable heights
        visible_count, start_idx, end_idx = self._get_visible_messages_variable(height, message_heights)

        # Check if we're in single message mode (message too long for window)
        is_single_message_mode = (visible_count == 1 and
                                  start_idx == self.message_cursor_idx and
                                  message_heights[self.message_cursor_idx] >= height - 2)

        if is_single_message_mode:
            return self._get_single_message_display_lines(height, width, colors_enabled)

        # Build display lines for multi-message view
        for i in range(start_idx, end_idx):
            role, content, timestamp = self.messages[i]

            # Check if selected using mixin method (only if not read-only)
            is_selected = self.is_item_selected(i) if not self.read_only else False

            # Format selection and cursor indicators using the indicators module
            if self.read_only:
                # In read-only mode, show minimal indicators
                selection_indicator = ""
                cursor_indicator = "• " if i == self.message_cursor_idx else "  "
            else:
                selection_indicator = SelectionIndicators.format_selection_box(is_selected)
                cursor_indicator = SelectionIndicators.format_cursor(
                    i == self.message_cursor_idx, style="triangle"
                )

            # Format message header
            if role == 'user':
                role_text = "User"
            elif role == 'assistant':
                role_text = "Assistant"
            elif role == 'system':
                role_text = "System"
            else:
                role_text = role.capitalize()
            timestamp_text = self._format_timestamp(timestamp)

            if colors_enabled:
                # Build colored header parts
                header_parts = []
                # Selection and cursor indicators - default color
                header_parts.append((f"{cursor_indicator}{selection_indicator} ", COLOR_DEFAULT))
                # Role with appropriate color
                role_color = get_role_color(role)
                header_parts.append((role_text, role_color))
                # Timestamp with metadata color
                if timestamp_text:
                    header_parts.append((timestamp_text, COLOR_METADATA))
                # Colon separator
                header_parts.append((":", COLOR_DEFAULT))
                lines.append(header_parts)
            else:
                header = f"{cursor_indicator}{selection_indicator} {role_text}{timestamp_text}:"
                lines.append(header)

            # Add wrapped content lines
            content_width = max(10, width - 6)  # Account for borders and indentation
            for line in content.split('\n'):
                if len(lines) < height - 2:  # Leave room for borders
                    wrapped_lines = self._word_wrap(line, content_width)
                    for wrapped in wrapped_lines:
                        if len(lines) < height - 2:
                            if colors_enabled:
                                # Indented content with default color
                                lines.append([("    ", COLOR_DEFAULT), (wrapped, COLOR_DEFAULT)])
                            else:
                                lines.append(f"    {wrapped}")

            # Add separator between messages if not the last
            if i < end_idx - 1 and len(lines) < height - 2:
                if colors_enabled:
                    lines.append([("", COLOR_DEFAULT)])
                else:
                    lines.append("")

        # Add status line if in visual mode (only if not read-only)
        if self.visual_mode and not self.read_only:
            if colors_enabled:
                lines.append([("", COLOR_DEFAULT)])
                lines.append([(SelectionIndicators.VISUAL_MODE, COLOR_DEFAULT)])
            else:
                lines.append("")
                lines.append(SelectionIndicators.VISUAL_MODE)

        return lines

    def _get_single_message_display_lines(self, height: int, width: int, colors_enabled: bool = False) -> List[Union[str, List[Tuple[str, int]]]]:
        """Get display lines for single message mode with gradual scrolling.

        Args:
            height: Available height for content
            width: Available width for content
            colors_enabled: Whether to return colored output

        Returns:
            List of formatted message lines (strings or color tuple lists)
        """
        lines = []
        available_height = height - 2  # Account for borders

        if self.visual_mode:
            available_height -= 2  # Leave room for visual mode indicator

        if self.message_cursor_idx >= len(self.messages):
            return lines

        role, content, timestamp = self.messages[self.message_cursor_idx]

        # Check if selected using mixin method (only if not read-only)
        is_selected = self.is_item_selected(self.message_cursor_idx) if not self.read_only else False

        # Format selection and cursor indicators using the indicators module
        if self.read_only:
            # In read-only mode, show minimal indicators
            selection_indicator = ""
            cursor_indicator = "• "
        else:
            selection_indicator = SelectionIndicators.format_selection_box(is_selected)
            cursor_indicator = SelectionIndicators.format_cursor(True, style="triangle")

        # Format message header
        if role == 'user':
            role_text = "User"
        elif role == 'assistant':
            role_text = "Assistant"
        elif role == 'system':
            role_text = "System"
        else:
            role_text = role.capitalize()
        timestamp_text = self._format_timestamp(timestamp)

        # Generate all lines for this message first
        all_lines = []

        # Add header
        if colors_enabled:
            header_parts = []
            header_parts.append((f"{cursor_indicator}{selection_indicator} ", COLOR_DEFAULT))
            role_color = get_role_color(role)
            header_parts.append((role_text, role_color))
            if timestamp_text:
                header_parts.append((timestamp_text, COLOR_METADATA))
            header_parts.append((":", COLOR_DEFAULT))
            all_lines.append(header_parts)
        else:
            header = f"{cursor_indicator}{selection_indicator} {role_text}{timestamp_text}:"
            all_lines.append(header)

        # Add wrapped content lines
        content_width = max(10, width - 8)  # Account for borders, indentation, and scroll indicator
        for line in content.split('\n'):
            wrapped_lines = self._word_wrap(line, content_width)
            for wrapped in wrapped_lines:
                if colors_enabled:
                    all_lines.append([("    ", COLOR_DEFAULT), (wrapped, COLOR_DEFAULT)])
                else:
                    all_lines.append(f"    {wrapped}")

        # Calculate scroll indicators
        start_line = max(0, self._internal_scroll_offset)
        end_line = min(len(all_lines), start_line + available_height)

        can_scroll_up = start_line > 0
        can_scroll_down = end_line < len(all_lines)

        # Add lines with scroll indicators
        display_lines = all_lines[start_line:end_line]
        for i, line in enumerate(display_lines):
            # Calculate scroll indicator for this line
            scroll_indicator = ""
            if i == 0 and can_scroll_up:
                scroll_indicator = "↑"
            elif i == len(display_lines) - 1 and can_scroll_down:
                scroll_indicator = "↓"
            elif can_scroll_up or can_scroll_down:
                scroll_indicator = "│"

            if colors_enabled and isinstance(line, list):
                # Add scroll indicator to colored line
                line_with_scroll = line.copy()
                if scroll_indicator:
                    # Pad to right edge and add scroll indicator
                    line_content_width = sum(len(part[0]) for part in line)
                    padding_needed = max(0, width - 4 - line_content_width - 1)  # -4 for borders, -1 for indicator
                    if padding_needed > 0:
                        line_with_scroll.append((" " * padding_needed, COLOR_DEFAULT))
                    line_with_scroll.append((scroll_indicator, COLOR_METADATA))
                lines.append(line_with_scroll)
            else:
                # Add scroll indicator to plain text line
                if scroll_indicator:
                    line_str = str(line)
                    line_content_width = len(line_str)
                    padding_needed = max(0, width - 4 - line_content_width - 1)  # -4 for borders, -1 for indicator
                    padded_line = line_str + " " * padding_needed + scroll_indicator
                    lines.append(padded_line)
                else:
                    lines.append(line)

        # Add status line if in visual mode (only if not read-only)
        if self.visual_mode and not self.read_only and len(lines) < available_height:
            if colors_enabled:
                lines.append([("", COLOR_DEFAULT)])
                lines.append([(SelectionIndicators.VISUAL_MODE, COLOR_DEFAULT)])
            else:
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

        # Check if we're in single message mode
        # We'll use a reasonable default width for detection, actual width will be used in display
        message_heights = self._calculate_message_heights(self.messages, 80)  # Use reasonable default width
        is_single_message_mode = (self.message_cursor_idx < len(message_heights) and
                                  message_heights[self.message_cursor_idx] >= pane_height - 2)

        # Navigation with Up/Down arrows
        if key == curses.KEY_UP:
            if is_single_message_mode:
                # Scroll within the current message
                if self._internal_scroll_offset > 0:
                    self._internal_scroll_offset -= 1
                elif self.cursor_idx > 0:
                    # Move to previous message and reset internal scroll
                    self.cursor_idx -= 1
                    self.message_cursor_idx = self.cursor_idx
                    self._internal_scroll_offset = 0
                    # Calculate scroll to end of previous message if it's also long
                    if self.cursor_idx < len(message_heights):
                        prev_msg_height = message_heights[self.cursor_idx]
                        if prev_msg_height >= pane_height - 2:
                            # Position at end of previous message
                            self._internal_scroll_offset = max(0, prev_msg_height - (pane_height - 2))
            else:
                # Standard multi-message navigation
                if self.cursor_idx > 0:
                    self.cursor_idx -= 1
                    self.message_cursor_idx = self.cursor_idx
                    self._internal_scroll_offset = 0  # Reset internal scroll
                    # If cursor moved above visible area, scroll up
                    if self.cursor_idx < self.message_scroll_offset:
                        self.message_scroll_offset = self.cursor_idx

        elif key == curses.KEY_DOWN:
            if is_single_message_mode:
                # Calculate total lines for current message
                role, content, timestamp = self.messages[self.message_cursor_idx]
                content_width = max(10, 80 - 6)  # Use reasonable default width calculation
                all_lines = 1  # Header
                for line in content.split('\n'):
                    wrapped_lines = self._word_wrap(line, content_width)
                    all_lines += len(wrapped_lines)

                available_height = pane_height - 2
                if self.visual_mode:
                    available_height -= 2

                # Scroll within the current message
                if self._internal_scroll_offset + available_height < all_lines:
                    self._internal_scroll_offset += 1
                elif self.cursor_idx < len(self.messages) - 1:
                    # Move to next message and reset internal scroll
                    self.cursor_idx += 1
                    self.message_cursor_idx = self.cursor_idx
                    self._internal_scroll_offset = 0
            else:
                # Standard multi-message navigation
                if self.cursor_idx < len(self.messages) - 1:
                    self.cursor_idx += 1
                    self.message_cursor_idx = self.cursor_idx
                    self._internal_scroll_offset = 0  # Reset internal scroll
                    # Use pane height for scrolling calculations
                    visible_items = self._visible_message_items(pane_height)
                    # If cursor moved below visible area, scroll down to keep cursor visible
                    if self.cursor_idx >= self.message_scroll_offset + visible_items:
                        self.message_scroll_offset = self.cursor_idx - visible_items + 1
                        # Ensure scroll doesn't go beyond the last page
                        max_scroll = max(0, len(self.messages) - visible_items)
                        self.message_scroll_offset = min(self.message_scroll_offset, max_scroll)

        # Delegate selection operations to mixin (only if not read-only)
        elif not self.read_only:
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
    
    def _calculate_message_heights(self, messages: List[Tuple[str, str, any]], width: int) -> List[int]:
        """Calculate height needed for each message with word wrapping.
        
        Args:
            messages: List of (role, content, timestamp) tuples
            width: Available width for display
        
        Returns:
            List of heights for each message
        """
        heights = []
        content_width = max(10, width - 6)  # Account for borders and indentation
        
        for role, content, timestamp in messages:
            # Header line
            height = 1
            
            # Content lines with word wrapping
            content_lines = content.split('\n')
            for line in content_lines:
                if len(line) <= content_width:
                    height += 1
                else:
                    # Word wrap long lines
                    wrapped = self._word_wrap(line, content_width)
                    height += len(wrapped)
            
            # Add separator line (except for last message)
            height += 1
            
            heights.append(height)
        
        return heights
    
    def _word_wrap(self, text: str, width: int) -> List[str]:
        """Word wrap text to specified width.
        
        Args:
            text: Text to wrap
            width: Maximum width per line
            
        Returns:
            List of wrapped lines
        """
        return word_wrap(text, width)
    
    def _get_visible_messages_variable(
        self, 
        height: int, 
        message_heights: List[int]
    ) -> Tuple[int, int, int]:
        """Calculate visible messages with variable heights.
        
        Args:
            height: Available screen height
            message_heights: Heights for each message
        
        Returns:
            Tuple of (visible_count, start_idx, end_idx)
        """
        if not self.messages:
            return 0, 0, 0
        
        available_height = height - 2  # Borders
        if self.visual_mode:
            available_height -= 2  # Visual mode indicator
        
        # Handle extremely large single message
        if self.message_cursor_idx < len(message_heights):
            cursor_height = message_heights[self.message_cursor_idx]
            if cursor_height >= available_height:
                # Show only the cursor message with scrolling
                return 1, self.message_cursor_idx, self.message_cursor_idx + 1
        
        # Calculate visible range based on scroll offset and heights
        current_height = 0
        start_idx = self.message_scroll_offset
        end_idx = start_idx
        
        for i in range(start_idx, len(self.messages)):
            if i < len(message_heights):
                msg_height = message_heights[i]
                if current_height + msg_height <= available_height:
                    current_height += msg_height
                    end_idx = i + 1
                else:
                    break
        
        # Ensure cursor is visible
        if self.message_cursor_idx < start_idx:
            # Scroll up to show cursor
            self.message_scroll_offset = self.message_cursor_idx
            return self._get_visible_messages_variable(height, message_heights)
        elif self.message_cursor_idx >= end_idx:
            # Scroll down to show cursor
            # Calculate new start to fit cursor
            new_start = self.message_cursor_idx
            test_height = message_heights[self.message_cursor_idx] if self.message_cursor_idx < len(message_heights) else 3
            
            while new_start > 0 and test_height < available_height:
                new_start -= 1
                if new_start < len(message_heights):
                    test_height += message_heights[new_start]
                    if test_height > available_height:
                        new_start += 1
                        break
            
            self.message_scroll_offset = new_start
            return self._get_visible_messages_variable(height, message_heights)
        
        return end_idx - start_idx, start_idx, end_idx
    
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
            self._internal_scroll_offset = 0
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
        self._internal_scroll_offset = 0  # Reset internal scroll
    
    def scroll_to_cursor(self, viewport_height: int, border_size: int = 2) -> None:
        """Ensure cursor is visible in viewport with variable message heights.
        
        Args:
            viewport_height: Total height available for display
            border_size: Size of borders to subtract from height
        """
        if not self.messages or not hasattr(self, 'cursor_idx'):
            return
        
        # For variable heights, we need to trigger a recalculation
        # The _get_visible_messages_variable method will handle cursor visibility
        self._needs_message_view_init = True