import logging
import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

from toyota_rag.config import settings
from toyota_rag.models import ChunkMetadata, DocumentPage, TextChunk
from toyota_rag.parser import DocumentParser

logger = logging.getLogger(__name__)

# Маркер границы страницы, вставляемый между текстами страниц
_PAGE_MARKER_RE = re.compile(r"<<PAGE:(\d+)>>")

# Разделитель глоссарных записей у Оно
_GLOSSARY_DELIMITER = "►"


class TextChunker:
    """Нарезка документов на смысловые фрагменты с перекрытием."""

    def __init__(
        self,
        default_chunk_size: int = settings.CHUNK_SIZE,
        default_overlap: int = settings.CHUNK_OVERLAP,
    ):
        self.default_chunk_size = default_chunk_size
        self.default_overlap = default_overlap

    # ------------------------------------------------------------------
    # Публичный маршрутизатор
    # ------------------------------------------------------------------

    def split_pages(self, pages: list[DocumentPage]) -> list[TextChunk]:
        """
        Разбивает список страниц одной книги на чанки.

        Маршрутизация:
        - Слайды / Executive Summary → _split_slides
        - Глоссарные страницы (Ohno) → _split_glossary
        - Остальные → _split_narrative с размерами, зависящими от автора
        """
        if not pages:
            return []

        title = pages[0].book_title
        author = pages[0].author

        # --- Слайды -------------------------------------------------
        title_lower = title.lower()
        if (
            "executive summary" in title_lower
            or "slides" in title_lower
            or "slide" in title_lower
        ):
            logger.info("Книга «%s» → слайдовый режим (%d стр.)", title, len(pages))
            return self._split_slides(pages)

        # --- Определяем глоссарные страницы -------------------------
        parser = DocumentParser()
        glossary_page_numbers = parser.find_glossary_pages(pages)

        glossary_pages: list[DocumentPage] = []
        narrative_pages: list[DocumentPage] = []
        for page in pages:
            if page.page_number in glossary_page_numbers:
                glossary_pages.append(page)
            else:
                narrative_pages.append(page)

        # --- Размеры чанков по автору --------------------------------
        if "Ohno" in author:
            chunk_size, overlap = 800, 100
        else:
            chunk_size, overlap = self.default_chunk_size, self.default_overlap

        chunks: list[TextChunk] = []

        if narrative_pages:
            logger.info(
                "Книга «%s» → narrative (%d стр., size=%d, overlap=%d)",
                title,
                len(narrative_pages),
                chunk_size,
                overlap,
            )
            chunks.extend(self._split_narrative(narrative_pages, chunk_size, overlap))

        if glossary_pages:
            logger.info(
                "Книга «%s» → glossary (%d стр.)",
                title,
                len(glossary_pages),
            )
            chunks.extend(self._split_glossary(glossary_pages))

        return chunks

    # ------------------------------------------------------------------
    # Стратегия: повествовательный текст
    # ------------------------------------------------------------------

    def _split_narrative(
        self,
        pages: list[DocumentPage],
        size: int,
        overlap: int,
    ) -> list[TextChunk]:
        """
        Рекурсивное разбиение повествовательного текста.

        Между страницами вставляются маркеры <<PAGE:N>>, чтобы после
        нарезки можно было определить, к какой странице относится чанк.
        """
        if not pages:
            return []

        book_title = pages[0].book_title
        author = pages[0].author

        # Собираем единый текст с маркерами страниц
        parts: list[str] = []
        for page in pages:
            parts.append(f"\n\n<<PAGE:{page.page_number}>>\n\n")
            parts.append(page.text)
        full_text = "".join(parts)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " "],
        )
        raw_chunks = splitter.split_text(full_text)

        chunks: list[TextChunk] = []
        for idx, raw in enumerate(raw_chunks):
            # Находим ВСЕ маркеры страниц внутри чанка
            markers = list(_PAGE_MARKER_RE.finditer(raw))
            if markers:
                # Используем номер страницы из ПЕРВОГО маркера
                page_number = int(markers[0].group(1))
            else:
                # Маркера нет — чанк целиком внутри одной страницы;
                # ищем ближайший маркер в предыдущих чанках (уже определён)
                page_number = (
                    chunks[-1].metadata.page_number if chunks else pages[0].page_number
                )

            # Удаляем все маркеры из текста чанка
            clean = _PAGE_MARKER_RE.sub("", raw).strip()
            if not clean:
                continue

            header = f"[Source: {book_title} | Author: {author} | Page: {page_number}]"
            content = f"{header}\n{clean}"

            chunks.append(
                TextChunk(
                    content=content,
                    metadata=ChunkMetadata(
                        book_title=book_title,
                        author=author,
                        page_number=page_number,
                        chunk_index=idx,
                        doc_type="book",
                    ),
                )
            )

        # Пересчитываем chunk_index последовательно (после фильтрации пустых)
        for i, chunk in enumerate(chunks):
            chunk.metadata.chunk_index = i

        logger.info("Narrative: %d чанков из %d страниц", len(chunks), len(pages))
        return chunks

    # ------------------------------------------------------------------
    # Стратегия: слайды
    # ------------------------------------------------------------------

    def _split_slides(self, pages: list[DocumentPage]) -> list[TextChunk]:
        """
        Каждая страница слайда = ровно один чанк без дополнительной нарезки.
        """
        chunks: list[TextChunk] = []
        for idx, page in enumerate(pages):
            header = f"[Source: {page.book_title} | Author: {page.author} | Page: {page.page_number}]"
            content = f"{header}\n{page.text}"

            chunks.append(
                TextChunk(
                    content=content,
                    metadata=ChunkMetadata(
                        book_title=page.book_title,
                        author=page.author,
                        page_number=page.page_number,
                        chunk_index=idx,
                        doc_type="slides",
                    ),
                )
            )

        logger.info("Slides: %d чанков", len(chunks))
        return chunks

    # ------------------------------------------------------------------
    # Стратегия: глоссарий
    # ------------------------------------------------------------------

    def _split_glossary(self, pages: list[DocumentPage]) -> list[TextChunk]:
        """
        Разбивает глоссарий по разделителю ► (U+25BA).

        Каждая пара «термин + определение» = отдельный чанк.
        """
        if not pages:
            return []

        book_title = pages[0].book_title
        author = pages[0].author

        # Собираем текст с маркерами страниц, чтобы отследить привязку
        parts: list[str] = []
        for page in pages:
            parts.append(f"<<PAGE:{page.page_number}>>")
            parts.append(page.text)
        full_text = "".join(parts)

        if _GLOSSARY_DELIMITER in full_text:
            # Текст до первого '►' — это заголовок раздела ("Glossary of Major Terms"),
            # поэтому берем только записи после первого разделителя
            entries = full_text.split(_GLOSSARY_DELIMITER)[1:]
        else:
            entries = [full_text]

        chunks: list[TextChunk] = []
        for entry_raw in entries:
            # Определяем номер страницы по ПЕРВОМУ маркеру в записи
            markers = list(_PAGE_MARKER_RE.finditer(entry_raw))
            if markers:
                page_number = int(markers[0].group(1))
            else:
                # Нет маркера — наследуем от предыдущего чанка
                page_number = (
                    chunks[-1].metadata.page_number if chunks else pages[0].page_number
                )

            clean = _PAGE_MARKER_RE.sub("", entry_raw).strip()
            if not clean:
                continue

            term_text = (
                f"► {clean}" if not clean.startswith(_GLOSSARY_DELIMITER) else clean
            )
            header = f"[Source: {book_title} | Author: {author} | Page: {page_number}]"
            content = f"{header}\n{term_text}"

            chunks.append(
                TextChunk(
                    content=content,
                    metadata=ChunkMetadata(
                        book_title=book_title,
                        author=author,
                        page_number=page_number,
                        chunk_index=len(chunks),
                        doc_type="glossary",
                    ),
                )
            )

        logger.info("Glossary: %d записей из %d страниц", len(chunks), len(pages))
        return chunks
