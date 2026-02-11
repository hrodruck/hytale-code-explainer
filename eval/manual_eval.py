import time
import argparse
import csv
from datetime import datetime
from typing import List

from src.adapters.retrieval import QdrantCodeRetriever
from src.adapters.llm import get_llm_completer
from src.application.application import get_initial_history, process_conversation_turn


def load_queries(input_path: str) -> List[str]:
    with open(input_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


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

    if response_times:
        avg_time = sum(response_times) / len(response_times)
        total_time = sum(response_times)
        print(f"Average response time: {avg_time:.2f} seconds (n={len(response_times)})")
        print(f"Total processing time: {total_time:.2f} seconds")
    
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"data/eval_dataset/generated_answers_{timestamp}.csv"

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["query", "answer", "response_time_seconds"])  
        for q, a, t in zip(questions, answers, response_times):
            writer.writerow([q, a, f"{t:.2f}"])

    print(f"Generation complete: {len(queries)} answers generated.")
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()