import tempfile

from toyota_rag.config import settings
from toyota_rag.embeddings import FastEmbedService
from toyota_rag.models import ChunkMetadata, TextChunk
from toyota_rag.vector_store import QdrantVectorStore


def test_fastembed_service():
    embedder = FastEmbedService()
    texts = [
        "Elimination of waste is the primary goal of lean manufacturing.",
        "Just-in-time means producing only what is needed, when it is needed.",
    ]
    vectors = embedder.embed_texts(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == settings.VECTOR_SIZE  # 384 dimensions

    query_vec = embedder.embed_query("What is JIT?")
    assert len(query_vec) == settings.VECTOR_SIZE


def test_qdrant_vector_store():
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = QdrantVectorStore(
            storage_path=tmp_dir,
            collection_name="test_toyota_kb",
        )
        store.ensure_collection(vector_size=384)

        embedder = FastEmbedService()
        chunks = [
            TextChunk(
                content="[Source: Test | Author: Ohno | Page: 1]\nKanban is an operating tool for pull systems.",
                metadata=ChunkMetadata(
                    book_title="Test",
                    author="Ohno",
                    page_number=1,
                    chunk_index=0,
                    doc_type="book",
                ),
            ),
            TextChunk(
                content="[Source: Test | Author: Liker | Page: 2]\nGenchi Genbutsu means go and see for yourself.",
                metadata=ChunkMetadata(
                    book_title="Test",
                    author="Liker",
                    page_number=2,
                    chunk_index=1,
                    doc_type="book",
                ),
            ),
        ]
        texts = [c.content for c in chunks]
        vectors = embedder.embed_texts(texts)

        store.upsert_chunks(chunks, vectors)

        info = store.get_collection_info()
        assert info["points_count"] == 2

        query_vec = embedder.embed_query("How does kanban work in pull systems?")
        results = store.search(query_vec, limit=2, score_threshold=0.3)

        assert len(results) >= 1
        assert "Kanban" in results[0].content
        assert results[0].score > 0.4
        assert results[0].metadata.author == "Ohno"
