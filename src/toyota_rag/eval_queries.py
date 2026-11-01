# eval_queries.py
from toyota_rag.pipeline import IngestionPipeline

BENCHMARK_CASES = [
    {
        "query": "What are the 8 types of waste according to TPS?",
        "expected_keywords": ["overproduction", "waiting", "inventory", "muda"],
        "expected_author": "Jeffrey K. Liker",
    },
    {
        "query": "How does Taiichi Ohno explain the 5 whys root cause analysis?",
        "expected_keywords": ["lubrication", "pump", "fuse", "strainer"],
        "expected_author": "Taiichi Ohno",
    },
    {
        "query": "What was the role of the obeya room in the Prius development?",
        "expected_keywords": ["obeya", "big room", "Uchiyamada"],
        "expected_author": "Jeffrey K. Liker",
    },
    {
        "query": "What is the difference between takt time and cycle time?",
        "expected_keywords": ["takt", "customer demand", "operating time"],
        "expected_author": "Taiichi Ohno",
    },
]


def run_benchmark():
    pipe = IngestionPipeline()
    print("=== ЗАПУСК ПРОВЕРКИ РЕЛЕВАНТНОСТИ БАЗЫ ЗНАНИЙ ===")

    for case in BENCHMARK_CASES:
        print(f"\nВопрос: {case['query']}")
        results = pipe.search(case["query"], limit=3)

        found_texts = " ".join([r.content.lower() for r in results])
        matched_kw = [kw for kw in case["expected_keywords"] if kw in found_texts]

        status = "PASSED" if len(matched_kw) >= 2 else "WARNING (Low match)"
        print(f"Статус: {status} | Совпало ключевых слов: {matched_kw}")
        if results:
            print(f"Топ-1 источник: {results[0].metadata.book_title} (Score: {results[0].score:.4f})")


if __name__ == "__main__":
    run_benchmark()