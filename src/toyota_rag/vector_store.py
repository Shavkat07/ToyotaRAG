"""Модуль для работы с векторным хранилищем Qdrant в локальном (embedded) режиме."""

import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from toyota_rag.config import settings
from toyota_rag.models import ChunkMetadata, SearchResult, TextChunk

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """Взаимодействие с базой данных Qdrant в локальном embedded-режиме."""

    def __init__(
        self,
        storage_path: str = str(settings.QDRANT_STORAGE_DIR),
        collection_name: str = settings.COLLECTION_NAME,
    ):
        """Инициализация клиента Qdrant в embedded-режиме (без Docker).

        Args:
            storage_path: Путь к директории хранения данных Qdrant.
            collection_name: Имя коллекции для хранения векторов.
        """
        self.storage_path = storage_path
        self.collection_name = collection_name
        self.client = QdrantClient(path=storage_path)
        logger.info(
            "Qdrant клиент инициализирован (storage_path=%s, collection=%s)",
            storage_path,
            collection_name,
        )

    def ensure_collection(self, vector_size: int = settings.VECTOR_SIZE) -> None:
        """Создает коллекцию, если она отсутствует.

        Args:
            vector_size: Размерность вектора эмбеддинга (по умолчанию 384 для bge-small).
        """
        if self.client.collection_exists(self.collection_name):
            logger.info("Коллекция '%s' уже существует.", self.collection_name)
        else:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info(
                "Коллекция '%s' создана (vector_size=%d, distance=COSINE).",
                self.collection_name,
                vector_size,
            )

    def upsert_chunks(
        self,
        chunks: list[TextChunk],
        vectors: list[list[float]],
        batch_size: int = 128,
    ) -> None:
        """Сохранение векторов и payload в базу пакетами.

        Args:
            chunks: Список текстовых чанков с метаданными.
            vectors: Список эмбеддинг-векторов, соответствующих чанкам.
            batch_size: Размер пакета для загрузки.

        Raises:
            ValueError: Если количество чанков не совпадает с количеством векторов.
        """
        if len(chunks) != len(vectors):
            raise ValueError(
                f"Количество чанков ({len(chunks)}) не совпадает "
                f"с количеством векторов ({len(vectors)})."
            )

        # Получаем текущее количество точек для избежания коллизий ID
        collection_info = self.client.get_collection(self.collection_name)
        start_id = collection_info.points_count or 0

        points = [
            PointStruct(
                id=start_id + i,
                vector=vector,
                payload={"content": chunk.content, **chunk.metadata.model_dump()},
            )
            for i, (chunk, vector) in enumerate(zip(chunks, vectors))
        ]

        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(collection_name=self.collection_name, points=batch)
            logger.debug(
                "Загружен пакет %d–%d из %d точек.",
                i,
                min(i + batch_size, len(points)) - 1,
                len(points),
            )

        logger.info(
            "Успешно загружено %d точек в коллекцию '%s'.",
            len(points),
            self.collection_name,
        )

    def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: float = 0.5,
    ) -> list[SearchResult]:
        """Поиск ближайших векторов с извлечением текста и метаданных.

        Args:
            query_vector: Вектор запроса.
            limit: Максимальное количество результатов.
            score_threshold: Минимальный порог релевантности (cosine similarity).

        Returns:
            Список результатов поиска, отсортированных по убыванию score.
        """
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold,
        )

        search_results: list[SearchResult] = []
        for point in results.points:
            payload = point.payload
            search_results.append(
                SearchResult(
                    content=payload["content"],
                    score=point.score,
                    metadata=ChunkMetadata(
                        book_title=payload["book_title"],
                        author=payload["author"],
                        page_number=payload["page_number"],
                        chunk_index=payload["chunk_index"],
                        doc_type=payload.get("doc_type", "book"),
                        extra=payload.get("extra", {}),
                    ),
                )
            )

        logger.info(
            "Поиск вернул %d результатов (limit=%d, threshold=%.2f).",
            len(search_results),
            limit,
            score_threshold,
        )
        return search_results

    def get_collection_info(self) -> dict:
        """Возвращает информацию о коллекции для команды stats.

        Returns:
            Словарь с именем коллекции, количеством точек и статусом.
        """
        collection = self.client.get_collection(self.collection_name)
        info = {
            "name": self.collection_name,
            "points_count": collection.points_count or 0,
            "status": str(collection.status),
        }
        logger.info("Информация о коллекции: %s", info)
        return info
