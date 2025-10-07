"""Helper module to create mock Codex CLI logs for E2E testing."""

import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _create_codex_log_file(
    file_path: Path,
    messages: List[Tuple[str, str]],
    start_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Write a Codex-style JSONL log file and return basic metadata."""

    if start_time is None:
        start_time = datetime.now() - timedelta(hours=1)

    entries = []
    current = start_time
    for role, content in messages:
        entry = {
            "type": "response_item",
            "timestamp": current.isoformat(timespec="seconds") + "Z",
            "payload": {
                "type": "message",
                "role": role,
                "content": content,
            },
        }
        entries.append(entry)
        current += timedelta(minutes=1)

    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + "\n")

    # Normalize timestamps for deterministic ordering in tests
    modified = start_time + timedelta(minutes=len(messages))
    epoch_seconds = modified.timestamp()
    os.utime(file_path, (epoch_seconds, epoch_seconds))

    return {
        "modified": modified.isoformat(),
        "size": file_path.stat().st_size,
    }


def create_mock_codex_home(
    base_path: Path,
    sessions_data: Optional[List[List[Tuple[str, str]]]] = None,
) -> List[Tuple[str, Dict[str, Any]]]:
    """Create a mock ~/.codex directory structure with session logs."""

    sessions_dir = base_path / ".codex" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    if sessions_data is None:
        sessions_data = [
            [
                ("user", "Codex user message"),
                ("assistant", "Codex assistant response"),
            ]
        ]

    created_logs: List[Tuple[str, Dict[str, Any]]] = []
    base_time = datetime.now() - timedelta(days=1)

    for index, messages in enumerate(sessions_data):
        session_id = f"session-{uuid.uuid4().hex[:8]}"
        session_time = base_time + timedelta(hours=index * 2)
        log_path = sessions_dir / session_id / "messages.jsonl"
        metadata = _create_codex_log_file(log_path, messages, start_time=session_time)
        relative_uri = f"{session_id}/messages.jsonl"
        created_logs.append((relative_uri, metadata))

    return created_logs
