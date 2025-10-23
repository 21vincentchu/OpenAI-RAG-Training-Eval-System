#!/usr/bin/env python3
"""
RAG Evaluation Script using OpenAI Evals Framework
Evaluates the ChromaDB vector store RAG system for accuracy
"""

import json
import os
from pathlib import Path
from typing import Dict, List
from openai import OpenAI
from dotenv import load_dotenv
from chroma_vector_store import query_with_context
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# CONFIG
GROUND_TRUTH_FILE = Path("ground_truth_dataset.jsonl")
EVAL_MODEL = "gpt-4o-mini"  # Model used as judge
RESULTS_FILE = Path("eval_results.json")


def load_ground_truth() -> List[Dict]:
    """Load ground truth Q&A pairs from JSONL file."""
    data = []
    with open(GROUND_TRUTH_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def evaluate_answer_with_llm(question: str, generated: str, ideal: str) -> Dict:
    """
    Use GPT-4 as a judge to evaluate the generated answer.
    Returns score (1-5) and reasoning.
    """
    prompt = f"""You are evaluating a question-answering system's response for a laboratory equipment documentation system.

Question: {question}

Expected Answer (Ground Truth): {ideal}

Generated Answer: {generated}

Rate the generated answer on the following criteria (1-5 scale):
1. Correctness: Does it contain the correct information?
2. Completeness: Does it cover all key points from the ground truth?
3. Conciseness: Is it clear and not overly verbose?

Provide:
- Overall score (1-5, where 5 is perfect)
- Brief reasoning (2-3 sentences)

Respond in JSON format:
{{"score": <1-5>, "reasoning": "<explanation>"}}
"""

    response = client.chat.completions.create(
        model=EVAL_MODEL,
        messages=[
            {"role": "system", "content": "You are an expert evaluator of question-answering systems. Respond only with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)


def calculate_exact_match(generated: str, ideal: str) -> bool:
    """Calculate if answers match exactly (normalized)."""
    return generated.strip().lower() == ideal.strip().lower()


def run_evaluation():
    """Run complete evaluation pipeline."""
    print("=" * 80)
    print("RAG EVALUATION - ChromaDB Vector Store")
    print("=" * 80)

    # Load ground truth
    ground_truth = load_ground_truth()
    print(f"\nLoaded {len(ground_truth)} ground truth Q&A pairs\n")

    results = []
    total_latency = 0
    exact_matches = 0
    total_llm_score = 0

    for i, item in enumerate(ground_truth, 1):
        question = item["question"]
        ideal_answer = item["ideal"]

        print(f"[{i}/{len(ground_truth)}] {question}")

        # Get generated answer from RAG system
        try:
            generated_answer, latency = query_with_context(question)
            total_latency += latency
        except Exception as e:
            print(f"  ✗ ERROR: {e}\n")
            results.append({
                "question": question,
                "ideal": ideal_answer,
                "generated": None,
                "error": str(e)
            })
            continue

        # Check exact match
        is_exact = calculate_exact_match(generated_answer, ideal_answer)
        if is_exact:
            exact_matches += 1

        # Evaluate with LLM judge
        print(f"  Evaluating with LLM judge...")
        eval_result = evaluate_answer_with_llm(question, generated_answer, ideal_answer)
        score = eval_result["score"]
        reasoning = eval_result["reasoning"]
        total_llm_score += score

        print(f"  Score: {score}/5")
        print(f"  Reasoning: {reasoning}")
        print(f"  Latency: {latency:.3f}s")
        print(f"  Exact Match: {'✓' if is_exact else '✗'}\n")

        results.append({
            "question": question,
            "ideal": ideal_answer,
            "generated": generated_answer,
            "latency": latency,
            "exact_match": is_exact,
            "llm_score": score,
            "llm_reasoning": reasoning
        })

    # Calculate aggregate metrics
    num_evaluated = len([r for r in results if "error" not in r])
    avg_latency = total_latency / num_evaluated if num_evaluated > 0 else 0
    avg_llm_score = total_llm_score / num_evaluated if num_evaluated > 0 else 0
    exact_match_rate = exact_matches / num_evaluated if num_evaluated > 0 else 0

    summary = {
        "total_questions": len(ground_truth),
        "evaluated": num_evaluated,
        "errors": len(ground_truth) - num_evaluated,
        "exact_match_rate": exact_match_rate,
        "average_llm_score": avg_llm_score,
        "average_latency": avg_latency,
        "score_distribution": {
            "5": len([r for r in results if r.get("llm_score") == 5]),
            "4": len([r for r in results if r.get("llm_score") == 4]),
            "3": len([r for r in results if r.get("llm_score") == 3]),
            "2": len([r for r in results if r.get("llm_score") == 2]),
            "1": len([r for r in results if r.get("llm_score") == 1])
        }
    }

    # Save results
    output = {
        "summary": summary,
        "detailed_results": results
    }

    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print summary
    print("=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Total Questions:      {summary['total_questions']}")
    print(f"Successfully Evaluated: {summary['evaluated']}")
    print(f"Errors:               {summary['errors']}")
    print(f"\nExact Match Rate:     {summary['exact_match_rate']:.1%}")
    print(f"Average LLM Score:    {summary['average_llm_score']:.2f}/5.00")
    print(f"Average Latency:      {summary['average_latency']:.3f}s")
    print(f"\nScore Distribution:")
    for score in [5, 4, 3, 2, 1]:
        count = summary['score_distribution'][str(score)]
        print(f"  {score}/5: {count} ({count/num_evaluated*100:.1f}%)")
    print(f"\nDetailed results saved to: {RESULTS_FILE}")
    print("=" * 80)


if __name__ == "__main__":
    run_evaluation()
