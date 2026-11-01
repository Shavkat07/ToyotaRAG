# src/toyota_rag/pipeline.py
import time
from pathlib import Path
from typing import List, Optional

from toyota_rag.config import settings
from toyota_rag.models import SearchResult
from toyota_rag.parser import DocumentParser
from toyota_rag.chunker import TextChunker
from toyota_rag.embeddings import BaseEmbeddingService, FastEmbedService
from toyota_rag.vector_store import QdrantVectorStore


class IngestionPipeline:
    def __init__(
        self,
        parser: Optional[DocumentParser] = None,
        chunker: Optional[TextChunker] = None,
        embedder: Optional[BaseEmbeddingService] = None,
        vector_store: Optional[QdrantVectorStore] = None,
    ):
        self.parser = parser or DocumentParser()
        self.chunker = chunker or TextChunker()
        self.embedder = embedder or FastEmbedService()
        self.vector_store = vector_store or QdrantVectorStore()

    def run_file(self, file_path: Path, title: str, author: str) -> int:
        if not file_path.exists():
            raise FileNotFoundError(f"Файл {file_path} не существует.")

        start_time = time.time()
        print(f"\n[1/4] Парсинг документа: {file_path.name}...")
        pages = self.parser.parse_pdf(file_path, title, author)
        print(f"  -> Извлечено страниц: {len(pages)}")

        print(f"[2/4] Нарезка текста на чанки...")
        chunks = self.chunker.split_pages(pages)
        print(f"  -> Сформировано чанков: {len(chunks)}")

        print(f"[3/4] Генерация эмбеддингов ({self.embedder.model_name})...")
        texts = [chunk.content for chunk in chunks]
        vectors = self.embedder.embed_texts(texts)
        print(f"  -> Векторизовано {len(vectors)} элементов")

        print(f"[4/4] Загрузка данных в Qdrant...")
        self.vector_store.ensure_collection()
        self.vector_store.upsert_chunks(chunks, vectors)

        elapsed = time.time() - start_time
        print(f"✓ Завершено за {elapsed:.2f} сек. Загружено чанков: {len(chunks)}")
        return len(chunks)

    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        query_vector = self.embedder.embed_query(query)
        return self.vector_store.search(query_vector, limit=limit)