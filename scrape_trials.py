import requests
import json

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
MAX_RECORDS = 500  # Total number of trials to fetch
PAGE_SIZE = 100    # Number of trials per page

def clean_list(items):
    return [item for item in items if item.strip()]

def normalize(value):
    return value.strip() if isinstance(value, str) and value.strip() else None

def fetch_trials(keyword="medtech", max_records=MAX_RECORDS):
    trials = []
    page_token = None
    fetched = 0

    while fetched < max_records:
        params = {
            "query.term": keyword,
            "pageSize": PAGE_SIZE,
            "format": "json"
        }
        if page_token:
            params["pageToken"] = page_token

        response = requests.get(BASE_URL, params=params)
        data = response.json()

        studies = data.get("studies", [])
        for study in studies:
            protocol = study.get("protocolSection", {})
            trial = {
                "id": normalize(protocol.get("identificationModule", {}).get("nctId", "")),
                "title": normalize(protocol.get("identificationModule", {}).get("briefTitle", "")),
                "condition": clean_list(protocol.get("conditionsModule", {}).get("conditions", [])),
                "intervention": clean_list([
                    i.get("name", "") for i in protocol.get("armsInterventionsModule", {}).get("interventions", [])
                ]),
                "phase": normalize(protocol.get("designModule", {}).get("phase", "")),
                "type": normalize(protocol.get("designModule", {}).get("studyType", "")),
                "status": normalize(protocol.get("statusModule", {}).get("overallStatus", "")),
                "start_date": normalize(protocol.get("statusModule", {}).get("startDateStruct", {}).get("date", "")),
                "completion_date": normalize(protocol.get("statusModule", {}).get("completionDateStruct", {}).get("date", "")),
                "sponsor": normalize(protocol.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name", "")),
                "location": clean_list([
                    loc.get("locationFacility", "") for loc in protocol.get("contactsLocationsModule", {}).get("locations", [])
                ]),
                "enrollment": normalize(protocol.get("designModule", {}).get("enrollmentInfo", {}).get("actualEnrollment", ""))
}

            trials.append(trial)

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
    
    
