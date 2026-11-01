from pathlib import Path
from toyota_rag.parser import DocumentParser
from toyota_rag.chunker import TextChunker
from toyota_rag.embeddings import BaseEmbeddingService, FastEmbedService
from toyota_rag.vector_store import QdrantVectorStore


class IngestionPipeline:
    """Координатор сквозного процесса загрузки книги в базу."""

    def __init__(
        self,
        parser: DocumentParser = None,
        chunker: TextChunker = None,
        embedder: BaseEmbeddingService = None,
        vector_store: QdrantVectorStore = None,
    ):
        self.parser = parser or DocumentParser()
        self.chunker = chunker or TextChunker()
        self.embedder = embedder or FastEmbedService()
        self.vector_store = vector_store or QdrantVectorStore()

    def run(self, file_path: Path, book_title: str, author: str) -> int:
        """
        Полный цикл: файл -> страницы -> чанки -> векторы -> Qdrant.
        Возвращает количество загруженных чанков.
        """
        # TODO: Реализовать последовательный вызов компонентов
        raise NotImplementedError