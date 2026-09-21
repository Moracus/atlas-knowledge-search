# Atlas

> Open-source, self-hostable RAG backend for developer knowledge.

Atlas indexes code and documentation using structure-aware chunking, stores embeddings in PostgreSQL + pgvector, and retrieves the minimum relevant context for cloud LLMs. Repositories stay local—only retrieved context is sent to the LLM.

> **Current status:** V0 focuses entirely on the CLI workflow.

---

## Features

- Structure-aware chunking (Python + JavaScript via Tree-sitter)
- Markdown and text document ingestion
- Local repository indexing
- Batch embedding pipeline
- Semantic vector search with pgvector
- OpenAI-compatible LLM providers
- Workspace-based indexing (`.atlas/session.json`)

---

## Architecture

```text
              Local Repository
                     │
                     ▼
            Repository Scanner
                     │
                     ▼
        Tree-sitter / Text Chunkers
                     │
                     ▼
                Chunk Objects
                     │
                     ▼
         PostgreSQL + pgvector
                     │
                     ▼
            Vector Similarity Search
                     │
                     ▼
          Retrieved Context + Citations
                     │
                     ▼
                 Cloud LLM
```

---

## Tech Stack

| Layer | Technology |
|--------|------------|
| Language | Python 3.12 |
| CLI | Typer |
| Database | PostgreSQL + pgvector |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Queue | Redis |
| Embeddings | Qwen3-Embedding-0.6B |
| Parsing | Tree-sitter |

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/atlas
cd atlas
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -e .
```

### 4. Start PostgreSQL

Only PostgreSQL and redis runs in Docker.

```bash
docker compose up -d
```

This starts a Postgres instance with the `pgvector` extension enabled.

### 5. Start Redis

Run Redis 

```bash
see step 4
```

### 6. Configure environment

Create a `.env` file:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/atlas
REDIS_URL=redis://localhost:6379

EMBEDDING_PROVIDER=qwen
LLM_PROVIDER=openai

OPENAI_API_KEY=your_key_here
```

### 7. Run migrations

```bash
alembic upgrade head
```

Atlas is now ready.

---

## CLI Workflow

```bash
# Initialize current repository
atlas init

# Ask questions about the indexed project
atlas ask "Where is authentication implemented?"

# View workspace status
atlas status

# Remove the current workspace index
atlas clean
```

Detailed command documentation will live in a separate document.

---

## Supported Files

### Code

- Python
- JavaScript

### Documents

- Markdown
- TXT
- PDF

Unsupported languages currently fall back to plain text ingestion (no AST chunking).

---

## How V0 Works

1. Scan the repository
2. Extract plain text where needed
3. Chunk files using Tree-sitter (when supported)
4. Store chunks and metadata
5. Generate embeddings in batches
6. Persist vectors to pgvector
7. Retrieve top-k chunks during `atlas ask`

Embeddings are generated **after** chunk creation, making chunking deterministic and independent of the embedding model.

---

## Current Limitations

V0 intentionally keeps the indexing pipeline simple.

- No incremental indexing
- No content hash tracking
- No duplicate chunk detection
- No reranking stage
- Python and JavaScript are the only AST-supported languages
- Markdown uses basic text chunking
- `.gitignore` is not respected during repository scanning
- Repository indexing is sequential

---

## Future Improvements

### Retrieval

- Incremental indexing via SHA-256 hashes
- Re-index only modified files
- Cross-encoder reranking
- Hybrid search (BM25 + vector)
- Metadata-aware retrieval

### Parsing

- TypeScript support
- Go / Rust parsers
- Rich Markdown hierarchy
- Dependency extraction
- Recursive splitting of oversized functions

### Developer Experience

- Background embedding workers
- Parallel repository indexing
- HTTP API
- VS Code extension
- Multiple embedding provider support

---

---

## Philosophy

Atlas separates the retrieval pipeline into independent layers:

- **Chunkers** identify semantic units.
- **Embeddings** make those units searchable.
- **Vector search** retrieves relevant context.
- **LLMs** generate answers from retrieved evidence.

The goal is not to send more context—it is to send **better context**.
