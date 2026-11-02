# src/toyota_rag/eval_queries.py
import sys
from typing import Any

from toyota_rag.pipeline import IngestionPipeline

BENCHMARK_CASES: list[dict[str, Any]] = [
    {
        "id": 1,
        "query": "What are the 8 types of waste identified by Toyota?",
        "expected_keywords": [
            "overproduction",
            "waiting",
            "inventory",
            "muda",
            "waste",
        ],
        "expected_author": "Jeffrey K. Liker",
        "description": "8 types of waste (muda) including unused employee creativity",
    },
    {
        "id": 2,
        "query": "Explain the difference between labor saving and worker saving according to Taiichi Ohno.",
        "expected_keywords": ["labor", "worker", "saving", "man"],
        "expected_author": "Taiichi Ohno",
        "description": "Labor saving vs worker saving / man saving distinction in TPS",
    },
    {
        "id": 3,
        "query": "How did Chief Engineer Uchiyamada utilize the Obeya system during the development of the Prius?",
        "expected_keywords": ["obeya", "uchiyamada", "prius", "room"],
        "expected_author": "Jeffrey K. Liker",
        "description": "Obeya (big room) system during Prius project",
    },
    {
        "id": 4,
        "query": "What is the five why method and what was the machine stoppage example?",
        "expected_keywords": ["why", "fuse", "lubrication", "pump", "shaft"],
        "expected_author": "Taiichi Ohno",
        "description": "5 Whys root cause analysis with machine stoppage example",
    },
    {
        "id": 5,
        "query": "What is Heijunka and why does leveling production come before pull systems?",
        "expected_keywords": ["heijunka", "leveling", "production", "pull"],
        "expected_author": "Taiichi Ohno",
        "description": "Heijunka production leveling as foundation for pull system",
    },
]


def run_benchmark(min_score: float = 0.70) -> bool:
    pipe = IngestionPipeline()
    print("=" * 70)
    print("=== ЗАПУСК ПРОВЕРКИ РЕЛЕВАНТНОСТИ БАЗЫ ЗНАНИЙ (RAG BENCHMARK) ===")
    print(f"Критерий DoD: релевантность (Score) >= {min_score:.2f} и ключевые слова")
    print("=" * 70)

    all_passed = True

    for case in BENCHMARK_CASES:
        print(f"\n[Тест {case['id']}] Вопрос: «{case['query']}»")
        print(f"Целевой автор: {case['expected_author']} | Тема: {case['description']}")

        results = pipe.search(case["query"], limit=3, score_threshold=0.3)

        if not results:
            print("❌ СТАТУС: FAILED (Ничего не найдено в базе)")
            all_passed = False
            continue

        top_result = results[0]
        found_texts = " ".join([r.content.lower() for r in results])
        matched_kw = [kw for kw in case["expected_keywords"] if kw in found_texts]

        score_ok = top_result.score >= min_score
        keywords_ok = len(matched_kw) >= 2
        author_ok = any(
            case["expected_author"].lower() in r.metadata.author.lower()
            for r in results
        )

        test_passed = score_ok and keywords_ok

        status_icon = "✓ PASSED" if test_passed else "⚠️ WARNING / FAILED"
        if not test_passed:
            all_passed = False

        print(f"Статус: {status_icon}")
        print(
            f"  • Top-1 Score:     {top_result.score:.4f} (>= {min_score}: {'ДА' if score_ok else 'НЕТ'})"
        )
        print(
            f"  • Top-1 Источник:  {top_result.metadata.book_title} (стр. {top_result.metadata.page_number})"
        )
        print(
            f"  • Автор:           {top_result.metadata.author} (соответствует: {'ДА' if author_ok else 'НЕТ'})"
        )
        print(
            f"  • Ключевые слова:  найдено {len(matched_kw)}/{len(case['expected_keywords'])}: {matched_kw}"
        )
        print(f"  • Фрагмент цитаты:\n    {top_result.content.strip()[:200]}...")

    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ИТОГ БЕНЧМАРКА: ВСЕ 5 ТЕСТОВ УСПЕШНО ПРОЙДЕНЫ!")
    else:
        print("⚠️ ИТОГ БЕНЧМАРКА: Некоторые тесты требуют внимания.")
    print("=" * 70)
    return all_passed


if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)
