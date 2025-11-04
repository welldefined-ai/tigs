"""Command-line interface for Tigs."""

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import click
import yaml

from .storage import TigsRepo
from .tui import TigsStoreApp, TigsViewApp, CURSES_AVAILABLE
from .specs_manager import SpecsManager
from .specs_manager.structure_loader import StructureLoader
from .chat_providers import get_chat_parser


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
@click.option(
    "--commit",
    type=str,
    default=None,
    help="Focus on specific commit (shows 2-pane layout)",
)
@click.option(
    "--suggest",
    type=str,
    default=None,
    help='Pre-select suggested messages (format: "<log_uri>:<idx>,<idx>;<log_uri>:<idx>")',
)
@click.pass_context
def store_command(ctx: click.Context, commit: str, suggest: str) -> None:
    """Launch interactive TUI for selecting commits and messages."""
    if not CURSES_AVAILABLE:
        click.echo("Error: curses library not available", err=True)
        sys.exit(1)

    store = ctx.obj["store"]

    # Parse suggestions if provided
    suggestions = None
    if suggest:
        try:
            suggestions = _parse_suggestions(suggest)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    app = TigsStoreApp(store, target_commit=commit, suggestions=suggestions)
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
    "--structure",
    "-s",
    type=str,
    default=None,
    help="Spec structure to use (currently only 'web-app' is available). Custom structures can be added to templates/structures/.",
)
@click.option(
    "--examples", is_flag=True, help="Generate example specifications for each type"
)
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to initialize specs (defaults to current directory)",
)
def init_specs(structure: Optional[str], examples: bool, path: Optional[Path]) -> None:
    """Initialize specs directory structure.

    Creates a specs/ directory with subdirectories based on the chosen structure.
    Default structure is 'web-app' with: capabilities, data-models, api, architecture.

    Custom structures can be created by adding directories to templates/structures/.
    Use 'tigs list-structures' to see all available structures.
    """
    root_path = path or Path.cwd()
    manager = SpecsManager(root_path)

    try:
        result = manager.init_structure(structure_name=structure, with_examples=examples)

        click.echo(f"✓ Initialized specs directory at {root_path / 'specs'}")

        # Separate specs and commands for clearer display
        specs_items = [
            p
            for p in result["created"]
            if "/specs/" in str(p) or str(p).endswith("specs")
        ]
        claude_items = [p for p in result["created"] if "/.claude/" in str(p)]

        if specs_items:
            click.echo(f"\nCreated specs structure ({len(specs_items)} items):")
            for created_path in specs_items:
                rel_path = Path(created_path).relative_to(root_path)
                click.echo(f"  - {rel_path}")

        if claude_items:
            click.echo("\n✓ Created Claude Code slash commands:")
            for created_path in claude_items:
                rel_path = Path(created_path).relative_to(root_path)
                # Show command names more prominently
                if created_path.endswith(".md"):
                    command_name = Path(created_path).stem
                    click.echo(f"  - /{command_name}")
                else:
                    click.echo(f"  - {rel_path}")

        if examples:
            click.echo("\n✓ Generated example specifications")
            click.echo(
                "  Review examples in each subdirectory to understand the format"
            )

        click.echo("\nNext steps:")
        click.echo("  1. Review specs/README.md for format guidelines")
        if claude_items:
            click.echo("  2. Use AI slash commands:")
            click.echo("     /bootstrap - Bootstrap specs from existing code")
            click.echo("     /change    - Plan new features")
            click.echo("     /validate  - Check specs format")
            click.echo("     /archive   - Merge completed changes")
            click.echo(
                "  3. Or use CLI: tigs list-specs, tigs show-spec, tigs validate-specs"
            )
        else:
            click.echo("  2. Create your first spec using an AI assistant")
            click.echo("  3. Validate specs: tigs validate-specs --all")

    except FileExistsError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("\nThe specs/ directory already exists in this location.", err=True)
        click.echo(
            "If you want to reinitialize, please remove or rename the existing directory.",
            err=True,
        )
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error initializing specs: {e}", err=True)
        sys.exit(1)


