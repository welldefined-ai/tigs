# Tigs - Talks in Git → Specs

[![CI](https://github.com/welldefined-ai/tigs/actions/workflows/ci.yml/badge.svg)](https://github.com/welldefined-ai/tigs/actions/workflows/ci.yml)
[![Discord Chat](https://img.shields.io/discord/1382712250598690947?logo=discord)](https://discord.gg/Tv4EcTu5YX)
[![PyPI](https://img.shields.io/pypi/v/tigs)](https://pypi.org/project/tigs/)

> Talk is cheap. Show me the code.
> — Linus Torvalds

Linus coded Git. Now, let's talk about Tigs.

> **Code is cheap. Show me the talk.**

## What is Tigs?

Tigs is a Git-based chat management system that captures and versions your AI development conversations alongside your code. In the LLM era, the "why" behind code lives in chats—prompts, design debates, and micro-discoveries that vanish across tools and tabs. Tigs preserves this context as traceable dev artifacts in your Git repository.

"Tig" in the name is simply "git" spelled in reverse.

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

## Quick Start

**Best with Claude Code**: Run `tigs` inside a Git repository that has Claude Code sessions. Your chat history will be automatically loaded and ready to store with commits!

```bash
# Install
pip install tigs  # or: pipx install tigs

# In your Git repository
cd /path/to/your/repo

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
```

## How It Works

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
Yes for chat curation and traceability. The auto-spec generation module is in active development.

**How does sync work with multiple users?**
Tigs uses `tigs pull` to fetch and merge remote chats. The default `union` strategy preserves all conversations separately (no message mixing). Each user's chat remains an independent conversation. If conflicts occur, the custom merger auto-resolves by combining all chats as separate YAML documents.

**What are the merge strategies?**
- `union` (default): Combine local and remote chats, preserving all conversations
- `ours`: Keep local chats on conflict
- `theirs`: Keep remote chats on conflict
- `manual`: Require manual conflict resolution

## Development Philosophy

Tigs is developed in [this LLM-native way](https://github.com/sublang-ai/sublang): its requirements and design are expressed through talks with an LLM and translated into code. By bootstrapping itself, Tigs will manage its own talks and define its own specifications.

The specifications are language-agnostic and can be translated into different programming languages. Currently, we provide implementations in Python and Node.js.

## Roadmap

- [ ] Direct integrations with popular AI tools and IDEs
- [ ] Auto-generated specifications from commits + chats
- [ ] CI/CD hooks for "talk coverage" in PRs
- [ ] Multi-language implementations beyond Python/Node.js

## Contributing

We welcome contributions! Here's how to get involved:

- ⭐ **Star the repository** if you find Tigs useful
- 🐛 **File issues** for bugs or feature requests
- 🤝 **Submit PRs** for new adapters or improvements
- 💬 **Join our Discord**: https://discord.gg/8krkc4z5wK
- 📖 **Share your use cases** to help shape the roadmap

---

*For the new generation of AI-empowered software development.*
