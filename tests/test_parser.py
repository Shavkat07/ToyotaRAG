import re

import pytest

from toyota_rag.config import settings
from toyota_rag.models import DocumentPage
from toyota_rag.parser import DocumentParser

parser = DocumentParser()

WATERMARK = (
    "This document is created with the unregistered version of Document2PDF Pilot."
)


def _find_pdf(name: str):
    for folder in (settings.DATA_DIR / "raw", settings.DATA_DIR):
        if (folder / name).exists():
            return folder / name
    return None


def test_removes_watermark_and_team_lib():
    text = f"Some text.\nTeam LiB\n4 PREVIOUS NEXT >\nMore text.\n{WATERMARK}"
    cleaned = parser.clean_text(text)
    assert "Document2PDF" not in cleaned
    assert "Team LiB" not in cleaned
    assert "PREVIOUS" not in cleaned
    assert "Some text." in cleaned and "More text." in cleaned


def test_repairs_hyphenation():
    assert parser.clean_text("stan-\ndardization of work") == "standardization of work"


def test_normalizes_whitespace():
    cleaned = parser.clean_text("a\xa0b    c\td\n\n\n\n\ne")
    assert cleaned == "a b c d\n\ne"


def test_drops_standalone_page_numbers_but_keeps_numbered_items():
    cleaned = parser.clean_text("First line\n45\n3. sedan-type body")
    assert "\n45" not in cleaned
    assert "3. sedan-type body" in cleaned


def test_slide_mode_keeps_layout():
    text = "THE 14 PRINCIPLES\n- Base decisions on\n- long-term thinking\n1\n2"
    cleaned = parser.clean_text(text, preserve_layout=True)
    assert cleaned.splitlines() == text.splitlines()


def test_find_glossary_pages():
    def page(n, text):
        return DocumentPage(text=text, page_number=n, book_title="b", author="a")

    pages = [
        page(11, "Contents Glossary of Major Terms 143"),
        page(143, "Postscript to the Original Japanese Edition"),
        page(144, "Glossary of Major Terms As a guide to understanding"),
        page(145, "► Andon A signboard"),
        page(153, "Editor's Notes Chapter 1"),
    ]
    assert parser.find_glossary_pages(pages) == {144, 145}


@pytest.mark.parametrize(
    "name",
    [
        "mcgraw-hill-thetoyotaway-14managementprinciples.pdf",
        "toyota-production-system-beyond-large-scale-production.pdf",
    ],
)
def test_real_books_are_clean(name):
    path = _find_pdf(name)
    if path is None:
        pytest.skip(f"{name} not found in data/")
    pages = parser.parse_pdf(path, "Title", "Author")
    assert pages
    for page in pages:
        assert "Document2PDF" not in page.text
        assert "Team LiB" not in page.text
        assert "\t" not in page.text
        assert not re.search(
            r"\w-\n\w", page.text
        )  # " -\n" это тире, а не перенос слова
