# crypto_collector.py
import requests
import json
import os
from datetime import datetime
import time

# Define cryptocurrency assets
CRYPTO_ASSETS = ["bitcoin", "ethereum"]

def fetch_coingecko_data(coin_id):
    """Fetch current and historical data from CoinGecko API (free tier)"""
    
    # Current market data
    market_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    
    try:
        market_response = requests.get(market_url)
        market_response.raise_for_status()
        market_data = market_response.json()
        
        # Historical price data (last 30 days)
        history_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=30&interval=daily"
        history_response = requests.get(history_url)
        history_response.raise_for_status()
        history_data = history_response.json()
        
        # Be respectful of API rate limits
        time.sleep(1.5)
        
        return {
            "market_data": market_data,
            "history_data": history_data
        }
    
    except Exception as e:
        print(f"Error fetching data for {coin_id}: {str(e)}")
        return None

def fetch_crypto_news(coin):
    """Fetch crypto-specific news from crypto news RSS aggregator"""
    
    # Using Cryptopanic API (has a generous free tier)
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token=YOUR_FREE_TOKEN&currencies={coin}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        news_data = response.json()
        
        # Be respectful of API rate limits
        time.sleep(1)
        
        return news_data
    
    except Exception as e:
        print(f"Error fetching news for {coin}: {str(e)}")
        return {"results": []}  # Return empty results on error

def save_crypto_data(data, news, coin_id):
    """Save cryptocurrency data and news to separate files"""
    
    # Create directory if it doesn't exist
    for directory in [f"news/{coin_id}", f"technical_analysis/{coin_id}"]:
        os.makedirs(directory, exist_ok=True)
    
    # Save market and historical data
    if data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"technical_analysis/{coin_id}/{coin_id}_data_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Saved technical data to {filename}")
    
    # Save news data
    if news and "results" in news:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"news/{coin_id}/{coin_id}_news_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(news, f, indent=2)
        
        print(f"Saved {len(news['results'])} news items to {filename}")

# Collect data for each cryptocurrency
for coin in CRYPTO_ASSETS:
    print(f"Collecting data for {coin}...")
    
    # Fetch market and historical data
    market_data = fetch_coingecko_data(coin)
    
    # Fetch news
    news_data = fetch_crypto_news(coin)
    
    # Save data
    save_crypto_data(market_data, news_data, coin)
    
    print(f"Completed {coin}\n")
