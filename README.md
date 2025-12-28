# Tigs - Talks in Git → Specs

[![CI](https://github.com/welldefined-ai/tigs/actions/workflows/ci.yml/badge.svg)](https://github.com/welldefined-ai/tigs/actions/workflows/ci.yml)
[![Discord Chat](https://img.shields.io/discord/1382712250598690947?logo=discord)](https://discord.gg/Tv4EcTu5YX)
[![PyPI](https://img.shields.io/pypi/v/tigs)](https://pypi.org/project/tigs/)

> Talk is cheap. Show me the code.
> — Linus Torvalds

Linus coded Git. Now, let's talk about Tigs.

> **Code is cheap. Show me the talk.**

## What is Tigs?

Tigs is a Git-based development context management system that bridges AI conversations and structured specifications. It captures and versions both:
- **AI chats** - Your development conversations, prompts, and design debates
- **Specifications** - Multi-dimensional specs for capabilities, data models, APIs, and architecture

In the LLM era, the "why" behind code lives in chats and evolves through specs. Tigs preserves this context as traceable, version-controlled artifacts in your Git repository.

"Tig" in the name is simply "git" spelled in reverse.

## Why Tigs?

The biggest bug in software engineering isn't a crash — it's forgetting why. When someone asks "Why is this function designed this way?", too often the answer is "I think the AI suggested it?"

Tigs solves this by:
- **Preserving decision rationale** - Never lose that god-tier prompt or design debate
- **Creating traceable history** - Every "why" has a link you can follow
- **Accelerating onboarding** - New contributors understand the conversation, not just the code
- **Building prompt libraries** - Your best AI interactions become reusable team assets

## Key Features

### Chat Management
- **Non-invasive storage** - Uses Git notes; never rewrites your commits
- **Fast TUI interface** - Navigate commits, select chats, and link them effortlessly
- **Tool-agnostic** - Works with chats from Claude Code, Gemini CLI, Qwen Code and more
- **Version-controlled context** - Your reasoning becomes greppable, diffable, and reviewable

### Specification Management
- **Multi-dimensional specs** - Support for capabilities, data models, APIs, and architecture
- **Delta-based changes** - Track incremental changes with ADDED/MODIFIED/REMOVED operations
- **Type-specific validation** - Automated format checking for each specification type
- **AI-assisted workflows** - Claude Code slash commands for creating and managing specs
- **Spec generation** - Bootstrap specs from existing codebase

## Quick Start

**Best with Claude Code**: Run `tigs` inside a Git repository that has Claude Code sessions. Your chat history will be automatically loaded and ready to store with commits!

```bash
# Install
pip install tigs  # or: pipx install tigs

# In your Git repository
cd /path/to/your/repo

# === Chat Management ===
# Launch the TUI to attach chats to commits
tigs store

# Review linked chats
tigs view

# Sync with remote (fetch, pull, push)
tigs pull   # Fetch and merge remote chats (default: union strategy)
tigs push   # Push your chats to remote

# Or specify merge strategy
tigs pull --strategy=ours    # Keep local on conflict
tigs pull --strategy=theirs  # Keep remote on conflict

# === Specification Management ===
# Initialize specs structure in your project
tigs init-specs [--examples]

# List all specifications
tigs list-specs [--type <type>] [--json]

# Display specification content
tigs show-spec <name> [--type <type>]

# Validate specifications
tigs validate-specs [--all] [--strict]

# Archive completed changes
tigs archive-change <change-id>

# === Claude Code Integration ===
# Use these slash commands in Claude Code:
# /change     - Create comprehensive change proposals
# /bootstrap  - Generate specs from existing code
# /validate   - Validate specs format
# /archive    - Merge completed changes
```

### Provider discovery

Tigs now discovers every supported chat provider through
[`cligent`](https://pypi.org/project/cligent/). By default the logs pane
shows sessions from Claude Code, Gemini CLI, and Qwen Code if their local
history is present, including nested Claude project folders that share the
same prefix as your current working directory.

To narrow the scan, set the `TIGS_CHAT_PROVIDERS` environment variable to a
comma- or space-separated list of provider ids:

```bash
# Only load Claude and Gemini logs, skipping Qwen
TIGS_CHAT_PROVIDERS="claude-code,gemini-cli" tigs store
```

Recursive project discovery can be disabled with
`TIGS_CHAT_RECURSIVE=0` if you only want logs from the current project
folder:

```bash
TIGS_CHAT_RECURSIVE=0 tigs store
```

The logs pane tags each entry with the provider name so mixed sessions are
easy to spot.

## Specification Management

Tigs provides a comprehensive specification management system supporting four types of specifications:

### Specification Types

1. **Capabilities** - Behavioral requirements with structured scenarios (WHEN/THEN/AND)
2. **Data Models** - Database schemas with entities, fields, constraints, and relationships
3. **API Specifications** - Endpoint definitions with request/response formats and status codes
4. **Architecture** - System design, components, and architectural decision records (ADRs)

### Delta-Based Change Management

Changes are managed incrementally using delta operations, isolated in `specs/changes/<change-id>/` until validated and archived:

```markdown
## ADDED Requirements
### Requirement: User Authentication
The system SHALL authenticate users via OAuth.

## MODIFIED Requirements
### Requirement: Session Management
[Updated content...]

## REMOVED Requirements
### Requirement: Legacy Auth

## RENAMED Requirements
### Requirement: Old Name → New Name
```

### Directory Structure

```
specs/
├── capabilities/     # Behavioral specifications
├── data-models/      # Data structure specifications
├── api/              # API endpoint specifications
├── architecture/     # Architecture and design specifications
└── changes/          # Incremental changes
    ├── [change-id]/  # Active changes
    └── archive/      # Completed changes
```

### Usage Example

```bash
# Initialize specs in your project
tigs init-specs --examples

# Create a new change using AI assistance (Claude Code)
/change

# Validate all specifications
tigs validate-specs --all

# Archive a completed change
tigs archive-change add-user-auth
```

## How It Works

### Chat Management TUI

The TUI shows:
- **Left panel**: Your repository's commit history
- **Middle panel**: Chat messages from selected logs
- **Right panel**: Available chat sessions/files

Simply select the conversations that matter and attach them to relevant commits. Tigs stores this metadata in Git notes, keeping your commit hashes intact.

## FAQ

**Does Tigs modify my commits?**
No. Tigs uses Git notes to store metadata. Your commit hashes remain unchanged.

**Where is chat data stored?**
In your repository as log files and Git notes. You maintain full control through Git remotes.

**What about privacy?**
Tigs operates locally. Treat chat notes like any code history when pushing to remotes.

**Is this production-ready?**
Yes. Chat management is stable and widely used. Specification management is feature-complete with validation, change tracking, and archival.

**How does sync work with multiple users?**
Tigs uses `tigs pull` to fetch and merge remote chats. The default `union` strategy preserves all conversations separately (no message mixing). Each user's chat remains an independent conversation. If conflicts occur, the custom merger auto-resolves by combining all chats as separate YAML documents.

**What are the merge strategies?**
- `union` (default): Combine local and remote chats, preserving all conversations
- `ours`: Keep local chats on conflict
- `theirs`: Keep remote chats on conflict
- `manual`: Require manual conflict resolution

**How do specs relate to chats?**
Chats capture your development conversations and AI interactions. Specs formalize those conversations into structured, validated documentation. Together, they provide complete development context: the informal reasoning (chats) and the formal requirements (specs).

## Development Philosophy

Tigs is developed in an LLM-native way: its requirements and design are expressed through talks with an LLM and translated into code. By bootstrapping itself, Tigs will manage its own talks and define its own specifications.

The specifications are language-agnostic and can be translated into different programming languages. Currently, we provide implementations in Python and Node.js.

## Roadmap

- [x] Specification management system with validation
- [x] Delta-based change tracking and archival
- [x] Claude Code integration with slash commands
- [ ] Direct integrations with more AI tools and IDEs
- [ ] Enhanced spec generation from commits + chats (bootstrap available)
- [ ] CI/CD hooks for "talk coverage" and spec validation in PRs
- [ ] Multi-language implementations beyond Python/Node.js
- [ ] Spec dependency graph visualization
- [ ] Cross-reference validation and broken link detection

## Contributing

We welcome contributions! Here's how to get involved:

- ⭐ **Star the repository** if you find Tigs useful
- 🐛 **File issues** for bugs or feature requests
- 🤝 **Submit PRs** for new adapters or improvements
- 💬 **Join our Discord**: https://discord.gg/8krkc4z5wK
- 📖 **Share your use cases** to help shape the roadmap

---

*For the new generation of AI-empowered software development.*
