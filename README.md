# Tig - Talk in Git

Tig is a Git-based talk management system for software development.
It captures and manages talks between human developers and AI — including prompts (contexts, instructions, queries, etc.) and responses of any format — as the medium to express software requirements, design, and implementation.
Talk management in Tig encompasses the storage, retrieval, and comprehension of these talks.

The name "tig" is simply "git" spelled in reverse.

> Talk is cheap. Show me the code.  
> — Linus Torvalds

Linus coded Git. Now, let's talk about Tig.

> Code is cheap. Show me the talk.

## Features

- **Stores selected talk history or summaries** linked to specific code commits, preserving the rationale behind code changes.
- **Transforms raw talks into well-defined working states** that represent requirements, design, and implementation.
-	**Augments working states** with knowledge graphs and visual design views, enabling developers to recall or better understand the software.
- **Tracks revisions and evolution** of both talks and their corresponding working states over time.

## Development

Tig is developed in [the LLM-native way](https://github.com/welldefined-ai/sublang): its requirements and design are expressed through talks with an LLM and translated into code.
These talks must be coherent, consistent, and self-contained by defining working states with the help of the LLM.

These working states serve as language-agnostic specifications that can be translated into code across different programming languages.
Currently, we provide implementations in Python and Node.js.

## Contribution
