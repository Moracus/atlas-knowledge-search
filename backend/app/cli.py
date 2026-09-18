import asyncio
from pathlib import Path

import typer

from app.application.ingest import IngestApplication
from app.core.discovery.scanner import RepositoryScanner
from app.db.database import SessionLocal

app = typer.Typer(
    help="Atlas CLI - Structure-aware repository indexing"
)


@app.command()
def ingest(repo: str):
    """
    Index an entire repository into Atlas.
    """

    repo_path = Path(repo).resolve()

    if not repo_path.exists():
        typer.secho("Repository does not exist.", fg=typer.colors.RED)
        raise typer.Exit(1)

    if not repo_path.is_dir():
        typer.secho("Path must be a directory.", fg=typer.colors.RED)
        raise typer.Exit(1)

    asyncio.run(_ingest_repo(repo_path))


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

    try:
        for i, file in enumerate(files, start=1):
            typer.echo(
                f"[{i}/{len(files)}] {file.relative_path}",
                nl=False,
            )

            try:
                await ingest_app.ingest_local_file(
                    absolute_path=file.absolute_path,
                    relative_path=file.relative_path,
                    repo_name=repo_path.name,
                )

                indexed += 1
                typer.secho("  ✓", fg=typer.colors.GREEN)

            except Exception as e:
                db.rollback()
                typer.secho(f"  ✗ {e}", fg=typer.colors.RED)

        typer.echo()
        typer.secho("Indexing complete!", fg=typer.colors.GREEN, bold=True)
        typer.echo(f"Repository : {repo_path.name}")
        typer.echo(f"Documents  : {indexed}/{len(files)}")

    finally:
        db.close()


if __name__ == "__main__":
    app()