import requests
import json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
MAX_RECORDS = 500  # Total number of trials to fetch
PAGE_SIZE = 100    # Number of trials per page

def clean_list(items):
    return [item for item in items if item.strip()]

def normalize(value):
    return value.strip() if isinstance(value, str) and value.strip() else None

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, json.JSONDecodeError))
)
def make_api_request(params):
    """Make API request with retry logic"""
    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def fetch_trials(keyword="medtech", max_records=500):
    trials = []
    page_token = None
    fetched = 0

    while fetched < max_records:
        params = {
            "query.term": keyword,
            "pageSize": min(100, max_records - fetched),
            "format": "json"
        }
        if page_token:
            params["pageToken"] = page_token

        try:
            data = make_api_request(params)
            
            studies = data.get("studies", [])
            for study in studies:
                protocol_section = study.get("protocolSection", {})
                identification_module = protocol_section.get("identificationModule", {})
                status_module = protocol_section.get("statusModule", {})
                sponsor_module = protocol_section.get("sponsorCollaboratorsModule", {})
                
                trial = {
                    "id": identification_module.get("nctId"),
                    "title": identification_module.get("briefTitle"),
                    "condition": clean_list(identification_module.get("conditions", [])),
                    "intervention": clean_list([i.get("interventionName", "") 
                                              for i in protocol_section.get("armsInterventionsModule", {}).get("interventions", [])]),
                    "phase": protocol_section.get("designModule", {}).get("phases", [None])[0] if protocol_section.get("designModule", {}).get("phases") else None,
                    "type": protocol_section.get("designModule", {}).get("studyType"),
                    "status": status_module.get("overallStatus"),
                    "start_date": status_module.get("startDateStruct", {}).get("date"),
                    "completion_date": status_module.get("completionDateStruct", {}).get("date"),
                    "sponsor": sponsor_module.get("leadSponsor", {}).get("name"),
                    "location": [],
                    "enrollment": protocol_section.get("designModule", {}).get("enrollmentInfo", {}).get("count")
                }
                # Clean None values
                trial = {k: v for k, v in trial.items() if v is not None}
                trials.append(trial)
            
            fetched += len(studies)
            page_token = data.get("nextPageToken")
            if not page_token:
                break
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            break
        except json.JSONDecodeError:
            print("❌ JSON decode failed")
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

    
    
