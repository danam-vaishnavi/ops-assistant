"""
Tools the agent can call while triaging a new ticket. Each one is a plain
Python function with a clear docstring -- Gemini reads the docstring and
type hints to decide when and how to call it, so keep them accurate.
"""
from retrieval.search import search

DUPLICATE_THRESHOLD = 0.55


def check_duplicate(ticket_text: str) -> dict:
    """Checks whether a new ticket is likely a duplicate of an existing,
    recurring issue by finding its closest match in the issue database.

    Args:
        ticket_text: The title and/or description of the new ticket.

    Returns:
        A dict with is_duplicate (bool), matched_issue_number (int or None),
        matched_title (str or None), similarity (float), and url (str or None).
    """
    results = search(ticket_text, k=1)
    if not results:
        return {"is_duplicate": False, "matched_issue_number": None,
                "matched_title": None, "similarity": 0.0, "url": None}

    top = results[0]
    is_dup = top["similarity"] >= DUPLICATE_THRESHOLD
    return {
        "is_duplicate": is_dup,
        "matched_issue_number": top["issue_number"] if is_dup else None,
        "matched_title": top["title"] if is_dup else None,
        "similarity": round(top["similarity"], 3),
        "url": top["url"] if is_dup else None,
    }


def suggest_category(ticket_text: str) -> dict:
    """Suggests a category/label for a new ticket by finding similar past
    issues and looking at what labels were actually used on them.

    Args:
        ticket_text: The title and/or description of the new ticket.

    Returns:
        A dict with suggested_labels (list of str, most common first) and
        based_on_issue_numbers (list of int, the issues that informed the suggestion).
    """
    results = search(ticket_text, k=5)
    label_counts: dict[str, int] = {}
    for r in results:
        for label in r["labels"]:
            label_counts[label] = label_counts.get(label, 0) + 1

    ranked = sorted(label_counts.items(), key=lambda x: -x[1])
    return {
        "suggested_labels": [label for label, _ in ranked[:3]],
        "based_on_issue_numbers": [r["issue_number"] for r in results],
    }
