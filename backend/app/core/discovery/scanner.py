from dataclasses import dataclass
from pathlib import Path


# Directories we never want to index
IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".idea",
    ".vscode",
    "dist",
    "build",
}

# File types Atlas currently supports
SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".c",
    ".cpp",
    ".cc",
    ".cxx",
    ".h",
    ".hpp",
    ".md",
    ".txt",
    ".json",
    ".yml",
    ".yaml",
}


@dataclass
class DiscoveredFile:
    absolute_path: Path
    relative_path: str


class RepositoryScanner:
    """Recursively discover supported files inside a repository."""

    def scan(self, repo_path: str | Path) -> list[DiscoveredFile]:
        root = Path(repo_path).resolve()

        if not root.exists():
            raise FileNotFoundError(f"{root} does not exist")

        if not root.is_dir():
            raise NotADirectoryError(f"{root} is not a directory")

        discovered: list[DiscoveredFile] = []

        for file in root.rglob("*"):
            if not file.is_file():
                continue

            # Skip ignored directories
            if any(part in IGNORE_DIRS for part in file.parts):
                continue

            if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            relative = file.relative_to(root).as_posix()

            discovered.append(
                DiscoveredFile(
                    absolute_path=file,
                    relative_path=relative,
                )
            )

        # Deterministic ordering
        discovered.sort(key=lambda f: f.relative_path)

        return discovered