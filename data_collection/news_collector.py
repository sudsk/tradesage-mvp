# news_collector.py
import requests
import json
import os
from datetime import datetime, timedelta

# Free API sources with generous limits
NEWS_SOURCES = [
    {
        "name": "marketaux",
        "url": "https://api.marketaux.com/v1/news/all",
        "key_param": "api_token",
        "api_key": "YOUR_FREE_API_KEY",  # Sign up at marketaux.com
        "symbols_param": "symbols",
        "limit": 100
    },
    {
        "name": "gnews",
        "url": "https://gnews.io/api/v4/search",
        "key_param": "token",
        "api_key": "YOUR_FREE_API_KEY",  # Sign up at gnews.io
        "query_param": "q",
        "limit": 1000
    }
]

INSTRUMENTS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "Bitcoin", "Ethereum", "Treasury Yields", "Gold", "Brent Crude"]

def fetch_news(source_config, query):
    params = {
        source_config["key_param"]: source_config["api_key"],
        "limit": source_config["limit"]
    }
    
    # Handle different API parameter structures
    if "symbols_param" in source_config and query in ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA"]:
        params[source_config["symbols_param"]] = query
    elif "query_param" in source_config:
        params[source_config["query_param"]] = query
    
    response = requests.get(source_config["url"], params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching from {source_config['name']}: {response.status_code}")
        return None

def save_articles(articles, instrument, source_name):
    # Create directory if it doesn't exist
    output_dir = f"news/{instrument}"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/{source_name}_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(articles, f, indent=2)
    
    print(f"Saved {len(articles)} articles to {filename}")

# Collect news for each instrument
for instrument in INSTRUMENTS:
    print(f"Collecting news for {instrument}...")
    
    for source in NEWS_SOURCES:
        articles = fetch_news(source, instrument)
        if articles:
            save_articles(articles, instrument, source["name"])
            
    print(f"Completed {instrument}\n")
