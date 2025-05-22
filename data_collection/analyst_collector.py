# analyst_collector.py
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
import newspaper
from newspaper import Article
import random

# Publicly available analyst sites
ANALYST_SOURCES = [
    {"name": "seeking_alpha", "url": "https://seekingalpha.com/stock-ideas"},
    {"name": "motley_fool", "url": "https://www.fool.com/investing-news/"},
    {"name": "yahoo_analysis", "url": "https://finance.yahoo.com/topic/analyst-opinions/"},
    {"name": "investing_analysis", "url": "https://www.investing.com/analysis/stock-markets"}
]

INSTRUMENTS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", 
               "Bitcoin", "Ethereum", "Treasury", "Gold", "Oil", "Brent"]

def get_urls_from_page(url, instrument):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        
        # Filter links that might be articles and contain our instrument keyword
        article_urls = []
        for link in links:
            href = link['href']
            link_text = link.text.strip().lower()
            
            # Check if link appears to be an article and contains our keyword
            if (instrument.lower() in link_text and
                ("/article/" in href or "/news/" in href or "/analysis/" in href)):
                
                # Make sure it's a full URL
                if href.startswith('/'):
                    base_url = url.split('//')[0] + '//' + url.split('//')[1].split('/')[0]
                    href = base_url + href
                
                article_urls.append(href)
        
        return list(set(article_urls))  # Remove duplicates
    
    except Exception as e:
        print(f"Error fetching from {url}: {str(e)}")
        return []

def extract_article_content(url):
    try:
        article = Article(url)
        article.download()
        time.sleep(1)  # Be respectful to the server
        article.parse()
        
        return {
            "title": article.title,
            "text": article.text,
            "authors": article.authors,
            "publish_date": article.publish_date.isoformat() if article.publish_date else None,
            "url": url
        }
    except Exception as e:
        print(f"Error extracting from {url}: {str(e)}")
        return None

def save_analyst_reports(reports, instrument, source_name):
    # Create directory if it doesn't exist
    output_dir = f"analyst_reports/{instrument}"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/{source_name}_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(reports, f, indent=2)
    
    print(f"Saved {len(reports)} analyst reports to {filename}")

# Collect analyst reports for each instrument
for instrument in INSTRUMENTS:
    print(f"Collecting analyst reports for {instrument}...")
    
    for source in ANALYST_SOURCES:
        print(f"  Checking {source['name']}...")
        
        article_urls = get_urls_from_page(source['url'], instrument)
        
        if not article_urls:
            print(f"  No relevant articles found for {instrument} in {source['name']}")
            continue
        
        print(f"  Found {len(article_urls)} potential articles. Processing...")
        
        reports = []
        # Limit to 5 articles per source to avoid overloading
        for url in article_urls[:5]:
            article_data = extract_article_content(url)
            if article_data:
                reports.append(article_data)
            
            # Be very respectful with delays
            time.sleep(random.uniform(1.0, 3.0))
        
        if reports:
            save_analyst_reports(reports, instrument, source['name'])
        
    print(f"Completed {instrument}\n")
