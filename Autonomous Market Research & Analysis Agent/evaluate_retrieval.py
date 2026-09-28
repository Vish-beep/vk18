from evaluation import evaluate_retrieval

# Replace these IDs with IDs from your own labelled evaluation set.
# This script demonstrates Precision@3, Recall@3 and MRR.
retrieved = ["chunk-1", "chunk-7", "chunk-3"]
relevant = {"chunk-7", "chunk-3"}

print(evaluate_retrieval(retrieved, relevant, k=3))
