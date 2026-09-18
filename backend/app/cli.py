import asyncio
from pathlib import Path

import typer
from sqlalchemy import select

from app.application.ingest import IngestApplication
from app.core.discovery.scanner import RepositoryScanner
from app.db.database import SessionLocal
from app.db.models import Chunk
from app.db.models import ProcessingStatus
from app.embeddings.service import EmbeddingService
from app.services.vector_search import VectorSearchService

app = typer.Typer(
    help="Atlas CLI - Structure-aware repository indexing"
)


@app.command()
def ingest(repo: str):
    """Index an entire repository into Atlas."""

    repo_path = Path(repo).resolve()

    if not repo_path.exists():
        typer.secho("Repository does not exist.", fg=typer.colors.RED)
        raise typer.Exit(1)

    if not repo_path.is_dir():
        typer.secho("Path must be a directory.", fg=typer.colors.RED)
        raise typer.Exit(1)

    asyncio.run(_ingest_repo(repo_path))


@app.command()
def ask(query: str, k: int = 5):
    """Semantic search over indexed chunks."""

    db = SessionLocal()

    try:
        embeddings = EmbeddingService()
        search = VectorSearchService(db, embeddings)

        results = search.search(query, k)

        if not results:
            typer.secho("No matching chunks found.", fg=typer.colors.YELLOW)
            return

        typer.echo()
        typer.secho(f'Query: "{query}"', bold=True)
        typer.echo()

        for i, chunk in enumerate(results, start=1):
            typer.secho(
                f"[{i}] {chunk.file_path}:{chunk.start_line}-{chunk.end_line}",
                fg=typer.colors.CYAN,
            )
            typer.echo(chunk.text[:300].strip())
            typer.echo("-" * 60)

    finally:
        db.close()


async def _ingest_repo(repo_path: Path):
    scanner = RepositoryScanner()
    files = scanner.scan(repo_path)

    if not files:
        typer.secho("No supported files found.", fg=typer.colors.YELLOW)
        return

    typer.secho(
        f"Found {len(files)} supported files\n",
        fg=typer.colors.GREEN,
    )

    db = SessionLocal()
    ingest_app = IngestApplication(db)

    indexed = 0
    chunks =[]

    try:
        # -------- Chunking pipeline --------
        for i, file in enumerate(files, start=1):
            typer.echo(
                f"[{i}/{len(files)}] {file.relative_path}",
                nl=False,
            )

            try:
                created_chunks=await ingest_app.ingest_local_file(
                    absolute_path=file.absolute_path,
                    relative_path=file.relative_path,
                    repo_name=repo_path.name,
                )
                chunks.extend(created_chunks)

                indexed += 1
                typer.secho("  ✓", fg=typer.colors.GREEN)

            except Exception as e:
                db.rollback()
                typer.secho(f"  ✗ {e}", fg=typer.colors.RED)

        # -------- Embedding pipeline --------
        typer.echo()
        typer.secho("Generating embeddings...", fg=typer.colors.BLUE)

        embedding_service = EmbeddingService()

        if chunks:
            vectors = embedding_service.embed_batch(
                [chunk.text for chunk in chunks]
            )

            for chunk, vector in zip(chunks, vectors):
                chunk.embedding = vector
                chunk.embedding_status = ProcessingStatus.completed

            db.commit()

            typer.secho(
                f"Embedded {len(chunks)} chunks ✓",
                fg=typer.colors.GREEN,
            )
        else:
            typer.secho("No pending chunks to embed.", fg=typer.colors.YELLOW)

        typer.echo()
        typer.secho("Indexing complete!", fg=typer.colors.GREEN, bold=True)
        typer.echo(f"Repository : {repo_path.name}")
        typer.echo(f"Documents  : {indexed}/{len(files)}")
        typer.echo(f"Chunks     : {len(chunks)}")

    finally:
        db.close()


if __name__ == "__main__":
    app()