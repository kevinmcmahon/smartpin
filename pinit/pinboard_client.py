# ABOUTME: Wrapper for Pinboard API interactions using pinboard-tools library
# ABOUTME: Handles bookmark creation and synchronization with local database

import json
from pathlib import Path
from typing import Any

from pinboard_tools import BidirectionalSync, init_database
from pinboard_tools.database.models import Database
from pinboard_tools.sync.bidirectional import SyncDirection


def ensure_database_initialized(db_path: str | None = None) -> str:
    """
    Ensure the pinboard-tools database is initialized.

    Args:
        db_path: Path to SQLite database file (defaults to ~/.pinit/bookmarks.db)

    Returns:
        The database path used
    """
    if db_path is None:
        config_dir = Path.home() / ".pinit"
        config_dir.mkdir(exist_ok=True)
        db_path = str(config_dir / "bookmarks.db")

    init_database(db_path)
    return db_path


def add_bookmark(
    api_token: str,
    url: str,
    title: str,
    description: str | None = "",
    tags: list[str] | None = None,
    shared: bool = True,
    toread: bool = False,
    db_path: str | None = None,
) -> bool:
    """
    Add a bookmark to Pinboard using pinboard-tools.

    This function uses the simple approach from the pinboard-tools documentation
    where we just sync with the remote service.

    Args:
        api_token: Pinboard API token (username:token format)
        url: The URL to bookmark
        title: The title of the bookmark
        description: Extended description (optional)
        tags: List of tags (optional)
        shared: Whether the bookmark is public (default: True)
        toread: Whether to mark as "to read" (default: False)
        db_path: Path to SQLite database file (optional)

    Returns:
        True if successful, False otherwise
    """
    if tags is None:
        tags = []

    try:
        # Ensure database is initialized
        ensure_database_initialized(db_path)

        # For now, use the simple pinboard API directly since the
        # pinboard-tools sync approach is more complex than needed
        # for single bookmark addition
        import pinboard

        pb = pinboard.Pinboard(api_token)
        result = pb.posts.add(
            url=url,
            description=title,  # Pinboard calls the title "description"
            extended=description or "",  # Pinboard calls the description "extended"
            tags=tags,
            shared=shared,
            toread=toread,
        )

        return bool(result)

    except Exception:
        return False


def add_bookmark_from_json(
    api_token: str, bookmark_data: str | dict[str, Any], db_path: str | None = None
) -> bool:
    """
    Add a bookmark to Pinboard from JSON data using pinboard-tools.

    Args:
        api_token: Pinboard API token (username:token format)
        bookmark_data: Either a JSON string or a dictionary with bookmark data
        db_path: Path to SQLite database file (optional)

    Returns:
        True if successful, False otherwise
    """
    if isinstance(bookmark_data, str):
        data = json.loads(bookmark_data)
    else:
        data = bookmark_data

    return add_bookmark(
        api_token=api_token,
        url=data["url"],
        title=data["title"],
        description=data.get("description", ""),
        tags=data.get("tags", []),
        db_path=db_path,
    )


def sync_all_bookmarks(api_token: str, db_path: str | None = None) -> dict[str, Any]:
    """
    Perform a full bidirectional sync of all bookmarks.

    Args:
        api_token: Pinboard API token (username:token format)
        db_path: Path to SQLite database file (optional)

    Returns:
        Dictionary with sync results including errors count
    """
    try:
        # Ensure database is initialized
        db_path_used = ensure_database_initialized(db_path)

        # Create database and sync client
        db = Database(db_path_used)
        sync = BidirectionalSync(db=db, api_token=api_token)

        # Perform full bidirectional sync
        results = sync.sync(direction=SyncDirection.BIDIRECTIONAL)

        return results

    except Exception as e:
        return {"errors": 1, "error_message": str(e)}
