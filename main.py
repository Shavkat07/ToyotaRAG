# main.py
import argparse
import sys
from pathlib import Path

from toyota_rag.config import settings
from toyota_rag.pipeline import BOOKS_REGISTRY, IngestionPipeline


def get_dir_size(path: Path) -> str:
    """Возвращает форматированный размер директории."""
    if not path.exists():
        return "0 B"
    total_bytes = sum(f.stat().st_size for f in path.glob("**/*") if f.is_file())
    for unit in ["B", "KB", "MB", "GB"]:
        if total_bytes < 1024:
            return f"{total_bytes:.2f} {unit}"
        total_bytes /= 1024
    return f"{total_bytes:.2f} TB"


def handle_ingest(args):
    pipeline = IngestionPipeline()
    total_indexed = 0

    if args.all:
        print("=== НАЧАЛО ИНДЕКСАЦИИ ВСЕХ ДОКУМЕНТОВ ===")
        for book in BOOKS_REGISTRY:
            filename = book.get("file") or book.get("filename")
            path = settings.RAW_DATA_DIR / filename
            is_slides = book.get("is_slides", False)
            total_indexed += pipeline.run_file(
                file_path=path,
                title=book["title"],
                author=book["author"],
                is_slide_deck=is_slides,
            )
        print(f"\n✓ Все книги проиндексированы. Суммарно чанков в базе: {total_indexed}")
    elif args.file:
        file_path = settings.RAW_DATA_DIR / args.file
        title = args.title or args.file
        author = args.author or "Unknown"
        is_slides = getattr(args, "is_slides", False)
        pipeline.run_file(file_path, title, author, is_slide_deck=is_slides)
    else:
        print("Ошибка: укажите флаг --all или передайте имя файла через --file.")
        sys.exit(1)


def handle_search(args):
    pipeline = IngestionPipeline()
    print(f"\nПоисковый запрос: '{args.query}' (limit={args.limit}, threshold={args.threshold})\n" + "=" * 60)
    results = pipeline.search(
        args.query,
        limit=args.limit,
        score_threshold=args.threshold,
    )

    if not results:
        print("Ничего не найдено (попробуйте понизить порог --threshold).")
        return

    for idx, res in enumerate(results, start=1):
        print(
            f"[{idx}] Score: {res.score:.4f} | {res.metadata.book_title} | "
            f"Автор: {res.metadata.author} | Стр. {res.metadata.page_number} "
            f"(Тип: {res.metadata.doc_type})"
        )
        print("-" * 60)
        print(res.content.strip())
        print("=" * 60)


def handle_stats(args):
    pipeline = IngestionPipeline()
    try:
        info = pipeline.get_stats()
        storage_size = get_dir_size(settings.QDRANT_STORAGE_DIR)
        print("\n=== СТАТИСТИКА БАЗЫ ЗНАНИЙ QDRANT ===")
        print(f"Коллекция:      {info['name']}")
        print(f"Всего точек:    {info['points_count']}")
        print(f"Статус:         {info['status']}")
        print(f"Путь хранилища: {settings.QDRANT_STORAGE_DIR}")
        print(f"Размер на диске:{storage_size}")
        print("=" * 37)
    except Exception as exc:  # noqa: BLE001
        print(f"Ошибка получения статистики (возможно, коллекция еще не создана): {exc}")


def main():
    parser = argparse.ArgumentParser(description="Toyota RAG Knowledge Base CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. Индексация
    ingest_p = subparsers.add_parser("ingest", help="Индексация документов")
    ingest_p.add_argument("--all", action="store_true", help="Индексировать все 3 книги из data/raw")
    ingest_p.add_argument("--file", type=str, help="Имя конкретного PDF в каталоге data/raw")
    ingest_p.add_argument("--title", type=str, help="Название книги (опционально)")
    ingest_p.add_argument("--author", type=str, help="Автор книги (опционально)")
    ingest_p.add_argument("--is-slides", action="store_true", help="Флаг: обрабатывать как презентацию/слайды")

    # 2. Поиск
    search_p = subparsers.add_parser("search", help="Семантический поиск по базе")
    search_p.add_argument("--query", type=str, required=True, help="Строка запроса")
    search_p.add_argument("--limit", type=int, default=5, help="Количество результатов (по умолчанию 5)")
    search_p.add_argument(
        "--threshold", type=float, default=0.5, help="Минимальный порог релевантности (по умолчанию 0.5)"
    )

    # 3. Статистика
    subparsers.add_parser("stats", help="Статистика коллекции и объем данных")

    args = parser.parse_args()
    if args.command == "ingest":
        handle_ingest(args)
    elif args.command == "search":
        handle_search(args)
    elif args.command == "stats":
        handle_stats(args)


if __name__ == "__main__":
    main()
