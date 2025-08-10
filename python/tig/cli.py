"""Command-line interface for Tig."""

import sys
from pathlib import Path
from typing import Optional

import click

from .store import TigStore


@click.group()
@click.option("--repo", "-r", type=click.Path(exists=True, path_type=Path),
              help="Path to Git repository (defaults to current directory)")
@click.pass_context
def main(ctx: click.Context, repo: Optional[Path]) -> None:
    """Tig - Talk in Git.
    
    Store and manage text objects in Git repositories.
    """
    ctx.ensure_object(dict)
    try:
        ctx.obj["store"] = TigStore(repo)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("content", type=str)
@click.option("--id", "-i", "object_id", help="Object ID (generated if not provided)")
@click.pass_context
def store(ctx: click.Context, content: str, object_id: Optional[str]) -> None:
    """Store text content in the repository."""
    store = ctx.obj["store"]
    try:
        obj_id = store.store(content, object_id)
        click.echo(obj_id)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("object_id", type=str)
@click.pass_context
def show(ctx: click.Context, object_id: str) -> None:
    """Show content of a stored object."""
    store = ctx.obj["store"]
    try:
        content = store.retrieve(object_id)
        click.echo(content, nl=False)
    except KeyError:
        click.echo(f"Error: Object not found: {object_id}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.pass_context
def list(ctx: click.Context) -> None:
    """List all stored object IDs."""
    store = ctx.obj["store"]
    try:
        object_ids = store.list()
        for obj_id in object_ids:
            click.echo(obj_id)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("object_id", type=str)
@click.pass_context
def delete(ctx: click.Context, object_id: str) -> None:
    """Delete a stored object."""
    store = ctx.obj["store"]
    try:
        store.delete(object_id)
        click.echo(f"Deleted: {object_id}")
    except KeyError:
        click.echo(f"Error: Object not found: {object_id}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--push", is_flag=True, help="Push objects to remote")
@click.option("--pull", is_flag=True, help="Pull objects from remote")
@click.argument("remote", type=str, default="origin")
@click.pass_context
def sync(ctx: click.Context, push: bool, pull: bool, remote: str) -> None:
    """Sync objects with remote repository."""
    if not push and not pull:
        click.echo("Error: Specify --push or --pull", err=True)
        sys.exit(1)
    
    store = ctx.obj["store"]
    
    try:
        if push:
            result = store._run_git(["push", remote, "refs/tig/*:refs/tig/*"])
            click.echo(f"Pushed objects to {remote}")
        
        if pull:
            result = store._run_git(["fetch", remote, "refs/tig/*:refs/tig/*"])
            click.echo(f"Pulled objects from {remote}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()