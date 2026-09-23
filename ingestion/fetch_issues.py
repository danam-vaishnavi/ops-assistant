"""
Pulls issues from microsoft/vscode via the GitHub REST API and saves the
raw, untouched response to data/raw/. Cleaning/chunking happens later,
separately -- this script's only job is getting real data onto disk.
"""
import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["GITHUB_TOKEN"]
REPO = "microsoft/vscode"
OUT_PATH = "data/raw/vscode_issues.json"
NUM_PAGES = 20          # 100 issues per page -> ~2000 issues
PER_PAGE = 100

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}

def fetch_issues():
    all_issues = []
    for page in range(1, NUM_PAGES + 1):
        url = f"https://api.github.com/repos/{REPO}/issues"
        params = {
            "state": "all",       # open AND closed -- closed issues often have resolutions in comments
            "per_page": PER_PAGE,
            "page": page,
            "sort": "created",
            "direction": "desc",
        }
        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            print(f"No more issues at page {page}, stopping.")
            break

        # GitHub's /issues endpoint also returns pull requests -- filter those out
        batch = [i for i in batch if "pull_request" not in i]
        all_issues.extend(batch)
        print(f"Page {page}: fetched {len(batch)} issues (total so far: {len(all_issues)})")

        remaining = int(resp.headers.get("X-RateLimit-Remaining", 1))
        if remaining < 5:
            print("Approaching rate limit, sleeping 60s...")
            time.sleep(60)
        else:
            time.sleep(0.5)  # be polite even with a token

    return all_issues

def main():
    os.makedirs("data/raw", exist_ok=True)
    issues = fetch_issues()
    with open(OUT_PATH, "w") as f:
        json.dump(issues, f)
    print(f"\nSaved {len(issues)} issues to {OUT_PATH}")

if __name__ == "__main__":
    main()
