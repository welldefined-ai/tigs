"""Main TUI application for tigs store command."""

import curses
import os
import sys
from datetime import datetime, timedelta

from ..chat_providers import get_chat_parser

from .commits_view import CommitView
from .messages_view import MessageView
from .logs_view import LogsView
from .layout_manager import LayoutManager
from .pane_renderer import PaneRenderer
from .text_utils import clear_iterm2_scrollback


class TigsStoreApp:
    """Main TUI application for selecting and storing commits/messages."""

    MIN_WIDTH = 80
    MIN_HEIGHT = 24

    def __init__(self, store, target_commit=None, suggestions=None):
        """Initialize the TUI application.

        Args:
            store: TigsRepo instance for Git operations
            target_commit: Optional commit SHA to focus on (enables 2-pane layout)
            suggestions: Optional dict mapping log_uri to list of message indices to pre-select
        """
        self.store = store
        self.target_commit = target_commit
        self.suggestions = suggestions or {}
        self.focused_pane = (
            0 if target_commit else 0
        )  # 0=messages (2-pane), 0=commits (3-pane)
        self.running = True
        self.status_message = ""  # Status message to display
        self.status_message_time = None  # When status was set
        self._colors_enabled = False  # Track if colors were successfully initialized

        # Initialize chat parser
        try:
            self.chat_parser = get_chat_parser()
        except Exception:
            # Handle cligent initialization errors gracefully
            self.chat_parser = None

        self.provider_warnings = getattr(self.chat_parser, "warnings", ())
        self.provider_errors = getattr(self.chat_parser, "errors", {})
        if (
            self.chat_parser
            and not getattr(self.chat_parser, "has_providers", False)
            and not self.status_message
        ):
            warning = next(iter(self.provider_warnings), "No chat providers available")
            self.status_message = warning
            self.status_message_time = datetime.now()

        # Initialize layout manager
        self.layout_manager = LayoutManager()

        # Initialize view components
        self.commit_view = CommitView(self.store)
        self.message_view = MessageView(self.chat_parser)
        self.log_view = LogsView(self.chat_parser)

        # Give layout manager to commit view for horizontal scrolling
        self.commit_view.layout_manager = self.layout_manager

        # If target_commit is specified, filter commits to only show that one
        if self.target_commit:
            self.commit_view.filter_to_commit(self.target_commit)

        # Load initial data
        if self.chat_parser:
            self.log_view.load_logs()

            # Mark logs that have suggestions
            if self.suggestions:
                self.log_view.mark_suggested_logs(set(self.suggestions.keys()))

            # Auto-load messages for the first log
            log_uri = self.log_view.get_selected_log_uri()
            if log_uri:
                self.message_view.load_messages(log_uri)

                # Apply suggestions if provided
                if self.suggestions and log_uri in self.suggestions:
                    self.message_view.pre_select_messages(self.suggestions[log_uri])

                # Update message selection for any initially selected commits
                self._update_message_selection_for_selected_commits()

    def run(self) -> None:
        """Run the TUI application."""
        try:
            curses.wrapper(self._run)
        except KeyboardInterrupt:
            pass  # Exit gracefully on Ctrl+C
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def _run(self, stdscr) -> None:
        """Main TUI loop.

        Args:
            stdscr: The curses standard screen
        """
        # Set up curses
        try:
            curses.curs_set(0)  # Hide cursor
        except curses.error:
            pass  # Some terminals don't support hiding cursor
        stdscr.keypad(True)  # Enable special keys
        curses.noecho()

        # Initialize colors if available
        self._colors_enabled = False
        if curses.has_colors() and not self._no_color():
            try:
                curses.start_color()
                try:
                    curses.use_default_colors()
                    use_default_ok = True
                except curses.error:
                    use_default_ok = False

                if use_default_ok:
                    curses.init_pair(1, -1, -1)
                else:
                    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)

                # Color pairs matching tig's scheme:
                curses.init_pair(
                    2, curses.COLOR_CYAN, -1 if use_default_ok else curses.COLOR_BLACK
                )  # Author, focused border
                curses.init_pair(
                    3, curses.COLOR_GREEN, -1 if use_default_ok else curses.COLOR_BLACK
                )  # Commit SHA, additions
                curses.init_pair(
                    4, curses.COLOR_YELLOW, -1 if use_default_ok else curses.COLOR_BLACK
                )  # Date, headers
                curses.init_pair(
                    5,
                    curses.COLOR_MAGENTA,
                    -1 if use_default_ok else curses.COLOR_BLACK,
                )  # Refs, diff chunks
                curses.init_pair(
                    6, curses.COLOR_RED, -1 if use_default_ok else curses.COLOR_BLACK
                )  # Deletions
                curses.init_pair(
                    7, curses.COLOR_BLUE, -1 if use_default_ok else curses.COLOR_BLACK
                )  # Other metadata

                self._colors_enabled = True
            except curses.error:
                # leave colors off gracefully
                self._colors_enabled = False

        # Main loop
        while self.running:
            height, width = stdscr.getmaxyx()

            # Check minimum size
            if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
                # Don't exit, just show message and wait
                stdscr.clear()

                # Show size warning
                try:
                    stdscr.addstr(0, 0, "Terminal too small!")
                    stdscr.addstr(2, 0, f"Required: {self.MIN_WIDTH}x{self.MIN_HEIGHT}")
                    stdscr.addstr(3, 0, f"Current:  {width}x{height}")
                    stdscr.addstr(5, 0, "Please resize terminal")
                    stdscr.addstr(6, 0, "or press 'q' to quit")
                except curses.error:
                    # Terminal is really small, just show what we can
                    try:
                        stdscr.addstr(
                            0, 0, f"Resize: {self.MIN_WIDTH}x{self.MIN_HEIGHT}"
                        )
                    except curses.error:
                        pass

                stdscr.refresh()

                # Handle input while too small
                stdscr.timeout(100)  # Non-blocking with 100ms timeout
                key = stdscr.getch()

                if key == ord("q") or key == ord("Q"):
                    self.running = False
                elif key == curses.KEY_RESIZE:
                    # Terminal was resized, loop will check size again
                    pass

                continue  # Skip normal drawing, check size again

            # Reset to blocking input for normal operation
            stdscr.timeout(-1)

            # Clear iTerm2 scrollback buffer + standard curses clear
            clear_iterm2_scrollback()
            stdscr.clear()

            # Calculate pane dimensions
            pane_height = height - 1  # Reserve bottom for status bar

            # Determine layout mode: 2-pane or 3-pane
            is_2_pane_mode = self.target_commit is not None

            if is_2_pane_mode:
                # 2-PANE LAYOUT (Messages | Logs)
                # Calculate widths for 2 panes
                log_count = len(self.log_view.logs) if self.log_view.logs else 0

                if log_count == 0:
                    message_width = width
                    log_pane_width = 0
                else:
                    # Simple split: 60% messages, 40% logs
                    message_width = int(width * 0.6)
                    log_pane_width = width - message_width

                # Get message display lines
                message_lines = self.message_view.get_display_lines(
                    pane_height, message_width, self._colors_enabled
                )

                # Draw messages pane (starts at x=0)
                PaneRenderer.draw_pane(
                    stdscr,
                    0,
                    0,
                    pane_height,
                    message_width,
                    "Messages",
                    self.focused_pane == 0,
                    message_lines,
                    self._colors_enabled,
                )

                # Draw logs pane if wide enough
                if log_pane_width >= 2:
                    log_lines = self.log_view.get_display_lines(
                        pane_height, log_pane_width, self._colors_enabled
                    )
                    PaneRenderer.draw_pane(
                        stdscr,
                        0,
                        message_width,
                        pane_height,
                        log_pane_width,
                        "Logs",
                        self.focused_pane == 1,
                        log_lines,
                        self._colors_enabled,
                    )

            else:
                # 3-PANE LAYOUT (Commits | Messages | Logs)
                # Get commit titles for width calculation
                commit_titles = [c["subject"] for c in self.commit_view.commits]
                log_count = len(self.log_view.logs) if self.log_view.logs else 0

                # Calculate dynamic widths
                if self.layout_manager.needs_recalculation(width):
                    commit_width, message_width, log_width = (
                        self.layout_manager.calculate_column_widths(
                            width,
                            commit_titles,
                            log_count,
                            read_only_mode=False,  # Full prefix with checkboxes
                        )
                    )
                else:
                    commit_width, message_width, log_width = (
                        self.layout_manager.cached_widths
                    )

                # Handle no logs case - give extra space to messages
                if log_count == 0:
                    message_width = width - commit_width
                    log_pane_width = 0
                else:
                    log_pane_width = log_width

                # Get commit display lines
                commit_lines = self.commit_view.get_display_lines(
                    pane_height, commit_width, self._colors_enabled
                )

                # DEBUG: Add status to see if commits are loading
                if not commit_lines:
                    commit_lines = [f"DEBUG: {len(self.commit_view.commits)} commits"]

                # Draw commits pane
                PaneRenderer.draw_pane(
                    stdscr,
                    0,
                    0,
                    pane_height,
                    commit_width,
                    "Commits",
                    self.focused_pane == 0,
                    commit_lines,
                    self._colors_enabled,
                )

                # Get message display lines
                message_lines = self.message_view.get_display_lines(
                    pane_height, message_width, self._colors_enabled
                )

                # Draw messages pane
                PaneRenderer.draw_pane(
                    stdscr,
                    0,
                    commit_width,
                    pane_height,
                    message_width,
                    "Messages",
                    self.focused_pane == 1,
                    message_lines,
                    self._colors_enabled,
                )

                # Draw logs pane if wide enough
                if log_pane_width >= 2:
                    log_lines = self.log_view.get_display_lines(
                        pane_height, log_pane_width, self._colors_enabled
                    )
                    PaneRenderer.draw_pane(
                        stdscr,
                        0,
                        commit_width + message_width,
                        pane_height,
                        log_pane_width,
                        "Logs",
                        self.focused_pane == 2,
                        log_lines,
                        self._colors_enabled,
                    )

            # Draw status bar
            self._draw_status_bar(stdscr, height - 1, width)

            # Refresh to show everything
            stdscr.refresh()

            # Handle input
            key = stdscr.getch()
            num_panes = 2 if is_2_pane_mode else 3

            if key == ord("q") or key == ord("Q"):
                self.running = False
            elif key == ord("\n") or key == 10:  # Enter key
                self._handle_store_operation(stdscr)
            elif key == ord("\t"):  # Tab
                self.focused_pane = (self.focused_pane + 1) % num_panes
            elif key == curses.KEY_BTAB or key == 353:  # Shift-Tab
                self.focused_pane = (self.focused_pane - 1) % num_panes
            elif key == curses.KEY_RESIZE:
                self._handle_resize(stdscr)
                continue  # Redraw with new dimensions
            elif is_2_pane_mode:
                # 2-pane mode: pane 0 = messages, pane 1 = logs
                if self.focused_pane == 0:  # Messages pane focused
                    self.message_view.handle_input(stdscr, key, pane_height)
                elif self.focused_pane == 1:  # Logs pane focused
                    if self.log_view.handle_input(key):
                        # Log selection changed, reload messages
                        log_uri = self.log_view.get_selected_log_uri()
                        if log_uri:
                            self.message_view.load_messages(log_uri)

                            # Apply suggestions if provided for this log
                            if self.suggestions and log_uri in self.suggestions:
                                self.message_view.pre_select_messages(
                                    self.suggestions[log_uri]
                                )
            else:
                # 3-pane mode: pane 0 = commits, pane 1 = messages, pane 2 = logs
                if self.focused_pane == 0:  # Commits pane focused
                    if self.commit_view.handle_input(key, pane_height):
                        # Commit selection changed (Space was pressed), update message selection
                        self._update_message_selection_for_selected_commits()
                elif self.focused_pane == 1:  # Messages pane focused
                    self.message_view.handle_input(stdscr, key, pane_height)
                elif self.focused_pane == 2:  # Logs pane focused
                    if self.log_view.handle_input(key):
                        # Log selection changed, reload messages
                        log_uri = self.log_view.get_selected_log_uri()
                        if log_uri:
                            self.message_view.load_messages(log_uri)
                            # After loading new messages, update selection based on selected commits
                            self._update_message_selection_for_selected_commits()

    def _draw_status_bar(self, stdscr, y: int, width: int) -> None:
        """Draw the status bar.

        Args:
            stdscr: The curses screen
            y: Y position for status bar
            width: Width of screen
        """
        # Show status message if recent (within 5 seconds)
        if self.status_message and self.status_message_time:
            elapsed = datetime.now() - self.status_message_time
            if elapsed < timedelta(seconds=5):
                status_text = self.status_message
            else:
                self.status_message = ""  # Clear old message
                status_text = self._get_contextual_help()
        else:
            status_text = self._get_contextual_help()

        # Add size warning if getting close to minimum
        height = stdscr.getmaxyx()[0]
        if width < self.MIN_WIDTH + 10 or height < self.MIN_HEIGHT + 5:
            status_text += (
                f" | Size: {width}x{height} (min: {self.MIN_WIDTH}x{self.MIN_HEIGHT})"
            )

        # Use reverse video for status bar (honor NO_COLOR)
        if self._colors_enabled:
            stdscr.attron(curses.A_REVERSE)

        # Clear the line and add status text
        status_line = status_text.ljust(width)[: width - 1]
        try:
            stdscr.addstr(y, 0, status_line)
        except curses.error:
            pass

        if self._colors_enabled:
            stdscr.attroff(curses.A_REVERSE)

    def _handle_store_operation(self, stdscr) -> None:
        """Handle the store operation when Enter is pressed.

        Args:
            stdscr: The curses screen for prompts
        """
        # Get selected commits
        selected_commits = self.commit_view.get_selected_shas()

        # Validate that commit is selected
        if not selected_commits:
            self.status_message = "Error: No commit selected"
            self.status_message_time = datetime.now()
            return

        # Get current log URI
        current_log_uri = self.log_view.get_selected_log_uri()
        if not current_log_uri:
            self.status_message = "Error: No log selected"
            self.status_message_time = datetime.now()
            return

        # Store to the selected commit (should be only one)
        sha = selected_commits[0]  # Single commit selection
        num_selected = len(self.message_view.selected_messages)

        try:
            # Update messages for current log URI
            success = self._update_commit_messages_for_log_uri(sha, current_log_uri)

            if success:
                if num_selected > 0:
                    self.status_message = f"Stored {num_selected} messages → {sha[:7]} (log: {current_log_uri})"
                else:
                    self.status_message = (
                        f"Removed messages from {sha[:7]} (log: {current_log_uri})"
                    )
            else:
                self.status_message = f"No changes made to {sha[:7]}"

        except Exception as e:
            self.status_message = f"Error: {sha[:7]}: {str(e)}"

        self.status_message_time = datetime.now()

        # Clear selections after successful storage
        if "Error:" not in self.status_message:
            self.commit_view.clear_selection()
            self.message_view.clear_selection()

            # Update commit indicators (reload to get updated notes status)
            self.commit_view.load_commits()

    def _update_commit_messages_for_log_uri(
        self, sha: str, current_log_uri: str
    ) -> bool:
        """Update messages for a specific log URI in a commit's stored chat.

        Args:
            sha: The commit SHA
            current_log_uri: The log URI to update messages for

        Returns:
            True if changes were made, False if no changes
        """
        try:
            # Get existing chat content from git notes
            existing_content = self.store.show_chat(sha)
        except (KeyError, Exception):
            existing_content = None

        # 1. Get all existing associated messages for the commit
        all_existing_messages = []
        if existing_content and self.chat_parser:
            try:
                existing_chat = self.chat_parser.decompose(existing_content)
                all_existing_messages = existing_chat.messages
            except Exception:
                all_existing_messages = []

        # 2. Remove messages that belong to the current log URI
        messages_from_other_logs = []
        for msg in all_existing_messages:
            msg_log_uri = msg.log_uri if hasattr(msg, "log_uri") else "unknown"
            if msg_log_uri != current_log_uri:
                messages_from_other_logs.append(msg)

        # 3. Add currently selected messages to the list
        final_messages = messages_from_other_logs.copy()
        if self.message_view.selected_messages:
            # Get selected messages directly from message_view
            for idx in self.message_view.selected_messages:
                if idx < len(self.message_view.messages):
                    msg = self.message_view.messages[idx]
                    final_messages.append(msg)

        # 4. Save the final list or remove if empty
        if not final_messages:
            # No messages left - remove git note
            if existing_content:
                self.store.remove_chat(sha)
                return True
            return False
        else:
            # We have messages - compose them directly and store
            new_content = self.chat_parser.compose(*final_messages)
            if new_content:
                # Remove existing chat first if it exists
                if existing_content:
                    self.store.remove_chat(sha)
                self.store.add_chat(sha, new_content)
                return True

        return False

    def _prompt_overwrite(self, stdscr, sha: str) -> bool:
        """Prompt user to overwrite existing note.

        Args:
            stdscr: The curses screen
            sha: The commit SHA

        Returns:
            True if user wants to overwrite
        """
        # Simple implementation - always overwrite for now
        # Could be enhanced with actual prompt dialog
        return True

    def _handle_resize(self, stdscr) -> None:
        """Handle terminal resize event.

        Args:
            stdscr: The curses screen
        """
        # Clear and refresh to get new dimensions
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Force recalculation of column widths
        self.layout_manager.cached_widths = None

        # Reset message view to recalculate heights
        self.message_view._needs_message_view_init = True

        # Ensure cursors are visible
        pane_height = height - 1
        self.commit_view.scroll_to_cursor(pane_height)
        self.message_view.scroll_to_cursor(pane_height)

    def _update_message_selection_for_selected_commits(self) -> None:
        """Update message selection based on stored chat content for selected commits and current log URI."""
        if not self.message_view.messages:
            return

        # Clear current selection
        self.message_view.selected_messages.clear()

        # Get the selected commit SHA (should be only one)
        selected_shas = self.commit_view.get_selected_shas()
        if not selected_shas:
            return

        # Get current log URI
        current_log_uri = self.log_view.get_selected_log_uri()
        if not current_log_uri:
            return

        sha = selected_shas[0]  # Single commit selection

        try:
            # Get raw chat content from git notes
            content = self.store.show_chat(sha)

            if content and self.chat_parser:
                try:
                    # Parse the stored chat content
                    stored_chat = self.chat_parser.decompose(content)

                    # Extract stored messages only for the current log URI
                    stored_messages_for_current_log = []
                    for msg in stored_chat.messages:
                        msg_log_uri = (
                            msg.log_uri if hasattr(msg, "log_uri") else "unknown"
                        )
                        if msg_log_uri == current_log_uri:
                            # Handle role conversion
                            if hasattr(msg, "role"):
                                role = msg.role
                                if hasattr(role, "value"):
                                    role = role.value
                                else:
                                    role = str(role).lower()
                            else:
                                role = "unknown"

                            content_text = (
                                msg.content if hasattr(msg, "content") else str(msg)
                            )
                            stored_messages_for_current_log.append((role, content_text))

                    # Compare with current messages and select matches from current log URI
                    for stored_idx, (stored_role, stored_content) in enumerate(
                        stored_messages_for_current_log
                    ):
                        # Find this stored message in the current messages
                        for i, msg in enumerate(self.message_view.messages):
                            current_role = (
                                msg.role.value
                                if hasattr(msg.role, "value")
                                else str(msg.role)
                            )
                            current_content = (
                                msg.content if hasattr(msg, "content") else str(msg)
                            )
                            message_log_uri = msg.log_uri
                            # Only consider messages from the current log URI
                            if message_log_uri == current_log_uri:
                                if current_role == stored_role:
                                    # Normalize line endings and trailing spaces for comparison
                                    current_clean = (
                                        current_content.strip()
                                        .replace("\r\n", "\n")
                                        .replace("\r", "\n")
                                    )
                                    stored_clean = (
                                        stored_content.strip()
                                        .replace("\r\n", "\n")
                                        .replace("\r", "\n")
                                    )

                                    # Remove trailing spaces from each line (both before newlines and at end of string)
                                    import re

                                    current_normalized = re.sub(
                                        r"[ \t]+$",
                                        "",
                                        current_clean,
                                        flags=re.MULTILINE,
                                    )
                                    stored_normalized = re.sub(
                                        r"[ \t]+$", "", stored_clean, flags=re.MULTILINE
                                    )

                                    if current_normalized == stored_normalized:
                                        self.message_view.selected_messages.add(i)
                                        break  # Found this stored message, move to next stored message

                except Exception:
                    # If parsing fails, ignore
                    pass

        except (KeyError, Exception):
            # No chat for this commit or error occurred - ignore
            pass

    def _get_contextual_help(self) -> str:
        """Get contextual help text based on focused pane.

        Returns:
            Help text appropriate for the currently focused pane
        """
        base_help = "Tab: switch | Enter: store | q: quit"

        if self.focused_pane == 0:  # Commits pane
            return f"Space: select | {base_help}"
        elif self.focused_pane == 1:  # Messages pane
            return f"Space: select | ↑/↓: jump messages | j/k: scroll | {base_help}"
        elif self.focused_pane == 2:  # Logs pane
            return f"↑/↓: navigate | {base_help}"
        else:
            return base_help

    def _no_color(self) -> bool:
        """Check if colors should be disabled via NO_COLOR environment variable.

        Returns:
            True if NO_COLOR is set and non-empty
        """
        return bool(os.environ.get("NO_COLOR", "").strip())
