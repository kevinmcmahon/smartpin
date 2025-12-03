# ABOUTME: CLI interface for pinit using Click framework
# ABOUTME: Handles command-line parsing and user interaction

import os
import sys
from pathlib import Path

import click
import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel

from .extractor import PinboardBookmarkExtractor
from .pinboard_client import add_bookmark, sync_all_bookmarks

console = Console()


def ensure_config_dir() -> Path:
    """Ensure user config directory exists and return its path."""
    config_dir = Path.home() / ".pinit"
    config_dir.mkdir(exist_ok=True)
    return config_dir


def load_config() -> None:
    """Load configuration from environment variables.

    Loads configuration in the following priority order:
    1. System environment variables (highest priority)
    2. Local .env file in current directory
    3. User config at ~/.pinit/config (lowest priority)
    """
    # Load in reverse priority order (lowest to highest)
    # User config directory
    user_config_dir = Path.home() / ".pinit"
    user_config_file = user_config_dir / "config"
    if user_config_file.exists():
        load_dotenv(user_config_file)

    # Local .env in current directory
    local_env = Path(".env")
    if local_env.exists():
        load_dotenv(local_env, override=True)

    # System environment variables have highest priority by default


def get_api_token() -> str | None:
    """Get Pinboard API token from environment."""
    token = os.getenv("PINBOARD_API_TOKEN")
    if not token:
        user_config_dir = Path.home() / ".pinit"
        console.print("[red]Error:[/red] PINBOARD_API_TOKEN not found in environment")
        console.print(
            "\nPlease set your Pinboard API token using one of these methods:"
        )
        console.print("\n1. Set environment variable:")
        console.print("   export PINBOARD_API_TOKEN=your_username:your_token")
        console.print("\n2. Create a user config file at ~/.pinit/config:")
        console.print(f"   mkdir -p {user_config_dir}")
        console.print(
            f"   echo 'PINBOARD_API_TOKEN=your_username:your_token' > {user_config_dir / 'config'}"
        )
        console.print("\n3. Create a local .env file in current directory:")
        console.print("   echo 'PINBOARD_API_TOKEN=your_username:your_token' > .env")
    return token


@click.group()
@click.version_option(package_name="smartpin")
def cli() -> None:
    """Pinit - AI-powered Pinboard bookmark manager.

    Automatically extracts metadata from web pages using AI to create
    organized bookmarks for your Pinboard account.

    Configuration:
      API tokens can be configured in three ways (in priority order):
      1. PINBOARD_API_TOKEN environment variable
      2. .env file in current directory
      3. ~/.pinit/config user configuration

      Run 'pinit config --init' to set up user configuration interactively.

    Examples:
      pinit add https://example.com
      pinit add https://example.com --dry-run
      pinit config --init  # Set up configuration
      pinit config         # Show current configuration
    """
    load_config()


