import logging
import re
from pathlib import Path

from pypdf import PdfReader

from toyota_rag.models import DocumentPage

logger = logging.getLogger(__name__)

# pypdf шумит предупреждениями о шрифтах, на результат они не влияют
logging.getLogger("pypdf").setLevel(logging.ERROR)

WATERMARK_RE = re.compile(
    r"This\s+document\s+is\s+created\s+with\s+the\s+unregistered\s+version\s+of\s+Document2PDF\s+Pilot\."
)
TEAM_LIB_RE = re.compile(r"Team\s+LiB")
NAV_RE = re.compile(r"(?:\d+\s*)?PREVIOUS\s+NEXT\s*>?")
PAGE_TRACKER_RE = re.compile(
    r"^[ ]*(?:page[ ]+)?\d{1,4}[ ]*$", re.IGNORECASE | re.MULTILINE
)
HYPHEN_BREAK_RE = re.compile(r"(\b\w+)-\n(\w+\b)")

GLOSSARY_HEADING_RE = re.compile(r"Glossary\s+of\s+Major\s+Terms", re.IGNORECASE)
GLOSSARY_END_RE = re.compile(r"^\s*Editor['’]s\s+Notes", re.IGNORECASE)


class DocumentParser:
    """Извлечение текста из PDF/EPUB с очисткой от технического мусора."""

    def __init__(self):
        pass

    def clean_text(self, text: str, preserve_layout: bool = False) -> str:
        """
        Удаляет переносы строк внутри слов, колонтитулы и артефакты PDF.

        preserve_layout=True (слайды): не склеивает переносы и не трогает строки из одних цифр,
        чтобы не ломать маркированные списки.
        """
        text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
        text = WATERMARK_RE.sub("", text)
        text = TEAM_LIB_RE.sub("", text)
        text = NAV_RE.sub("", text)

        # \xad - мягкий перенос, \xa0 - неразрывный пробел, \t - разделитель слов в книге Оно
        text = re.sub(r"\xad\n?", "", text)
        text = text.replace("\xa0", " ").replace("\t", " ")
        text = re.sub(r"[ ]{2,}", " ", text)
        text = re.sub(r"[ ]+\n", "\n", text)
        text = re.sub(r"\n[ ]+", "\n", text)

        if not preserve_layout:
            text = HYPHEN_BREAK_RE.sub(r"\1\2", text)
            text = PAGE_TRACKER_RE.sub("", text)

        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def find_glossary_pages(self, pages: list[DocumentPage]) -> set[int]:
        """
        Номера страниц глоссария (раздел "Glossary of Major Terms" у Оно).
        Границы ищутся по тексту: от последнего заголовка до "Editor's Notes",
        потому что номера в печатной версии не совпадают с индексом PDF.
        """
        start = None
        for index, page in enumerate(pages):
            if GLOSSARY_HEADING_RE.search(page.text[:200]):
                start = index
        if start is None:
            return set()

        numbers = {pages[start].page_number}
        for page in pages[start + 1 :]:
            if GLOSSARY_END_RE.match(page.text):
                break
            numbers.add(page.page_number)
        return numbers

    def parse_pdf(
        self,
        file_path: Path,
        book_title: str,
        author: str,
        is_slide_deck: bool = False,
    ) -> list[DocumentPage]:
        """
        Постраничное чтение PDF с привязкой метаданных книги.
        Пустые и нечитаемые страницы пропускаются, нумерация остаётся исходной (с 1).
        """
        reader = PdfReader(str(file_path))
        pages: list[DocumentPage] = []

        for number, pdf_page in enumerate(reader.pages, start=1):
            try:
                raw = pdf_page.extract_text() or ""
            except Exception as exc:  # noqa: BLE001  битая страница не должна ронять всю книгу
                logger.warning(
                    "%s: страница %d не прочитана (%s)", file_path.name, number, exc
                )
                continue

            text = self.clean_text(raw, preserve_layout=is_slide_deck)
            if not text:
                continue
            pages.append(
                DocumentPage(
                    text=text, page_number=number, book_title=book_title, author=author
                )
            )

        logger.info(
            "%s: %d из %d страниц с текстом",
            file_path.name,
            len(pages),
            len(reader.pages),
        )
        return pages
