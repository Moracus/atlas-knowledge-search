import json
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import UUID


ATLAS_DIR = ".atlas"
SESSION_FILE = "session.json"


@dataclass
class SessionMetadata:
    session_id: UUID
    repo_name: str
    root_path: str
    embedding_model: str
    atlas_version: str = "0.1.0"


class WorkspaceSessionManager:
    """Handles reading and writing the local .atlas/session.json file."""

    @staticmethod
    def atlas_dir(root: Path) -> Path:
        return root / ATLAS_DIR

    @staticmethod
    def session_path(root: Path) -> Path:
        return WorkspaceSessionManager.atlas_dir(root) / SESSION_FILE

    @staticmethod
    def create(root: Path, metadata: SessionMetadata) -> None:
        atlas = WorkspaceSessionManager.atlas_dir(root)
        atlas.mkdir(exist_ok=True)

        data = asdict(metadata)
        data["session_id"] = str(metadata.session_id)

        with open(
            WorkspaceSessionManager.session_path(root),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load(root: Path) -> SessionMetadata:
        with open(
            WorkspaceSessionManager.session_path(root),
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        data["session_id"] = UUID(data["session_id"])
        return SessionMetadata(**data)

    @staticmethod
    def exists(root: Path) -> bool:
        return WorkspaceSessionManager.session_path(root).exists()

    @staticmethod
    def delete(root: Path) -> None:
        path = WorkspaceSessionManager.session_path(root)

        if path.exists():
            path.unlink()

        atlas = WorkspaceSessionManager.atlas_dir(root)
        if atlas.exists() and not any(atlas.iterdir()):
            atlas.rmdir()