@main.command("list-structures")
def list_structures() -> None:
    """List all available spec structures.

    Shows all spec structure templates that can be used with 'tigs init-specs --structure'.
    """
    try:
        loader = StructureLoader()
        structures = loader.list_structures()

        if not structures:
            click.echo("No structures found.")
            return

        click.echo("Available spec structures:\n")
        for structure_name in structures:
            try:
                structure = loader.load_structure(structure_name)
                spec_types = ", ".join(structure.get_spec_type_names())
                click.echo(f"  {structure.name}")
                click.echo(f"    Description: {structure.description}")
                click.echo(f"    Spec types: {spec_types}")
                click.echo()
            except Exception as e:
                click.echo(f"  {structure_name} (error loading: {e})")

        click.echo("Use 'tigs show-structure <name>' for details on a specific structure.")
        click.echo("Use 'tigs init-specs --structure <name>' to initialize with a structure.")

    except Exception as e:
        click.echo(f"Error listing structures: {e}", err=True)
        sys.exit(1)


@main.command("show-structure")
@click.argument("name", type=str)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def show_structure(name: str, output_json: bool) -> None:
    """Show detailed information about a spec structure.

    NAME is the structure name (e.g., web-app)
    """
    try:
        loader = StructureLoader()
        info = loader.get_structure_info(name)

        if output_json:
            click.echo(json.dumps(info, indent=2))
            return

        click.echo(f"Structure: {info['name']}")
        click.echo(f"Version: {info['version']}")
        click.echo(f"Author: {info['author']}")
        click.echo(f"\nDescription:")
        click.echo(f"  {info['description']}")

        click.echo(f"\nSpec Types:")
        for spec_type, details in info['spec_types'].items():
            click.echo(f"  {spec_type}/")
            click.echo(f"    {details['description']}")

        click.echo(f"\nRequired Commands:")
        for cmd in info['required_commands']:
            click.echo(f"  /{cmd}")

        click.echo(f"\nUsage:")
        click.echo(f"  tigs init-specs --structure {info['name']}")

    except FileNotFoundError as e:
        click.echo(f"Error: Structure '{name}' not found", err=True)
        click.echo("\nUse 'tigs list-structures' to see available structures.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error showing structure: {e}", err=True)
        sys.exit(1)


@main.command("list-specs")
@click.option(
    "--type",
    "-t",
    "spec_type",
    type=click.Choice(["capabilities", "data-models", "api", "architecture"]),
    help="Filter by specification type",
)
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to specs directory (defaults to current directory)",
)
def list_specs_command(
    spec_type: Optional[str], json_output: bool, path: Optional[Path]
) -> None:
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
            click.echo("  - Use an AI assistant with: /change")
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


@main.command("show-spec")
@click.argument("name", type=str)
@click.option(
    "--type",
    "-t",
    "spec_type",
    type=click.Choice(["capabilities", "data-models", "api", "architecture"]),
    help="Specify spec type to disambiguate",
)
@click.option(
    "--json", "json_output", is_flag=True, help="Output in JSON format with metadata"
)
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to specs directory (defaults to current directory)",
)
def show_spec_command(
    name: str, spec_type: Optional[str], json_output: bool, path: Optional[Path]
) -> None:
    """Show the content of a specification.

    NAME is the specification name (directory name).

    If multiple specs with the same name exist in different types,
    use --type to specify which one to show.
    """
    root_path = path or Path.cwd()
    manager = SpecsManager(root_path)

    try:
        spec_info = manager.show_spec(name, spec_type=spec_type)

        if json_output:
            # Output JSON format with metadata
            click.echo(json.dumps(spec_info, indent=2))
            return

        # Human-readable format
        type_display = spec_info["type"].replace("-", " ").title()
        click.echo(f"Spec: {spec_info['name']} ({type_display})")
        click.echo(f"Path: {spec_info['path']}")
        click.echo("=" * 80)
        click.echo(spec_info["content"], nl=False)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error showing spec: {e}", err=True)
        sys.exit(1)


