from typing import List
from toyota_rag.models import DocumentPage, TextChunk
from toyota_rag.config import settings


class TextChunker:
    """Нарезка документов на смысловые фрагменты с перекрытием."""

    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, chunk_overlap: int = settings.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_pages(self, pages: List[DocumentPage]) -> List[TextChunk]:
        """
        Разбивает список страниц на чанки с сохранением номеров страниц и книги.
        """
        # TODO: Реализовать RecursiveCharacterTextSplitter и сборку TextChunk
        raise NotImplementedError