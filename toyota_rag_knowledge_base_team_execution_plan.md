# Toyota Knowledge Base: RAG Ingestion Pipeline & Architecture Blueprint

This document specifies the technical architecture, data contracts, and task allocations for the Toyota Knowledge Base RAG (Retrieval-Augmented Generation) system.

---

## 1. Project Overview & Technical Stack

The objective of this project is to parse, sanitize, chunk, vectorize, and ingest three foundational literary sources on the Toyota Production System (TPS) and Lean Management into a local **Qdrant** vector database using **FastEmbed**.

### Core Technical Stack
* **Language & Runtime:** Python 3.10+ managed via `uv`
* **Vector Database:** `qdrant-client` (embedded local storage mode at `data/qdrant_storage/`)
* **Embedding Engine:** `fastembed` (`BAAI/bge-small-en-v1.5`, 384 dimensions, cosine distance)
* **Text Processing & Chunking:** `pypdf`, `langchain-text-splitters`
* **Data Validation & Schemas:** `pydantic`, `pydantic-settings`

---

## 2. Source Material Analysis

The raw data consists of three PDF documents residing in `data/raw/`:

| File Name | Pages | Author / Nature | Structural Characteristics & Parsing Challenges |
|---|---|---|---|
| `mcgraw-hill-thetoyotaway-14managementprinciples.pdf` | 366 | Jeffrey K. Liker | Full-length academic/industrial narrative. Contains recurring artifacts from conversion tools: `Document2PDF Pilot` watermark, `Team LiB` headers, and `PREVIOUS / NEXT` navigation tags. |
| `toyota-production-system-beyond-large-scale-production.pdf` | 195 | Taiichi Ohno | Primary historical source. Compact, philosophical, and terminology-dense (*Muda*, *Muri*, *Mura*, *Kanban*, *Jidoka*, *Heijunka*). Contains an essential terminal glossary (pp. 121–130) that must be preserved as high-precision definitional chunks. |
| `thetoyotaway.pdf` | 131 | Jeffrey K. Liker (Executive Summary) | Slide deck / executive brief. Not a linear narrative book. Each page is an isolated topical slide (diagrams, quotes, 14-principle summaries). Must **not** be split using standard sliding text windows. |

---

## 3. Directory Layout & Module Responsibilities

```text
toyota-rag/
├── data/
│   ├── raw/                  # Place the 3 raw PDF files here
│   └── qdrant_storage/       # Embedded Qdrant database records (gitignored)
├── src/
│   └── toyota_rag/
│       ├── __init__.py       # Package marker
│       ├── config.py         # Global settings (Pydantic BaseSettings)
│       ├── models.py         # Central data contracts (DocumentPage, TextChunk, SearchResult)
│       ├── parser.py         # Text extraction and regex artifact cleansing
│       ├── chunker.py        # Adaptive chunking and metadata enrichment
│       ├── embeddings.py     # Embedding abstractions and FastEmbed service
│       ├── vector_store.py   # Qdrant client, schema management, upsert, and search
│       └── pipeline.py       # Orchestrator integrating all components
├── tests/
│   ├── test_parser.py
│   ├── test_chunker.py
│   └── test_search.py
├── main.py                   # CLI entry point (ingest, inspect, search)
├── pyproject.toml
└── TEAM_EXECUTION_PLAN.md
```

---

## 4. Shared Data Contracts (`src/toyota_rag/models.py`)

All team members must conform strictly to these immutable schema definitions:

```python
from typing import Dict, Any
from pydantic import BaseModel, Field


class DocumentPage(BaseModel):
    """Raw parsed page before text chunking."""

    text: str = Field(
        ..., description="Sanitized plain text extracted from a single page"
    )
    page_number: int = Field(
        ..., description="1-based page number within the source file"
    )
    book_title: str = Field(..., description="Canonical title of the source book")
    author: str = Field(..., description="Author of the source document")


class ChunkMetadata(BaseModel):
    """Metadata payload stored alongside each vector in Qdrant."""

    book_title: str
    author: str
    page_number: int
    chunk_index: int
    doc_type: str = Field("book", description="'book', 'slides', or 'glossary'")
    extra: Dict[str, Any] = Field(default_factory=dict)


class TextChunk(BaseModel):
    """Processed text slice prepared for embedding generation and upsertion."""

    content: str = Field(..., description="Text content sent to the embedding model")
    metadata: ChunkMetadata


class SearchResult(BaseModel):
    """Semantic query match returned from vector storage."""

    content: str
    score: float
    metadata: ChunkMetadata
```

