# Tig Python Package

This is the Python implementation of Tig (Talk in Git) - a system for storing and managing text objects in Git repositories.

## Installation

```bash
pip install tig
```

Or using uv:

```bash
uv pip install tig
```

## Usage

### CLI Commands

```bash
# Store text content
tig store "Hello, this is my chat content"
# Output: a1b2c3d4e5f6...

# Store with custom ID
tig store "Another chat" --id my-chat-1

# Show content
tig show my-chat-1

# List all objects
tig list

# Delete an object
tig delete my-chat-1

# Sync with remote
tig sync --push origin
tig sync --pull origin
```

### Python API

```python
from tig import TigStore

# Initialize store
store = TigStore()

# Store content
object_id = store.store("My chat content")

# Retrieve content
content = store.retrieve(object_id)

# List all objects
object_ids = store.list()

# Delete object
store.delete(object_id)
```

## Development

```bash
# Clone the repository
git clone https://github.com/welldefined-ai/tig.git
cd tig/python

# Install with uv
uv pip install -e .

# Run tests
uv run pytest

# Type checking
uv run mypy tig

# Linting
uv run ruff check .
```