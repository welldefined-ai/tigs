"""Helper module to create mock Claude logs for E2E testing."""

import json
import uuid
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple


def create_mock_session_file(
    output_path: Path,
    messages: List[Tuple[str, str]],
    project_name: str = "test-project",
    start_time: datetime = None,
) -> Dict[str, Any]:
    """Create a mock JSONL session file similar to Claude logs.

    Args:
        output_path: Path where the JSONL file will be created
        messages: List of (role, content) tuples
        project_name: Name of the project for metadata
        start_time: Starting timestamp for messages

    Returns:
        Dictionary with session metadata (id, size, project, accessible)
    """
    if start_time is None:
        start_time = datetime.now() - timedelta(hours=2)

    session_id = str(uuid.uuid4())
    log_entries = []
    current_time = start_time

    # Generate messages in Claude log format
    for i, (role, content) in enumerate(messages):
        msg_uuid = f"msg_{uuid.uuid4().hex[:8]}"

        log_entry = {
            "parentUuid": None if i == 0 else f"msg_{uuid.uuid4().hex[:8]}",
            "isSidechain": False,
            "userType": "external" if role == "user" else "assistant",
            "cwd": f"/Users/testuser/Projects/{project_name.lower().replace(' ', '-')}",
            "sessionId": session_id,
            "version": "1.0.109",
            "gitBranch": "main",
            "type": role,
            "message": {"role": role, "content": [{"type": "text", "text": content}]},
            "uuid": msg_uuid,
            "timestamp": current_time.isoformat() + "Z",
        }

        # Add model for assistant messages
        if role == "assistant":
            log_entry["message"]["model"] = "claude-3-5-sonnet-20241022"

        log_entries.append(log_entry)

        # Advance time for next message
        current_time += timedelta(minutes=2)

    # Write JSONL file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for entry in log_entries:
            f.write(json.dumps(entry) + "\n")

    # Return metadata
    return {
        "id": session_id,
        "accessible": True,
        "size": output_path.stat().st_size,
        "project": project_name,
        "modified": datetime.now().isoformat(),
    }


def create_mock_claude_home(
    base_path: Path, sessions_data: List[List[Tuple[str, str]]] = None, cwd: Path = None
) -> List[Tuple[str, Dict[str, Any]]]:
    """Create a mock ~/.claude directory structure with session files.

    Args:
        base_path: Base path for the mock home directory
        sessions_data: List of message lists, each containing (role, content) tuples.
                      If None, creates default test sessions.
        cwd: Current working directory to determine project folder name.
             If None, uses the current project's python directory

    Returns:
        List of tuples (log_id, metadata) compatible with cligent
    """
    # Determine the project folder name based on cwd
    if cwd is None:
        # Default to the python directory - get it dynamically
        test_dir = Path(__file__).parent.parent.parent
        cwd = test_dir / "python"

    # Convert path to project folder name (replace / with -)
    # Cligent keeps the leading dash, so we should too
    project_folder_name = str(cwd).replace("/", "-")

    # Create the correct directory structure that cligent expects
    claude_dir = base_path / ".claude" / "projects" / project_folder_name
    claude_dir.mkdir(parents=True, exist_ok=True)

    # Default test sessions if none provided
    if sessions_data is None:
        sessions_data = [
            [
                ("user", "Test message 1"),
                ("assistant", "Test response 1"),
                ("user", "Test message 2"),
                ("assistant", "Test response 2"),
            ]
        ]

    logs = []
    start_time = datetime.now() - timedelta(days=1)

    for i, messages in enumerate(sessions_data):
        # Create session file directly in the project folder with UUID name
        session_id = str(uuid.uuid4())
        session_file = claude_dir / f"{session_id}.jsonl"

        metadata = create_mock_session_file(
            session_file,
            messages=messages,
            project_name=project_folder_name,
            start_time=start_time + timedelta(hours=i * 3),
        )

        # Use the session UUID as log ID (this is what cligent expects)
        logs.append((session_id, metadata))

    return logs
