from pathlib import Path
import mimetypes
import pymupdf  # PyMuPDF
from uuid import UUID
from app.db.models import Document
from dataclasses import dataclass

TEXT_EXTENSIONS = {
    ".txt", ".md",
    ".py", ".js", ".ts",
    ".cpp", ".c", ".hpp", ".h",
    ".java", ".go", ".rs",
    ".html", ".css", ".json",
    ".yml", ".yaml", ".xml"
}

@dataclass
class ExtractionResult:
    path:str
    characters: int


class IngestionService:

    async def ingest(self, file_path: str,document_id:str) -> str:
        path = Path(file_path)

        file_type = self.detect_type(path)

        if file_type == "pdf":
            text = self.extract_pdf(path)

        elif file_type == "text":
            text = self.extract_text(path)

        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

        

        output = f"storage/extracted/{document_id}.txt"

        Path(output).write_text(text, encoding="utf-8")


        # Later -> save into chunks / embeddings
        # print("=" * 50)
        # print(text[:1500])
        # print("=" * 50)

        # return text

        return ExtractionResult(path=output,characters=len(text))

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