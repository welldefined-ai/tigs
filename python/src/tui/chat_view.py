"""Chat view for showing formatted chat messages associated with commits."""

import curses
from typing import List, Union, Tuple

from cligent.core.models import Message, Role

from ..chat_providers import get_chat_parser
from .messages_view import MessageView


class ChatView:
    """Displays formatted chat messages associated with a commit using MessageView."""

    def __init__(self, store):
        """Initialize chat view.

        Args:
            store: TigsRepo instance for Git operations
        """
        self.store = store
        self.current_sha = None

        # Initialize chat parser
        try:
            self.chat_parser = get_chat_parser()
        except Exception:
            # Handle cligent initialization errors gracefully
            self.chat_parser = None

        # Initialize message view for display
        self.message_view = MessageView(self.chat_parser)
        self.message_view.read_only = True  # Make it read-only for view mode

    def load_chat(self, sha: str) -> None:
        """Load chat content for a commit.

        Args:
            sha: Full SHA of the commit
        """
        if sha == self.current_sha:
            return

        self.current_sha = sha

        try:
            # Try to get chat content
            content = self.store.show_chat(sha)
            if content:
                if self.chat_parser:
                    try:
                        chat = self.chat_parser.decompose(content)

                        self.message_view.messages = list(chat.messages)
                        self.message_view.prepare_messages_for_display()
                        self.message_view.items = self.message_view.messages
                        self.message_view.cursor_idx = 0
                        self.message_view.message_cursor_idx = 0
                        self.message_view._internal_scroll_offset = 0
                        self.message_view._needs_message_view_init = True

                    except Exception as e:
                        self._show_raw_content(
                            f"PARSING ERROR: {str(e)}\n\nRAW CONTENT:\n{content}"
                        )
                else:
                    self._show_raw_content(content)
            else:
                self.message_view.messages = []
                self.message_view.items = []

        except KeyError:
            # No chat found for this commit
            self.message_view.messages = []
            self.message_view.items = []
        except Exception as e:
            # Error loading chat - show debug info
            self._show_raw_content(f"LOADING ERROR: {str(e)}")

    def _show_raw_content(self, content: str) -> None:
        """Fallback to show raw content if parsing fails."""
        # Create a single system message to display the content
        system_message = Message(
            role=Role.SYSTEM,
            content=content,
            provider="system",
            log_uri="system://local",
        )
        self.message_view.messages = [system_message]
        self.message_view.items = self.message_view.messages
        self.message_view.cursor_idx = 0
        self.message_view.message_cursor_idx = 0
        self.message_view._internal_scroll_offset = 0
        self.message_view._needs_message_view_init = True

    def handle_input(self, key: int, pane_height: int) -> bool:
        """Handle keyboard input for scrolling.

        Args:
            key: Key code
            pane_height: Height of the pane

        Returns:
            True if handled, False otherwise
        """
        if not self.message_view.messages:
            return False

        # Handle up/down navigation (read-only, no selection)
        if key == curses.KEY_UP:
            self.message_view.handle_input(None, key, pane_height)
            return True
        elif key == curses.KEY_DOWN:
            self.message_view.handle_input(None, key, pane_height)
            return True
        return False

    def get_display_lines(
        self, height: int, width: int, colors_enabled: bool = False
    ) -> List[Union[str, List[Tuple[str, int]]]]:
        """Get display lines for the chat pane.

        Args:
            height: Available height for content
            width: Available width for content
            colors_enabled: Whether to return colored output

        Returns:
            List of formatted message lines
        """
        if not self.current_sha:
            if colors_enabled:
                from .color_constants import COLOR_DEFAULT

                return [[("No commit selected", COLOR_DEFAULT)]]
            return ["No commit selected"]

        if not self.message_view.messages:
            if colors_enabled:
                from .color_constants import COLOR_DEFAULT

                return [[("(No chat for this commit)", COLOR_DEFAULT)]]
            return ["(No chat for this commit)"]

        # Use the message view's display logic with gradual scrolling
        return self.message_view.get_display_lines(height, width, colors_enabled)