@main.command("archive-change")
@click.argument("change_id", type=str)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--no-validate", is_flag=True, help="Skip validation checks")
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to specs directory (defaults to current directory)",
)
def archive_change_command(
    change_id: str, yes: bool, no_validate: bool, path: Optional[Path]
) -> None:
    """Archive a change by merging delta specs into main specs.

    CHANGE_ID is the name of the change directory in specs/changes/.

    This command:
    1. Validates the change structure (unless --no-validate)
    2. Parses delta specifications
    3. Merges changes into main specifications
    4. Moves the change to archive with date prefix

    Example:
      tigs archive-change add-user-authentication
    """
    root_path = path or Path.cwd()
    manager = SpecsManager(root_path)

    try:
        # Get change directory info
        change_dir = root_path / "specs" / "changes" / change_id

        if not change_dir.exists():
            click.echo(f"Error: Change '{change_id}' not found", err=True)
            click.echo("\nAvailable changes:", err=True)
            changes_dir = root_path / "specs" / "changes"
            if changes_dir.exists():
                changes = [
                    d.name
                    for d in changes_dir.iterdir()
                    if d.is_dir() and d.name != "archive"
                ]
                if changes:
                    for change in changes:
                        click.echo(f"  - {change}", err=True)
                else:
                    click.echo("  (none)", err=True)
            sys.exit(1)

        # Show summary and confirm
        if not yes:
            click.echo(f"About to archive change: {change_id}")
            click.echo(f"Change directory: {change_dir}")

            # Show what will be merged
            click.echo("\nDelta specifications found:")
            found_any = False
            for spec_type in ["capabilities", "data-models", "api", "architecture"]:
                delta_dir = change_dir / spec_type
                if delta_dir.exists():
                    specs = [d.name for d in delta_dir.iterdir() if d.is_dir()]
                    if specs:
                        found_any = True
                        click.echo(f"  {spec_type}:")
                        for spec in specs:
                            click.echo(f"    - {spec}")

            if not found_any:
                click.echo("  (none found)")

            click.echo()
            if not click.confirm("Proceed with archiving?"):
                click.echo("Aborted.")
                sys.exit(0)

        # Perform archive
        result = manager.archive_change(change_id, skip_validation=no_validate)

        click.echo(f"✓ Archived change: {change_id}")
        click.echo(f"\nMerged {len(result['merged'])} specification(s):")
        for merged_path in result["merged"]:
            click.echo(f"  - {merged_path}")

        click.echo(f"\nArchived to: {result['archive_path']}")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error archiving change: {e}", err=True)
        sys.exit(1)


