"""Command-line interface for Tigs."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click

from .storage import TigsRepo
from .tui import TigsStoreApp, TigsViewApp, CURSES_AVAILABLE
from .specs_manager import SpecsManager


@click.group()
@click.option(
    "--repo",
    "-r",
    type=click.Path(exists=True, path_type=Path),
    help="Path to Git repository (defaults to current directory)",
)
@click.pass_context
def main(ctx: click.Context, repo: Optional[Path]) -> None:
    """Tigs - Talks in Git → Specs.

    Store and manage chats for Git commits using Git notes.
    """
    ctx.ensure_object(dict)
    try:
        ctx.obj["store"] = TigsRepo(repo)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("add-chat")
@click.argument("commit", type=str, default="HEAD", required=False)
@click.option("--message", "-m", help="Chat content (if not provided, opens editor)")
@click.pass_context
def add_chat(ctx: click.Context, commit: str, message: Optional[str]) -> None:
    """Add chat content to a commit."""
    store = ctx.obj["store"]

    # Get chat content
    if message is None:
        message = click.edit("# Enter your chat content here\n")
        if message is None:
            click.echo("Aborted: No content provided", err=True)
            sys.exit(1)
        # Remove the comment line
        message = "\n".join(
            line for line in message.split("\n") if not line.strip().startswith("#")
        ).strip()
        if not message:
            click.echo("Aborted: No content provided", err=True)
            sys.exit(1)
    elif not message.strip():
        click.echo("Error: No content provided", err=True)
        sys.exit(1)

    try:
        resolved_sha = store.add_chat(commit, message)
        click.echo(f"Added chat to commit: {resolved_sha}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("show-chat")
@click.argument("commit", type=str, default="HEAD", required=False)
@click.pass_context
def show_chat(ctx: click.Context, commit: str) -> None:
    """Show chat content for a commit."""
    store = ctx.obj["store"]
    try:
        content = store.show_chat(commit)
        click.echo(content, nl=False)
    except KeyError:
        click.echo(f"Error: No chat found for commit: {commit}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("list-chats")
@click.pass_context
def list_chats(ctx: click.Context) -> None:
    """List all commits that have chats."""
    store = ctx.obj["store"]
    try:
        commit_shas = store.list_chats()
        for commit_sha in commit_shas:
            click.echo(commit_sha)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("remove-chat")
@click.argument("commit", type=str, default="HEAD", required=False)
@click.pass_context
def remove_chat(ctx: click.Context, commit: str) -> None:
    """Remove chat from a commit."""
    store = ctx.obj["store"]
    try:
        store.remove_chat(commit)
        click.echo(f"Removed chat from commit: {commit}")
    except KeyError:
        click.echo(f"Error: No chat found for commit: {commit}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("push")
@click.argument("remote", type=str, default="origin")
@click.pass_context
def push(ctx: click.Context, remote: str) -> None:
    """Push chats to remote repository.

    This command ensures all commits with chats are pushed to the remote
    before pushing the chats themselves, preventing orphaned notes.
    """
    store = ctx.obj["store"]
    try:
        store.push_chats(remote)
        click.echo(f"Successfully pushed chats to '{remote}'")
    except ValueError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or str(e)
        if "non-fast-forward" in error_msg or "rejected" in error_msg:
            click.echo(f"Error pushing chats: {error_msg}", err=True)
            click.echo(
                "\nThe remote has diverged from your local notes.",
                err=True,
            )
            click.echo("To resolve:", err=True)
            click.echo("  1. Pull remote notes first: tigs pull", err=True)
            click.echo("  2. Then push again: tigs push", err=True)
            click.echo("\nOr choose a specific merge strategy:", err=True)
            click.echo("  tigs pull --strategy=theirs  # Use remote version", err=True)
            click.echo("  tigs pull --strategy=ours    # Use local version", err=True)
        else:
            click.echo(f"Error pushing chats: {error_msg}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("pull")
@click.argument("remote", type=str, default="origin")
@click.option(
    "--strategy",
    "-s",
    type=click.Choice(["manual", "ours", "theirs", "union"]),
    default="union",
    help="Merge strategy for conflicting notes",
)
@click.pass_context
def pull(ctx: click.Context, remote: str, strategy: str) -> None:
    """Fetch and merge chats from remote repository.

    This command fetches remote notes and merges them with your local notes
    using the specified strategy. Default is 'union' which preserves both
    local and remote notes.

    Strategies:
      manual: Require manual conflict resolution
      ours:   Keep local notes on conflict
      theirs: Keep remote notes on conflict
      union:  Combine local and remote notes (default)
    """
    store = ctx.obj["store"]
    try:
        store.pull_chats(remote, strategy)
        click.echo(f"Successfully pulled and merged chats from '{remote}'")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or str(e)
        click.echo(f"Error pulling chats: {error_msg}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("fetch")
@click.argument("remote", type=str, default="origin")
@click.pass_context
def fetch(ctx: click.Context, remote: str) -> None:
    """Fetch chats from remote repository to staging namespace.

    This command downloads remote notes without modifying your local notes.
    The remote notes are stored in refs/notes-remote/<remote>/chats for
    inspection and merging via 'tigs pull'.
    """
    store = ctx.obj["store"]
    try:
        # Fetch to staging namespace (safe, never overwrites local notes)
        store._run_git(
            ["fetch", remote, f"refs/notes/chats:refs/notes-remote/{remote}/chats"]
        )
        click.echo(f"Successfully fetched chats from '{remote}' to staging namespace")
        click.echo(f"  Remote notes: refs/notes-remote/{remote}/chats")
        click.echo("  Use 'tigs pull' to merge with your local notes")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or str(e)
        click.echo(f"Error fetching chats: {error_msg}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# Keep the old commands for backward compatibility but mark as deprecated
@main.command("push-chats", hidden=True)
@click.argument("remote", type=str, default="origin")
@click.pass_context
def push_chats(ctx: click.Context, remote: str) -> None:
    """[DEPRECATED] Use 'tigs push' instead."""
    click.echo(
        "Warning: 'push-chats' is deprecated. Use 'tigs push' instead.", err=True
    )
    store = ctx.obj["store"]
    try:
        store._run_git(["push", remote, "refs/notes/chats:refs/notes/chats"])
        click.echo(f"Pushed chats to {remote}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("fetch-chats", hidden=True)
@click.argument("remote", type=str, default="origin")
@click.pass_context
def fetch_chats(ctx: click.Context, remote: str) -> None:
    """[DEPRECATED] Use 'tigs fetch' instead."""
    click.echo(
        "Warning: 'fetch-chats' is deprecated. Use 'tigs fetch' instead.", err=True
    )
    store = ctx.obj["store"]
    try:
        store._run_git(["fetch", remote, "refs/notes/chats:refs/notes/chats"])
        click.echo(f"Fetched chats from {remote}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("store")
@click.pass_context
def store_command(ctx: click.Context) -> None:
    """Launch interactive TUI for selecting commits and messages."""
    if not CURSES_AVAILABLE:
        click.echo("Error: curses library not available", err=True)
        sys.exit(1)

    store = ctx.obj["store"]
    app = TigsStoreApp(store)
    try:
        app.run()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("view")
@click.pass_context
def view_command(ctx: click.Context) -> None:
    """Launch interactive TUI for exploring commits and associated chats."""
    if not CURSES_AVAILABLE:
        click.echo("Error: curses library not available", err=True)
        sys.exit(1)

    store = ctx.obj["store"]
    app = TigsViewApp(store)
    try:
        app.run()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("init-specs")
@click.option(
    "--examples",
    is_flag=True,
    help="Generate example specifications for each type"
)
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to initialize specs (defaults to current directory)"
)
def init_specs(examples: bool, path: Optional[Path]) -> None:
    """Initialize specs directory structure.

    Creates a specs/ directory with subdirectories for:
    - capabilities/  (behavioral specifications)
    - data-models/   (database schemas and entities)
    - api/          (REST/GraphQL endpoints)
    - architecture/ (system design and ADRs)
    - changes/      (incremental changes)
    """
    root_path = path or Path.cwd()
    manager = SpecsManager(root_path)

    try:
        result = manager.init_structure(with_examples=examples)

        click.echo(f"✓ Initialized specs directory at {root_path / 'specs'}")
        click.echo(f"\nCreated {len(result['created'])} items:")
        for created_path in result['created']:
            # Show relative path for cleaner output
            rel_path = Path(created_path).relative_to(root_path)
            click.echo(f"  - {rel_path}")

        if examples:
            click.echo("\n✓ Generated example specifications")
            click.echo("  Review examples in each subdirectory to understand the format")

        click.echo("\nNext steps:")
        click.echo("  1. Review specs/README.md for format guidelines")
        click.echo("  2. Create your first spec: tig new-spec <name> --type <type>")
        click.echo("  3. Start tracking changes: tig new-change <change-id>")

    except FileExistsError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("\nThe specs/ directory already exists in this location.", err=True)
        click.echo("If you want to reinitialize, please remove or rename the existing directory.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error initializing specs: {e}", err=True)
        sys.exit(1)


@main.command("list-specs")
@click.option(
    "--type",
    "-t",
    "spec_type",
    type=click.Choice(["capabilities", "data-models", "api", "architecture"]),
    help="Filter by specification type"
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output in JSON format"
)
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to specs directory (defaults to current directory)"
)
def list_specs_command(spec_type: Optional[str], json_output: bool, path: Optional[Path]) -> None:
    """List all specifications in the project.

    Scans the specs/ directory and displays all discovered specifications,
    grouped by type. Use --type to filter by a specific type.
    """
    root_path = path or Path.cwd()
    manager = SpecsManager(root_path)

    try:
        specs = manager.list_specs(spec_type=spec_type)

        if json_output:
            # Output JSON format
            click.echo(json.dumps(specs, indent=2))
            return

        # Human-readable format
        total_count = sum(len(spec_list) for spec_list in specs.values())

        if total_count == 0:
            click.echo("No specifications found.")
            click.echo("\nCreate your first spec:")
            click.echo("  - Use an AI assistant with: /new-spec")
            click.echo("  - Or manually create in specs/ directory")
            return

        click.echo(f"Found {total_count} specification(s):\n")

        for stype, spec_list in specs.items():
            if not spec_list:
                continue

            # Format type name nicely
            type_display = stype.replace("-", " ").title()
            click.echo(f"{type_display} ({len(spec_list)}):")

            for spec in spec_list:
                click.echo(f"  - {spec['name']}")
                click.echo(f"    {spec['path']}")

            click.echo()  # Empty line between types

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error listing specs: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
