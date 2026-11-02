"""CLI entry point for running the RAG evaluation benchmarks."""
import sys
from pathlib import Path

# Добавляем src в sys.path на случай прямого запуска
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from toyota_rag.eval_queries import run_benchmark

if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)
