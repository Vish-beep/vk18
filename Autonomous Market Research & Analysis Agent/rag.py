from evaluation import evaluate_answer
from ollama_client import get_embedding, generate_text
from vector_store import search
from config import TOP_K

def retrieve_documents(question, top_k=TOP_K):
    query_embedding = get_embedding(question)
    return search(query_embedding, top_k=top_k)

def build_prompt(question, documents):
    source_blocks = []
    for i, doc in enumerate(documents, start=1):
        source_blocks.append(
            f"SOURCE {i} | FILE: {doc['source']} | "
            f"SCORE: {doc['score']}\n{doc['text']}"
        )
    context = "\n\n".join(source_blocks)
    return f"""
You are a grounded enterprise document research assistant.

Answer ONLY from the supplied sources.
Do not use outside knowledge.
Do not invent or infer unsupported facts.
If the sources do not contain the answer, say:
"The answer is not available in the retrieved sources."

At the end, include a short "Sources used" line listing the source numbers.

QUESTION:
{question}

RETRIEVED SOURCES:
{context}

ANSWER:
"""

def answer_question(question):
    documents = retrieve_documents(question)
    if not documents:
        return {
            "answer": "No indexed documents are available.",
            "sources": [],
            "evaluation": {
                "grounded": False,
                "grounding_score": 0.0,
                "source_count": 0,
            },
        }
    answer = generate_text(build_prompt(question, documents))
    return {
        "answer": answer,
        "sources": documents,
        "evaluation": evaluate_answer(answer, documents),
    }
