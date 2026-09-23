"""
Bootstraps a labeled eval set from real issues: each issue's own title
becomes a synthetic query, and its issue_number/labels become the known-
correct answer. If retrieval can't find an issue using its own title,
that's a real, meaningful failure -- not a made-up test case.
"""
import os
import json
import random
import psycopg2
from dotenv import load_dotenv

load_dotenv()
random.seed(42)

N_SAMPLES = 40
OUT_PATH = "eval/eval_set.json"


def main():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ON (issue_number) issue_number, title, labels
        FROM chunks
        WHERE array_length(labels, 1) > 0
        ORDER BY issue_number, chunk_id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    print(f"Issues with at least one label: {len(rows)}")
    sample = random.sample(rows, min(N_SAMPLES, len(rows)))

    eval_set = [
        {"query": title, "expected_issue_number": issue_number, "expected_labels": labels}
        for issue_number, title, labels in sample
    ]

    os.makedirs("eval", exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(eval_set, f, indent=2)

    print(f"Wrote {len(eval_set)} eval examples to {OUT_PATH}")
    print("Sample:", json.dumps(eval_set[0], indent=2))


if __name__ == "__main__":
    main()