---

## 5. Team Member Work Breakdown

```
                            [ models.py ]
                   (Shared Data Models & Schemas)
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
┌──────────────────┐                           ┌──────────────────┐
│  MEMBER 1 (DATA) │                           │   MEMBER 2 (NLP) │
│    parser.py     │                           │    chunker.py    │
│  - PDF parsing   │                           │  - Multi-strategy│
│  - Regex cleanup │                           │    chunking      │
│  - OCR/Doc clean │                           │  - Metadata tag  │
└────────┬─────────┘                           └────────┬─────────┘
         │ DocumentPage                                 │ TextChunk
         └───────────────────────┬──────────────────────┘
                                 ▼
                       ┌───────────────────┐
                       │   MEMBER 3 (DB)   │
                       │   embeddings.py   │
                       │  vector_store.py  │
                       │  - FastEmbed      │
                       │  - Qdrant Storage │
                       └─────────┬─────────┘
                                 │
                                 ▼
                       ┌───────────────────┐
                       │  MEMBER 4 (LEAD)  │
                       │    pipeline.py    │
                       │      main.py      │
                       │  - Orchestrator   │
                       │  - CLI & Testing  │
                       └───────────────────┘
```

---

### Member 1: Data Ingestion & Sanitization (`parser.py`)

* **Primary File:** `src/toyota_rag/parser.py`
* **Dependencies:** `pypdf`, `re`, `pathlib`
* **Input:** Raw PDF binaries in `data/raw/`
* **Output:** `List[DocumentPage]`

#### Detailed Tasks
1. **PDF Text Extraction:** Implement robust page-by-page extraction using `pypdf.PdfReader`. Gracefully handle blank, unreadable, or image-only pages.
2. **Regex Cleaning Engine:** Implement `clean_text(text: str) -> str` targeting specific artifacts found in our three files:
   * **Watermarks:** Strip `r"This document is created with the unregistered version of Document2PDF Pilot\."`
   * **Colophon & Navigational Noise:** Strip `r"Team LiB"`, `r"(?:4\s*)?PREVIOUS\s+NEXT>?"`, and standalone page trackers.
   * **Hyphenation Repair:** De-hyphenate words broken across line wraps: transform `r"(\b\w+)-\n(\w+\b)"` into `\1\2` (e.g., `"stan-\ndardization"` $\to$ `"standardization"`).
   * **Whitespace Normalization:** Collapse multiple spaces, non-breaking spaces (`\xa0`), and excessive consecutive blank lines (`\n{3,}` $\to$ `\n\n`).
3. **Slide Deck Extraction Strategy:** Build a dedicated branch for `thetoyotaway.pdf`. Keep slide title, bullet points, and speaker notes coherent within a single string without destroying list layouts.
4. **Glossary Extraction Strategy:** Detect the terminal glossary section in Ohno's book (pages 121–130) and tag these pages with `doc_type="glossary"` in the metadata.

#### Interface to Implement
```python
class DocumentParser:
    def __init__(self): ...

    def clean_text(self, text: str) -> str: ...

    def parse_pdf(
        self, file_path: Path, book_title: str, author: str, is_slide_deck: bool = False
    ) -> List[DocumentPage]: ...
```

#### Definition of Done (DoD)
* Unit tests demonstrate that zero instances of `Document2PDF Pilot` or `Team LiB` remain in the extracted pages.
* No words remain broken by soft hyphens across line endings.
* `parser.parse_pdf(...)` runs completely on all three PDFs without memory leaks or unhandled exceptions.

---

### Member 2: Chunking Strategy & Metadata Architecture (`chunker.py`)

* **Primary File:** `src/toyota_rag/chunker.py`
* **Dependencies:** `langchain-text-splitters`, `src/toyota_rag/models.py`, `src/toyota_rag/config.py`
* **Input:** `List[DocumentPage]`
* **Output:** `List[TextChunk]`

