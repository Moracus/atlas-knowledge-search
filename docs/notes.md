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


## 2. Chunkers return data, not database models

Rejected:

```python
PythonChunker(db).chunk(...)
```

Chosen:

```python
chunks = PythonChunker().chunk(...)
```

Every chunker returns a list of `ChunkData` objects, which are pure domain models.

The orchestration layer (`IngestApplication`) is responsible for converting them into SQLAlchemy `Chunk` models and persisting them.

**Reason:**

- Easier unit testing
- Reusable from CLI and HTTP
- No nested database sessions
- Chunkers remain framework-independent

---

## 3. Structure over fixed-size chunks

Atlas does **not** chunk by token count.

Primary semantic boundaries are:

- imports
- classes
- functions
- methods

Current implementation uses **Tree-sitter** to extract these structural nodes rather than arbitrary line ranges.

Example:

```python
class AuthService:
    def login(self):
        ...
```

Produces two retrieval units:

- `class → AuthService`
- `method → AuthService.login`

This preserves both architectural and implementation context.

Recursive splitting for oversized functions is intentionally deferred.

---

## 4. Multi-language AST support

V0 supports two programming languages using Tree-sitter:

| Language | Parser |
|----------|--------|
| Python | `tree-sitter-python` |
| JavaScript | `tree-sitter-javascript` |

Language selection is centralized through:

```python
BaseChunker.detect_language(file_path)
```

The `ChunkingService` acts as the dispatcher:

```
.py  → PythonChunker
.js  → JavaScriptChunker
```

This keeps callers completely unaware of parser implementations and makes adding future languages (TypeScript, Go, Rust) a one-line registration.

---

# CLI vs HTTP Ingestion Pipelines

Atlas now has **two entrypoints** that share the exact same indexing pipeline.

## CLI (Repository Ingestion)

```
atlas ingest ./my-repo
        │
        ▼
RepositoryScanner
        │
        ▼
IngestApplication.ingest_local_file()
        │
        ▼
Copy → storage/uploads
        │
        ▼
IngestionService
        │
        ▼
ChunkingService
        │
        ▼
Persist Document + Chunks
```

The scanner recursively discovers supported files and preserves their **repository-relative paths**.

Example:

```
src/auth/service.py
```

becomes the canonical path stored in the database.

---

## HTTP (Single File Upload)

```
UploadFile
     │
     ▼
save_document()
     │
     ▼
Create pending Document + Job
     │
     ▼
ARQ Worker
     │
     ▼
IngestApplication.ingest_existing_document()
     │
     ▼
IngestionService
     │
     ▼
ChunkingService
     │
     ▼
Persist Chunks
```

Unlike the CLI, HTTP does not have repository context.

For uploaded files:

```
relative_path = original filename
```

Example:

```
auth.py
```

The worker never performs scanning; it simply consumes the already-created `Document`.

---

# Relative Path Strategy

A new `relative_path` field exists on `Document`.

This is intentionally different from `storage_path`.

| Field | Purpose |
|--------|---------|
| `storage_path` | Internal Atlas filesystem location |
| `relative_path` | Original repository location used for retrieval and citations |

Example:

```
storage_path
storage/uploads/91ab3d.py

relative_path
src/auth/service.py
```

Chunk metadata always uses `relative_path`, never the storage location.

---

# Current Limitations

- Only Python and JavaScript are AST-supported.
- Markdown chunker is not implemented.
- Fallback chunker for unsupported languages is not implemented.
- Large functions/classes are not recursively split.
- Dependency extraction is still empty.
- Heading hierarchy exists in the schema but is unused until Markdown support.
- `.gitignore` is not respected yet by `RepositoryScanner`.
- CLI indexes repositories sequentially (no parallel workers).

---

# Future Improvements

## Background enrichment

Chunk creation intentionally finishes **before** any AI processing.

Future asynchronous pipeline:

```
Chunk
 │
 ├── Embedding Worker
 │      ↓
 │   pgvector
 │
 └── Summary Worker
        ↓
   LLM summary
```

Both update existing chunk rows without blocking ingestion.

---

## Markdown Chunker

Markdown should become a first-class structural parser.

Planned metadata:

- heading hierarchy
- section boundaries
- start/end lines
- heading-based chunk types

This will allow documentation retrieval to behave similarly to code retrieval.

---

## Repository Discovery

`RepositoryScanner` is intentionally minimal in V0.

Planned additions:

- `.gitignore` support
- configurable ignore patterns
- binary file detection
- parallel file discovery
- language statistics during indexing

---

# Guiding Principle

> **Chunking identifies semantic units. Embeddings, summaries, and retrieval intelligence enrich those units later, but should never be required to create them.**