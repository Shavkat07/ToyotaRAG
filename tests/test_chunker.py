from toyota_rag.chunker import TextChunker
from toyota_rag.models import DocumentPage


def test_narrative_chunking_liker():
    pages = [
        DocumentPage(
            text="Toyota's philosophy is rooted in long-term thinking. " * 30,
            page_number=1,
            book_title="The Toyota Way: 14 Management Principles",
            author="Jeffrey K. Liker",
        ),
        DocumentPage(
            text="Continuous flow brings problems to the surface. " * 30,
            page_number=2,
            book_title="The Toyota Way: 14 Management Principles",
            author="Jeffrey K. Liker",
        ),
    ]

    chunker = TextChunker()
    chunks = chunker.split_pages(pages)

    assert len(chunks) > 1
    for i, chunk in enumerate(chunks):
        assert chunk.metadata.doc_type == "book"
        assert chunk.metadata.author == "Jeffrey K. Liker"
        assert chunk.metadata.chunk_index == i
        assert chunk.content.startswith("[Source: The Toyota Way")
        assert "Author: Jeffrey K. Liker" in chunk.content
        assert chunk.metadata.page_number in [1, 2]


def test_narrative_chunking_ohno_size():
    # Ohno's book should use chunk_size=800, overlap=100
    pages = [
        DocumentPage(
            text="Eliminating waste is the foundation of TPS. " * 40,
            page_number=10,
            book_title="Toyota Production System: Beyond Large-Scale Production",
            author="Taiichi Ohno",
        )
    ]
    chunker = TextChunker()
    chunks = chunker.split_pages(pages)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.metadata.author == "Taiichi Ohno"
        assert chunk.metadata.doc_type == "book"
        assert "Taiichi Ohno" in chunk.content


def test_slides_chunking():
    # 1 page = 1 chunk, no split, doc_type="slides"
    pages = [
        DocumentPage(
            text="Slide 1: Principle 1 - Long Term Philosophy\n• Point A\n• Point B",
            page_number=1,
            book_title="The Toyota Way - Executive Summary",
            author="Jeffrey K. Liker",
        ),
        DocumentPage(
            text="Slide 2: Principle 2 - Create Flow\n• Point C\n• Point D",
            page_number=2,
            book_title="The Toyota Way - Executive Summary",
            author="Jeffrey K. Liker",
        ),
    ]

    chunker = TextChunker()
    chunks = chunker.split_pages(pages)

    assert len(chunks) == 2
    assert chunks[0].metadata.doc_type == "slides"
    assert chunks[1].metadata.doc_type == "slides"
    assert chunks[0].metadata.page_number == 1
    assert chunks[1].metadata.page_number == 2
    assert "Slide 1" in chunks[0].content
    assert "Slide 2" in chunks[1].content


def test_glossary_chunking():
    glossary_text = (
        "Glossary of Major Terms\n\n"
        "► Andon\nA light board used for visual management to indicate machine status.\n\n"
        "► Autonomation\nAutomation with a human touch or jidoka.\n\n"
        "► Kanban\nAn operating tool that provides pickup and delivery instructions."
    )
    pages = [
        DocumentPage(
            text=glossary_text,
            page_number=145,
            book_title="Toyota Production System: Beyond Large-Scale Production",
            author="Taiichi Ohno",
        )
    ]

    chunker = TextChunker()
    chunks = chunker._split_glossary(pages)

    assert len(chunks) == 3
    terms = [c.content for c in chunks]
    assert any("Andon" in t for t in terms)
    assert any("Autonomation" in t for t in terms)
    assert any("Kanban" in t for t in terms)

    for chunk in chunks:
        assert chunk.metadata.doc_type == "glossary"
        assert chunk.metadata.page_number == 145
        assert chunk.content.startswith("[Source: Toyota Production System")
