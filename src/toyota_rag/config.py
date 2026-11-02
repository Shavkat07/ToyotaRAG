from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Пути
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    QDRANT_STORAGE_DIR: Path = DATA_DIR / "qdrant_storage"

    # Параметры Qdrant
    COLLECTION_NAME: str = "toyota_knowledge_base"
    VECTOR_SIZE: int = 384  # 384 для bge-small, 1024 для bge-m3

    # Модель эмбеддингов
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"

    # Параметры чанкинга
    CHUNK_SIZE: int = 1200
    CHUNK_OVERLAP: int = 150


settings = Settings()
