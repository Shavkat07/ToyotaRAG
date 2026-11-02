# Toyota RAG Knowledge Base — Статус задач

## Общий прогресс проекта: 100% (Все компоненты реализованы и протестированы)

### Участник 1: Data Ingestion & Sanitization (`parser.py`)
- [x] Постраничное извлечение текста через `pypdf.PdfReader`
- [x] Очистка водяных знаков `Document2PDF Pilot`
- [x] Очистка `Team LiB` и навигационных тегов `PREVIOUS / NEXT`
- [x] Восстановление переносов строк внутри слов (de-hyphenation)
- [x] Нормализация пробелов и табуляций
- [x] Режим презентаций (`preserve_layout=True`)
- [x] Поиск страниц глоссария по тексту (`find_glossary_pages`)
- [x] Unit-тесты (`tests/test_parser.py`) — 8/8 пройдены

### Участник 2: Chunking Strategy & Metadata (`chunker.py`)
- [x] Адаптивная маршрутизация по модальности документа (`split_pages`)
- [x] Повествовательный текст (Liker: 1200 симв., overlap 150; Ohno: 800 симв., overlap 100)
- [x] Сохранение точных номеров страниц через маркеры `<<PAGE:N>>`
- [x] Слайд-дека: 1 слайд = 1 чанк (`doc_type="slides"`, без внутрислайдового дробления)
- [x] Глоссарий Оно: разбиение по `►` (`doc_type="glossary"`, каждый термин в отдельный чанк)
- [x] Контекстный заголовок для каждого чанка: `[Source: ... | Author: ... | Page: ...]`
- [x] Последовательный счетчик `chunk_index`
- [x] Unit-тесты (`tests/test_chunker.py`) — 4/4 пройдены

### Участник 3: Embeddings & Vector Store (`embeddings.py`, `vector_store.py`)
- [x] Абстрактный базовый класс `BaseEmbeddingService`
- [x] Сервис `FastEmbedService` на базе `BAAI/bge-small-en-v1.5` (384 измерения)
- [x] Батчевая генерация эмбеддингов (`embed_texts`) и запросов (`embed_query`)
- [x] Клиент `QdrantVectorStore` в локальном embedded-режиме (`data/qdrant_storage`)
- [x] Создание коллекции с `Distance.COSINE` (`ensure_collection`)
- [x] Батчевый upsert чанков с payload и защитой от коллизий ID (`upsert_chunks`)
- [x] Поиск ближайших векторов с порогом `score_threshold` (`search`)
- [x] Метод сбора статистики коллекции (`get_collection_info`)
- [x] Unit-тесты (`tests/test_search.py`) — 2/2 пройдены

### Участник 4: Pipeline Orchestrator, CLI & QA (`pipeline.py`, `main.py`, `eval_queries.py`)
- [x] Сквозной конвейер `IngestionPipeline` (парсинг → нарезка → векторизация → загрузка)
- [x] Реестр книг `BOOKS_REGISTRY` с поддержкой флага `is_slides`
- [x] CLI `main.py ingest --all` / `main.py ingest --file ...`
- [x] CLI `main.py search --query "..." --limit 5 --threshold 0.5`
- [x] CLI `main.py stats` (количество точек, статус, размер на диске)
- [x] Набор бенчмарков из 5 специализированных запросов (`eval_queries.py`)
- [x] Критерий DoD: релевантность $\ge 0.70$ для всех 5 запросов — **100% пройдены**
- [x] Проверка линтером и форматирование (`ruff check` & `ruff format`) — без ошибок

