# Rules

## Commit Message Format

- Use `<type>(<optional scope>)<optional !>: <subject>` format.
- Type: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `ci`, `build`, `perf`, or `chore`.
- Subject: imperative, ≤50 chars, no period. Example: `feat(auth): add OAuth login`.
- Body: explain **what/why** (not how), wrap at 72 chars, use bullets if clearer.
- Signature (if co-authored by AI), e.g.:

  🤖 Generated with [Codex CLI](https://github.com/openai/codex)

  Co-authored-by: Codex CLI <cligent@welldefined.ai>

- Optionally add `!` for breaking changes.

## Python Implementation

- Directory: `python/`
- Package name: `tigs`
- Package manager: `uv`
- Registry: PyPI
- Source layout: `python/src/` (no nested `src/tigs/` directory)

On first setup, if a uv virtual environment is not present in the python directory, create one with `uv init`.
