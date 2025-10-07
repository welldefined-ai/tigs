"""Logs view management for TUI."""

import curses
from typing import List, Tuple, Optional, Union
from datetime import datetime

from .color_constants import COLOR_METADATA


class LogsView:
    """Manages logs display and interaction."""

    def __init__(self, chat_parser):
        """Initialize logs view.

        Args:
            chat_parser: ChatParser instance for loading logs
        """
        self.chat_parser = chat_parser
        self.logs = []  # List of (log_uri, metadata) tuples
        self.selected_log_idx = 0
        self.log_scroll_offset = 0

    def load_logs(self) -> None:
        """Load logs from cligent."""
        if not self.chat_parser:
            return

        try:
            logs = self.chat_parser.list_logs()
            # Sort by modification time (newest first)
            self.logs = sorted(logs, key=lambda x: x[1]["modified"], reverse=True)

            # Auto-select the latest log
            if self.logs and self.selected_log_idx == 0:
                self.selected_log_idx = 0
        except Exception:
            self.logs = []

    def get_display_lines(
        self, height: int, width: int = 18, colors_enabled: bool = False
    ) -> List[Union[str, List[Tuple[str, int]]]]:
        """Get display lines for logs pane.

        Args:
            height: Available height for content
            width: Available width for content (default 18 for logs pane)
            colors_enabled: Whether to return colored output

        Returns:
            List of formatted log lines (strings or color tuple lists)
        """
        lines = []

        if not self.logs:
            if self.chat_parser:
                lines.append("No logs found")
            else:
                lines.append("Cligent not available")
            return lines

        # Reserve space for footer
        available_lines = height - 3  # -2 for borders, -1 for footer

        # Each log entry takes 2 lines (provider+date on line 1, time on line 2)
        lines_per_log = 2
        visible_count = min(available_lines // lines_per_log, len(self.logs))

        # Adjust scroll offset if needed
        if self.selected_log_idx < self.log_scroll_offset:
            self.log_scroll_offset = self.selected_log_idx
        elif self.selected_log_idx >= self.log_scroll_offset + visible_count:
            self.log_scroll_offset = self.selected_log_idx - visible_count + 1

        # Build display lines
        for i in range(
            self.log_scroll_offset,
            min(self.log_scroll_offset + visible_count, len(self.logs)),
        ):
            log_id, metadata = self.logs[i]
            timestamp = self._format_timestamp(metadata.get("modified", ""))
            provider_label = metadata.get("provider_label") or metadata.get(
                "provider", ""
            )

            # Build display with provider and timestamp
            display_parts = []
            if provider_label:
                display_parts.append(str(provider_label))
            if timestamp:
                # Split timestamp into date and time for wrapping
                ts = timestamp.strip()
                if " " in ts:
                    date_part, time_part = ts.split(" ", 1)
                    display_parts.append(date_part)
                else:
                    display_parts.append(ts)
                    time_part = None
            else:
                time_part = None

            first_line = " ".join(part for part in display_parts if part)
            if not first_line:
                first_line = log_id.split(":", 1)[-1] if ":" in log_id else log_id

            # Format: "▶ details" for selected, "  details" for others
            prefix = "▶" if i == self.selected_log_idx else " "
            lines.append(f"{prefix} {first_line}")

            # Add time on second line if present
            if time_part:
                lines.append(f"  {time_part}")

        # Pad to put footer at the bottom
        while len(lines) < available_lines:
            lines.append("")

        # Add status footer showing current position
        status = f"({self.selected_log_idx + 1}/{len(self.logs)})"
        # The width passed is the pane width, but content is drawn with width - 4
        # (2 for borders, 2 for padding), so the actual usable width is width - 4
        actual_width = max(1, width - 4)

        # If status is too long for the width, truncate it
        if len(status) > actual_width:
            status = status[:actual_width]

        # Right-align with padding
        padding = max(0, actual_width - len(status))
        status_line = " " * padding + status

        if colors_enabled:
            lines.append([(status_line, COLOR_METADATA)])
        else:
            lines.append(status_line)

        return lines

    def handle_input(self, key: int) -> bool:
        """Handle input when logs pane is focused.

        Args:
            key: The key pressed

        Returns:
            True if log selection changed (requiring message reload)
        """
        if not self.logs:
            return False

        selection_changed = False

        if key == curses.KEY_UP:
            if self.selected_log_idx > 0:
                self.selected_log_idx -= 1
                selection_changed = True
        elif key == curses.KEY_DOWN:
            if self.selected_log_idx < len(self.logs) - 1:
                self.selected_log_idx += 1
                selection_changed = True

        return selection_changed

    def get_selected_log_uri(self) -> Optional[str]:
        """Get the URI of the currently selected log.

        Returns:
            Log URI or None if no logs available
        """
        if self.logs and 0 <= self.selected_log_idx < len(self.logs):
            return self.logs[self.selected_log_idx][0]
        return None

    def _format_timestamp(self, timestamp_str: str) -> str:
        """Format timestamp to short datetime format.

        Args:
            timestamp_str: ISO format timestamp string

        Returns:
            Formatted datetime string in MM-DD HH:MM format
        """
        try:
            # Parse the timestamp
            ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            # Use consistent MM-DD HH:MM format
            return ts.strftime("%m-%d %H:%M")
        except (ValueError, AttributeError, TypeError):
            # Fallback to showing part of the timestamp
            return timestamp_str[:11] if len(timestamp_str) > 11 else timestamp_str
