CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    issue_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    labels TEXT[],
    state TEXT,
    created_at TIMESTAMPTZ,
    text TEXT NOT NULL,
    embedding vector(384)
);

-- No ivfflat index: exact search is more reliable at this dataset size (see Step 6 finding).
