"""Command-line interface for Tigs."""

import subprocess
import sys
from pathlib import Path
from typing import Optional

import click

from .store import TigsStore
from .tui import TigsStoreApp, TigsViewApp, CURSES_AVAILABLE


@click.group()
@click.option("--repo", "-r", type=click.Path(exists=True, path_type=Path),
              help="Path to Git repository (defaults to current directory)")
@click.pass_context
def main(ctx: click.Context, repo: Optional[Path]) -> None:
    """Tigs - Talks in Git → Specs.

    Store and manage chats for Git commits using Git notes.
    """
    ctx.ensure_object(dict)
    try:
        ctx.obj["store"] = TigsStore(repo)
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
        message = "\n".join(line for line in message.split("\n") 
                           if not line.strip().startswith("#")).strip()
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
@click.option("--force", "-f", is_flag=True, help="Force push even if commits are not pushed")
@click.pass_context
def push(ctx: click.Context, remote: str, force: bool) -> None:
    """Push chats to remote repository.

    This command ensures all commits with chats are pushed to the remote
    before pushing the chats themselves, preventing orphaned notes.
    """
    store = ctx.obj["store"]
    try:
        store.push_chats(remote, force=force)
        click.echo(f"Successfully pushed chats to '{remote}'")
    except ValueError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or str(e)
        click.echo(f"Error pushing chats: {error_msg}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("fetch")
@click.argument("remote", type=str, default="origin")
@click.pass_context
def fetch(ctx: click.Context, remote: str) -> None:
    """Fetch chats from remote repository."""
    store = ctx.obj["store"]
    try:
        store._run_git(["fetch", remote, "refs/notes/chats:refs/notes/chats"])
        click.echo(f"Successfully fetched chats from '{remote}'")
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
    click.echo("Warning: 'push-chats' is deprecated. Use 'tigs push' instead.", err=True)
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
    click.echo("Warning: 'fetch-chats' is deprecated. Use 'tigs fetch' instead.", err=True)
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


if __name__ == "__main__":
    main()