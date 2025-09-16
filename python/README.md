# Tigs Python Package

Tigs (Talks in Git → Specs) is a CLI tool for storing and managing LLM chats in Git associated with code commits.

## Installation

```bash
pip install tigs
```

Or using uv:

```bash
uv pip install tigs
```

## Quick Start

Tigs provides two main interactive TUI (Terminal User Interface) commands:

### `tigs store` - Select and Store Chats

Launch an interactive interface to select commits and messages to associate with code commits:

```bash
tigs store
```

The store interface features:
- **Three-pane layout**: Commits (left), Messages (center), Logs (right)
- **Keyboard navigation**:
  - `j/k` or `↑/↓` - Navigate up/down
  - `Space` - Toggle selection
  - `v` - Visual selection mode
  - `a` - Select all
  - `c` - Clear selections
  - `Tab` - Switch between panes
  - `s` - Store selected items as a chat
  - `q` - Quit

### `tigs view` - Browse and Read Chats

Explore existing chats associated with your commits:

```bash
tigs view
```

The view interface displays:
- **Three-column layout**: Commits list, Commit details, Chat content
- **Navigation**: Browse through commits and view associated chats
- **Read-only mode**: Safely explore without modifying data

## Syncing with Remote Repositories

Share your chats across team members using Git's native push/pull:

```bash
# Push chats to remote repository
tigs push

# Fetch chats from remote repository
tigs fetch
```

The `push` command validates that all commits with chats are pushed to the remote before pushing the notes, preventing orphaned references.

## Low-Level Commands

For automation and scripting, Tigs provides direct CLI commands:

```bash
# Add chat to current commit (HEAD)
tigs add-chat -m "Chat content in YAML format"

# Add chat to specific commit
tigs add-chat abc123 -m "Chat content"

# Show chat for current commit
tigs show-chat

# Show chat for specific commit
tigs show-chat abc123

# List all commits that have chats
tigs list-chats

# Remove chat from commit
tigs remove-chat abc123
```

### Interactive Editor

If you don't provide the `-m` flag, tigs opens your default editor:

```bash
# Opens editor for chat content
tigs add-chat
```

## Chat Format

Chats are stored in YAML format following the `tigs.chat/v1` schema:

```yaml
schema: tigs.chat/v1
messages:
- role: user
  content: What does this commit implement?
- role: assistant
  content: This commit adds authentication using JWT tokens.
```

## Git Integration

Tigs stores chats as Git notes in `refs/notes/chats`, which means:

- **Version controlled**: Chats are part of Git history
- **Distributed**: Push/pull chats like any Git data
- **Non-invasive**: Doesn't modify commits or require rebasing
- **Compatible**: Works with any Git workflow
- **Efficient**: Git's fanout structure handles large scale

You can also use standard Git commands:
```bash
# View notes directly
git notes --ref=refs/notes/chats show <commit>

# Push notes manually
git push origin refs/notes/chats
```

## Use Cases

- **Code Review**: Attach review discussions with LLM to specific commits
- **Documentation**: Add design & implementation notes and decisions
- **Learning**: Annotate commits with explanations for team members
- **AI Assistance**: Store AI conversations about code changes
- **Debugging**: Keep notes about bug investigations tied to commits

## Requirements

- Python 3.8+
- Git 2.17+
- Terminal with UTF-8 support
- Unix-like system (Linux, macOS, WSL)