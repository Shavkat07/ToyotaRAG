from pathlib import Path
from typing import List
from toyota_rag.models import DocumentPage


class DocumentParser:
    """Извлечение текста из PDF/EPUB с очисткой от технического мусора."""

    def __init__(self):
        pass

    def clean_text(self, text: str) -> str:
        """
        Удаляет переносы строк внутри слов, колонтитулы и артефакты PDF.
        """
        # TODO: Реализовать regex-очистку и дегифенизацию
        raise NotImplementedError

    def parse_pdf(self, file_path: Path, book_title: str, author: str) -> List[DocumentPage]:
        """
        Постраничное чтение PDF с привязкой метаданных книги.
        """
        # TODO: Реализовать чтение через PyPDF / PyMuPDF
        raise NotImplementedError