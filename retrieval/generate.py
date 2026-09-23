"""
RAG generation: takes a user question, retrieves relevant issue chunks,
and asks Gemini to answer grounded ONLY in that retrieved context, citing
the specific issue(s) it used. This is the piece that turns raw retrieval
results into an actual usable answer.
"""
import os
import time
from google import genai
from google.genai import errors as genai_errors
from dotenv import load_dotenv
from retrieval.search import search

load_dotenv()
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

MODEL_NAME = "gemini-flash-lite-latest"

SYSTEM_PROMPT = """You are an operational assistant that helps triage software issues by finding and summarizing similar past issues.

Rules you MUST follow:
1. Answer ONLY using the retrieved issues provided below. Do not use any outside knowledge.
2. Every claim you make must cite the specific issue number(s) it came from, like "(#336233)".
3. If the retrieved issues do not actually answer the question, say so clearly instead of guessing.
4. Be concise -- a few sentences, not an essay.
"""


def build_context(chunks: list[dict]) -> str:
    parts = []
    for c in chunks:
        parts.append(
            f"Issue #{c['issue_number']} - {c['title']} (state: {c['state']})\n"
            f"{c['text']}\n"
        )
    return "\n---\n".join(parts)


def _generate_with_retry(prompt: str, max_retries: int = 4):
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=MODEL_NAME, contents=prompt)
        except genai_errors.ServerError as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt  # 1s, 2s, 4s, 8s
            print(f"Model overloaded (attempt {attempt + 1}/{max_retries}), retrying in {wait}s...")
            time.sleep(wait)


def answer(question: str, k: int = 5) -> dict:
    retrieved = search(question, k=k)
    context = build_context(retrieved)

    prompt = f"{SYSTEM_PROMPT}\n\nRetrieved issues:\n{context}\n\nQuestion: {question}\n\nAnswer:"

    response = _generate_with_retry(prompt)

    return {
        "question": question,
        "answer": response.text,
        "sources": [
            {"issue_number": c["issue_number"], "title": c["title"], "url": c["url"]}
            for c in retrieved
        ],
    }


if __name__ == "__main__":
    import sys
    question = " ".join(sys.argv[1:]) or "Why might the extension host crash on startup?"
    result = answer(question)
    print("Question:", result["question"])
    print("\nAnswer:\n", result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"  #{s['issue_number']} - {s['title']} ({s['url']})")
