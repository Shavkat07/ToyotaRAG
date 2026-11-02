# src/toyota_rag/pipeline.py
import logging
import time
from pathlib import Path
from typing import Any

from toyota_rag.chunker import TextChunker
from toyota_rag.embeddings import BaseEmbeddingService, FastEmbedService
from toyota_rag.models import SearchResult
from toyota_rag.parser import DocumentParser
from toyota_rag.vector_store import QdrantVectorStore

logger = logging.getLogger(__name__)

BOOKS_REGISTRY = [
    {
        "file": "mcgraw-hill-thetoyotaway-14managementprinciples.pdf",
        "filename": "mcgraw-hill-thetoyotaway-14managementprinciples.pdf",
        "title": "The Toyota Way: 14 Management Principles",
        "author": "Jeffrey K. Liker",
        "is_slides": False,
    },
    {
        "file": "toyota-production-system-beyond-large-scale-production.pdf",
        "filename": "toyota-production-system-beyond-large-scale-production.pdf",
        "title": "Toyota Production System: Beyond Large-Scale Production",
        "author": "Taiichi Ohno",
        "is_slides": False,
    },
    {
        "file": "thetoyotaway.pdf",
        "filename": "thetoyotaway.pdf",
        "title": "The Toyota Way - Executive Summary",
        "author": "Jeffrey K. Liker",
        "is_slides": True,
    },
]


class IngestionPipeline:
    def __init__(
        self,
        parser: DocumentParser | None = None,
        chunker: TextChunker | None = None,
        embedder: BaseEmbeddingService | None = None,
        vector_store: QdrantVectorStore | None = None,
    ):
        self.parser = parser or DocumentParser()
        self.chunker = chunker or TextChunker()
        self.embedder = embedder or FastEmbedService()
        self.vector_store = vector_store or QdrantVectorStore()

    def run_file(
        self,
        file_path: Path,
        title: str,
        author: str,
        is_slide_deck: bool = False,
    ) -> int:
        if not file_path.exists():
            raise FileNotFoundError(f"Файл {file_path} не существует.")

        start_time = time.time()
        print(
            f"\n[1/4] Парсинг документа: {file_path.name} (is_slides={is_slide_deck})..."
        )
        pages = self.parser.parse_pdf(
            file_path=file_path,
            book_title=title,
            author=author,
            is_slide_deck=is_slide_deck,
        )
        print(f"  -> Извлечено страниц с текстом: {len(pages)}")

        print("[2/4] Нарезка текста на чанки...")
        chunks = self.chunker.split_pages(pages)
        print(f"  -> Сформировано чанков: {len(chunks)}")

        if not chunks:
            print("  -> Предупреждение: не сформировано ни одного чанка.")
            return 0

        print(f"[3/4] Генерация эмбеддингов ({self.embedder.model_name})...")
        texts = [chunk.content for chunk in chunks]
        vectors = self.embedder.embed_texts(texts)
        print(f"  -> Векторизовано {len(vectors)} элементов")

        print("[4/4] Загрузка данных в Qdrant...")
        self.vector_store.ensure_collection()
        self.vector_store.upsert_chunks(chunks, vectors)

        elapsed = time.time() - start_time
        print(f"✓ Завершено за {elapsed:.2f} сек. Загружено чанков: {len(chunks)}")
        return len(chunks)

    def search(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.5,
    ) -> list[SearchResult]:
        query_vector = self.embedder.embed_query(query)
        return self.vector_store.search(
            query_vector,
            limit=limit,
            score_threshold=score_threshold,
        )

    def get_stats(self) -> dict[str, Any]:
        return self.vector_store.get_collection_info()
