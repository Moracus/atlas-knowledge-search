# Ingestion Pipeline Notes

> Purpose: Record the architectural decisions behind Atlas' ingestion pipeline, the tradeoffs made, and the limitations of the current V0 implementation.

---

# Goal

The ingestion pipeline is responsible for converting uploaded developer knowledge into a normalized plain-text representation that later stages (chunking, embeddings, retrieval) can consume.

Current supported inputs:

- PDF
- Markdown
- TXT
- Source code (`.py`, `.js`, `.ts`, `.c`, `.cpp`, `.java`, etc.)

The output of ingestion is **plain text + metadata**, not embeddings.

---

# Pipeline Architecture

Upload API
        │
        ▼
Store original file
        │
        ▼
Create Job (queued)
        │
        ▼
ARQ Worker
        │
        ▼
IngestionService
        │
        ├── Detect file type
        ├── Extract plain text
        ├── Save extracted text
        └── Return metadata
        │
        ▼
Update Document + Job status

The worker orchestrates the process.

The ingestion service performs the transformation.

---

# Design Decisions

## 1. ARQ Worker is an orchestrator

**Decision:** Keep business logic out of the worker.

The worker should only:

- Fetch the Job
- Fetch the Document
- Update statuses
- Call services
- Commit database changes

It should **not** contain parsing or extraction logic.

Reason:

- Easier testing
- Reusable services
- Cleaner separation of concerns

---

## 2. IngestionService does NOT access the database

**Decision:** The service receives only the data it needs (document ID, storage path), not a database session.

Avoid:

```python
IngestionService(document_id)
```

where the service creates its own DB session.

Prefer:

```python
result = await ingestion.ingest(
    document_id=doc.id,
    storage_path=doc.storage_path
)
```

Reason:

- Single transaction owned by worker
- No nested SQLAlchemy sessions
- Service becomes framework-independent
- Easy unit testing

---

## 3. Extracted text is stored as a file, not inside Postgres

### Rejected approach

Store the entire extracted text inside a `TEXT` column.

Problems:

- Large database size
- Slower backups
- Mixing metadata with document blobs
- Harder migration to object storage

### Chosen approach

```
storage/
├── uploads/
│   └── <document_id>.pdf
└── extracted/
    └── <document_id>.txt
```

Database stores only:

```python
storage_path
extracted_path
```

Reason:

- Local filesystem works for development
- Same schema works with S3/R2/MinIO later
- Chunker can reread extracted text without reparsing PDFs

---

## 4. Use PyMuPDF instead of pymupdf4llm

### Why not pymupdf4llm?

`pymupdf4llm` is optimized for producing Markdown specifically for LLM prompts.

Atlas is **not** trying to generate prompt-ready documents.

Its goal is to build its own structure-aware retrieval pipeline.

### Chosen library

- PyMuPDF (`fitz`)

Reason:

- Lower-level API
- Faster
- Access to pages and metadata
- Doesn't impose its own formatting decisions

The parser should remain dumb; Atlas owns the intelligence later.

---

## 5. Normalize every document into plain text

Regardless of input:

| Input | Output |
|---------|--------|
| PDF | Plain text |
| Markdown | Plain text |
| Python | Plain text |
| C++ | Plain text |
| JSON | Plain text |

This gives every later pipeline stage a consistent interface.

Future structural parsing (Tree-sitter) will happen **after** ingestion.

---

# Current Responsibilities

## Worker

- Queue execution
- Status updates
- Error handling
- Database commits

## IngestionService

- Detect file type
- Extract text
- Save `.txt`
- Return extraction result

## Repository

- Database queries only

---

# Current Limitations (V0)

- No OCR for scanned PDFs
- No DOCX support
- No HTML parsing beyond raw text
- No syntax-aware code parsing
- No image extraction
- No tables or layout preservation
- No chunk generation yet

These are intentionally deferred.

---

# Future Evolution

Current:

PDF
 ↓
Text Extraction
 ↓
Save .txt

V1:

PDF
 ↓
Text Extraction
 ↓
Structure-aware Chunking
 ↓
Embeddings
 ↓
pgvector

The ingestion layer should remain unchanged even as indexing evolves.

---

# Guiding Principle

> **Ingestion converts files into normalized text. Retrieval intelligence belongs in later layers, not inside the parser.**