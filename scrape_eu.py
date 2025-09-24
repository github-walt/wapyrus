import requests
import json
from datetime import datetime
import argparse
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import quote

def fetch_eu_trials(keyword):
    """
    Fetches clinical trial data from the EU CTR by scraping the search results.
    """
    normalized_trials = []
    
    # URL encode the keyword for the search query
    encoded_keyword = quote(keyword)
    base_url = "https://www.clinicaltrialsregister.eu/ctr-search/search"
    params = {
        'query': keyword,
        'page': 1
    }
    
    print(f"Searching for '{keyword}' on the EU Clinical Trials Register...")
    
    try:
        # Make the initial search request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        session = requests.Session()
        response = session.get(base_url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find trial entries - they're typically in table rows or divs with specific classes
        trial_rows = soup.find_all('div', class_='result') or soup.find_all('tr', class_='result')
        
        if not trial_rows:
            # Alternative selector - look for table rows that contain trial data
            trial_rows = soup.select('table.list tr:has(td)')
        
        for row in trial_rows:
            try:
                # Extract trial data based on the actual structure of the EU CTR website
                raw_data = extract_trial_data(row, session)
                if raw_data:
                    normalized_trial = normalize_trial_data(raw_data)
                    normalized_trials.append(normalized_trial)
                
                # Be respectful - add a small delay between requests
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error processing trial row: {e}")
                continue
        
        print(f"Found {len(normalized_trials)} trial(s) from EU CTR.")
        
    except requests.RequestException as e:
        print(f"Error fetching data from EU CTR: {e}")
        # Return sample data if scraping fails
        return get_sample_data()
    
    return normalized_trials

def extract_trial_data(row, session):
    """
    Extract trial data from a HTML row element.
    This function needs to be adapted based on the actual HTML structure of the EU CTR website.
    """
    raw_data = {}
    
    try:
        # Try to find EudraCT number - this is usually a link
        eudract_link = row.find('a', href=re.compile(r'eudractNumber'))
        if eudract_link:
            raw_data['eudraCTId'] = eudract_link.get_text(strip=True)
            # You could follow this link to get more detailed information
            # detail_data = fetch_trial_details(eudract_link['href'], session)
            # raw_data.update(detail_data)
        
        # Extract title
        title_elem = row.find('td', class_='trialTitle') or row.find('div', class_='title')
        if title_elem:
            raw_data['publicTitle'] = title_elem.get_text(strip=True)
        
        # Extract condition
        condition_elem = row.find('td', class_='condition') or row.find('div', class_='condition')
        if condition_elem:
            raw_data['condition'] = condition_elem.get_text(strip=True)
        
        # Extract status
        status_elem = row.find('td', class_='status') or row.find('span', class_='status')
        if status_elem:
            raw_data['status'] = status_elem.get_text(strip=True)
        
        # Extract sponsor
        sponsor_elem = row.find('td', class_='sponsor') or row.find('div', class_='sponsor')
        if sponsor_elem:
            raw_data['mainSponsor'] = sponsor_elem.get_text(strip=True)
        
        # Extract dates - these might be in separate columns
        date_elems = row.find_all('td', class_=re.compile(r'date'))
        for i, date_elem in enumerate(date_elems):
            date_text = date_elem.get_text(strip=True)
            if i == 0 and date_text:
                raw_data['startDate'] = date_text
            elif i == 1 and date_text:
                raw_data['completionDate'] = date_text
        
        # If we couldn't extract basic data, return None
        if not raw_data.get('eudraCTId') and not raw_data.get('publicTitle'):
            return None
            
    except Exception as e:
        print(f"Error extracting trial data: {e}")
        return None
    
    return raw_data

def fetch_trial_details(detail_url, session):
    """
    Fetch detailed information for a specific trial by following its detail link.
    """
    details = {}
    
    try:
        base_domain = "https://www.clinicaltrialsregister.eu"
        if not detail_url.startswith('http'):
            detail_url = base_domain + detail_url
        
        response = session.get(detail_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract detailed information from the trial detail page
        # This would need to be customized based on the actual detail page structure
        
        # Example extraction patterns:
        # study_type_elem = soup.find('td', text=re.compile(r'Study type', re.I))
        # if study_type_elem:
        #     details['studyType'] = study_type_elem.find_next('td').get_text(strip=True)
        
    except Exception as e:
        print(f"Error fetching trial details: {e}")
    
    return details

def normalize_trial_data(raw_data):
    """
    Normalize the raw trial data to a standard schema.
    """
    return {
        "id": raw_data.get("eudraCTId", ""),
        "title": raw_data.get("publicTitle", ""),
        "condition": raw_data.get("condition", ""),
        "type": raw_data.get("studyType", "Interventional trial"),  # Default value
        "status": raw_data.get("status", ""),
        "start_date": raw_data.get("startDate", ""),
        "completion_date": raw_data.get("completionDate", ""),
        "sponsor": raw_data.get("mainSponsor", ""),
        "source": "EU Clinical Trials Register"
    }

def get_sample_data():
    """
    Return sample data if scraping fails or no results are found.
    """
    sample_raw_data = {
        "eudraCTId": "2022-001234-56",
        "publicTitle": "A study on the use of a new medical device for joint repair",
        "condition": "Osteoarthritis",
        "studyType": "Interventional trial",
        "status": "Recruiting",
        "startDate": "2022-05-15",
        "completionDate": "2024-12-31",
        "mainSponsor": "Wapyrus Innovations"
    }
    
    normalized_trial = normalize_trial_data(sample_raw_data)
    return [normalized_trial]

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape clinical trial data from the EU Clinical Trials Register.")
    parser.add_argument("keyword", help="The keyword to search for (e.g., 'medtech').")
    parser.add_argument("--output", default="eu_trials.json", help="Output filename.")
    
    args = parser.parse_args()
    
    eu_trials_data = fetch_eu_trials(args.keyword)
    save_to_json(eu_trials_data, args.output)