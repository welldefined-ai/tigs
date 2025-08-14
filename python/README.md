# Tigs Python Package

This is the Python implementation of Tigs (Talks in Git → Specs) - a system for storing and managing text objects in Git repositories.

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

```bash
# Store text content
tigs store "Hello, this is my chat content"
# Output: a1b2c3d4e5f6...

# Store with custom ID
tigs store "Another chat" --id my-chat-1

# Show content
tigs show my-chat-1

# List all objects
tigs list

# Delete an object
tigs delete my-chat-1

# Sync with remote
tigs sync --push origin
tigs sync --pull origin
```

### Python API

```python
from tigs import TigsStore

# Initialize store
store = TigsStore()

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