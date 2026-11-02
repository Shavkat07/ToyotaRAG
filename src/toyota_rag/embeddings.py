import logging
from abc import ABC, abstractmethod

from fastembed import TextEmbedding

from toyota_rag.config import settings

logger = logging.getLogger(__name__)


class BaseEmbeddingService(ABC):
    """Базовый интерфейс для сервиса генерации эмбеддингов."""

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Генерация плотных векторов для списка строк."""

    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        """Генерация вектора для поискового запроса."""


class FastEmbedService(BaseEmbeddingService):
    """Локальные эмбеддинги на базе FastEmbed (ONNX Runtime)."""

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        logger.info("Загрузка модели эмбеддингов: %s", model_name)
        self._model = TextEmbedding(model_name=model_name)

    def embed_texts(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        """Батчевая генерация эмбеддингов для списка текстов.

        Args:
            texts: Список строк для кодирования.
            batch_size: Размер батча для инференса.

        Returns:
            Список плотных векторов (list[float]) для каждого входного текста.
        """
        logger.info("Генерация эмбеддингов для %d текстов", len(texts))
        embeddings = self._model.embed(texts, batch_size=batch_size)
        return [vec.tolist() for vec in embeddings]

    def embed_query(self, query: str) -> list[float]:
        """Генерация вектора для одного поискового запроса.

        Args:
            query: Строка запроса.

        Returns:
            Плотный вектор (list[float]) для запроса.
        """
        return self.embed_texts([query])[0]
