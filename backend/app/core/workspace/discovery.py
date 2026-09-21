from pathlib import Path


def find_workspace_root(start: Path | None = None) -> Path | None:
    """
    Walk upward until a .atlas directory is found.

    Example:
        repo/src/controllers -> repo/
    """

    current = (start or Path.cwd()).resolve()

    while True:
        if (current / ".atlas").exists():
            return current

        if current.parent == current:
            return None

        current = current.parent