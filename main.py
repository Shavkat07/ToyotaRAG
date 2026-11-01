import argparse
from pathlib import Path
from toyota_rag.config import settings
from toyota_rag.pipeline import IngestionPipeline


def main():
    parser = argparse.ArgumentParser(description="Toyota Knowledge Base CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Команда индексации
    ingest_parser = subparsers.add_parser("ingest", help="Загрузить книгу в векторную базу")
    ingest_parser.add_argument("--file", type=str, required=True, help="Имя файла в data/raw/")
    ingest_parser.add_argument("--title", type=str, required=True, help="Название книги")
    ingest_parser.add_argument("--author", type=str, required=True, help="Автор")

    # Команда поиска для валидации
    search_parser = subparsers.add_parser("search", help="Проверить поиск по базе")
    search_parser.add_argument("--query", type=str, required=True, help="Поисковый запрос")
    search_parser.add_argument("--limit", type=int, default=3, help="Количество результатов")

    args = parser.parse_args()

    if args.command == "ingest":
        file_path = settings.RAW_DATA_DIR / args.file
        print(f"Запуск индексации: {file_path}")
        # pipeline = IngestionPipeline()
        # pipeline.run(file_path, args.title, args.author)

    elif args.command == "search":
        print(f"Поиск: {args.query}")
        # TODO: Поиск по вектору


if __name__ == "__main__":
    main()