@cli.command()
@click.argument("url")
@click.option("--dry-run", is_flag=True, help="Extract metadata without saving")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON")
@click.option("--private", is_flag=True, help="Make bookmark private")
@click.option("--toread", is_flag=True, help="Mark as 'to read'")
@click.option(
    "--model",
    default=None,
    help="LLM model to use (default: anthropic/claude-sonnet-4-0)",
    envvar="PINIT_MODEL",
)
def add(
    url: str,
    dry_run: bool,
    output_json: bool,
    private: bool,
    toread: bool,
    model: str | None,
) -> None:
    """Add a URL to Pinboard with AI-extracted metadata.

    The AI will analyze the webpage content and extract:
    - Title: The main content title (not just the HTML title)
    - Description: A 1-2 sentence summary
    - Tags: 3-8 relevant tags for organization

    Options:
      --dry-run     Preview extraction without saving to Pinboard
      --json        Output raw JSON instead of formatted display
      --private     Mark bookmark as private (default: public)
      --toread      Mark bookmark as "to read"
      --model       Specify AI model (default: anthropic/claude-sonnet-4-0)

    Examples:
      pinit add https://example.com
      pinit add https://example.com --dry-run
      pinit add https://example.com --private --toread
      pinit add https://example.com --model gpt-4 --json
    """
    try:
        # Use model from option/env or default
        model_name = model or "anthropic/claude-sonnet-4-0"

        # Extract bookmark data
        with console.status(f"[yellow]Analyzing webpage with {model_name}...[/yellow]"):
            extractor = PinboardBookmarkExtractor(model_name=model_name)
            bookmark = extractor.extract_bookmark(url)

        if output_json:
            console.print(JSON.from_data(bookmark))
        else:
            # Display formatted output
            panel = Panel.fit(
                f"[bold]Title:[/bold] {bookmark['title']}\n"
                f"[bold]URL:[/bold] {bookmark['url']}\n"
                f"[bold]Description:[/bold] {bookmark.get('description', 'N/A')}\n"
                f"[bold]Tags:[/bold] {', '.join(bookmark.get('tags', []))}",
                title="[green]Extracted Bookmark[/green]",
                border_style="green",
            )
            console.print(panel)

        if dry_run:
            console.print("\n[yellow]Dry run mode - bookmark not saved[/yellow]")
            return

        # Get API token
        api_token = get_api_token()
        if not api_token:
            sys.exit(1)

        # Save to Pinboard
        with console.status("[yellow]Saving to Pinboard...[/yellow]"):
            # Apply private and toread flags
            result = add_bookmark(
                api_token=api_token,
                url=bookmark["url"],
                title=bookmark["title"],
                description=bookmark.get("description", ""),
                tags=bookmark.get("tags", []),
                shared=not private,  # private flag inverts shared
                toread=toread,
            )

        if result:
            console.print("\n[green]✓ Bookmark saved successfully![/green]")
        else:
            console.print("\n[red]✗ Failed to save bookmark[/red]")
            sys.exit(1)

    except httpx.HTTPError as e:
        console.print(f"[red]Error fetching webpage:[/red] {e}")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]Error extracting bookmark data:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.option("--init", is_flag=True, help="Initialize user configuration")