@main.command("validate-specs")
@click.option("--all", "validate_all", is_flag=True, help="Validate all specifications")
@click.option(
    "--type",
    "-t",
    "spec_type",
    type=click.Choice(["capabilities", "data-models", "api", "architecture"]),
    help="Validate only specific type",
)
@click.option(
    "--change", "-c", "change_id", type=str, help="Validate specs in a specific change"
)
@click.option("--strict", is_flag=True, help="Treat warnings as errors")
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to specs directory (defaults to current directory)",
)
def validate_specs_command(
    validate_all: bool,
    spec_type: Optional[str],
    change_id: Optional[str],
    strict: bool,
    path: Optional[Path],
) -> None:
    """Validate specification format and structure.

    Checks that specifications follow the defined format rules:
    - Required sections present
    - Correct heading hierarchy
    - Valid requirement/scenario format
    - Proper use of modal verbs (SHALL/MUST)

    Examples:
      tigs validate-specs --all                # All specs
      tigs validate-specs --type capabilities  # Only capabilities
      tigs validate-specs --change my-change   # Only in change
      tigs validate-specs --all --strict       # Warnings = errors
    """
    root_path = path or Path.cwd()
    manager = SpecsManager(root_path)

    try:
        # Validate
        results = manager.validate_specs(
            spec_type=spec_type, change_id=change_id, strict=strict
        )

        # Count totals
        total_specs = 0
        total_errors = 0
        total_warnings = 0
        specs_with_errors = 0
        specs_with_warnings = 0

        # Display results
        has_any_issues = False

        for stype, type_results in results.items():
            if not type_results:
                continue

            total_specs += len(type_results)

            # Check if any specs have issues
            specs_with_issues = [r for r in type_results if r.has_issues]
            if not specs_with_issues:
                continue

            has_any_issues = True

            # Display type header
            type_display = stype.replace("-", " ").title()
            click.echo(f"\n{type_display}:")
            click.echo("=" * 60)

            for result in specs_with_issues:
                if result.errors:
                    specs_with_errors += 1
                    total_errors += len(result.errors)
                if result.warnings:
                    specs_with_warnings += 1
                    total_warnings += len(result.warnings)

                # Display spec path
                click.echo(f"\n{result.spec_path}")

                # Display errors
                if result.errors:
                    for issue in result.errors:
                        click.echo(f"  {issue}", err=True)

                # Display warnings
                if result.warnings:
                    for issue in result.warnings:
                        # In strict mode, warnings are shown as errors
                        if strict:
                            click.echo(f"  {issue}", err=True)
                        else:
                            click.echo(f"  {issue}")

        # Summary
        click.echo("\n" + "=" * 60)
        if not has_any_issues:
            click.echo(f"✓ All {total_specs} specification(s) passed validation")
            sys.exit(0)
        else:
            click.echo("✗ Validation completed with issues:")
            click.echo(f"  Total specs: {total_specs}")
            click.echo(f"  Specs with errors: {specs_with_errors}")
            click.echo(f"  Specs with warnings: {specs_with_warnings}")
            click.echo(f"  Total errors: {total_errors}")
            click.echo(f"  Total warnings: {total_warnings}")

            # Exit with error code if there are errors or strict mode warnings
            if total_errors > 0 or (strict and total_warnings > 0):
                sys.exit(1)
            else:
                sys.exit(0)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error validating specs: {e}", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)


