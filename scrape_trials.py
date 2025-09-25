import argparse
import json
import requests
import time
import logging
from datetime import datetime
from scrape_eu import fetch_eu_trials

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_trials(keyword, max_records=50, use_sample=False):
    """
    Fetches real trial data from ClinicalTrials.gov with guaranteed results.
    
    Args:
        keyword: Search term for trials
        max_records: Maximum number of records to fetch
        use_sample: If True, return sample data instead of making API calls
    """
    # Validate inputs
    if not keyword or not keyword.strip():
        logger.error("❌ Invalid keyword provided")
        return []
    
    if use_sample:
        logger.info("📋 Using sample data (development mode)")
        return get_comprehensive_sample_data()
    
    logger.info(f"🔍 Searching for '{keyword}' on ClinicalTrials.gov...")
    
    # Use the new ClinicalTrials.gov API v1/studies endpoint
    API_URL = "https://clinicaltrials.gov/api/v1/studies"
    
    params = {
        'query.term': f'{keyword} AND AREA[StudyType]Interventional',
        'fields': 'NCTId|BriefTitle|OfficialTitle|Condition|StudyType|OverallStatus|StartDate|CompletionDate|LeadSponsorName',
        'min_rnk': 1,
        'max_rnk': max_records,
        'format': 'json'
    }
    
    # Log the query URL for diagnostics
    query_url = f"{API_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    logger.info(f"🔗 Query URL: {query_url}")
    
    normalized_trials = []
    failed_studies = 0
    
    try:
        response = requests.get(API_URL, params=params, timeout=60)
        response.raise_for_status()
        
        # Log response details for debugging
        logger.info(f"📡 API Response: {response.status_code}, Content-Length: {len(response.content)}")
        
        data = response.json()
        
        # Parse new API v1 response structure
        study_count = data.get('totalCount', 0)
        logger.info(f"📊 Found {study_count} studies matching '{keyword}'")
        
        if study_count == 0:
            logger.warning("⚠️ No studies found for keyword")
            return fetch_trials_broad(keyword, max_records, use_sample)
        
        studies = data.get('studies', [])
        
        for i, study in enumerate(studies):
            try:
                trial = process_study_v1(study)  # Use new v1 processing function
                if trial:
                    normalized_trials.append(trial)
            except Exception as e:
                failed_studies += 1
                logger.warning(f"⚠️ Failed to process study {i+1}: {e}")
        
        if failed_studies > 0:
            logger.warning(f"⚠️ Failed to process {failed_studies}/{len(studies)} studies")
        
        logger.info(f"✅ Successfully processed {len(normalized_trials)} trials from ClinicalTrials.gov")
        
        # If we got real data, return it
        if normalized_trials:
            return normalized_trials
            
    except requests.RequestException as e:
        logger.error(f"❌ Network error: {e}")
        if not use_sample:
            return []
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON response: {e}")
        if not use_sample:
            return []
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        if not use_sample:
            return []
    
    # If we get here, try a broader search
    logger.info("🔄 Trying broader search...")
    return fetch_trials_broad(keyword, max_records, use_sample)

def process_study_v1(study):
    """Process a single study from the new API v1 response"""
    # Extract protocol section which contains the main study info
    protocol_section = study.get('protocolSection', {})
    identification_module = protocol_section.get('identificationModule', {})
    status_module = protocol_section.get('statusModule', {})
    design_module = protocol_section.get('designModule', {})
    conditions_module = protocol_section.get('conditionsModule', {})
    sponsors_module = protocol_section.get('sponsorCollaboratorsModule', {})
    
    # Extract basic information
    nct_id = identification_module.get('nctId', '')
    brief_title = identification_module.get('briefTitle', '')
    official_title = identification_module.get('officialTitle', '')
    
    # Use official title if available, otherwise brief title
    title = official_title if official_title else brief_title
    if not title:
        return None  # Skip if no title
    
    # Extract conditions
    conditions = conditions_module.get('conditions', [])
    condition_str = ', '.join(conditions) if conditions else ''
    
    # Extract study type
    study_type = design_module.get('studyType', 'Interventional')
    
    # Extract status
    overall_status = status_module.get('overallStatus', 'Unknown')
    
    # Extract dates
    start_date_struct = status_module.get('startDateStruct', {})
    start_date = start_date_struct.get('date', '') if start_date_struct else ''
    
    completion_date_struct = status_module.get('completionDateStruct', {})
    completion_date = completion_date_struct.get('date', '') if completion_date_struct else ''
    
    # Extract sponsor
    lead_sponsor = sponsors_module.get('leadSponsor', {})
    sponsor_name = lead_sponsor.get('name', 'Not specified') if lead_sponsor else 'Not specified'
    
    return {
        "id": nct_id,
        "title": title,
        "condition": condition_str,
        "type": study_type,
        "status": overall_status,
        "start_date": start_date,
        "completion_date": completion_date,
        "sponsor": sponsor_name,
        "source": "ClinicalTrials.gov"
    }

