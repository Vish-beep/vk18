import re
from collections import Counter

def _tokens(text):
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())

def grounding_score(answer, documents):
    answer_tokens = set(_tokens(answer))
    source_tokens = set(_tokens(" ".join(d.get("text", "") for d in documents)))
    if not answer_tokens:
        return 0.0
    return len(answer_tokens & source_tokens) / len(answer_tokens)

def evaluate_answer(answer, documents):
    score = grounding_score(answer, documents)
    return {
        "grounded": score >= 0.20,
        "grounding_score": round(score, 4),
        "source_count": len(documents),
    }

def precision_at_k(retrieved_ids, relevant_ids, k):
    retrieved = retrieved_ids[:k]
    if not retrieved:
        return 0.0
    return sum(1 for x in retrieved if x in relevant_ids) / len(retrieved)

def recall_at_k(retrieved_ids, relevant_ids, k):
    if not relevant_ids:
        return 0.0
    retrieved = set(retrieved_ids[:k])
    return len(retrieved & set(relevant_ids)) / len(set(relevant_ids))

def mrr(retrieved_ids, relevant_ids):
    relevant = set(relevant_ids)
    for rank, item_id in enumerate(retrieved_ids, start=1):
        if item_id in relevant:
            return 1.0 / rank
    return 0.0

def evaluate_retrieval(retrieved_ids, relevant_ids, k=3):
    return {
        "precision_at_k": round(precision_at_k(retrieved_ids, relevant_ids, k), 4),
        "recall_at_k": round(recall_at_k(retrieved_ids, relevant_ids, k), 4),
        "mrr": round(mrr(retrieved_ids, relevant_ids), 4),
        "k": k,
    }