#### Detailed Tasks
1. **Dynamic Chunking per Document Modality:**
   * **Narrative Books (Liker's *The Toyota Way*):** Use `RecursiveCharacterTextSplitter` with `chunk_size=1200` characters, `chunk_overlap=150`, and separators `["\n\n", "\n", ". ", " "]`.
   * **Aphoristic Text (Ohno's *Toyota Production System*):** Use smaller chunk bounds: `chunk_size=800` characters, `chunk_overlap=100`, because Ohno's arguments are concise and shifts in topic happen quickly.
   * **Slide Deck (`thetoyotaway.pdf`):** Do **not** use character splitting across slide boundaries. Each page represents one complete conceptual card. Generate exactly **1 chunk per slide** (`chunk_overlap=0`).
   * **Glossary Section (Ohno pp. 121–130):** Split by individual term entries (e.g., `► Andon`, `► Autonomation`, `► Kanban`) so each term's definition is encapsulated inside its own chunk.
2. **Contextual Enrichment:** Prepend a structured header to every chunk before it is saved into `TextChunk.content`. This provides explicit semantic ground for dense vector retrieval:
   ```text
   [Source: The Toyota Way | Author: Jeffrey K. Liker | Page: 45]
   <sanitized chunk text>
   ```
3. **Metadata Index Tracking:** Maintain deterministic global and per-book integer counters (`chunk_index`), ensuring every point in the vector store can be mapped back to its exact origin.

#### Interface to Implement
```python
class TextChunker:
    def __init__(self, default_chunk_size: int = 1200, default_overlap: int = 150): ...

    def split_pages(self, pages: List[DocumentPage]) -> List[TextChunk]: ...

    def _split_narrative(
        self, pages: List[DocumentPage], size: int, overlap: int
    ) -> List[TextChunk]: ...

    def _split_slides(self, pages: List[DocumentPage]) -> List[TextChunk]: ...

    def _split_glossary(self, pages: List[DocumentPage]) -> List[TextChunk]: ...
```

#### Definition of Done (DoD)
* Chunks never truncate sentences midway when splitting narrative text.
* Slide pages are preserved as atomic units (1 slide = 1 chunk).
* All resulting chunks include the contextual header prefix and properly populated `ChunkMetadata`.

---

### Member 3: Embeddings & Vector Database Client (`embeddings.py`, `vector_store.py`)

* **Primary Files:** `src/toyota_rag/embeddings.py`, `src/toyota_rag/vector_store.py`
* **Dependencies:** `fastembed`, `qdrant-client`, `src/toyota_rag/models.py`, `src/toyota_rag/config.py`
* **Input:** `List[TextChunk]`
* **Output:** Persisted Qdrant collection, `search()` returning `List[SearchResult]`

#### Detailed Tasks
1. **Embedding Layer (`embeddings.py`):**
   * Encapsulate `fastembed.TextEmbedding` using the `BAAI/bge-small-en-v1.5` model (produces 384-dimensional dense vectors).
   * Implement batch processing: `embed_texts(texts: List[str], batch_size: int = 64) -> List[List[float]]`.
   * Implement single query vector generation: `embed_query(query: str) -> List[float]`.
2. **Vector Store Integration (`vector_store.py`):**
   * Initialize a local embedded `QdrantClient(path=settings.QDRANT_STORAGE_DIR)`.
   * Implement `ensure_collection(vector_size: int = 384)`: check if the collection exists; if not, initialize it with `Distance.COSINE`.
   * Implement `upsert_chunks(chunks: List[TextChunk], vectors: List[List[float]], batch_size: int = 128)`:
     * Generate continuous integer IDs or valid deterministic UUIDs for each point.
     * Attach full chunk metadata + the raw text content inside the Qdrant point `payload`.
     * Execute batch upserts to avoid client timeout or memory pressure.
   * Implement `search(query_vector: List[float], limit: int = 5, score_threshold: float = 0.5) -> List[SearchResult]`:
     * Execute Qdrant vector search.
     * Deserialize matches into `SearchResult` instances containing text, similarity score, and metadata.

#### Interfaces to Implement
```python
# embeddings.py
class BaseEmbeddingService(ABC):
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]: ...
    @abstractmethod
    def embed_query(self, query: str) -> List[float]: ...


class FastEmbedService(BaseEmbeddingService):
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"): ...


# vector_store.py
class QdrantVectorStore:
    def __init__(self, storage_path: Path, collection_name: str): ...

    def ensure_collection(self, vector_size: int = 384) -> None: ...

    def upsert_chunks(
        self, chunks: List[TextChunk], vectors: List[List[float]], batch_size: int = 128
    ) -> None: ...

    def search(
        self, query_vector: List[float], limit: int = 5, score_threshold: float = 0.5
    ) -> List[SearchResult]: ...
```

#### Definition of Done (DoD)
* Embedded database initializes locally at `data/qdrant_storage/` without requiring Docker or network daemons.
* Vectorizing 3,000 chunks completes in under 2 minutes on standard CPU hardware.
* A basic semantic test query returns valid cosine scores ($0.0 \le \text{score} \le 1.0$) with correct payloads.

---

### Member 4: Pipeline Orchestrator, CLI & Quality Validation (`pipeline.py`, `main.py`)

* **Primary Files:** `src/toyota_rag/pipeline.py`, `main.py`
* **Dependencies:** All previous modules (`parser`, `chunker`, `embeddings`, `vector_store`)
* **Input:** Raw document paths, CLI commands, test queries
* **Output:** End-to-end operational pipeline, evaluation benchmark report

#### Detailed Tasks
1. **Pipeline Execution Logic (`pipeline.py`):**
   * Wire the flow: `PDF Files` $\to$ `DocumentParser` $\to$ `TextChunker` $\to$ `FastEmbedService` $\to$ `QdrantVectorStore`.
   * Add step-by-step progress logging (number of pages extracted, chunks produced, vectors generated, points stored).
   * Implement a registry dictionary defining the 3 source books:
     ```python
     BOOKS_REGISTRY = [
         {
             "file": "mcgraw-hill-thetoyotaway-14managementprinciples.pdf",
             "title": "The Toyota Way: 14 Management Principles",
             "author": "Jeffrey K. Liker",
             "is_slides": False,
         },
         {
             "file": "toyota-production-system-beyond-large-scale-production.pdf",
             "title": "Toyota Production System: Beyond Large-Scale Production",
             "author": "Taiichi Ohno",
             "is_slides": False,
         },
         {
             "file": "thetoyotaway.pdf",
             "title": "The Toyota Way - Executive Summary",
             "author": "Jeffrey K. Liker",
             "is_slides": True,
         },
     ]
     ```
2. **Command Line Interface (`main.py`):**
   * `uv run python main.py ingest --all`: Trigger ingestion for all 3 documents.
   * `uv run python main.py search --query "..." --limit 5`: Run interactive vector queries and pretty-print the results with source citations.
   * `uv run python main.py stats`: Print total points stored, collection health, and storage footprint.
3. **RAG Quality Benchmark Suite:** Verify retrieval accuracy against 5 domain-specific test queries:
   * `"What are the 8 types of waste identified by Toyota?"`
   * `"Explain the difference between labor saving and worker saving according to Taiichi Ohno."`
   * `"How did Chief Engineer Uchiyamada utilize the Obeya system during the development of the Prius?"`
   * `"What is the five why method and what was the machine stoppage example?"`
   * `"What is Heijunka and why does leveling production come before pull systems?"`

#### Definition of Done (DoD)
* Running `python main.py ingest --all` ingests all three books from scratch without manual intervention.
* Each benchmark query retrieves relevant paragraphs with semantic similarity $\ge 0.70$ and displays correct page numbers and book titles.

---

## 6. Execution Timeline & Milestones

| Stage | Duration | Primary Focus | Critical Deliverable |
|---|---|---|---|
| **Phase 1** | Days 1–2 | Contracts & Dependencies | `models.py` and `config.py` committed; all dependencies locked in `pyproject.toml`. |
| **Phase 2** | Days 3–4 | Component Development | `parser.py` cleans all 3 PDFs; `chunker.py` handles books vs. slides; `vector_store.py` passes mock upsert tests. |
| **Phase 3** | Day 5 | Pipeline Integration | `pipeline.py` runs end-to-end on 1 book; vector generation throughput verified. |
| **Phase 4** | Day 6 | Full Ingestion & Benchmarking | All 3 documents indexed in local Qdrant; CLI commands finalized. |
| **Phase 5** | Day 7 | Quality Assurance & PR Merge | Benchmark queries evaluated; documentation updated; codebase finalized. |

---

## 7. Git Workflow & Collaboration Rules

1. **Branching Strategy:**
   * `feature/parser-cleaning` (Member 1)
   * `feature/chunking-strategy` (Member 2)
   * `feature/vector-store-fastembed` (Member 3)
   * `feature/pipeline-cli` (Member 4)
2. **Pull Request Protocol:**
   * Every PR must include unit tests for its respective module.
   * Do not commit local database files (`data/qdrant_storage/`) or large PDF binaries into Git history.
   * Code formatting: run `uv run ruff format .` and `uv run ruff check .` before pushing.