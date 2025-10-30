# Tigs Python Package

Tigs (Talks in Git → Specs) is a CLI tool for storing and managing LLM chats in Git associated with code commits.

## Why Tigs?

The biggest bug in software engineering isn't a crash — it's forgetting why. When someone asks "Why is this function designed this way?", too often the answer is "I think the AI suggested it?"

Tigs solves this by:
- **Preserving decision rationale** - Never lose that god-tier prompt or design debate
- **Creating traceable history** - Every "why" has a link you can follow
- **Accelerating onboarding** - New contributors understand the conversation, not just the code
- **Building prompt libraries** - Your best AI interactions become reusable team assets

## Key Features

- **Non-invasive storage** - Uses Git notes; never rewrites your commits
- **Fast TUI interface** - Navigate commits, select chats, and link them effortlessly
- **Tool-agnostic** - Works with chats from Claude Code, Gemini CLI, Qwen Code and more
- **Version-controlled context** - Your reasoning becomes greppable, diffable, and reviewable
- **Future: Auto-generated specs** - AI will read commits + chats to generate precise system specifications

## Installation

```bash
pip install tigs  # or: pipx install tigs
```

## Quick Start

Tigs provides two main interactive TUI (Terminal User Interface) commands:

With Claude Code, run `tigs` inside any directory of a Git repo that has Claude Code sessions.
All your chat history associated with the repo will be loaded and ready to store with commits!

### AI-Powered Workflow (Claude Code)

For Claude Code users, Tigs provides an intelligent slash command that automatically analyzes your code changes and suggests relevant chat messages to link:

```bash
/tigs::commit
```

This command:
1. **Creates your commit** - Follows your repo's commit message style
2. **Analyzes your changes** - Examines the diff to understand what changed
3. **Suggests relevant chats** - AI scores recent messages and pre-selects the most relevant ones
4. **Opens interactive TUI** - Shows a focused 2-pane layout with suggestions marked

The TUI will open in a new terminal window with:
- **Pre-selected messages** marked with `[x]` based on AI analysis
- **Suggested logs** marked with `*` for quick identification
- **Simple workflow**: Adjust selections with Space, press Enter to link, or 'q' to skip

This is the recommended workflow for linking chats to commits when using Claude Code!

### `tigs store` - Select and Store Chats

Launch an interactive interface to select commits and messages to associate with code commits:

```bash
tigs store

# Focus on specific commit with 2-pane layout
tigs store --commit abc123

# Pre-select suggested messages (used by /tigs::commit)
tigs store --commit abc123 --suggest "log-uri:0,5,7;other-log:2,8"
```

The store interface features:
- **Three-pane layout**: Commits (left), Messages (center), Logs (right)
- **Two-pane layout**: Messages (left), Logs (right) when `--commit` is used
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

### Provider discovery

Tigs reads chat histories through `cligent` adapters. Out of the box the
logs pane surfaces sessions from Claude Code, Gemini CLI, and Qwen Code when
those logs exist locally, including nested Claude project folders that match
the current directory's prefix.

To restrict the scan to specific adapters, set the `TIGS_CHAT_PROVIDERS`
environment variable before launching the TUI:

```bash
# Example: only show Claude Code conversations
TIGS_CHAT_PROVIDERS=claude-code tigs store
```

Every entry in the logs pane includes a provider label so you can quickly
spot which tool produced a session. Set `TIGS_CHAT_RECURSIVE=0` if you prefer
to limit discovery to the exact project directory you launched Tigs from.

## Syncing with Remote Repositories

Share your chats across team members using Git-native sync workflow:

```bash
# Pull (fetch + merge) chats from remote
tigs pull   # Default: union strategy (preserves all conversations)

# Or specify merge strategy
tigs pull --strategy=ours    # Keep local on conflict
tigs pull --strategy=theirs  # Keep remote on conflict

# Push chats to remote repository
tigs push
```

### How Sync Works

- **`tigs fetch`**: Downloads remote notes to staging namespace (`refs/notes-remote/<remote>/chats`) - safe, read-only
- **`tigs pull`**: Fetches and merges using git notes merge strategies
  - `union` (default): Combines all conversations separately, no message mixing
  - `ours`: Keep local notes on conflict
  - `theirs`: Keep remote notes on conflict
  - `manual`: Require manual resolution
- **`tigs push`**: Uploads your local notes to remote

The `push` command validates that all commits with chats are pushed to the remote before pushing the notes, preventing orphaned references.

**Multi-user workflow**: Each user's chat is preserved as an independent conversation. The default `union` strategy combines all chats using YAML multi-document format, ensuring no messages are mixed across different conversations.

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

# List recent chat messages for AI analysis (YAML output)
tigs list-messages --recent 10        # Most recent 10 logs
tigs list-messages --since 3h         # Last 3 hours
tigs list-messages --since 2025-10-29 # Since specific date
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