@main.command("list-logs")
@click.option(
    "--recent",
    type=int,
    default=10,
    help="Number of most recent logs to fetch. Default: 10",
)
def list_logs(recent: int) -> None:
    """List available chat logs with metadata (without messages).

    Returns lightweight metadata for logs including IDs, providers, and timestamps.
    Does NOT fetch message content, making it very fast and token-efficient.

    This command is designed for AI agents to discover available logs before
    selectively fetching messages with 'tigs list-messages <log-id>'.

    Examples:
      tigs list-logs              # Most recent 10 logs (default)
      tigs list-logs --recent 20  # Most recent 20 logs
      tigs list-logs --recent 5   # Most recent 5 logs
    """
    try:
        # Get chat parser
        parser = get_chat_parser()

        # List all logs (already sorted by modification time, newest first)
        logs_data = parser.list_logs()

        # Take most recent N logs
        filtered_logs = logs_data[:recent]

        # Build lightweight output (no message parsing required)
        output_logs = []
        for log_uri, metadata in filtered_logs:
            log_entry = {
                "id": log_uri,
                "provider": metadata.get("provider", ""),
                "provider_label": metadata.get("provider_label", ""),
                "modified": metadata.get("modified", ""),
            }
            output_logs.append(log_entry)

        # Output YAML
        output = {"logs": output_logs}
        click.echo(yaml.dump(output, default_flow_style=False, sort_keys=False))

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("list-messages")
@click.argument("log_id", type=str, required=False, default=None)
@click.option(
    "--recent",
    type=int,
    default=10,
    help="Number of most recent logs to fetch. Default: 10 (ignored if LOG_ID provided)",
)
@click.option(
    "--since",
    type=str,
    default=None,
    help='Time window for messages (e.g., "3h", "1d", "2025-10-29T10:00:00"). Overrides --recent. Ignored if LOG_ID provided.',
)
def list_messages(log_id: Optional[str], recent: int, since: Optional[str]) -> None:
    """List chat messages from configured providers for AI analysis.

    Two modes of operation:

    MODE 1: Fetch specific log (efficient, recommended for AI agents)
      tigs list-messages <log-id>

    MODE 2: Fetch multiple logs (legacy behavior)
      tigs list-messages --recent 10
      tigs list-messages --since 3h

    Mode 1 is designed for progressive analysis: AI agents can use 'tigs list-logs'
    to discover available logs, then fetch messages one log at a time until they
    find the complete conversation history.

    Examples:
      # Mode 1: Specific log (efficient)
      tigs list-messages claude-code:abc123.jsonl

      # Mode 2: Multiple logs (legacy)
      tigs list-messages                    # Most recent 10 logs (default)
      tigs list-messages --recent 5         # Most recent 5 logs
      tigs list-messages --since 3h         # Last 3 hours
      tigs list-messages --since "2025-10-29T10:00:00"  # Since specific time
    """
    try:
        # Get chat parser
        parser = get_chat_parser()

        # =================================================================
        # MODE 1: SPECIFIC LOG REQUESTED (new, efficient mode)
        # =================================================================
        if log_id:
            # Parse single log
            chat = parser.parse(log_id)
            if not chat or not chat.messages:
                click.echo(f"Error: No messages found in log: {log_id}", err=True)
                sys.exit(1)

            # Extract messages
            messages_list = []
            for index, message in enumerate(chat.messages):
                msg_dict = {
                    "index": index,
                    "role": message.role.value,
                    "content": message.content,
                }
                # Include timestamp if available
                if message.timestamp:
                    msg_dict["timestamp"] = message.timestamp.isoformat()
                messages_list.append(msg_dict)

            # Get metadata for this log
            all_logs = parser.list_logs()
            metadata = {}
            for uri, meta in all_logs:
                if uri == log_id:
                    metadata = meta
                    break

            # Build output for single log
            log_entry = {
                "uri": log_id,
                "provider": metadata.get("provider", ""),
                "modified": metadata.get("modified", ""),
                "messages": messages_list,
            }

            # Output YAML
            output = {"logs": [log_entry]}
            click.echo(yaml.dump(output, default_flow_style=False, sort_keys=False))
            return

        # =================================================================
        # MODE 2: MULTIPLE LOGS (existing behavior)
        # =================================================================

        # Determine filtering mode: time-based or count-based
        use_time_filter = since is not None

        if use_time_filter:
            # Parse the since parameter
            cutoff_time = _parse_since_parameter(since)
        else:
            cutoff_time = None

        # List all logs (already sorted by modification time, newest first)
        logs_data = parser.list_logs()

        # Filter logs based on mode
        if use_time_filter:
            # Time-based filtering: filter by cutoff time
            filtered_logs = []
            for log_uri, metadata in logs_data:
                modified_str = metadata.get("modified", "")
                if not modified_str:
                    continue

                try:
                    modified_time = datetime.fromisoformat(
                        modified_str.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    continue

                # Filter by cutoff time
                if modified_time >= cutoff_time:
                    filtered_logs.append((log_uri, metadata))
        else:
            # Count-based filtering: take most recent N logs
            filtered_logs = logs_data[:recent]

        # Process each filtered log and extract messages
        output_logs = []
        for log_uri, metadata in filtered_logs:
            # Parse the log to get messages
            try:
                chat = parser.parse(log_uri)
                if not chat or not chat.messages:
                    continue

                # Include ALL messages from this log
                messages_list = []
                for index, message in enumerate(chat.messages):
                    msg_dict = {
                        "index": index,
                        "role": message.role.value,
                        "content": message.content,
                    }
                    # Include timestamp if available
                    if message.timestamp:
                        msg_dict["timestamp"] = message.timestamp.isoformat()
                    messages_list.append(msg_dict)

                # Add log entry
                log_entry = {
                    "uri": log_uri,
                    "provider": metadata.get("provider", ""),
                    "modified": metadata.get("modified", ""),
                    "messages": messages_list,
                }
                output_logs.append(log_entry)

            except Exception:
                # Skip logs that fail to parse
                continue

        # Output YAML
        output = {"logs": output_logs}
        click.echo(yaml.dump(output, default_flow_style=False, sort_keys=False))

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _parse_suggestions(suggest: str):
    """Parse the --suggest parameter into a dictionary.

    Format: "<log_uri>:<idx>,<idx>;<log_uri>:<idx>,<idx>"
    Multiple logs separated by ';'
    Multiple indices per log separated by ','

    Example:
        "claude-code:/path/to/log:0,5,7;codex-cli:/path/to/log2:2,8"

    Returns:
        Dict[str, List[int]]: Mapping of log_uri to list of message indices

    Raises:
        ValueError: If the format is invalid
    """
    suggestions = {}

    # Split by semicolon to get individual log entries
    log_entries = suggest.split(";")

    for entry in log_entries:
        entry = entry.strip()
        if not entry:
            continue

        # Split by colon to separate log_uri and indices
        if ":" not in entry:
            raise ValueError(
                f"Invalid suggestion format: '{entry}'. "
                "Expected format: '<log_uri>:<index>,<index>'"
            )

        # Find the last colon to split (log_uri may contain colons like "claude-code:/path")
        last_colon_idx = entry.rfind(":")
        log_uri = entry[:last_colon_idx]
        indices_str = entry[last_colon_idx + 1 :]

        if not log_uri:
            raise ValueError(f"Empty log URI in suggestion: '{entry}'")

        if not indices_str:
            raise ValueError(f"No indices provided for log: '{log_uri}'")

        # Parse indices
        try:
            indices = [
                int(idx.strip()) for idx in indices_str.split(",") if idx.strip()
            ]
        except ValueError as e:
            raise ValueError(
                f"Invalid index in suggestion for log '{log_uri}': {e}"
            ) from e

        if not indices:
            raise ValueError(f"No valid indices for log: '{log_uri}'")

        suggestions[log_uri] = indices

    return suggestions


def _parse_since_parameter(since: str) -> datetime:
    """Parse the --since parameter into a datetime cutoff.

    Supports:
    - Relative: "3h", "30m", "2d", "1w"
    - Absolute: "2025-10-29T10:00:00" or "2025-10-29"

    Returns:
        datetime object representing the cutoff time

    Raises:
        ValueError: If the format is invalid
    """
    # Try parsing as relative time (e.g., "3h", "2d")
    relative_pattern = r"^(\d+)([mhdw])$"
    match = re.match(relative_pattern, since.strip())

    if match:
        value = int(match.group(1))
        unit = match.group(2)

        now = datetime.now()
        if unit == "m":
            delta = timedelta(minutes=value)
        elif unit == "h":
            delta = timedelta(hours=value)
        elif unit == "d":
            delta = timedelta(days=value)
        elif unit == "w":
            delta = timedelta(weeks=value)
        else:
            raise ValueError(f"Invalid time unit: {unit}")

        return now - delta

    # Try parsing as absolute timestamp
    try:
        # Try with time component
        return datetime.fromisoformat(since)
    except ValueError:
        pass

    try:
        # Try as date only (add time 00:00:00)
        return datetime.fromisoformat(f"{since}T00:00:00")
    except ValueError:
        pass

    raise ValueError(
        f"Invalid --since format: '{since}'. "
        "Use relative (e.g., '3h', '2d') or absolute (e.g., '2025-10-29T10:00:00')"
    )


if __name__ == "__main__":
    main()
