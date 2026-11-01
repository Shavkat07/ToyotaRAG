from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DocumentPage(BaseModel):
    """Сырая страница книги после первичного парсинга."""
    text: str
    page_number: int
    book_title: str
    author: str


class ChunkMetadata(BaseModel):
    """Метаданные для векторного хранилища."""
    book_title: str
    author: str
    page_number: int
    chunk_index: int
    extra: Dict[str, Any] = Field(default_factory=dict)


class TextChunk(BaseModel):
    """Готовый чанк для векторизации и сохранения."""
    content: str
    metadata: ChunkMetadata


class SearchResult(BaseModel):
    """Результат семантического поиска."""
    content: str
    score: float
    metadata: ChunkMetadata