import requests
import json

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
MAX_RECORDS = 500  # Total number of trials to fetch
PAGE_SIZE = 100    # Number of trials per page

def clean_list(items):
    return [item for item in items if item.strip()]

def normalize(value):
    return value.strip() if isinstance(value, str) and value.strip() else None

import requests

def fetch_trials(keyword="medtech", max_records=500):
    trials = []
    page_token = None
    fetched = 0

    while fetched < max_records:
        params = {
            "query.term": keyword,
            "pageSize": 100,
            "format": "json"
        }
        if page_token:
            params["pageToken"] = page_token

        response = requests.get("https://clinicaltrials.gov/api/v2/studies", params=params)

        if response.status_code != 200:
            print(f"❌ API returned status {response.status_code}")
            break

        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            print("❌ Failed to decode JSON from API response")
            break

        studies = data.get("studies", [])
        # ... continue parsing trials as before ...

        fetched += len(studies)
        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return trials


def save_to_json(trials, filename="knowledge_base.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(trials, f, indent=2)

if __name__ == "__main__":
    trials = fetch_trials()
    save_to_json(trials)
    print(f"Saved {len(trials)} trials to knowledge_base.json")
    
def update_knowledge_base(keyword="medtech", filename="knowledge_base.json"):
    trials = fetch_trials(keyword)
    save_to_json(trials, filename)

    
    
