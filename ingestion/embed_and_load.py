"""
Embeds every chunk locally with sentence-transformers (all-MiniLM-L6-v2,
384-dim, free, no API calls) and loads it into the Postgres `chunks` table
alongside its metadata, so retrieval.py can later run similarity search
directly in the database.
"""
import os
import json
import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

load_dotenv()

CHUNKS_PATH = "data/processed/chunks.json"
MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 64


def main():
    with open(CHUNKS_PATH) as f:
        chunks = json.load(f)

    print(f"Loading embedding model ({MODEL_NAME})... this downloads once, then caches locally.")
    model = SentenceTransformer(MODEL_NAME)

    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, batch_size=BATCH_SIZE, show_progress_bar=True)

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()

    print("Loading into Postgres...")
    for chunk, emb in tqdm(zip(chunks, embeddings), total=len(chunks)):
        cur.execute(
            """
            INSERT INTO chunks (chunk_id, issue_number, title, url, labels, state, created_at, text, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (chunk_id) DO UPDATE SET embedding = EXCLUDED.embedding
            """,
            (
                chunk["chunk_id"], chunk["issue_number"], chunk["title"], chunk["url"],
                chunk["labels"], chunk["state"], chunk["created_at"], chunk["text"],
                emb.tolist(),
            ),
        )
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM chunks")
    total = cur.fetchone()[0]
    print(f"\nDone. Rows in chunks table: {total}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
