import requests
import json
import csv
import logging
import argparse
from typing import List, Dict, Any

API_URL = "https://clinicaltrials.gov/api/v2/studies"

def fetch_trials(
    keyword: str = "medtech",
    max_records: int = 100,
    status: str = None,
    page_size: int = 100
) -> List[Dict[str, Any]]:
    """Fetch clinical trials from ClinicalTrials.gov API with pagination."""
    logging.info("Fetching trials for keyword='%s', status='%s', max_records=%d", keyword, status, max_records)
    trials = []
    page_token = None
    fetched = 0

    while fetched < max_records:
        params = {
            "query.term": keyword,
            "pageSize": min(page_size, max_records - fetched),
            "format": "json",
        }
        if status:
            params["filters.overallStatus"] = status
        if page_token:
            params["pageToken"] = page_token

        try:
            response = requests.get(API_URL, params=params, timeout=30)
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
                    "url": f"https://clinicaltrials.gov/study/{identification_module.get('nctId', '')}",
                }
                trials.append(trial)
            fetched += len(studies)
            page_token = data.get("nextPageToken")
            if not studies or not page_token:
                break
        except requests.exceptions.RequestException as e:
            logging.error("HTTP error: %s", e)
            break
        except Exception as e:
            logging.error("Unexpected error: %s", e)
            break

    logging.info("Fetched %d trials", len(trials))
    return trials[:max_records]

def save_to_json(trials: List[Dict[str, Any]], filename: str):
    """Save trials to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(trials, f, indent=2)
    logging.info("Saved %d records to '%s'", len(trials), filename)

def save_to_csv(trials: List[Dict[str, Any]], filename: str):
    """Save trials to a CSV file."""
    if not trials:
        logging.warning("No trials to save.")
        return
    fieldnames = list(trials[0].keys())
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trials)
    logging.info("Saved %d records to '%s'", len(trials), filename)

def main():
    parser = argparse.ArgumentParser(description="Fetch clinical trials from ClinicalTrials.gov")
    parser.add_argument("--keyword", default="medtech", help="Search keyword")
    parser.add_argument("--max_records", type=int, default=100, help="Maximum number of records")
    parser.add_argument("--status", default=None, help="Trial recruitment status (e.g., RECRUITING)")
    parser.add_argument("--output", default="knowledge_base.json", help="Output filename")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    parser.add_argument("--log", default="info", choices=["debug", "info", "warning", "error"], help="Log level")

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log.upper()))

    trials = fetch_trials(args.keyword, args.max_records, args.status)
    if args.format == "json":
        save_to_json(trials, args.output)
    else:
        save_to_csv(trials, args.output)

if __name__ == "__main__":
    main()