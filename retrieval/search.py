"""
Retrieval over the embedded GitHub issue chunks stored in Postgres/pgvector.
Same embedding model as ingestion, so query and chunk vectors live in the
same space -- this consistency is exactly what makes retrieval work at all.
"""
import os
import psycopg2
from dotenv import load_dotenv
from fastembed import TextEmbedding

load_dotenv()

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model = None


def _load_model():
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=MODEL_NAME)
    return _model


def search(query: str, k: int = 5, fetch_multiplier: int = 4) -> list[dict]:
    """Retrieves the top-k most similar chunks, deduplicated by issue_number
    so a single heavily-chunked issue can't crowd out other relevant issues.
    We over-fetch (k * fetch_multiplier) raw candidates, then keep only each
    issue's single best-scoring chunk, in similarity order, until we have k."""
    model = _load_model()
    query_embedding = list(model.embed([query]))[0].tolist()

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute(
        """
        SELECT chunk_id, issue_number, title, url, labels, state, text,
               1 - (embedding <=> %s::vector) AS similarity
        FROM chunks
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (query_embedding, query_embedding, k * fetch_multiplier),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    seen_issues = set()
    results = []
    for row in rows:
        issue_number = row[1]
        if issue_number in seen_issues:
            continue
        seen_issues.add(issue_number)
        results.append({
            "chunk_id": row[0],
            "issue_number": row[1],
            "title": row[2],
            "url": row[3],
            "labels": row[4],
            "state": row[5],
            "text": row[6],
            "similarity": float(row[7]),
        })
        if len(results) >= k:
            break
    return results


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "extension host crashes on startup"
    print(f"Query: {query}\n")
    for r in search(query, k=5):
        print(f"[{r['similarity']:.3f}] #{r['issue_number']} - {r['title']}")
        print(f"    labels: {r['labels']} | state: {r['state']}")
        print(f"    {r['url']}")
        print()
