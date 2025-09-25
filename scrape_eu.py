import requests
import json
import logging
from datetime import datetime
import argparse
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import quote, urljoin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_eu_trials(keyword, use_sample=False):
    """
    Fetches comprehensive EU clinical trial data.
    
    Args:
        keyword: Search term for trials
        use_sample: If True, return sample data instead of making API calls
    """
    # Validate inputs
    if not keyword or not keyword.strip():
        logger.error("❌ Invalid keyword provided")
        return []
    
    if use_sample:
        logger.info("📋 Using sample EU data (development mode)")
        return get_comprehensive_eu_sample_data(keyword)
    
    logger.info(f"🔍 Searching for '{keyword}' on EU Clinical Trials Register...")
    
    try:
        # Attempt real EU scraping
        real_trials = attempt_real_eu_scraping(keyword)
        if real_trials:
            logger.info(f"✅ Successfully fetched {len(real_trials)} real EU trials")
            return real_trials
        else:
            logger.warning("⚠️ No real EU trials found, returning empty list")
            return []
    except Exception as e:
        logger.error(f"❌ EU scraping failed: {e}")
        return []

def attempt_real_eu_scraping(keyword):
    """
    Attempt to scrape real data from EU Clinical Trials Register.
    This is a basic implementation that can be enhanced.
    """
    try:
        # EU CTR search URL
        base_url = "https://www.clinicaltrialsregister.eu/ctr-search/search"
        
        # Parameters for the search
        params = {
            'query': keyword,
            'page': 1
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info(f"🌐 Attempting to scrape EU CTR for '{keyword}'...")
        
        response = requests.get(base_url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse the HTML response
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for trial results (this is a basic implementation)
        # The actual EU CTR structure may require more sophisticated parsing
        trial_elements = soup.find_all('div', class_='result')
        
        trials = []
        for element in trial_elements[:10]:  # Limit to first 10 results
            try:
                # Extract basic information (this would need to be adapted to actual HTML structure)
                title_elem = element.find('h3') or element.find('a')
                title = title_elem.get_text(strip=True) if title_elem else f"EU Trial for {keyword}"
                
                # Generate a basic trial structure
                trial = {
                    "id": f"EU-{len(trials)+1:04d}-{keyword[:4].upper()}",
                    "title": title,
                    "condition": keyword.title(),
                    "type": "Interventional",
                    "status": "Unknown",
                    "start_date": "",
                    "completion_date": "",
                    "sponsor": "EU Sponsor",
                    "source": "EU Clinical Trials Register"
                }
                trials.append(trial)
                
            except Exception as e:
                logger.warning(f"⚠️ Error parsing EU trial element: {e}")
                continue
        
        if trials:
            logger.info(f"✅ Scraped {len(trials)} trials from EU CTR")
            return [normalize_trial_data(trial) for trial in trials]
        else:
            logger.warning("⚠️ No trials found in EU CTR response")
            return []
            
    except requests.RequestException as e:
        logger.error(f"❌ Network error accessing EU CTR: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Error scraping EU CTR: {e}")
        raise

def get_comprehensive_eu_sample_data(keyword):
    """Return comprehensive realistic EU trial data"""
    
    base_trials = [
        {
            "eudraCTId": "2023-001234-56",
            "publicTitle": "Multicenter Clinical Investigation of Novel Cardiac Ablation Catheter for Atrial Fibrillation",
            "condition": "Paroxysmal Atrial Fibrillation",
            "studyType": "Interventional",
            "status": "Ongoing",
            "startDate": "2023-03-15",
            "completionDate": "2025-12-31",
            "mainSponsor": "European Cardiovascular Research Institute"
        },
        {
            "eudraCTId": "2023-002345-67",
            "publicTitle": "Post-Market Clinical Follow-up Study of Next-Generation Drug-Eluting Coronary Stent System",
            "condition": "Coronary Artery Disease, Ischemic Heart Disease",
            "studyType": "Observational",
            "status": "Active, not recruiting",
            "startDate": "2022-11-01",
            "completionDate": "2024-10-31",
            "mainSponsor": "EuroVascular Medical"
        },
        {
            "eudraCTId": "2024-001456-78",
            "publicTitle": "Prospective Study of AI-Based Software for Automated Detection of Diabetic Retinopathy",
            "condition": "Diabetic Retinopathy, Diabetes Mellitus",
            "studyType": "Diagnostic",
            "status": "Recruiting",
            "startDate": "2024-01-20",
            "completionDate": "2026-06-30",
            "mainSponsor": "MedTech AI Solutions GmbH"
        },
        {
            "eudraCTId": "2023-003567-89",
            "publicTitle": "Clinical Evaluation of Wearable Continuous Vital Signs Monitoring System for Hospitalized Patients",
            "condition": "Patient Monitoring, Hospitalized Patients",
            "studyType": "Interventional",
            "status": "Completed",
            "startDate": "2021-09-01",
            "completionDate": "2023-08-31",
            "mainSponsor": "EuroCare Monitoring Systems"
        },
        {
            "eudraCTId": "2024-002678-90",
            "publicTitle": "Randomized Controlled Trial of Robotic-Assisted Surgical System for Prostatectomy",
            "condition": "Prostate Cancer, Localized Prostate Neoplasms",
            "studyType": "Interventional",
            "status": "Not yet recruiting",
            "startDate": "2024-06-01",
            "completionDate": "2027-05-31",
            "mainSponsor": "European Urological Robotics Foundation"
        },
        {
            "eudraCTId": "2023-004789-01",
            "publicTitle": "Multicenter Study of Novel Bioabsorbable Scaffold for Coronary Revascularization",
            "condition": "Coronary Artery Stenosis, Myocardial Ischemia",
            "studyType": "Interventional",
            "status": "Ongoing",
            "startDate": "2023-08-01",
            "completionDate": "2026-07-31",
            "mainSponsor": "BioScaffold Europe Ltd."
        },
        {
            "eudraCTId": "2024-003890-12",
            "publicTitle": "Clinical Performance Study of Smart Insulin Delivery System with Closed-Loop Control",
            "condition": "Type 1 Diabetes, Insulin-Dependent Diabetes",
            "studyType": "Interventional",
            "status": "Recruiting",
            "startDate": "2024-02-15",
            "completionDate": "2025-12-31",
            "mainSponsor": "Diabetes Technology Europe"
        },
        {
            "eudraCTId": "2023-005901-23",
            "publicTitle": "Post-Market Surveillance of Advanced MRI-Compatible Neuromodulation System",
            "condition": "Parkinson Disease, Essential Tremor",
            "studyType": "Observational",
            "status": "Active, not recruiting",
            "startDate": "2022-12-01",
            "completionDate": "2024-11-30",
            "mainSponsor": "NeuroTech Europe SA"
        }
    ]
    
    # Add keyword-specific trials
    keyword_trials = []
    if "cardiac" in keyword.lower():
        keyword_trials.extend([
            {
                "eudraCTId": "2024-004012-34",
                "publicTitle": "Study of Novel Transcatheter Heart Valve System for Aortic Stenosis",
                "condition": "Aortic Valve Stenosis, Structural Heart Disease",
                "studyType": "Interventional",
                "status": "Recruiting",
                "startDate": "2024-03-01",
                "completionDate": "2028-02-28",
                "mainSponsor": "CardioStructural Innovations"
            }
        ])
    
    if "ortho" in keyword.lower() or "joint" in keyword.lower():
        keyword_trials.extend([
            {
                "eudraCTId": "2024-005123-45",
                "publicTitle": "Clinical Investigation of Patient-Specific 3D-Printed Orthopedic Implants",
                "condition": "Osteoarthritis, Joint Degeneration",
                "studyType": "Interventional",
                "status": "Not yet recruiting",
                "startDate": "2024-07-01",
                "completionDate": "2027-06-30",
                "mainSponsor": "OrthoCustom Solutions Europe"
            }
        ])
    
    all_trials = base_trials + keyword_trials
    logger.info(f"🇪🇺 Generated {len(all_trials)} comprehensive EU trials")
    
    return [normalize_trial_data(trial) for trial in all_trials]

def normalize_trial_data(raw_data):
    """Normalize the raw trial data to a standard schema."""
    return {
        "id": raw_data.get("eudraCTId", ""),
        "title": raw_data.get("publicTitle", "Unknown EU Trial"),
        "condition": raw_data.get("condition", ""),
        "type": raw_data.get("studyType", "Interventional"),
        "status": raw_data.get("status", "Unknown"),
        "start_date": raw_data.get("startDate", ""),
        "completion_date": raw_data.get("completionDate", ""),
        "sponsor": raw_data.get("mainSponsor", ""),
        "source": "EU Clinical Trials Register"
    }

def save_to_json(data, filename):
    """Save the collected data to a JSON file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"💾 Data successfully saved to {filename}")
    except Exception as e:
        logger.error(f"❌ Error saving data: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape clinical trial data from the EU Clinical Trials Register.")
    parser.add_argument("keyword", help="The keyword to search for (e.g., 'medtech').")
    parser.add_argument("--output", default="eu_trials.json", help="Output filename.")
    parser.add_argument("--use_sample", action="store_true", help="Use sample data instead of real scraping.")
    
    args = parser.parse_args()
    
    eu_trials_data = fetch_eu_trials(args.keyword, use_sample=args.use_sample)
    save_to_json(eu_trials_data, args.output)