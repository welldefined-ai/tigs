# Tigs Python Package

This is the Python implementation of Tigs (Talks in Git → Specs) - a system for storing and managing chat content for Git commits using Git notes.

## Installation

```bash
pip install tigs
```

Or using uv:

```bash
uv pip install tigs
```

## Usage

### CLI Commands

Tigs uses Git notes to associate chat content with specific commits:

```bash
# Add chat to current commit (HEAD)
tigs add-chat -m "This commit implements user authentication"

# Add chat to specific commit
tigs add-chat abc123 -m "Fixed the bug in this commit"

# Show chat for current commit
tigs show-chat

# Show chat for specific commit  
tigs show-chat abc123

# List all commits that have chats
tigs list-chats

# Remove chat from current commit
tigs remove-chat

# Remove chat from specific commit
tigs remove-chat abc123

# Sync chat notes with remote
tigs push-chats origin
tigs fetch-chats origin
```

### Interactive Editor

If you don't provide `-m` flag, tigs opens your default editor:

```bash
# Opens editor for chat content
tigs add-chat
```

### Git Integration

Tigs stores chats as Git notes in `refs/notes/chats`, which means:

- Chats are versioned and part of Git history
- You can use any Git commit reference (HEAD, branch names, SHAs, HEAD~1, etc.)
- Chat notes can be pushed/pulled like any other Git data
- Standard Git notes commands work: `git notes --ref=refs/notes/chats show <commit>`

### Python API

```python
from tigs import TigsStore

# Initialize store
store = TigsStore()

# Add chat to commit
commit_sha = store.add_chat("HEAD", "My chat content")

# Show chat content
content = store.show_chat("HEAD")

# List commits with chats
commit_shas = store.list_chats()

# Remove chat
store.remove_chat("HEAD")
```

## Development

```bash
# Clone the repository
git clone https://github.com/sublang-ai/tigs.git
cd tigs/python

# Install with uv
uv pip install -e .

# Run tests
uv run pytest

# Type checking
uv run mypy src

# Linting
uv run ruff check .
```

## How It Works

Tigs leverages Git's notes system to store chat content:

1. **Storage**: Chat content is stored as Git notes in `refs/notes/chats`
2. **Association**: Each note is associated with a specific commit SHA
3. **Sync**: Notes can be pushed/pulled using standard Git note refs
4. **History**: Changes to chats are tracked in the notes commit history
5. **Scalability**: Git's fanout tree structure handles large numbers of chats efficiently

This approach provides a distributed, versioned, and Git-native way to associate conversations with specific commits.