import time
import argparse
import csv
from datetime import datetime, timezone
from typing import List

import psycopg2
from psycopg2.extras import RealDictCursor

from src.adapters.retrieval import QdrantCodeRetriever
from src.adapters.llm import get_llm_completer
from src.application.application import get_initial_history, process_conversation_turn


def load_queries(input_path: str) -> List[str]:
    with open(input_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def get_recent_costs_since(start_time: datetime, expected_count: int) -> List[float]:
    """Fetch exact costs for this eval run from LiteLLM Postgres (time-windowed)."""
    conn = psycopg2.connect("postgresql://litellm:litellm@localhost:5432/litellm")
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Widen window by 30 seconds to catch LiteLLM's async logging
            window_start = start_time - timedelta(seconds=30)

            # Fetch successful costs only
            cur.execute(
                '''
                SELECT spend
                FROM "LiteLLM_SpendLogs"
                WHERE "startTime" >= %s
                  AND status = 'success'
                ORDER BY "startTime" ASC
                LIMIT %s
                ''',
                (window_start, expected_count * 3),   # allow a few extra in case of fallbacks/retries
            )
            rows = cur.fetchall()
            costs = [float(row["spend"] or 0.0) for row in rows]

            if len(costs) != expected_count:
                print(f"⚠️  Warning: Expected {expected_count} costs, got {len(costs)}. "
                      f"Some calls may have failed or been retried.")

            return costs[:expected_count]   # only return as many as we originally asked for
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="data/eval_dataset/questions.txt",
        help="Input file with one query per line",
    )
    args = parser.parse_args()

    queries = load_queries(args.input)

    retriever = QdrantCodeRetriever()
    completer = get_llm_completer()

    questions = []
    answers = []
    response_times = []

    eval_start = datetime.now(timezone.utc)   # ← used to isolate this run only

    print(f"Loaded {len(queries)} queries. Starting generation...\n")

    for index, query in enumerate(queries):
        print(f"Processing query {index + 1}/{len(queries)}")
        print(f"Query: {query}\n")

        history = get_initial_history()
        start_time = time.perf_counter()
        
        response, _, _ = process_conversation_turn(
            history, query, retriever, completer
        )
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        response_times.append(duration)
        
        print(f"Answer:\n{response}\n")
        print(f"Response time: {duration:.2f} seconds")
        print("-" * 80 + "\n")

        questions.append(query)
        answers.append(response)

    # === COST COLLECTION (zero impact on core code) ===
    print("Fetching costs from LiteLLM database...")
    costs = get_recent_costs_since(eval_start, len(queries))

    if response_times:
        avg_time = sum(response_times) / len(response_times)
        total_time = sum(response_times)
        avg_cost = sum(costs) / len(costs) if costs else 0.0
        total_cost = sum(costs)

        print(f"\nAverage response time: {avg_time:.2f} seconds")
        print(f"Average cost per question: ${avg_cost:.6f}")
        print(f"Total cost for this eval run: ${total_cost:.6f}")
        print(f"Total processing time: {total_time:.2f} seconds")

    # Save to CSV with cost column
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"data/eval_dataset/generated_answers_{timestamp}.csv"

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["query", "answer", "response_time_seconds", "cost_usd"])
        for q, a, t, c in zip(questions, answers, response_times, costs):
            writer.writerow([q, a, f"{t:.2f}", f"{c:.6f}"])

    print(f"\nGeneration complete: {len(queries)} answers generated.")
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()
