import asyncio
import uuid
from pathlib import Path

import typer

from atlas_cli.config import config_app, ensure_configured

app = typer.Typer(
    help="Atlas CLI - Structure-aware repository indexing",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")


@app.callback()
def main(ctx: typer.Context):
    # Runs before every command except `atlas config ...`
    if ctx.invoked_subcommand != "config":
        ensure_configured()

# ---------------------------------------------------------------------
# INIT
# ---------------------------------------------------------------------

@app.command()
def init():
    from app.core.workspace.session import WorkspaceSessionManager
    """
    Initialize Atlas in the current repository.
    """

    root = Path.cwd().resolve()

    if WorkspaceSessionManager.exists(root):
        typer.secho(
            "Atlas workspace already initialized.",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit()

    asyncio.run(_init_workspace(root))


async def _init_workspace(root: Path):
    from app.application.ingest import IngestApplication
    from app.core.discovery.scanner import RepositoryScanner
    from app.core.workspace.session import SessionMetadata, WorkspaceSessionManager
    from app.db.database import SessionLocal
    from app.db.models import ProcessingStatus, WorkspaceSession
    from app.embeddings.service import EmbeddingService
    scanner = RepositoryScanner()
    files = scanner.scan(root)

    if not files:
        typer.secho("No supported files found.", fg=typer.colors.YELLOW)
        return

    db = SessionLocal()

    try:
        embeddings = EmbeddingService()

        session = WorkspaceSession(
            id=uuid.uuid4(),
            repo_name=root.name,
            root_path=str(root),
            embedding_model=embeddings.model_name,
        )

        db.add(session)
        db.commit()

        metadata = SessionMetadata(
            session_id=session.id,
            repo_name=root.name,
            root_path=str(root),
            embedding_model=embeddings.model_name,
        )

        WorkspaceSessionManager.create(root, metadata)

        typer.secho(
            f"Found {len(files)} supported files\n",
            fg=typer.colors.GREEN,
        )

        ingest = IngestApplication(db)

        chunks = []
        indexed = 0

        for i, file in enumerate(files, start=1):
            typer.echo(
                f"[{i}/{len(files)}] {file.relative_path}",
                nl=False,
            )

            try:
                created = await ingest.ingest_local_file(
                    absolute_path=file.absolute_path,
                    relative_path=file.relative_path,
                    repo_name=root.name,
                    session_id=session.id,
                )

                chunks.extend(created)
                indexed += 1

                typer.secho("  ✓", fg=typer.colors.GREEN)

            except Exception as e:
                db.rollback()
                typer.secho(f"  ✗ {e}", fg=typer.colors.RED)

        typer.echo()
        typer.secho("Generating embeddings...", fg=typer.colors.BLUE)

        if chunks:
            vectors = embeddings.embed_batch([c.text for c in chunks])

            for chunk, vector in zip(chunks, vectors):
                chunk.embedding = vector
                chunk.embedding_status = ProcessingStatus.completed

            db.commit()

            typer.secho(
                f"Embedded {len(chunks)} chunks ✓",
                fg=typer.colors.GREEN,
            )

        typer.echo()
        typer.secho("Workspace initialized!", fg=typer.colors.GREEN, bold=True)
        typer.echo(f"Repository : {root.name}")
        typer.echo(f"Documents  : {indexed}")
        typer.echo(f"Chunks     : {len(chunks)}")

    finally:
        db.close()


# ---------------------------------------------------------------------
# ASK
# ---------------------------------------------------------------------

@app.command()
def ask(
    query: str,
    k: int = 10,
    model: str = "gpt-5",
):
    """Ask questions about the current workspace."""

    from app.core.workspace.discovery import find_workspace_root
    from app.core.workspace.session import WorkspaceSessionManager
    from app.db.database import SessionLocal
    from app.embeddings.service import EmbeddingService
    from app.services.vector_search import VectorSearchService
    from app.retrieval.assembler import ContextAssembler
    from app.llm.factory import get_llm_provider

    import asyncio

    root = find_workspace_root()

    if root is None:
        typer.secho(
            "Not inside an Atlas workspace. Run `atlas init` first.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    metadata = WorkspaceSessionManager.load(root)
    db = SessionLocal()

    try:
        # 1. Retrieve relevant chunks
        search = VectorSearchService(db, EmbeddingService())

        chunks = search.search(
            query=query,
            session_id=metadata.session_id,
            k=k,
        )

        if not chunks:
            typer.secho("No matching chunks found.", fg=typer.colors.YELLOW)
            return

        # 2. Assemble LLM context
        assembler = ContextAssembler()
        messages, sources = assembler.build(query, chunks)

        # 3. Generate answer
        provider = get_llm_provider()

        typer.echo()
        typer.secho(f'Question: "{query}"', bold=True)
        typer.secho("Thinking...\n", fg=typer.colors.BLUE)

        answer = asyncio.run(
            provider.generate(
                messages=messages,
                model=model,
            )
        )

        # 4. Render output
        typer.echo(answer)
        typer.echo()

        typer.secho("Sources", bold=True, fg=typer.colors.GREEN)
        typer.echo("-" * 40)

        for src in sources:
            typer.echo(
                f"[{src.id}] {src.file_path}:{src.start_line}-{src.end_line}"
            )

    finally:
        db.close()
# ---------------------------------------------------------------------
# STATUS
# ---------------------------------------------------------------------

@app.command()
def status():
    from app.core.workspace.discovery import find_workspace_root
    from app.core.workspace.session import WorkspaceSessionManager
    from app.db.database import SessionLocal
    from app.db.models import WorkspaceSession
    """
    Show information about the current workspace.
    """

    root = find_workspace_root()

    if root is None:
        typer.secho("No Atlas workspace found.", fg=typer.colors.RED)
        raise typer.Exit(1)

    metadata = WorkspaceSessionManager.load(root)

    db = SessionLocal()

    try:
        session = db.get(WorkspaceSession, metadata.session_id)

        if session is None:
            typer.secho(
                "Workspace metadata exists but database session is missing.",
                fg=typer.colors.RED,
            )
            return

        typer.secho("Atlas Workspace", bold=True)
        typer.echo(f"Repository : {session.repo_name}")
        typer.echo(f"Root       : {session.root_path}")
        typer.echo(f"Model      : {session.embedding_model}")
        typer.echo(f"Session ID : {session.id}")

    finally:
        db.close()


# ---------------------------------------------------------------------
# CLEAN
# ---------------------------------------------------------------------

@app.command()
    
def clean(stale: bool = typer.Option(False, "--stale", help="Remove all stale workspaces")):
    from sqlalchemy import delete
    from app.core.workspace.discovery import find_workspace_root
    from app.core.workspace.session import WorkspaceSessionManager
    from app.db.database import SessionLocal
    from app.db.models import WorkspaceSession
    """
    Delete the current workspace or stale workspaces.
    """

    db = SessionLocal()

    try:
        if stale:
            count = db.query(WorkspaceSession).delete()
            db.commit()

            typer.secho(
                f"Removed {count} stale workspace(s).",
                fg=typer.colors.GREEN,
            )
            return

        root = find_workspace_root()

        if root is None:
            typer.secho("No Atlas workspace found.", fg=typer.colors.RED)
            raise typer.Exit(1)

        metadata = WorkspaceSessionManager.load(root)

        db.execute(
            delete(WorkspaceSession).where(
                WorkspaceSession.id == metadata.session_id
            )
        )
        db.commit()

        WorkspaceSessionManager.delete(root)

        typer.secho(
            "Workspace cleaned successfully.",
            fg=typer.colors.GREEN,
        )

    finally:
        db.close()


if __name__ == "__main__":
    app()