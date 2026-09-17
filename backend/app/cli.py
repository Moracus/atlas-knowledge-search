import typer
from pathlib import Path

from app.services.chunking.service import ChunkingService
from app.services.ingestion.service import IngestionService

app = typer.Typer()

@app.command()
def ingest(path: str):
    print("=="*50)
    print(path)
    file = Path(path)
    print(file)

    if not file.exists():
        typer.echo("File not found.")
        raise typer.Exit(1)

    ingestion = IngestionService()
    chunker = ChunkingService()

    text = ingestion.extract_text(file)

    chunks = chunker.chunk_file(
        text=text,
        file_path=str(file),
    )

    typer.echo(f"\nGenerated {len(chunks)} chunks\n")

    for i, chunk in enumerate(chunks):
        typer.echo("=" * 60)
        typer.echo(f"[{i}] {chunk.chunk_type}")
        typer.echo(f"Name : {chunk.name}")
        typer.echo(f"Lines: {chunk.start_line}-{chunk.end_line}")
        typer.echo("-" * 60)
        typer.echo(chunk.text)
        typer.echo()

if __name__ == "__main__":
    app()