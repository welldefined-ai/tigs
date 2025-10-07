"""Generate mock Claude session files for testing."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import uuid


def create_mock_session_file(
    output_path: Path,
    num_messages: int = 10,
    project_name: str = "test-project",
    start_time: datetime = None,
    messages: List[tuple] = None,
) -> Dict[str, Any]:
    """Create a mock JSONL session file similar to Claude logs.

    Args:
        output_path: Path where the JSONL file will be created
        num_messages: Number of messages to generate
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

    if messages is None:
        message_sequence = []
        for i in range(num_messages):
            is_user = i % 2 == 0
            if is_user:
                message_sequence.append(
                    (
                        "user",
                        f"User message {i // 2 + 1}: Can you help me with task {i // 2 + 1}?",
                    )
                )
            else:
                message_sequence.append(
                    (
                        "assistant",
                        "Assistant response {}: I'll help you with task {}. Here's what we need to do...".format(
                            i // 2 + 1, i // 2 + 1
                        ),
                    )
                )
    else:
        message_sequence = messages

    for i, (role, content) in enumerate(message_sequence):
        is_user = role == "user"
        type_val = role

        log_entry = {
            "parentUuid": None if i == 0 else f"msg_{uuid.uuid4().hex[:8]}",
            "isSidechain": False,
            "userType": "external" if is_user else "assistant",
            "cwd": f"/Users/testuser/Projects/{project_name.lower().replace(' ', '-')}",
            "sessionId": session_id,
            "version": "1.0.109",
            "gitBranch": "main",
            "type": type_val,
            "message": {"role": role, "content": [{"type": "text", "text": content}]},
            "uuid": f"msg_{uuid.uuid4().hex[:8]}",
            "timestamp": current_time.isoformat() + "Z",
        }

        if role == "assistant":
            log_entry["message"]["model"] = "claude-3-5-sonnet-20241022"

        log_entries.append(log_entry)
        current_time += timedelta(minutes=2)

    # Write JSONL file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for msg in log_entries:
            f.write(json.dumps(msg) + "\n")

    # Return metadata
    return {
        "id": session_id,
        "accessible": True,
        "size": output_path.stat().st_size,
        "project": project_name,
    }


def create_mock_claude_home(
    base_path: Path,
    sessions_data: List[List[tuple]] = None,
    num_sessions: int = 3,
    cwd: Path = None,
) -> List[tuple]:
    """Create a mock ~/.claude directory structure with session files.

    Args:
        base_path: Base path for the mock home directory
        num_sessions: Number of session files to create
        cwd: Optional working directory to mirror for project naming

    Returns:
        List of tuples (session_path, metadata) compatible with claude_logs fixture
    """
    claude_dir = base_path / ".claude" / "projects"
    claude_dir.mkdir(parents=True, exist_ok=True)

    if cwd is None:
        cwd = Path.cwd()

    project_dir_name = str(cwd.resolve()).replace("/", "-")
    project_dir = claude_dir / project_dir_name
    project_dir.mkdir(parents=True, exist_ok=True)

    sessions = []
    start_time = datetime.now() - timedelta(days=1)

    if sessions_data is None:
        message_sets = [None] * num_sessions
    else:
        message_sets = sessions_data

    for i, messages in enumerate(message_sets):
        session_file = project_dir / f"session-{i + 1}.jsonl"

        if messages is None:
            message_count = 4 + i * 2  # 4, 6, 8 messages
            metadata = create_mock_session_file(
                session_file,
                num_messages=message_count,
                project_name=project_dir_name,
                start_time=start_time + timedelta(hours=i * 3),
            )
        else:
            metadata = create_mock_session_file(
                session_file,
                messages=messages,
                project_name=project_dir_name,
                start_time=start_time + timedelta(hours=i * 3),
            )

        relative_path = session_file.relative_to(base_path)
        sessions.append((str(relative_path), metadata))

    return sessions


def create_large_session(output_path: Path, num_messages: int = 50) -> Dict[str, Any]:
    """Create a large mock session for testing scalability.

    Args:
        output_path: Path where the JSONL file will be created
        num_messages: Number of messages to generate

    Returns:
        Dictionary with session metadata
    """
    return create_mock_session_file(
        output_path,
        num_messages=num_messages,
        project_name="Large Test Project",
        start_time=datetime.now() - timedelta(hours=24),
    )


def create_complex_message_session(output_path: Path) -> Dict[str, Any]:
    """Create a session with complex message content (code, markdown, etc.).

    Args:
        output_path: Path where the JSONL file will be created

    Returns:
        Dictionary with session metadata
    """
    session_id = str(uuid.uuid4())
    messages = []
    current_time = datetime.now() - timedelta(hours=1)

    # Message with code request
    msg_uuid1 = f"msg_{uuid.uuid4().hex[:8]}"
    messages.append(
        {
            "parentUuid": None,
            "isSidechain": False,
            "userType": "external",
            "cwd": "/Users/testuser/Projects/complex-test",
            "sessionId": session_id,
            "version": "1.0.109",
            "gitBranch": "main",
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Can you write a Python function to calculate factorial?",
                    }
                ],
            },
            "uuid": msg_uuid1,
            "timestamp": current_time.isoformat() + "Z",
        }
    )

    current_time += timedelta(minutes=1)

    # Response with code block
    msg_uuid2 = f"msg_{uuid.uuid4().hex[:8]}"
    messages.append(
        {
            "parentUuid": msg_uuid1,
            "isSidechain": False,
            "userType": "assistant",
            "cwd": "/Users/testuser/Projects/complex-test",
            "sessionId": session_id,
            "version": "1.0.109",
            "gitBranch": "main",
            "type": "assistant",
            "message": {
                "role": "assistant",
                "model": "claude-3-5-sonnet-20241022",
                "content": [
                    {
                        "type": "text",
                        "text": """Here's a Python function to calculate factorial:

```python
def factorial(n):
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    elif n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n - 1)
```

This uses recursion to calculate the factorial.""",
                    }
                ],
            },
            "uuid": msg_uuid2,
            "timestamp": current_time.isoformat() + "Z",
        }
    )

    current_time += timedelta(minutes=2)

    # Message with special characters
    msg_uuid3 = f"msg_{uuid.uuid4().hex[:8]}"
    messages.append(
        {
            "parentUuid": msg_uuid2,
            "isSidechain": False,
            "userType": "external",
            "cwd": "/Users/testuser/Projects/complex-test",
            "sessionId": session_id,
            "version": "1.0.109",
            "gitBranch": "main",
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What about handling Unicode? Like émojis 🚀 and symbols → ← ≤ ≥?",
                    }
                ],
            },
            "uuid": msg_uuid3,
            "timestamp": current_time.isoformat() + "Z",
        }
    )

    # Write JSONL file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for msg in messages:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")

    return {
        "id": session_id,
        "accessible": True,
        "size": output_path.stat().st_size,
        "project": "Complex Content Test",
    }
