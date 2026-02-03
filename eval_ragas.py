import argparse
import csv
from typing import List

from ragas.metrics.collections import Faithfulness, AnswerCorrectness
from ragas.embeddings import HuggingFaceEmbeddings
from datasets import Dataset
from ragas.llms import llm_factory
from openai import AsyncOpenAI

from src.adapters.retrieval import QdrantCodeRetriever, ContextCapturingRetriever
from src.adapters.llm import GrokCompleter
from src.application.application import get_initial_history, process_conversation_turn

def load_queries(input_path: str) -> List[str]:
    with open(input_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="queries.txt", help="Input file with one query per line")
    parser.add_argument("--ground_truth", default="ground_truth.txt", help="Input file with one ground truth answer per line")
    parser.add_argument("--output", default="ragas_results.csv", help="Output CSV file")
    args = parser.parse_args()

    queries = load_queries(args.input)
    ground_truths = load_queries(args.ground_truth)

    if len(queries) != len(ground_truths):
        raise ValueError(f"Number of queries ({len(queries)}) and ground truths ({len(ground_truths)}) must match")

    base_retriever = QdrantCodeRetriever()
    capturing_retriever = ContextCapturingRetriever(base_retriever)
    completer = GrokCompleter()
    judge_llm = llm_factory('gpt-4o-mini', client=AsyncOpenAI(), max_tokens=16384)
    
    embeddings = HuggingFaceEmbeddings(model="mixedbread-ai/mxbai-embed-large-v1")
    
    faithfulness_metric = Faithfulness(llm=judge_llm)
    correctness_metric = AnswerCorrectness(llm=judge_llm, embeddings=embeddings)
    
    questions = []
    contexts_list = []
    answers = []
    ground_truth_list = []
    metrics_results = {
        "faithfulness": [],
        "answer_correctness": []
    }
    
    for index, query in enumerate(queries):
        print(f'Processing query index {index}.\nQuery is:\n{query}')
        history = get_initial_history()

        response, _, _ = process_conversation_turn(
            history, query, capturing_retriever, completer
        )

        captured_context = capturing_retriever.get_captured_context()
        ground_truth = ground_truths[index]

        questions.append(query)
        contexts_list.append([captured_context])  
        answers.append(response)
        ground_truth_list.append(ground_truth)
        
        faithfulness_result = faithfulness_metric.score(
            user_input=query,
            response=response,
            retrieved_contexts=[captured_context]
        )
        metrics_results["faithfulness"].append(faithfulness_result)
        
        correctness_result = correctness_metric.score(
            user_input=query,
            response=response,
            reference=ground_truth
            
        )
        metrics_results["answer_correctness"].append(correctness_result)

    eval_dataset = Dataset.from_dict({
        "question": questions,
        "contexts": contexts_list,
        "answer": answers,
        "ground_truth": ground_truth_list,
    })

    faith_scores = metrics_results["faithfulness"]
    corr_scores = metrics_results["answer_correctness"]

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["query", "context", "answer", "ground_truth", "faithfulness", "answer_correctness"])
        for q, ctx_list, ans, gt, f_score, c_score in zip(questions, contexts_list, answers, ground_truth_list, faith_scores, corr_scores):
            writer.writerow([q, ctx_list[0], ans, gt, f_score, c_score])

    print(f"Evaluation complete. Results written to {args.output}")
    print(f"Average faithfulness: {sum(faith_scores)/len(faith_scores):.3f} (n={len(faith_scores)})")
    print(f"Average answer_correctness: {sum(corr_scores)/len(corr_scores):.3f} (n={len(corr_scores)})")

if __name__ == "__main__":
    main()