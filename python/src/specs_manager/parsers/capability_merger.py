"""Merger for capability specifications."""

import re
from pathlib import Path
from typing import Dict, List


class CapabilityMerger:
    """Merges capability delta changes into main specification."""

    def __init__(self, main_spec_file: Path):
        """Initialize merger with main spec file.

        Args:
            main_spec_file: Path to the main specification file
        """
        self.main_spec_file = main_spec_file
        self.content = main_spec_file.read_text() if main_spec_file.exists() else ""

    def apply_changes(self, delta: Dict[str, List[Dict[str, str]]]) -> str:
        """Apply delta changes to main specification.

        Args:
            delta: Parsed delta from CapabilityDeltaParser

        Returns:
            Updated specification content
        """
        content = self.content

        # Apply in order: RENAMED → REMOVED → MODIFIED → ADDED
        content = self._apply_renamed(content, delta.get("renamed", []))
        content = self._apply_removed(content, delta.get("removed", []))
        content = self._apply_modified(content, delta.get("modified", []))
        content = self._apply_added(content, delta.get("added", []))

        return content

    def _apply_renamed(self, content: str, renamed: List[Dict[str, str]]) -> str:
        """Apply RENAMED operations."""
        for item in renamed:
            old_name = item.get("old_name", "")
            new_name = item.get("new_name", "")

            if not old_name or not new_name:
                continue

            # Find and replace the requirement name
            pattern = rf"(###\s+Requirement:\s+){re.escape(old_name)}(\s|$)"
            replacement = rf"\g<1>{new_name}\g<2>"
            content = re.sub(pattern, replacement, content)

        return content

    def _apply_removed(self, content: str, removed: List[Dict[str, str]]) -> str:
        """Apply REMOVED operations."""
        for item in removed:
            req_name = item.get("name", "")
            if not req_name:
                continue

            # Find and remove the entire requirement block
            # Match from ### Requirement: to the next ### Requirement: or end of Requirements section
            pattern = rf"###\s+Requirement:\s+{re.escape(req_name)}.*?(?=###\s+Requirement:|##\s+(?!#)|$)"
            content = re.sub(pattern, "", content, flags=re.DOTALL)

        return content

    def _apply_modified(self, content: str, modified: List[Dict[str, str]]) -> str:
        """Apply MODIFIED operations."""
        for item in modified:
            req_name = item.get("name", "")
            new_content = item.get("content", "")

            if not req_name or not new_content:
                continue

            # Find and replace the entire requirement block
            pattern = rf"###\s+Requirement:\s+{re.escape(req_name)}.*?(?=###\s+Requirement:|##\s+(?!#)|$)"
            content = re.sub(pattern, new_content + "\n\n", content, flags=re.DOTALL)

        return content

    def _apply_added(self, content: str, added: List[Dict[str, str]]) -> str:
        """Apply ADDED operations."""
        if not added:
            return content

        # Find the Requirements section
        req_section_match = re.search(r"##\s+Requirements", content)
        if not req_section_match:
            # No Requirements section, add one
            content += "\n\n## Requirements\n\n"
            req_section_match = re.search(r"##\s+Requirements", content)

        # Find the end of Requirements section (next ## header or end of file)
        start_pos = req_section_match.end()
        next_section = re.search(r"\n##\s+(?!#)", content[start_pos:])

        if next_section:
            insert_pos = start_pos + next_section.start()
        else:
            insert_pos = len(content)

        # Insert all added requirements
        added_content = "\n\n".join(
            item.get("content", "") for item in added if item.get("content")
        )
        if added_content:
            content = (
                content[:insert_pos]
                + "\n\n"
                + added_content
                + "\n"
                + content[insert_pos:]
            )

        return content
