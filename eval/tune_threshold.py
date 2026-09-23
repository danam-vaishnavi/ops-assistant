"""
Sweeps candidate similarity thresholds for duplicate detection against the
eval set, so DUPLICATE_THRESHOLD in agent/tools.py is chosen from real data
instead of a guess. Reuses the same top-1 retrieval call for every threshold
tested, so this stays fast even with several candidates.
"""
import json
from retrieval.search import search

EVAL_SET_PATH = "eval/eval_set.json"
CANDIDATE_THRESHOLDS = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]


def main():
    with open(EVAL_SET_PATH) as f:
        eval_set = json.load(f)

    # Get each query's top-1 match + similarity once
    top1_data = []
    for item in eval_set:
        result = search(item["query"], k=1)
        if not result:
            continue
        top1_data.append({
            "correct_match": result[0]["issue_number"] == item["expected_issue_number"],
            "similarity": result[0]["similarity"],
        })

    print(f"{'Threshold':<10}{'Accuracy':<10}{'Flagged as duplicate':<22}")
    for t in CANDIDATE_THRESHOLDS:
        correct = sum(1 for d in top1_data if d["correct_match"] and d["similarity"] >= t)
        flagged = sum(1 for d in top1_data if d["similarity"] >= t)
        accuracy = correct / len(top1_data)
        print(f"{t:<10}{accuracy:<10.3f}{flagged}/{len(top1_data)}")


if __name__ == "__main__":
    main()
