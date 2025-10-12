"""Message view management for TUI."""

import curses
from typing import List, Tuple, Set, Union

from .selection_mixin import VisualSelectionMixin
from .scrollable_mixin import ScrollableMixin
from .indicators import SelectionIndicators
from .text_utils import word_wrap
from .color_constants import get_role_color, COLOR_METADATA, COLOR_DEFAULT


class MessageView(VisualSelectionMixin, ScrollableMixin):
    """Manages message display and interaction."""

    def __init__(self, chat_parser, default_to_first_message: bool = False):
        """Initialize message view.

        Args:
            chat_parser: ChatParser instance for loading messages
            default_to_first_message: If True, cursor starts at first message; if False, starts at last message
        """
        VisualSelectionMixin.__init__(self)  # Initialize selection mixin
        ScrollableMixin.__init__(self)  # Initialize scrollable mixin
        self.chat_parser = chat_parser
        self.messages = []
        self.items = self.messages  # Alias for mixin compatibility
        self.cursor_idx = 0  # Primary cursor index
        self.message_cursor_idx = (
            self.cursor_idx
        )  # Legacy alias for backward compatibility
        self.message_scroll_offset = 0  # Will be replaced with scroll_offset gradually
        self.selected_messages: Set[int] = set()  # Legacy alias
        self.selected_items = self.selected_messages  # Point to same set for mixin
        self._needs_message_view_init = True
        self._scroll_offset = 0  # Simple line-based scrolling offset
        self.read_only = False  # Flag for read-only mode
        self.separator_map = {}  # Map of {message_index: log_uri} for separators
        self._last_key = None  # Track last key for multi-key shortcuts like gg/GG
        self.default_to_first_message = (
            default_to_first_message  # Control default cursor position
        )

    def load_messages(self, log_uri: str) -> None:
        """Load messages for a specific log.

        Args:
            log_uri: URI of the log to load messages from
        """
        if not self.chat_parser:
            self.messages = []
            return

        try:
            chat = self.chat_parser.parse(log_uri)
            self.current_log_uri = log_uri  # Store log URI for compose()

            # Extract messages from the chat - store Message objects directly
            self.messages = list(chat.messages)

            # Position cursor at last message for new messages
            self.cursor_idx = max(0, len(self.messages) - 1)
            self.message_cursor_idx = self.cursor_idx  # Keep legacy alias in sync
            self.message_scroll_offset = 0
            self._scroll_offset = 0  # Reset scroll offset
            self.selected_messages.clear()
            # Update items reference for mixin
            self.items = self.messages

            # Defer cursor positioning until first draw when we have screen height
            self._needs_message_view_init = True
        except Exception:
            self.messages = []

    def prepare_messages_for_display(self):
        """Prepare messages for display by grouping and ordering them if needed.

        This method should be called by ViewApp after loading messages to handle
        multiple log files. It reorders messages and creates separator map.
        """
        if not self.messages:
            self.separator_map = {}
            return

        # Check if we have messages from multiple log files
        log_uris = set()
        for msg in self.messages:
            log_uri = getattr(msg, "log_uri", "unknown")
            log_uris.add(log_uri)

        if len(log_uris) <= 1:
            # Single log file or no messages - no separators needed
            self.separator_map = {}
            return

        # Multiple log files - group and reorder messages
        grouped_messages = {}
        for msg in self.messages:
            log_uri = getattr(msg, "log_uri", "unknown")
            if log_uri not in grouped_messages:
                grouped_messages[log_uri] = []
            grouped_messages[log_uri].append(msg)

        # Sort messages within each group by timestamp
        for log_uri, message_list in grouped_messages.items():
            message_list.sort(key=lambda x: x.timestamp or 0)

        # Rebuild messages list in grouped order and create separator map
        new_messages = []
        separator_map = {}

        for log_uri, message_list in grouped_messages.items():
            # Add all messages for this log group
            new_messages.extend(message_list)
            # Mark where separator should go (after the last message of this group)
            if len(new_messages) > 0:
                separator_map[len(new_messages) - 1] = log_uri

        self.messages = new_messages
        self.items = self.messages  # Update items reference for mixin
        self.separator_map = separator_map

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
        except (ValueError, AttributeError, TypeError):
            return ""

    def get_display_lines(
        self, height: int, width: int = 40, colors_enabled: bool = False
    ) -> List[Union[str, List[Tuple[str, int]]]]:
        """Get display lines for messages pane with bottom-anchored display.

        Args:
            height: Available height for content
            width: Available width for content
            colors_enabled: Whether to return colored output

        Returns:
            List of formatted message lines (strings or color tuple lists)
        """
        # Store width for use in handle_input
        self._last_width = width

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
        self._calculate_message_heights(self.messages, width)

        # Build ALL display lines for ALL messages (unified logic)
        all_lines = []

        for i in range(len(self.messages)):
            msg = self.messages[i]
            role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            content = msg.content if hasattr(msg, "content") else str(msg)
            timestamp = msg.timestamp

            # Check if selected using mixin method (only if not read-only)
            is_selected = self.is_item_selected(i) if not self.read_only else False

            # Format selection and cursor indicators using the indicators module
            if self.read_only:
                # In read-only mode, show minimal indicators
                selection_indicator = ""
                cursor_indicator = "• " if i == self.message_cursor_idx else "  "
            else:
                selection_indicator = SelectionIndicators.format_selection_box(
                    is_selected
                )
                cursor_indicator = SelectionIndicators.format_cursor(
                    i == self.message_cursor_idx, style="triangle"
                )

            # Format message header
            if role == "user":
                role_text = "User"
            elif role == "assistant":
                role_text = "Assistant"
            elif role == "system":
                role_text = "System"
            else:
                role_text = role.capitalize()
            timestamp_text = self._format_timestamp(timestamp)

            if colors_enabled:
                # Build colored header parts
                header_parts = []
                # Selection and cursor indicators - default color
                header_parts.append(
                    (f"{cursor_indicator}{selection_indicator} ", COLOR_DEFAULT)
                )
                # Role with appropriate color
                role_color = get_role_color(role)
                header_parts.append((role_text, role_color))
                # Timestamp with metadata color
                if timestamp_text:
                    header_parts.append((timestamp_text, COLOR_METADATA))
                # Colon separator
                header_parts.append((":", COLOR_DEFAULT))
                all_lines.append(header_parts)
            else:
                header = f"{cursor_indicator}{selection_indicator} {role_text}{timestamp_text}:"
                all_lines.append(header)

            # Add wrapped content lines
            content_width = max(10, width - 6)  # Account for borders and indentation
            for line in content.split("\n"):
                wrapped_lines = self._word_wrap(line, content_width)
                for wrapped in wrapped_lines:
                    if colors_enabled:
                        # Indented content with default color
                        all_lines.append(
                            [("    ", COLOR_DEFAULT), (wrapped, COLOR_DEFAULT)]
                        )
                    else:
                        all_lines.append(f"    {wrapped}")

            # Add separator between messages if not the last
            if i < len(self.messages) - 1:
                if colors_enabled:
                    all_lines.append([("", COLOR_DEFAULT)])
                else:
                    all_lines.append("")

            # Check if we need to add a log separator after this message
            if i in self.separator_map:
                log_uri = self.separator_map[i]
                # Create full-width separator with centered log URI
                center_text = f" log_uri: {log_uri} "
                total_width = width - 4  # Account for borders

                # Calculate padding needed
                if len(center_text) >= total_width:
                    # If text is too long, truncate
                    separator_text = center_text[:total_width]
                else:
                    # Calculate how many chars on each side
                    remaining = total_width - len(center_text)
                    left_chars = remaining // 2
                    right_chars = remaining - left_chars

                    left_fill = ">" * left_chars
                    right_fill = "<" * right_chars
                    separator_text = f"{left_fill}{center_text}{right_fill}"

                if colors_enabled:
                    all_lines.append([("", COLOR_DEFAULT)])
                    all_lines.append([(separator_text, COLOR_METADATA)])
                    all_lines.append([("", COLOR_DEFAULT)])
                else:
                    all_lines.append("")
                    all_lines.append(separator_text)
                    all_lines.append("")
        # Add status line if in visual mode (only if not read-only)
        if self.visual_mode and not self.read_only:
            if colors_enabled:
                all_lines.append([("", COLOR_DEFAULT)])
            else:
                all_lines.append("")
            if colors_enabled:
                all_lines.append([(SelectionIndicators.VISUAL_MODE, COLOR_DEFAULT)])
            else:
                all_lines.append(SelectionIndicators.VISUAL_MODE)

        # Apply simple scrolling: take a slice of all_lines based on scroll offset
        # Account for borders and footer
        available_content_height = height - 2  # Borders
        if self.visual_mode and not self.read_only:
            available_content_height -= 2  # Visual mode takes 2 lines
        available_content_height -= 1  # Reserve 1 line for footer

        start_line = self._scroll_offset
        end_line = start_line + available_content_height

        # Ensure we don't scroll past the beginning
        if start_line < 0:
            start_line = 0
            self._scroll_offset = 0

        # Ensure we don't scroll past the end (but allow scrolling to the very bottom)
        max_start_line = max(0, len(all_lines) - available_content_height)
        if start_line > max_start_line:
            start_line = max_start_line
            self._scroll_offset = start_line
            end_line = start_line + available_content_height

        # Get the visible lines
        lines = all_lines[start_line:end_line]

        # Add status footer showing current position (after scrolling adjustments)
        if self.messages:
            # Calculate how many lines we have for content (excluding footer)
            available_lines = height - 2  # Account for borders
            if self.visual_mode and not self.read_only:
                available_lines -= 2  # Visual mode takes 2 lines
            available_lines -= 1  # Reserve 1 line for footer

            # Trim lines if needed to make room for footer
            if len(lines) > available_lines:
                lines = lines[:available_lines]

            # Pad to push footer to bottom
            while len(lines) < available_lines:
                if colors_enabled:
                    lines.append([("", COLOR_DEFAULT)])
                else:
                    lines.append("")

            # Add the status footer
            status = f"({self.cursor_idx + 1}/{len(self.messages)})"
            # Right-align the status text
            padding = max(0, width - len(status) - 4)
            status_line = " " * padding + status

            if colors_enabled:
                lines.append([(status_line, COLOR_METADATA)])
            else:
                lines.append(status_line)

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

        # Handle 'gg' shortcut - jump to first message
        if key == ord("g") and self._last_key == ord("g"):
            # Jump to first message
            self.cursor_idx = 0
            self.message_cursor_idx = self.cursor_idx
            # Scroll to show the first message
            self._scroll_to_message(self.cursor_idx, pane_height)
            self._last_key = None  # Reset for next shortcut
            return

        # Handle 'GG' shortcut (Shift+G twice) - jump to last message
        elif key == ord("G") and self._last_key == ord("G"):
            # Jump to last message
            self.cursor_idx = len(self.messages) - 1
            self.message_cursor_idx = self.cursor_idx
            # Scroll to show the last message
            self._scroll_to_message(self.cursor_idx, pane_height)
            self._last_key = None  # Reset for next shortcut
            return

        # Store current key for next iteration (for gg/GG detection)
        self._last_key = key

        # Up/Down arrows: Message navigation
        if key == curses.KEY_UP:
            # Move to previous message (up)
            if self.cursor_idx > 0:
                self.cursor_idx -= 1
                self.message_cursor_idx = self.cursor_idx
                # Scroll to show the new current message
                self._scroll_to_message(self.cursor_idx, pane_height)

        elif key == curses.KEY_DOWN:
            # Move to next message (down)
            if self.cursor_idx < len(self.messages) - 1:
                self.cursor_idx += 1
                self.message_cursor_idx = self.cursor_idx
                # Scroll to show the new current message
                self._scroll_to_message(self.cursor_idx, pane_height)

        # Vim-like keys: j/k for scrolling
        elif key == ord("j"):
            # Scroll down by one line, but check if there's more content below
            if hasattr(self, "_last_width"):
                total_lines = self._calculate_total_content_lines(self._last_width)

                # Calculate available content height (consistent with get_display_lines)
                available_content_height = pane_height - 2  # Borders
                if self.visual_mode and not self.read_only:
                    available_content_height -= 2  # Visual mode takes 2 lines
                available_content_height -= 1  # Reserve 1 line for footer

                # Only scroll if we haven't reached the maximum scroll position
                max_scroll_offset = max(0, total_lines - available_content_height)
                if self._scroll_offset < max_scroll_offset:
                    self._scroll_offset += 1

        elif key == ord("k"):
            # Scroll up by one line
            if self._scroll_offset > 0:
                self._scroll_offset -= 1

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

    def _calculate_message_heights(
        self, messages: List[Tuple[str, str, any]], width: int
    ) -> List[int]:
        """Calculate height needed for each message with word wrapping.

        Args:
            messages: List of Message objects
            width: Available width for display

        Returns:
            List of heights for each message
        """
        heights = []
        content_width = max(10, width - 6)  # Account for borders and indentation

        for msg in messages:
            content = msg.content if hasattr(msg, "content") else str(msg)
            # Header line
            height = 1

            # Content lines with word wrapping
            content_lines = content.split("\n")
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
        self, height: int, message_heights: List[int]
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

        # Calculate visible range based on scroll offset and heights
        # Always try to fill the available space, allowing partial message display
        current_height = 0
        start_idx = self.message_scroll_offset
        end_idx = start_idx

        for i in range(start_idx, len(self.messages)):
            if i < len(message_heights):
                msg_height = message_heights[i]
                # Include message if it fits completely OR if we have space and it's the next message
                if current_height + msg_height <= available_height:
                    current_height += msg_height
                    end_idx = i + 1
                elif current_height == 0:
                    # Always include at least one message, even if it's too tall
                    end_idx = i + 1
                    break
                else:
                    # If there's remaining space, include this message for partial display
                    remaining_space = available_height - current_height
                    if remaining_space > 2:  # Need at least header + one line
                        end_idx = i + 1
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
            test_height = (
                message_heights[self.message_cursor_idx]
                if self.message_cursor_idx < len(message_heights)
                else 3
            )

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
            self._line_scroll_offset = 0
            return

        self._visible_message_items(height)

        # Position cursor based on configuration
        if self.default_to_first_message:
            # Start at the beginning of the conversation (first message)
            self.cursor_idx = 0
        else:
            # Start at the end of the conversation (last message)
            self.cursor_idx = max(0, len(self.messages) - 1)

        self.message_cursor_idx = self.cursor_idx
        # Scroll to show the cursor position
        self._scroll_to_message(self.cursor_idx, height)

    def _calculate_total_content_lines(self, width: int) -> int:
        """Calculate the total number of lines that would be generated for all content.

        Args:
            width: Available width for display

        Returns:
            Total number of content lines
        """
        if not self.messages:
            return 1  # "(No messages to display)"

        total_lines = 0
        content_width = max(10, width - 6)

        for i, msg in enumerate(self.messages):
            # Add 1 line for header
            total_lines += 1

            # Add lines for content
            for line in msg.content.split("\n"):
                wrapped_lines = self._word_wrap(line, content_width)
                total_lines += len(wrapped_lines)

            # Add separator line (except for last message)
            if i < len(self.messages) - 1:
                total_lines += 1

            # Add log separator lines if this message has a separator after it
            if i in self.separator_map:
                total_lines += 3  # blank line + separator + blank line

        # Add visual mode lines if applicable
        if self.visual_mode and not self.read_only:
            total_lines += 2  # blank line + visual mode indicator

        return total_lines

    def _scroll_to_message(self, message_idx: int, pane_height: int) -> None:
        """Scroll to make a specific message visible.

        Args:
            message_idx: Index of the message to scroll to
            pane_height: Height of the pane
        """
        if not self.messages or not hasattr(self, "_last_width"):
            return

        # Calculate which line the message header starts at
        line_offset = 0
        content_width = max(10, self._last_width - 6)

        for i in range(message_idx):
            # Add 1 line for header
            line_offset += 1

            # Add lines for content
            msg = self.messages[i]
            content = msg.content if hasattr(msg, "content") else str(msg)
            for line in content.split("\n"):
                wrapped_lines = self._word_wrap(line, content_width)
                line_offset += len(wrapped_lines)

            # Add separator line (except for last message)
            if i < len(self.messages) - 1:
                line_offset += 1

        # Scroll to show this message near the top of the viewport
        # Position the message header a few lines from the top for better visibility
        target_offset = max(0, line_offset - 2)
        self._scroll_offset = target_offset

    def scroll_to_cursor(self, viewport_height: int, border_size: int = 2) -> None:
        """Ensure cursor is visible in viewport with variable message heights.

        Args:
            viewport_height: Total height available for display
            border_size: Size of borders to subtract from height
        """
        if not self.messages or not hasattr(self, "cursor_idx"):
            return

        # Use the new scroll method
        self._scroll_to_message(self.cursor_idx, viewport_height)