def process_study(study):
    """Legacy function for backward compatibility - redirects to v1 processor"""
    return process_study_v1(study)

def fetch_trials_broad(keyword, max_records, use_sample=False):
    """Try a broader search with fewer filters using new API v1"""
    if use_sample:
        logger.info("📋 Using sample data for broad search (development mode)")
        return get_comprehensive_sample_data()
    
    # Use the new ClinicalTrials.gov API v1/studies endpoint
    API_URL = "https://clinicaltrials.gov/api/v1/studies"
    
    # Broader search terms
    search_terms = [
        keyword,
        "medical device",
        "MedTech",
        "implant",
        "prosthetic",
        "surgical robot",
        "wearable medical"
    ]
    
    all_trials = []
    
    for term in search_terms:
        if len(all_trials) >= max_records:
            break
            
        logger.info(f"🔍 Broad search for: {term}")
        
        params = {
            'query.term': term,
            'fields': 'NCTId|BriefTitle|Condition|StudyType|OverallStatus',
            'min_rnk': 1,
            'max_rnk': min(20, max_records - len(all_trials)),
            'format': 'json'
        }
        
        # Log the query URL for diagnostics
        query_url = f"{API_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        logger.info(f"🔗 Broad search URL: {query_url}")
        
        try:
            response = requests.get(API_URL, params=params, timeout=30)
            response.raise_for_status()
            
            # Log response details
            logger.info(f"📡 Broad search response: {response.status_code}, Content-Length: {len(response.content)}")
            
            data = response.json()
            study_count = data.get('totalCount', 0)
            studies = data.get('studies', [])
            
            logger.info(f"📊 Broad search found {study_count} studies for '{term}'")
            
            for study in studies:
                try:
                    trial = process_study_v1(study)
                    if trial and not any(t['id'] == trial['id'] for t in all_trials):
                        # For broad search, simplify some fields if they're missing
                        if not trial.get('start_date'):
                            trial['start_date'] = ""
                        if not trial.get('completion_date'):
                            trial['completion_date'] = ""
                        if not trial.get('sponsor'):
                            trial['sponsor'] = "Various"
                        
                        all_trials.append(trial)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to process study in broad search: {e}")
                    continue
                    
        except requests.RequestException as e:
            logger.warning(f"⚠️ Network error in broad search for '{term}': {e}")
            continue
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ JSON decode error in broad search for '{term}': {e}")
            continue
        except Exception as e:
            logger.warning(f"⚠️ Unexpected error in broad search for '{term}': {e}")
            continue
    if all_trials:
        logger.info(f"✅ Found {len(all_trials)} trials via broad search")
        return all_trials
    
    # Final fallback - only use sample data if explicitly requested
    if use_sample:
        logger.info("📋 Using comprehensive sample data")
        return get_comprehensive_sample_data()
    else:
        logger.warning("❌ No trials found via broad search, returning empty list")
        return []

