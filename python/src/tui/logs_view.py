"""Logs view management for TUI."""

import curses
from typing import List, Tuple, Optional
from datetime import datetime, timedelta


class LogsView:
    """Manages logs display and interaction."""
    
    def __init__(self, chat_parser):
        """Initialize logs view.
        
        Args:
            chat_parser: ChatParser instance for loading logs
        """
        self.chat_parser = chat_parser
        self.logs = []  # List of (log_id, metadata) tuples
        self.selected_log_idx = 0
        self.log_scroll_offset = 0
    
    def load_logs(self) -> None:
        """Load logs from cligent."""
        if not self.chat_parser:
            return
            
        try:
            logs = self.chat_parser.list_logs()
            # Sort by modification time (newest first)
            self.logs = sorted(logs, key=lambda x: x[1]['modified'], reverse=True)
            
            # Auto-select the latest log
            if self.logs and self.selected_log_idx == 0:
                self.selected_log_idx = 0
        except Exception:
            self.logs = []
    
    def get_display_lines(self, height: int) -> List[str]:
        """Get display lines for logs pane.
        
        Args:
            height: Available height for content
            
        Returns:
            List of formatted log lines
        """
        lines = []
        
        if not self.logs:
            if self.chat_parser:
                lines.append("No logs found")
            else:
                lines.append("Cligent not available")
            return lines
        
        # Calculate visible range with scrolling
        visible_count = min(height - 2, len(self.logs))  # -2 for borders
        
        # Adjust scroll offset if needed
        if self.selected_log_idx < self.log_scroll_offset:
            self.log_scroll_offset = self.selected_log_idx
        elif self.selected_log_idx >= self.log_scroll_offset + visible_count:
            self.log_scroll_offset = self.selected_log_idx - visible_count + 1
        
        # Build display lines
        for i in range(self.log_scroll_offset, min(self.log_scroll_offset + visible_count, len(self.logs))):
            log_id, metadata = self.logs[i]
            timestamp = self._format_timestamp(metadata.get('modified', ''))
            
            # Format: "• timestamp" for selected, "  timestamp" for others
            if i == self.selected_log_idx:
                lines.append(f"• {timestamp}")
            else:
                lines.append(f"  {timestamp}")
        
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
    
    def get_selected_log_id(self) -> Optional[str]:
        """Get the ID of the currently selected log.
        
        Returns:
            Log ID or None if no logs available
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
            ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            # Use consistent MM-DD HH:MM format
            return ts.strftime("%m-%d %H:%M")
        except:
            # Fallback to showing part of the timestamp
            return timestamp_str[:11] if len(timestamp_str) > 11 else timestamp_str