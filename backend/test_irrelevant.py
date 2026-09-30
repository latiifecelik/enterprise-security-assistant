from app.rag.retriever import retriever
from app.services.document_service import _rebuild_index
_rebuild_index()

queries = [
    "How do I bake a chocolate cake?",
    "What is the capital of France?",
    "Tell me a joke about dogs",
    "How to change a car tire?",
    "What is the weather in Paris?",
    "How should I investigate repeated failed SSH logins?",
    "What is password spraying?",
    "What log sources should I check for brute force?"
]

for q in queries:
    res = retriever.retrieve(q, top_k=3)
    best_score = res[0]["score"] if res else 0.0
    print(f"Query: '{q}' -> matches: {len(res)}, best score: {best_score}")
