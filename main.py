# main.py
import argparse
import sys
from pathlib import Path
from toyota_rag.config import settings
from toyota_rag.pipeline import IngestionPipeline

BOOKS_REGISTRY = [
    {
        "filename": "mcgraw-hill-thetoyotaway-14managementprinciples.pdf",
        "title": "The Toyota Way: 14 Management Principles",
        "author": "Jeffrey K. Liker",
    },
    {
        "filename": "toyota-production-system-beyond-large-scale-production.pdf",
        "title": "Toyota Production System: Beyond Large-Scale Production",
        "author": "Taiichi Ohno",
    },
    {
        "filename": "thetoyotaway.pdf",
        "title": "The Toyota Way: Executive Summary Slides",
        "author": "Jeffrey K. Liker",
    },
]


def handle_ingest(args):
    pipeline = IngestionPipeline()
    total_indexed = 0

    if args.all:
        for book in BOOKS_REGISTRY:
            path = settings.RAW_DATA_DIR / book["filename"]
            total_indexed += pipeline.run_file(path, book["title"], book["author"])
        print(f"\nВсе книги проиндексированы. Суммарно чанков в базе: {total_indexed}")
    elif args.file:
        file_path = settings.RAW_DATA_DIR / args.file
        title = args.title or args.file
        author = args.author or "Unknown"
        pipeline.run_file(file_path, title, author)
    else:
        print("Ошибка: укажите флаг --all или передайте имя файла через --file.")
        sys.exit(1)


def handle_search(args):
    pipeline = IngestionPipeline()
    print(f"\nПоисковый запрос: '{args.query}' (limit={args.limit})\n" + "-" * 50)
    results = pipeline.search(args.query, limit=args.limit)

    if not results:
        print("Ничего не найдено.")
        return

    for idx, res in enumerate(results, start=1):
        print(f"[{idx}] Score: {res.score:.4f} | {res.metadata.book_title} (стр. {res.metadata.page_number})")
        print(f"Фрагмент:\n{res.content.strip()}\n" + "-" * 50)


def main():
    parser = argparse.ArgumentParser(description="Toyota RAG Knowledge Base CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Индексация
    ingest_p = subparsers.add_parser("ingest", help="Индексация документов")
    ingest_p.add_argument("--all", action="store_true", help="Индексировать все 3 книги из data/raw")
    ingest_p.add_argument("--file", type=str, help="Имя конкретного PDF в каталоге data/raw")
    ingest_p.add_argument("--title", type=str, help="Название книги (опционально)")
    ingest_p.add_argument("--author", type=str, help="Автор книги (опционально)")

    # Поиск
    search_p = subparsers.add_parser("search", help="Семантический поиск по базе")
    search_p.add_argument("--query", type=str, required=True, help="Строка запроса")
    search_p.add_argument("--limit", type=int, default=3, help="Количество результатов")

    args = parser.parse_args()
    if args.command == "ingest":
        handle_ingest(args)
    elif args.command == "search":
        handle_search(args)


if __name__ == "__main__":
    main()