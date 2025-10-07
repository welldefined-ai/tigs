"""Main TUI application for tigs view command."""

import curses
import os
import sys

from .commits_view import CommitView
from .commit_details_view import CommitDetailsView
from .messages_view import MessageView
from .layout_manager import LayoutManager
from .pane_renderer import PaneRenderer
from .text_utils import clear_iterm2_scrollback
from ..chat_providers import get_chat_parser


class TigsViewApp:
    """Main TUI application for exploring commits and their associated chats."""

    MIN_WIDTH = 80
    MIN_HEIGHT = 24

    def __init__(self, store):
        """Initialize the TUI application.

        Args:
            store: TigsRepo instance for Git operations
        """
        self.store = store
        self.running = True
        self._colors_enabled = False
        self.focused_pane = 0  # 0=commits, 1=details, 2=chat

        # Initialize layout manager
        self.layout_manager = LayoutManager()

        # Initialize chat parser like store_app does
        try:
            self.chat_parser = get_chat_parser()
        except Exception:
            self.chat_parser = None

        # Initialize view components
        self.commit_view = CommitView(self.store, read_only=True)
        self.commit_details_view = CommitDetailsView(self.store)
        self.message_view = MessageView(self.chat_parser)
        self.message_view.read_only = True  # Make it read-only for view mode

        # Give layout manager to commit view for horizontal scrolling
        self.commit_view.layout_manager = self.layout_manager

        # Load initial data
        self.commit_view.load_commits()

        # Load details for first commit if available
        if self.commit_view.commits:
            sha = self.commit_view.get_cursor_sha()
            if sha:
                self.commit_details_view.load_commit_details(sha)
                self._load_chat_for_commit(sha)

    def _load_chat_for_commit(self, sha: str) -> None:
        """Load chat content for a commit directly into MessageView."""
        try:
            # Get raw chat content from git notes
            content = self.store.show_chat(sha)

            if content and self.chat_parser:
                # Use the new decompose() method to parse YAML directly
                try:
                    chat = self.chat_parser.decompose(content)

                    # Load parsed messages into MessageView (store Message objects directly)
                    self.message_view.messages = list(chat.messages)

                    # Prepare messages for display (handles grouping for multiple log files)
                    self.message_view.prepare_messages_for_display()

                    # Update MessageView state
                    self.message_view.items = self.message_view.messages
                    self.message_view.cursor_idx = 0
                    self.message_view.message_cursor_idx = 0
                    self.message_view._internal_scroll_offset = 0
                    self.message_view._needs_message_view_init = True

                except Exception as parse_error:
                    # Show parsing error as a system message
                    self.message_view.messages = [
                        (
                            "system",
                            f"Failed to parse chat: {str(parse_error)}\n\nRaw content:\n{content}",
                            None,
                        )
                    ]
                    self.message_view.items = self.message_view.messages
                    self.message_view.cursor_idx = 0
                    self.message_view.message_cursor_idx = 0
                    self.message_view._internal_scroll_offset = 0
                    self.message_view._needs_message_view_init = True

            else:
                # No chat content - clear messages
                self.message_view.messages = []
                self.message_view.items = []

        except KeyError:
            # No chat for this commit
            self.message_view.messages = []
            self.message_view.items = []
        except Exception as e:
            # Show error as a system message
            self.message_view.messages = [
                ("system", f"Error loading chat: {str(e)}", None)
            ]
            self.message_view.items = self.message_view.messages
            self.message_view.cursor_idx = 0
            self.message_view.message_cursor_idx = 0
            self.message_view._internal_scroll_offset = 0
            self.message_view._needs_message_view_init = True

    def run(self) -> None:
        """Run the TUI application."""
        try:
            curses.wrapper(self._run)
        except KeyboardInterrupt:
            pass
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
            curses.curs_set(0)
        except curses.error:
            pass
        stdscr.keypad(True)
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
                self._colors_enabled = False

        # Main loop
        while self.running:
            height, width = stdscr.getmaxyx()

            # Check minimum size
            if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
                # Clear iTerm2 scrollback buffer + standard curses clear
                clear_iterm2_scrollback()
                stdscr.clear()
                msg = f"Terminal too small: {width}x{height} (min: {self.MIN_WIDTH}x{self.MIN_HEIGHT})"
                try:
                    stdscr.addstr(height // 2, max(0, (width - len(msg)) // 2), msg)
                except curses.error:
                    pass
                stdscr.refresh()
                key = stdscr.getch()
                if key == ord("q") or key == ord("Q"):
                    self.running = False
                continue

            # Clear iTerm2 scrollback buffer + standard curses clear
            clear_iterm2_scrollback()
            stdscr.clear()

            # Calculate column widths using layout manager for consistency with store
            commit_titles = (
                [c["subject"] for c in self.commit_view.commits]
                if self.commit_view.commits
                else []
            )

            if self.layout_manager.needs_recalculation(width):
                commit_width, remaining_width, _ = (
                    self.layout_manager.calculate_column_widths(
                        width,
                        commit_titles,
                        0,
                        read_only_mode=True,  # No log column, shorter prefix in log view
                    )
                )
            else:
                commit_width, remaining_width, _ = self.layout_manager.cached_widths

            # Split remaining width evenly between details and chat
            details_width = remaining_width // 2
            chat_width = remaining_width - details_width

            pane_height = height - 1  # Leave room for status bar

            # Get display lines from each view
            commit_lines = self.commit_view.get_display_lines(
                pane_height, commit_width, self._colors_enabled
            )
            details_lines = self.commit_details_view.get_display_lines(
                pane_height, details_width, self._colors_enabled
            )
            chat_lines = self.message_view.get_display_lines(
                pane_height, chat_width, self._colors_enabled
            )

            # Draw panes with focus state using PaneRenderer
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
            PaneRenderer.draw_pane(
                stdscr,
                0,
                commit_width,
                pane_height,
                details_width,
                "Commit Details",
                self.focused_pane == 1,
                details_lines,
                self._colors_enabled,
            )
            PaneRenderer.draw_pane(
                stdscr,
                0,
                commit_width + details_width,
                pane_height,
                chat_width,
                "Chat",
                self.focused_pane == 2,
                chat_lines,
                self._colors_enabled,
            )

            # Draw status bar
            self._draw_status_bar(stdscr, height - 1, width)

            # Refresh to show everything
            stdscr.refresh()

            # Handle input
            key = stdscr.getch()
            if key == ord("q") or key == ord("Q"):
                self.running = False
            elif key == ord("\t"):  # Tab
                self.focused_pane = (self.focused_pane + 1) % 3
            elif key == curses.KEY_BTAB or key == 353:  # Shift-Tab
                self.focused_pane = (self.focused_pane - 1) % 3
            elif key == curses.KEY_RESIZE:
                continue
            else:
                # Route input to focused pane
                if self.focused_pane == 0:
                    # Commits pane - existing cursor navigation
                    if self.commit_view.handle_input(key, pane_height):
                        # Cursor moved, update other views
                        sha = self.commit_view.get_cursor_sha()
                        if sha:
                            self.commit_details_view.load_commit_details(sha)
                            self._load_chat_for_commit(sha)
                elif self.focused_pane == 1:
                    # Details pane - view scrolling
                    self.commit_details_view.handle_input(key, pane_height)
                elif self.focused_pane == 2:
                    # Chat pane - view scrolling
                    self.message_view.handle_input(None, key, pane_height)

    def _draw_status_bar(self, stdscr, y: int, width: int) -> None:
        """Draw the status bar.

        Args:
            stdscr: The curses screen
            y: Y position for status bar
            width: Width of screen
        """
        # Context-sensitive status based on focused pane
        if self.focused_pane == 0:
            status_text = "↑/↓: navigate commits | Tab: switch pane | q: quit"
        else:
            status_text = "↑/↓: scroll | Tab: switch pane | q: quit"

        # Add terminal size info
        height = stdscr.getmaxyx()[0]
        if width < self.MIN_WIDTH + 10 or height < self.MIN_HEIGHT + 5:
            status_text += (
                f" | Size: {width}x{height} (min: {self.MIN_WIDTH}x{self.MIN_HEIGHT})"
            )

        # Use reverse video for status bar
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

    def _no_color(self) -> bool:
        """Check if NO_COLOR environment variable is set."""
        return os.environ.get("NO_COLOR", "").strip() != ""
