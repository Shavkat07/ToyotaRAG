from abc import ABC, abstractmethod
from typing import List
import numpy as np
from toyota_rag.config import settings


class BaseEmbeddingService(ABC):
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Генерация плотных векторов для списка строк."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Генерация вектора для поискового запроса."""
        pass


class FastEmbedService(BaseEmbeddingService):
    """Локальные эмбеддинги на базе FastEmbed (ONNX Runtime)."""

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        # TODO: Инициализация TextEmbedding
        pass

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # TODO: Батчевая генерация эмбеддингов
        raise NotImplementedError

    def embed_query(self, query: str) -> List[float]:
        # TODO: Генерация эмбеддинга запроса
        raise NotImplementedError