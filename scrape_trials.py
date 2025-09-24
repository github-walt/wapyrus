# scrape_trials.py
import requests
import json

def fetch_trials(keyword="medtech", max_records=50):
    """Fetch clinical trials from ClinicalTrials.gov API"""
    trials = []
    
    try:
        params = {
            "query.term": keyword,
            "pageSize": min(max_records, 100),
            "format": "json"
        }
        
        response = requests.get(
            "https://clinicaltrials.gov/api/v2/studies", 
            params=params, 
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        studies = data.get("studies", [])
        
        for study in studies:
            protocol_section = study.get("protocolSection", {})
            identification_module = protocol_section.get("identificationModule", {})
            status_module = protocol_section.get("statusModule", {})
            sponsor_module = protocol_section.get("sponsorCollaboratorsModule", {})
            
            trial = {
                "id": identification_module.get("nctId", "Unknown"),
                "title": identification_module.get("briefTitle", "No title"),
                "condition": identification_module.get("conditions", []),
                "type": protocol_section.get("designModule", {}).get("studyType", "Unknown"),
                "status": status_module.get("overallStatus", "Unknown"),
                "sponsor": sponsor_module.get("leadSponsor", {}).get("name", "Unknown"),
                "start_date": status_module.get("startDateStruct", {}).get("date", "Unknown"),
            }
            trials.append(trial)
        
        print(f"✅ Successfully fetched {len(trials)} trials")
        return trials
        
    except Exception as e:
        print(f"❌ Error fetching trials: {e}")
        return []

def save_to_json(trials, filename="knowledge_base.json"):
    """Save trials to JSON file"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(trials, f, indent=2)

def update_knowledge_base():
    """Update the knowledge base with new trials"""
    trials = fetch_trials()
    save_to_json(trials)
    return trials