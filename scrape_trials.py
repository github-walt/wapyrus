import requests
import json
import os

def fetch_trials(keyword="medical device", max_results=10):
    """
    Fetch trials from the ClinicalTrials.gov v2 API.
    Returns a list of simplified trial dictionaries.
    """
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.term": keyword,
        "pageSize": max_results,
        "format": "json"   # request JSON output
    }

    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        print("URL:", response.url)
        print("Response status:", response.status_code)
        print("Response text:", response.text)
        raise Exception(f"Failed to fetch data: {response.status_code}")

    data = response.json()

    trials = data.get("studies", [])
    signals = []

    for t in trials:
        protocol = t.get("protocolSection", {})
        id_module = protocol.get("identificationModule", {})
        ct_id = id_module.get("nctId")
        title = id_module.get("officialTitle") or id_module.get("briefTitle")

        cond_module = protocol.get("conditionsModule", {})
        conditions = cond_module.get("conditions", [])

        signals.append({
            "id": ct_id,
            "title": title,
            "conditions": conditions
        })

    return signals


def update_knowledge_base(trials, filename="knowledge_base.json"):
    """
    Save trials into knowledge_base.json, appending if file exists.
    """
    # Load existing knowledge base if present
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                kb = json.load(f)
            except json.JSONDecodeError:
                kb = []
    else:
        kb = []

    # Extend and deduplicate by trial id
    existing_ids = {entry["id"] for entry in kb if "id" in entry}
    for trial in trials:
        if trial["id"] not in existing_ids:
            kb.append(trial)

    # Save back
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)

    print(f"✅ knowledge_base.json updated with {len(trials)} trials. Total now: {len(kb)}")


if __name__ == "__main__":
    print("🔍 Fetching clinical trial signals…")
    trials = fetch_trials(keyword="medical device", max_results=5)
    update_knowledge_base(trials)
