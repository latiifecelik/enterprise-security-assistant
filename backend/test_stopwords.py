import re
from sklearn.feature_extraction.text import TfidfVectorizer
from app.db.database import get_db
from app.db import repository

with get_db() as conn:
    chunks = repository.get_all_chunks(conn)

texts = [c["content"] for c in chunks]

vec = TfidfVectorizer(
    stop_words="english",
    strip_accents="unicode",
    lowercase=True,
    ngram_range=(1, 2),
    min_df=1,
    sublinear_tf=True
)
matrix = vec.fit_transform(texts)

from sklearn.metrics.pairwise import cosine_similarity

queries = [
    "How do I bake a chocolate cake?",
    "What is the capital of France?",
    "Tell me a joke about dogs",
    "How to change a car tire?",
    "What is the weather in Paris?",
    "What is the meaning of life?",
    "How should I investigate repeated failed SSH logins?",
    "What is password spraying?",
    "What log sources should I check for brute force?",
    "How to respond to phishing emails?"
]

print("=== WITH STOP WORDS ===")
for q in queries:
    # also check if any content word in q appears in vocabulary
    words = re.findall(r"\b[a-zA-Z]{3,}\b", q.lower())
    matched_features = [w for w in words if w in vec.vocabulary_]
    
    q_vec = vec.transform([q])
    sim = cosine_similarity(q_vec, matrix).flatten()
    best = sim.max()
    print(f"Query: '{q}'")
    print(f"   Matched vocab terms: {matched_features}")
    print(f"   Max similarity: {best:.4f}")
