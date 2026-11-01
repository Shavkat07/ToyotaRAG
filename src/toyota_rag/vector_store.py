from typing import List
from toyota_rag.config import settings
from toyota_rag.models import TextChunk, SearchResult


class QdrantVectorStore:
    """Взаимодействие с базой данных Qdrant."""

    def __init__(self, storage_path: str = str(settings.QDRANT_STORAGE_DIR), collection_name: str = settings.COLLECTION_NAME):
        self.storage_path = storage_path
        self.collection_name = collection_name
        # TODO: Инициализировать QdrantClient
        pass

    def ensure_collection(self, vector_size: int = settings.VECTOR_SIZE) -> None:
        """Создает коллекцию, если она отсутствует."""
        # TODO: Проверка и создание коллекции в Qdrant
        raise NotImplementedError

    def upsert_chunks(self, chunks: List[TextChunk], vectors: List[List[float]], batch_size: int = 128) -> None:
        """Сохранение векторов и payload в базу пакетами."""
        # TODO: Маппинг в PointStruct и пакетная загрузка
        raise NotImplementedError

    def search(self, query_vector: List[float], limit: int = 5) -> List[SearchResult]:
        """Поиск ближайших векторов с извлечением текста и метаданных."""
        # TODO: Вызов search в Qdrant и сборка SearchResult
        raise NotImplementedError