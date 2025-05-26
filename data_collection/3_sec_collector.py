# sec_collector.py
import requests
import os
import pandas as pd
import time
from datetime import datetime

# Company CIK codes (identifier for SEC EDGAR)
COMPANIES = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "GOOGL": "0001652044",
    "AMZN": "0001018724",
    "NVDA": "0001045810",
    "TSLA": "0001318605"
}

def fetch_company_filings(cik, filing_type="10-Q,10-K"):
    # SEC EDGAR API endpoint
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    
    headers = {
        "User-Agent": "Sample Company Name admin@example.com"  # SEC requires a user-agent
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        # Extract recent filings
        filings = []
        for form_type in filing_type.split(','):
            recent_filings = [
                {
                    "accessionNumber": accession_number,
                    "filingDate": data["filings"]["recent"]["filingDate"][i],
                    "form": data["filings"]["recent"]["form"][i],
                    "primaryDocument": data["filings"]["recent"]["primaryDocument"][i]
                }
                for i, accession_number in enumerate(data["filings"]["recent"]["accessionNumber"])
                if data["filings"]["recent"]["form"][i] == form_type
            ][:4]  # Get only the 4 most recent
            
            filings.extend(recent_filings)
        
        return filings
    else:
        print(f"Error fetching filings for CIK {cik}: {response.status_code}")
        return []

def download_filing_document(cik, accession_number, primary_document):
    # Format accession number by removing dashes
    accession_formatted = accession_number.replace("-", "")
    
    # Construct URL for the filing document
    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_formatted}/{primary_document}"
    
    headers = {
        "User-Agent": "Sample Company Name admin@example.com"  # SEC requires a user-agent
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error downloading filing {accession_number}: {response.status_code}")
        return None

def save_filing(content, ticker, accession_number, filing_date, form_type):
    # Create directory if it doesn't exist
    output_dir = f"earnings/{ticker}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the filing
    filename = f"{output_dir}/{ticker}_{form_type}_{filing_date}.html"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Saved {form_type} filing from {filing_date} to {filename}")

# Collect filings for each company
for ticker, cik in COMPANIES.items():
    print(f"Collecting filings for {ticker} (CIK: {cik})...")
    
    filings = fetch_company_filings(cik)
    
    for filing in filings:
        print(f"  Downloading {filing['form']} from {filing['filingDate']}...")
        
        # Add a delay to avoid rate limiting
        time.sleep(0.1)
        
        content = download_filing_document(
            cik, 
            filing["accessionNumber"], 
            filing["primaryDocument"]
        )
        
        if content:
            save_filing(
                content,
                ticker,
                filing["accessionNumber"],
                filing["filingDate"],
                filing["form"]
            )
    
    print(f"Completed {ticker}\n")
    # Add a longer delay between companies
    time.sleep(1)