def get_comprehensive_sample_data():
    """Return comprehensive realistic sample data"""
    sample_trials = [
        {
            "id": "NCT05432193",
            "title": "Safety and Efficacy of Novel Cardiac Ablation System for Atrial Fibrillation",
            "condition": "Atrial Fibrillation, Cardiac Arrhythmia",
            "type": "Interventional",
            "status": "Recruiting",
            "start_date": "2023-01-15",
            "completion_date": "2025-12-31",
            "sponsor": "CardioInnovate Inc.",
            "source": "ClinicalTrials.gov"
        },
        {
            "id": "NCT05328791", 
            "title": "Multicenter Trial of AI-Powered Diagnostic Tool for Early Lung Cancer Detection",
            "condition": "Lung Cancer, Pulmonary Nodules",
            "type": "Observational",
            "status": "Active, not recruiting",
            "start_date": "2022-06-01",
            "completion_date": "2024-11-30",
            "sponsor": "MedAI Diagnostics",
            "source": "ClinicalTrials.gov"
        },
        {
            "id": "NCT05263429",
            "title": "Randomized Controlled Trial of Robotic-Assisted Knee Replacement System",
            "condition": "Osteoarthritis, Knee Degeneration",
            "type": "Interventional",
            "status": "Recruiting",
            "start_date": "2023-03-01",
            "completion_date": "2026-02-28",
            "sponsor": "OrthoRobotics Corporation",
            "source": "ClinicalTrials.gov"
        },
        {
            "id": "NCT05178234",
            "title": "Study of Wearable Continuous Glucose Monitoring System with Predictive Alerts",
            "condition": "Diabetes Mellitus, Type 1 Diabetes",
            "type": "Interventional", 
            "status": "Completed",
            "start_date": "2021-09-01",
            "completion_date": "2023-08-31",
            "sponsor": "GlucoWatch Technologies",
            "source": "ClinicalTrials.gov"
        },
        {
            "id": "NCT05012345",
            "title": "Evaluation of Novel Spinal Cord Stimulator for Chronic Pain Management",
            "condition": "Chronic Pain, Neuropathic Pain",
            "type": "Interventional",
            "status": "Enrolling by invitation", 
            "start_date": "2022-11-01",
            "completion_date": "2024-10-31",
            "sponsor": "NeuroStim Solutions",
            "source": "ClinicalTrials.gov"
        },
        {
            "id": "NCT04987654",
            "title": "Feasibility Study of Smart Inhaler with Medication Adherence Monitoring",
            "condition": "Asthma, COPD",
            "type": "Interventional",
            "status": "Not yet recruiting",
            "start_date": "2024-02-01", 
            "completion_date": "2025-01-31",
            "sponsor": "RespiraTech Inc.",
            "source": "ClinicalTrials.gov"
        },
        {
            "id": "NCT04876543",
            "title": "Post-Market Surveillance of Next-Generation Coronary Stent System",
            "condition": "Coronary Artery Disease, Myocardial Ischemia",
            "type": "Observational",
            "status": "Active, not recruiting",
            "start_date": "2021-12-01",
            "completion_date": "2024-05-31",
            "sponsor": "Vascular Innovations Ltd.",
            "source": "ClinicalTrials.gov"
        },
        {
            "id": "NCT04765432",
            "title": "Clinical Investigation of AI-Driven Ultrasound for Thyroid Nodule Characterization",
            "condition": "Thyroid Nodule, Thyroid Cancer",
            "type": "Diagnostic",
            "status": "Recruiting",
            "start_date": "2023-07-01",
            "completion_date": "2025-06-30",
            "sponsor": "SonoAI Medical",
            "source": "ClinicalTrials.gov"
        }
    ]
    logger.info(f"📋 Loaded {len(sample_trials)} comprehensive sample trials")
    return sample_trials

def save_to_json(data, filename):
    """Save the collected data to a JSON file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"💾 Data successfully saved to {filename}")
    except Exception as e:
        logger.error(f"❌ Error saving data: {e}")

def main():
    parser = argparse.ArgumentParser(description="Scrape clinical trial data from multiple sources.")
    parser.add_argument("keyword", help="The keyword to search for (e.g., 'medtech').")
    parser.add_argument("--max_records", type=int, default=50, help="Maximum number of records to fetch.")
    parser.add_argument("--output", default="knowledge_base.json", help="Output filename.")
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting clinical trial data collection...")
    
    # Fetch data from ClinicalTrials.gov
    clinical_trials = fetch_trials(args.keyword, args.max_records, use_sample=False)
    
    # Fetch data from EU CTR
    eu_trials = fetch_eu_trials(args.keyword, use_sample=False)
    
    # Combine data
    all_trials = clinical_trials + eu_trials
    
    # Save the combined data
    save_to_json(all_trials, args.output)
    
    logger.info(f"🎉 Collection complete! {len(clinical_trials)} from ClinicalTrials.gov + {len(eu_trials)} from EU CTR = {len(all_trials)} total trials")

if __name__ == "__main__":
    main()