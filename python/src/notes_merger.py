"""Custom merger for chat notes conflicts.

This module handles merging of chat notes when conflicts occur during
git notes merge operations. It preserves the independence of each chat
conversation by using YAML multi-document format.
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


class ChatNotesMerger:
    """Custom merger for chat notes conflicts.

    This merger handles conflicts in chat notes by preserving each
    conversation as an independent YAML document. It does NOT sort
    or deduplicate messages across conversations, as each chat
    represents a complete, independent conversation.
    """

    def resolve_conflict(self, worktree_path: str) -> None:
        """Resolve chat notes conflicts in NOTES_MERGE_WORKTREE.

        Reads all conflicting note files from the worktree, parses them
        as YAML multi-documents, unions all conversations, and writes
        the resolved results back.

        Args:
            worktree_path: Path to .git/NOTES_MERGE_WORKTREE directory.

        Raises:
            RuntimeError: If resolution fails.
        """
        worktree = Path(worktree_path)
        if not worktree.exists():
            raise RuntimeError(f"Worktree does not exist: {worktree_path}")

        # Process each conflicting note file
        for note_file in worktree.iterdir():
            if note_file.is_file():
                self._resolve_note_file(note_file)

    def _resolve_note_file(self, note_file: Path) -> None:
        """Resolve a single note file.

        Args:
            note_file: Path to the conflicting note file.
        """
        try:
            # Read the conflicting content
            content = note_file.read_text(encoding="utf-8")

            # Parse as YAML multi-documents
            local_docs, remote_docs = self._parse_conflict_content(content)

            # Union: combine all documents without sorting/deduping messages
            all_docs = local_docs + remote_docs

            # Optionally deduplicate identical complete conversations
            unique_docs = self._dedup_conversations(all_docs)

            # Write resolved result back
            resolved = self._serialize_multidoc_yaml(unique_docs)
            note_file.write_text(resolved, encoding="utf-8")

        except Exception as e:
            raise RuntimeError(f"Failed to resolve {note_file}: {e}") from e

    def _parse_conflict_content(self, content: str) -> Tuple[List[dict], List[dict]]:
        """Parse conflicting note content.

        Git notes merge creates files with conflict markers or simply
        concatenates the local and remote versions. We need to split
        and parse them.

        Args:
            content: The conflicting note file content.

        Returns:
            Tuple of (local_docs, remote_docs).
        """
        # Check if content has Git conflict markers
        if "<<<<<<< " in content and "=======" in content and ">>>>>>> " in content:
            # Extract local and remote sections
            local_part = ""
            remote_part = ""
            in_local = False
            in_remote = False

            for line in content.split("\n"):
                if line.startswith("<<<<<<< "):
                    in_local = True
                    continue
                elif line.startswith("======="):
                    in_local = False
                    in_remote = True
                    continue
                elif line.startswith(">>>>>>> "):
                    in_remote = False
                    continue

                if in_local:
                    local_part += line + "\n"
                elif in_remote:
                    remote_part += line + "\n"

            local_docs = self._parse_multidoc_yaml(local_part)
            remote_docs = self._parse_multidoc_yaml(remote_part)
        else:
            # No conflict markers - this was a simple union by git
            # Try to parse as multi-doc YAML
            all_docs = self._parse_multidoc_yaml(content)
            # Split evenly (this is a heuristic - in practice, we may need better logic)
            mid = len(all_docs) // 2
            local_docs = all_docs[:mid]
            remote_docs = all_docs[mid:]

        return local_docs, remote_docs

    def _parse_multidoc_yaml(self, content: str) -> List[Dict[str, Any]]:
        """Parse YAML multi-document format.

        Args:
            content: YAML content, possibly with multiple documents.

        Returns:
            List of parsed YAML documents.
        """
        if not content or not content.strip():
            return []

        docs = []
        try:
            for doc in yaml.safe_load_all(content):
                if doc is not None:
                    docs.append(doc)
        except yaml.YAMLError as e:
            raise RuntimeError(f"Failed to parse YAML: {e}") from e

        return docs

    def _dedup_conversations(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate only if entire conversation is identical.

        This does NOT deduplicate individual messages - it only removes
        duplicate conversations (same schema + messages).

        Args:
            docs: List of conversation documents.

        Returns:
            List with duplicate conversations removed.
        """
        seen = []
        unique = []

        for doc in docs:
            # Create a hashable representation of the conversation
            # We compare the entire document structure
            doc_str = yaml.dump(doc, sort_keys=True)
            if doc_str not in seen:
                seen.append(doc_str)
                unique.append(doc)

        return unique

    def _serialize_multidoc_yaml(self, docs: List[Dict[str, Any]]) -> str:
        """Serialize to YAML multi-document format.

        Args:
            docs: List of conversation documents.

        Returns:
            YAML multi-document string.
        """
        if not docs:
            return ""

        parts = []
        for doc in docs:
            # Use default_flow_style=False to preserve block style
            yaml_str = yaml.dump(
                doc, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
            parts.append(yaml_str)

        # Join with YAML document separator
        return "---\n".join(parts)