def config(init: bool) -> None:
    """Show configuration information or initialize config.

    Without --init:
      Displays current API token status, AI model configuration,
      database location, and configuration file locations.

    With --init:
      Creates ~/.pinit/config configuration file interactively.
      Allows you to set API token, AI model, and database location.

    Configuration is loaded in priority order:
    1. System environment variables (highest priority)
    2. Local .env file in current directory
    3. User config at ~/.pinit/config
    """
    if init:
        # Initialize configuration
        config_dir = ensure_config_dir()
        config_file = config_dir / "config"

        console.print("[bold]Pinit Configuration Setup[/bold]\n")

        # Check if config already exists
        if config_file.exists():
            overwrite = click.confirm(
                f"Config file already exists at {config_file}. Overwrite?",
                default=False,
            )
            if not overwrite:
                console.print("[yellow]Configuration setup cancelled.[/yellow]")
                return

        # Get API token
        console.print("Please enter your Pinboard API token.")
        console.print(
            "[dim]You can find this at https://pinboard.in/settings/password[/dim]\n"
        )
        api_token = click.prompt("PINBOARD_API_TOKEN", hide_input=True)

        # Optionally get model
        console.print("\nOptionally, specify an AI model (press Enter for default).")
        console.print("[dim]Default: anthropic/claude-sonnet-4-0[/dim]")
        model = click.prompt("PINIT_MODEL", default="", show_default=False)

        # Optionally get database path
        console.print(
            "\nOptionally, specify database location (press Enter for default)."
        )
        default_db_path = str(config_dir / "bookmarks.db")
        console.print(f"[dim]Default: {default_db_path}[/dim]")
        db_path = click.prompt("PINIT_DB_PATH", default="", show_default=False)

        # Write config file
        with open(config_file, "w") as f:
            f.write("# Pinit configuration\n")
            f.write(f"PINBOARD_API_TOKEN={api_token}\n")
            if model:
                f.write(f"PINIT_MODEL={model}\n")
            if db_path:
                # Expand user path if provided
                expanded_db_path = os.path.expanduser(db_path)
                f.write(f"PINIT_DB_PATH={expanded_db_path}\n")

        # Set restrictive permissions
        config_file.chmod(0o600)

        console.print(f"\n[green]✓[/green] Configuration saved to {config_file}")
        console.print(
            "[dim]File permissions set to 600 (read/write for owner only)[/dim]"
        )
        return
    console.print("[bold]Pinit Configuration[/bold]\n")

    api_token = os.getenv("PINBOARD_API_TOKEN")
    if api_token:
        # Mask the token for security
        username = api_token.split(":")[0] if ":" in api_token else "unknown"
        console.print(f"[green]✓[/green] API Token configured for user: {username}")
    else:
        console.print("[red]✗[/red] API Token not configured")

    # Show model configuration
    model = os.getenv("PINIT_MODEL", "anthropic/claude-sonnet-4-0")
    console.print(f"\n[bold]Model:[/bold] {model}")
    if os.getenv("PINIT_MODEL"):
        console.print("  [dim](set via PINIT_MODEL environment variable)[/dim]")
    else:
        console.print("  [dim](using default)[/dim]")

    # Show database configuration
    from .pinboard_client import ensure_database_initialized

    db_path = ensure_database_initialized()
    console.print(f"\n[bold]Database:[/bold] {db_path}")
    if os.getenv("PINIT_DB_PATH"):
        console.print("  [dim](set via PINIT_DB_PATH environment variable)[/dim]")
    else:
        console.print("  [dim](using default location)[/dim]")

    # Check for config files
    local_env = Path(".env")
    user_config = Path.home() / ".pinit" / "config"

    console.print("\n[bold]Configuration files:[/bold]")
    if local_env.exists():
        console.print(f"  - Local: {local_env.absolute()} [green]✓[/green]")
    else:
        console.print("  - Local: ./.env [dim](not found)[/dim]")

    if user_config.exists():
        console.print(f"  - User: {user_config} [green]✓[/green]")
    else:
        console.print(f"  - User: {user_config} [dim](not found)[/dim]")

    if not api_token:
        console.print(
            "\n[yellow]Tip:[/yellow] Run 'pinit config --init' to set up configuration interactively."
        )


@cli.command()
@click.option(
    "--dry-run", is_flag=True, help="Show what would be synced without making changes"
)
def sync(dry_run: bool) -> None:
    """Sync all bookmarks between local database and Pinboard.

    This command uses the pinboard-tools library to maintain a local SQLite
    database of your bookmarks and performs bidirectional synchronization
    with Pinboard.in.

    The local database is stored at ~/.pinit/bookmarks.db and allows for
    advanced features like tag similarity detection and offline access.

    Examples:
      pinit sync           # Perform full bidirectional sync
      pinit sync --dry-run # Show what would be synced
    """
    try:
        # Get API token
        api_token = get_api_token()
        if not api_token:
            sys.exit(1)

        # Perform sync
        dry_run_suffix = " (dry run)" if dry_run else ""
        with console.status(f"[yellow]Syncing bookmarks{dry_run_suffix}...[/yellow]"):
            results = sync_all_bookmarks(api_token, dry_run=dry_run)

        # Report results
        if results.get("errors", 0) == 0:
            success_msg = (
                "✓ Sync preview completed!"
                if dry_run
                else "✓ Sync completed successfully!"
            )
            console.print(f"\n[green]{success_msg}[/green]")
            if "local_to_remote" in results:
                action = "Would sync" if dry_run else "Synced"
                console.print(
                    f"  Local → Remote: {action} {results['local_to_remote']} bookmarks"
                )
            if "remote_to_local" in results:
                action = "Would sync" if dry_run else "Synced"
                console.print(
                    f"  Remote → Local: {action} {results['remote_to_local']} bookmarks"
                )
        else:
            console.print(
                f"\n[red]✗ Sync completed with {results['errors']} errors[/red]"
            )
            if "error_message" in results:
                console.print(f"[red]Error: {results['error_message']}[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Sync failed:[/red] {e}")
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    cli()
