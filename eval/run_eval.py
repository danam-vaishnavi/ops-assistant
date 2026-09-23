"""
Runs the eval set through retrieval + the agentic tools (NOT the LLM --
these are deterministic, so we can measure them cheaply and fast) and
reports precision/recall-style metrics. This is what separates a real
evaluation from eyeballing a few example outputs.
"""
import json
from retrieval.search import search
from agent.tools import check_duplicate, suggest_category

EVAL_SET_PATH = "eval/eval_set.json"
RESULTS_PATH = "eval/eval_results.json"
K = 5


def main():
    with open(EVAL_SET_PATH) as f:
        eval_set = json.load(f)

    results = []
    hit_at_1 = 0
    recall_at_k = 0
    category_hits = 0
    duplicate_correct = 0

    for item in eval_set:
        query = item["query"]
        expected_issue = item["expected_issue_number"]
        expected_labels = set(item["expected_labels"])

        # --- Retrieval ---
        retrieved = search(query, k=K)
        retrieved_issue_numbers = [r["issue_number"] for r in retrieved]
        top1_correct = retrieved_issue_numbers[0] == expected_issue if retrieved_issue_numbers else False
        in_top_k = expected_issue in retrieved_issue_numbers
        hit_at_1 += int(top1_correct)
        recall_at_k += int(in_top_k)

        # --- Category suggestion ---
        cat_result = suggest_category(query)
        predicted_labels = set(cat_result["suggested_labels"])
        category_hit = len(predicted_labels & expected_labels) > 0
        category_hits += int(category_hit)

        # --- Duplicate detection (self-match sanity check) ---
        dup_result = check_duplicate(query)
        dup_correct = dup_result["is_duplicate"] and dup_result["matched_issue_number"] == expected_issue
        duplicate_correct += int(dup_correct)

        results.append({
            "query": query,
            "expected_issue": expected_issue,
            "top1_correct": top1_correct,
            "in_top_k": in_top_k,
            "category_hit": category_hit,
            "predicted_labels": list(predicted_labels),
            "expected_labels": list(expected_labels),
            "duplicate_correct": dup_correct,
        })

    n = len(eval_set)
    summary = {
        "n_examples": n,
        "hit_at_1": round(hit_at_1 / n, 3),
        f"recall_at_{K}": round(recall_at_k / n, 3),
        "category_hit_rate": round(category_hits / n, 3),
        "duplicate_detection_accuracy": round(duplicate_correct / n, 3),
    }

    with open(RESULTS_PATH, "w") as f:
        json.dump({"summary": summary, "details": results}, f, indent=2)

    print(json.dumps(summary, indent=2))
    print(f"\nFull per-example results saved to {RESULTS_PATH}")

    failures = [r for r in results if not r["top1_correct"]]
    if failures:
        print(f"\n{len(failures)} retrieval misses (worth a look for error analysis):")
        for f_ in failures[:5]:
            print(f"  Query: {f_['query'][:70]}")
            print(f"    Expected #{f_['expected_issue']}")


if __name__ == "__main__":
    main()
