# Operational Ticket Triage Assistant

A retrieval-augmented, agentic assistant for operational ticket triage — built on real GitHub issue data from `microsoft/vscode`, with a measured evaluation framework rather than eyeballed demo outputs.

**Live API:** https://ops-assistant-api.onrender.com/docs
**Live Dashboard:** https://ops-assistant-g8za4qh47r7p7jdywzkcnn.streamlit.app
**Data source:** 1,074 real issues (2,557 chunks) pulled from microsoft/vscode via the GitHub REST API

## What it does

1. **Retrieval** — embeds a new ticket and finds the most similar past issues via cosine similarity in Postgres/pgvector
2. **Grounded generation** — answers the ticket using *only* the retrieved issues, citing specific issue numbers (Gemini)
3. **Agentic triage** — the model autonomously decides to call two tools (`check_duplicate`, `suggest_category`) via native function calling, rather than a hardcoded pipeline

## Architecture

 GitHub Issues API → clean/chunk → fastembed (ONNX) → Postgres/pgvector (Neon)
│
┌───────────────────┴───────────────────┐
retrieval.search agent.triage
│ │
retrieval.generate ──────── Gemini (function calling)
│
FastAPI (Render) + Streamlit (Streamlit Cloud)



## Evaluation

Built a 40-example labeled eval set (bootstrapped from real issue titles as ground truth) and measured, rather than assumed:

| Metric | Score |
|---|---|
| Retrieval hit@1 | 82.5% |
| Retrieval recall@5 | 85% |
| Category suggestion hit rate | 85% |
| Duplicate detection accuracy | 65% → **77.5%** after threshold tuning |

**Two real findings from the eval process, not just the demo:**
- Postgres's `ivfflat` approximate-nearest-neighbor index gave *unreliable* retrieval at this dataset's small scale (~2,500 rows) — confirmed by comparing results before/after switching to exact search. Removed the index entirely.
- The initial duplicate-detection similarity threshold (0.65, a guess) was miscalibrated. Swept candidate thresholds against the eval set and found 0.55 gave a real, measured improvement (65% → 77.5% accuracy) without over-flagging unrelated tickets as duplicates — a tradeoff the eval set's lack of negative examples made necessary to reason about carefully rather than just picking the top accuracy score.

## Known limitations

- Retrieval struggles with very short/vague ticket titles (e.g. "no", "Ai") — insufficient semantic signal for any embedding model
- Eval set has no true negative examples (queries that should *not* match anything), so duplicate-detection false-positive rate isn't directly measured — only inferred by comparing against manual spot checks
- Corpus is a snapshot of ~1,074 recent vscode issues, not the full historical tracker

## Run it locally

```bash
git clone https://github.com/danam-vaishnavi/ops-assistant.git
cd ops-assistant
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# create .env with GITHUB_TOKEN, GOOGLE_API_KEY, DATABASE_URL
python3 -m ingestion.fetch_issues
python3 -m ingestion.clean_and_chunk
python3 -m ingestion.embed_and_load
streamlit run dashboard/app.py
```

## Tech stack

Python · FastAPI · Streamlit · Postgres/pgvector (Neon) · fastembed (ONNX) · Google Gemini (RAG + function-calling agent) · Docker · Render · Streamlit Community Cloud
EOF