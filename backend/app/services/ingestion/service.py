from pathlib import Path
import mimetypes
import pymupdf  # PyMuPDF
from uuid import UUID
from app.db.models import Document
from dataclasses import dataclass
from app.core.config import settings

TEXT_EXTENSIONS = {
    ".txt", ".md",
    ".py", ".js", ".ts",
    ".cpp", ".c", ".hpp", ".h",
    ".java", ".go", ".rs",
    ".html", ".css", ".json",
    ".yml", ".yaml", ".xml",".jsx"
}

@dataclass
class ExtractionResult:
    path:str
    characters: int
    text : str


class IngestionService:

    async def ingest(self, file_path: str, document_id: str) -> ExtractionResult:
        path = Path(file_path)

        file_type = self.detect_type(path)

        if file_type == "pdf":
            text = self.extract_pdf(path)
        elif file_type == "text":
            text = self.extract_text(path)
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

        output_dir = Path(settings.storage_dir).expanduser() / "extracted"
        output_dir.mkdir(parents=True, exist_ok=True)

        output = output_dir / f"{document_id}.txt"
        output.write_text(text, encoding="utf-8")

        return ExtractionResult(path=str(output), characters=len(text), text=text)

    def detect_type(self, path: Path) -> str:
        if path.suffix.lower() == ".pdf":
            return "pdf"

        if path.suffix.lower() in TEXT_EXTENSIONS:
            return "text"

        mime, _ = mimetypes.guess_type(path)

        if mime and mime.startswith("text"):
            return "text"

        raise ValueError("Unknown document type")

    def extract_text(self, path: Path) -> str:
        """Pure extraction. Used by CLI and worker."""
        return path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

    def extract_pdf(self, path: Path) -> str:
        doc = pymupdf.open(path)

        pages = []

        for page in doc:
            pages.append(page.get_text())

        doc.close()

        return "\n".join(pages)