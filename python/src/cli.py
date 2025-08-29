"""Command-line interface for Tigs."""

import sys
from pathlib import Path
from typing import Optional

import click

from .store import TigsStore


@click.group()
@click.option("--repo", "-r", type=click.Path(exists=True, path_type=Path),
              help="Path to Git repository (defaults to current directory)")
@click.pass_context
def main(ctx: click.Context, repo: Optional[Path]) -> None:
    """Tigs - Talks in Git → Specs.

    Store and manage chat objects in Git repositories.
    """
    ctx.ensure_object(dict)
    try:
        ctx.obj["store"] = TigsStore(repo)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("hash-chat")
@click.argument("content", type=str)
@click.option("--id", "-i", "object_id", help="Chat ID (generated if not provided)")
@click.pass_context
def hash_chat(ctx: click.Context, content: str, object_id: Optional[str]) -> None:
    """Compute chat ID and store chat content in the repository."""
    store = ctx.obj["store"]
    try:
        obj_id = store.store(content, object_id)
        click.echo(obj_id)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("cat-chat")
@click.argument("chat_id", type=str)
@click.pass_context
def cat_chat(ctx: click.Context, chat_id: str) -> None:
    """Display content of a stored chat."""
    store = ctx.obj["store"]
    try:
        content = store.retrieve(chat_id)
        click.echo(content, nl=False)
    except KeyError:
        click.echo(f"Error: Chat not found: {chat_id}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("ls-chats")
@click.pass_context
def ls_chats(ctx: click.Context) -> None:
    """List all stored chat IDs."""
    store = ctx.obj["store"]
    try:
        object_ids = store.list()
        for obj_id in object_ids:
            click.echo(obj_id)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("rm-chat")
@click.argument("chat_id", type=str)
@click.pass_context
def rm_chat(ctx: click.Context, chat_id: str) -> None:
    """Remove a stored chat."""
    store = ctx.obj["store"]
    try:
        store.delete(chat_id)
        click.echo(f"Deleted: {chat_id}")
    except KeyError:
        click.echo(f"Error: Chat not found: {chat_id}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("push-chats")
@click.argument("remote", type=str, default="origin")
@click.pass_context
def push_chats(ctx: click.Context, remote: str) -> None:
    """Push chat objects to remote repository."""
    store = ctx.obj["store"]
    try:
        store._run_git(["push", remote, "refs/tigs/chats/*:refs/tigs/chats/*"])
        click.echo(f"Pushed chats to {remote}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("fetch-chats")
@click.argument("remote", type=str, default="origin")
@click.pass_context
def fetch_chats(ctx: click.Context, remote: str) -> None:
    """Fetch chat objects from remote repository."""
    store = ctx.obj["store"]
    try:
        store._run_git(["fetch", remote, "refs/tigs/chats/*:refs/tigs/chats/*"])
        click.echo(f"Fetched chats from {remote}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

