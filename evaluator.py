from metrics.faithfulness import score_faithfulness
from metrics.relevance import score_relevance
from metrics.context_precision import score_context_precision
from rouge_score import rouge_scorer
import json
import os
from datetime import datetime

SCORES_FILE = "scores.json"
PASS_THRESHOLD = 0.6

def score_rouge(answer: str, context: str) -> float:
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(context, answer)
    return round(scores['rougeL'].fmeasure, 2)

def load_scores() -> list:
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_scores(scores: list):
    with open(SCORES_FILE, 'w') as f:
        json.dump(scores, f, indent=2)

def evaluate(question: str, answer: str, context: str) -> dict:
    print("Running faithfulness....")
    faithfulness = score_faithfulness(question, answer, context)

    print("Running Relevance.....")
    relevance = score_relevance(question, answer)

    print("Running Context Precision....")
    precision = score_context_precision(question, context)

    print("Running ROUGE....")
    rouge = score_rouge(answer, context)

    avg_llm_score = round(
        (faithfulness["score"] + relevance["score"] + precision["score"]) / 3, 2
    )

    verdict = "PASS" if avg_llm_score >= PASS_THRESHOLD else "FAIL"

    result = {
        "id": datetime.now().isoformat(),
        "question": question,
        "answer": answer,
        "context": context[:500],
        "scores": {
            "faithfulness": faithfulness["score"],
            "relevance": relevance["score"],
            "context_precision": precision["score"],
            "rouge_l": rouge,
            "average": avg_llm_score
        },
        "reasoning": {
            "faithfulness": faithfulness["reasoning"],
            "relevance": relevance["reasoning"],
            "context_precision": precision["reasoning"]
        },
        "verdict": verdict,
        "timestamp": datetime.now().isoformat()
    }

    all_scores = load_scores()
    all_scores.append(result)

    # Keep only the last 500 entries.
    if len(all_scores) > 500:
        all_scores = all_scores[-500:]

    save_scores(all_scores)

    return result