import argparse
import json
import requests
import time
from datetime import datetime

# Import the new function from your scrape_eu.py script
from scrape_eu import fetch_eu_trials

# You would have your existing functions here, like:
# fetch_trials, save_to_json, etc.

API_URL = "https://clinicaltrials.gov/api/v2/studies"
# The API_URL is used to access the ClinicalTrials.gov API directly.

def fetch_trials(keyword, max_records=50, status="RECRUITING"):
    """
    Fetches trial data from ClinicalTrials.gov API.
    """
    print(f"Searching for '{keyword}' on ClinicalTrials.gov...")
    params = {
        'format': 'json',
        'query.term': keyword,
        'filter.overallStatus': status,
        'count.overallStatus': 'true',
        'pageSize': max_records,
    }
    
    normalized_trials = []
    try:
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        for study in data.get('studies', []):
            trial = study.get('protocolSection', {})
            results = study.get('resultsSection', {})
            
            # Extract and normalize the data
            normalized_trial = {
                "id": trial.get('identificationModule', {}).get('nctId'),
                "title": trial.get('identificationModule', {}).get('officialTitle', 'No title'),
                "condition": ', '.join(trial.get('conditionsModule', {}).get('conditions', [])),
                "type": "Interventional" if trial.get('designModule', {}).get('studyType') == 'INTERVENTIONAL' else 'Observational',
                "status": trial.get('statusModule', {}).get('overallStatus'),
                "start_date": trial.get('statusModule', {}).get('startDateStruct', {}).get('date'),
                "completion_date": trial.get('statusModule', {}).get('primaryCompletionDateStruct', {}).get('date'),
                "sponsor": trial.get('sponsorCollaboratorsModule', {}).get('leadSponsor', {}).get('leadSponsorName', 'N/A'),
                "source": "ClinicalTrials.gov" # Add source field
            }
            normalized_trials.append(normalized_trial)
            
        print(f"Found {len(normalized_trials)} trial(s) from ClinicalTrials.gov.")
        
    except requests.RequestException as e:
        print(f"Error fetching data from ClinicalTrials.gov: {e}")
        
    return normalized_trials

def save_to_json(data, filename):
    """
    Save the collected data to a JSON file.
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving data to {filename}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Scrape clinical trial data from multiple sources.")
    parser.add_argument("keyword", help="The keyword to search for (e.g., 'medtech').")
    parser.add_argument("--max_records", type=int, default=50, help="Maximum number of records to fetch from ClinicalTrials.gov.")
    parser.add_argument("--status", default="RECRUITING", help="Filter by trial status (e.g., 'RECRUITING').")
    parser.add_argument("--output", default="knowledge_base.json", help="Output filename.")
    
    args = parser.parse_args()
    
    # 1. Fetch data from ClinicalTrials.gov
    all_trials = fetch_trials(args.keyword, args.max_records, args.status)
    
    # 2. Fetch data from EU CTR and extend the list
    print("\nStarting to scrape EU Clinical Trials Register...")
    eu_trials = fetch_eu_trials(args.keyword)
    all_trials.extend(eu_trials)
    
    # 3. Save the combined data
    save_to_json(all_trials, args.output)
    
    print("\n🎉 Scraping complete. Data from both sources has been merged and saved.")

if __name__ == "__main__":
    main()