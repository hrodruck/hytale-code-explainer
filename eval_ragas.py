import argparse
import csv
from typing import List

from ragas.metrics.collections import Faithfulness, AnswerCorrectness
from ragas.embeddings import HuggingFaceEmbeddings
from datasets import Dataset
from ragas.llms import llm_factory
from openai import AsyncOpenAI

from src.adapters.retrieval import QdrantCodeRetriever, ContextCapturingRetriever
from src.adapters.llm import get_llm_completer
from src.application.application import get_initial_history, process_conversation_turn


def load_queries(input_path: str) -> List[str]:
    with open(input_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/eval_dataset/questions.txt", help="Input file with one query per line")
    parser.add_argument("--ground_truth", default="data/eval_dataset/ground_truth_answers.txt", help="Input file with one ground truth answer per line")
    parser.add_argument("--output", default="data/eval_dataset/ragas_results.csv", help="Output CSV file")
    parser.add_argument("--compute-correctness", action="store_true", default=False, help="Whether to compute the AnswerCorrectness metric (requires embeddings and ground truth)")
    args = parser.parse_args()

    queries = load_queries(args.input)
    ground_truths = load_queries(args.ground_truth)

    if len(queries) != len(ground_truths):
        raise ValueError(f"Number of queries ({len(queries)}) and ground truths ({len(ground_truths)}) must match")

    base_retriever = QdrantCodeRetriever()
    capturing_retriever = ContextCapturingRetriever(base_retriever)
    completer = get_llm_completer()
    judge_llm = llm_factory('gpt-4o-mini', client=AsyncOpenAI(), max_tokens=16384)
    
    embeddings = HuggingFaceEmbeddings(model="mixedbread-ai/mxbai-embed-large-v1")
    
    faithfulness_metric = Faithfulness(llm=judge_llm)
    correctness_metric = None
    if args.compute_correctness:
        correctness_metric = AnswerCorrectness(llm=judge_llm, embeddings=embeddings)

    questions = []
    contexts_list = []
    answers = []
    ground_truth_list = []
    faith_scores = []
    corr_scores = [] if args.compute_correctness else None

    for index, query in enumerate(queries):
        print(f'Processing query index {index}.\nQuery is:\n{query}')
        history = get_initial_history()

        response, _, _ = process_conversation_turn(
            history, query, capturing_retriever, completer
        )

        captured_context = capturing_retriever.get_captured_context()
        captured_context = captured_context[:400000]  # Simple truncation to avoid exceeding evaluator context window
        ground_truth = ground_truths[index]

        questions.append(query)
        contexts_list.append([captured_context])  
        answers.append(response)
        ground_truth_list.append(ground_truth)
        
        # Always compute faithfulness
        faithfulness_result = faithfulness_metric.score(
            user_input=query,
            response=response,
            retrieved_contexts=[captured_context]
        )
        faith_scores.append(faithfulness_result)
        
        # Optionally compute correctness
        if args.compute_correctness:
            correctness_result = correctness_metric.score(
                user_input=query,
                response=response,
                reference=ground_truth
            )
            corr_scores.append(correctness_result)

    # Build dataset (kept for compatibility / future use)
    eval_dataset = Dataset.from_dict({
        "question": questions,
        "contexts": contexts_list,
        "answer": answers,
        "ground_truth": ground_truth_list,
    })

    # Write CSV
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["query", "context", "answer", "ground_truth", "faithfulness"]
        if args.compute_correctness:
            header.append("answer_correctness")
        writer.writerow(header)

        for i in range(len(questions)):
            row = [
                questions[i],
                contexts_list[i][0],
                answers[i],
                ground_truth_list[i],
                faith_scores[i]
            ]
            if args.compute_correctness:
                row.append(corr_scores[i])
            writer.writerow(row)

    print(f"Evaluation complete. Results written to {args.output}")
    print(f"Average faithfulness: {sum(faith_scores)/len(faith_scores):.3f} (n={len(faith_scores)})")
    if args.compute_correctness:
        print(f"Average answer_correctness: {sum(corr_scores)/len(corr_scores):.3f} (n={len(corr_scores)})")

if __name__ == "__main__":
    main()