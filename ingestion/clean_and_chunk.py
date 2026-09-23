"""
Cleans raw GitHub issue JSON into text chunks ready for embedding.
Each issue's title + body (+ top comments, if any) becomes one or more
chunks, each carrying metadata so retrieved results can be cited back
to a real issue number and URL.
"""
import json
import re
import os

RAW_PATH = "data/raw/vscode_issues.json"
OUT_PATH = "data/processed/chunks.json"

CHUNK_SIZE = 1000       # characters per chunk
CHUNK_OVERLAP = 150     # characters of overlap between consecutive chunks


def strip_noise(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)              # strip HTML tags
    text = re.sub(r"```.*?```", " ", text, flags=re.S)  # strip code blocks (too noisy for retrieval)
    text = re.sub(r"!\[.*?\]\(.*?\)", " ", text)        # strip markdown images
    text = re.sub(r"\[([^\]]*)\]\(.*?\)", r"\1", text)  # markdown links -> keep just the link text
    text = re.sub(r"\s+", " ", text).strip()            # collapse whitespace
    return text


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    if len(text) <= size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def main():
    with open(RAW_PATH) as f:
        issues = json.load(f)

    records = []
    skipped = 0
    for issue in issues:
        title = strip_noise(issue.get("title", ""))
        body = strip_noise(issue.get("body", ""))
        full_text = f"{title}. {body}".strip()

        if len(full_text) < 30:   # too short to be useful for retrieval
            skipped += 1
            continue

        labels = [l["name"] for l in issue.get("labels", [])]
        chunks = chunk_text(full_text, CHUNK_SIZE, CHUNK_OVERLAP)

        for i, chunk in enumerate(chunks):
            records.append({
                "chunk_id": f"{issue['number']}-{i}",
                "issue_number": issue["number"],
                "title": issue["title"],
                "url": issue["html_url"],
                "labels": labels,
                "state": issue["state"],
                "created_at": issue["created_at"],
                "text": chunk,
            })

    os.makedirs("data/processed", exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(records, f)

    print(f"Issues processed: {len(issues)}")
    print(f"Issues skipped (too short): {skipped}")
    print(f"Total chunks produced: {len(records)}")
    print(f"Avg chunks per issue: {len(records) / max(1, len(issues) - skipped):.2f}")


if __name__ == "__main__":
    main()
