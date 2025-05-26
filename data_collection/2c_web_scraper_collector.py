# web_scraper_collector.py
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
import random

# Financial news websites that allow scraping
NEWS_SITES = [
    {
        "name": "yahoo_finance",
        "base_url": "https://finance.yahoo.com",
        "search_url": "https://finance.yahoo.com/quote/{symbol}/news",
        "news_url": "https://finance.yahoo.com/topic/stock-market-news/"
    },
    {
        "name": "marketwatch", 
        "base_url": "https://www.marketwatch.com",
        "search_url": "https://www.marketwatch.com/tools/quotes/lookup.asp?siteID=mktw&Lookup={symbol}&Country=us&Type=All",
        "news_url": "https://www.marketwatch.com/latest-news"
    },
    {
        "name": "investing_com",
        "base_url": "https://www.investing.com",
        "news_url": "https://www.investing.com/news/latest-news"
    }
]

# Symbol mapping for URL construction
SYMBOL_MAPPING = {
    "AAPL": "AAPL",
    "MSFT": "MSFT", 
    "GOOGL": "GOOGL",
    "AMZN": "AMZN",
    "NVDA": "NVDA",
    "TSLA": "TSLA",
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
    "Gold": "GC=F",
    "Brent Crude": "CL=F"
}

def get_headers():
    """Get random headers to avoid detection"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

def scrape_yahoo_finance(instrument, symbol):
    """Scrape Yahoo Finance for news"""
    articles = []
    
    try:
        # Get news for specific symbol
        url = f"https://finance.yahoo.com/quote/{symbol}/news"
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find news articles (Yahoo Finance structure may change)
        news_items = soup.find_all('h3', class_='Mb(5px)')
        
        for item in news_items[:10]:  # Limit to 10 articles
            try:
                link_element = item.find('a')
                if link_element:
                    title = link_element.get_text().strip()
                    link = link_element.get('href')
                    
                    # Make sure link is absolute
                    if link.startswith('/'):
                        link = 'https://finance.yahoo.com' + link
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'source': 'yahoo_finance',
                        'instrument': instrument,
                        'collected_at': datetime.now().isoformat()
                    })
            except Exception as e:
                print(f"    Error processing article: {str(e)}")
                continue
                
    except Exception as e:
        print(f"    Error scraping Yahoo Finance for {symbol}: {str(e)}")
    
    return articles

def scrape_general_news(instrument, keywords):
    """Scrape general financial news and filter by keywords"""
    articles = []
    
    try:
        # MarketWatch latest news
        url = "https://www.marketwatch.com/latest-news"
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find headlines
        headlines = soup.find_all('a', class_='link')
        
        for headline in headlines[:20]:  # Check more headlines
            try:
                title = headline.get_text().strip()
                link = headline.get('href')
                
                # Check if title contains relevant keywords
                if any(keyword.lower() in title.lower() for keyword in keywords):
                    # Make sure link is absolute
                    if link.startswith('/'):
                        link = 'https://www.marketwatch.com' + link
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'source': 'marketwatch',
                        'instrument': instrument,
                        'collected_at': datetime.now().isoformat()
                    })
            except:
                continue
                
    except Exception as e:
        print(f"    Error scraping general news: {str(e)}")
    
    return articles

def collect_for_instrument(instrument):
    """Collect news for a specific instrument"""
    print(f"\nCollecting news for {instrument}...")
    all_articles = []
    
    # Get symbol if available
    symbol = SYMBOL_MAPPING.get(instrument)
    keywords = INSTRUMENT_KEYWORDS.get(instrument, [instrument])
    
    # Try symbol-specific scraping
    if symbol:
        print(f"  Scraping Yahoo Finance for {symbol}...")
        yahoo_articles = scrape_yahoo_finance(instrument, symbol)
        all_articles.extend(yahoo_articles)
        print(f"    Found {len(yahoo_articles)} articles")
        
        time.sleep(random.uniform(2, 5))  # Be respectful
    
    # Try general news scraping
    print(f"  Scraping general news with keywords: {keywords}")
    general_articles = scrape_general_news(instrument, keywords)
    all_articles.extend(general_articles)
    print(f"    Found {len(general_articles)} articles")
    
    # Save articles
    if all_articles:
        save_articles_scraping(all_articles, instrument)
    
    print(f"  Total articles for {instrument}: {len(all_articles)}")
    
    return len(all_articles)

def save_articles_scraping(articles, instrument):
    """Save scraped articles"""
    output_dir = f"news/{instrument}"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/scraped_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(articles, f, indent=2)
    
    print(f"    Saved to {filename}")

# Use the same INSTRUMENT_KEYWORDS from the RSS collector
INSTRUMENT_KEYWORDS = {
    "AAPL": ["apple", "iphone", "ipad", "mac", "tim cook"],
    "MSFT": ["microsoft", "windows", "azure", "office", "satya nadella"],
    "GOOGL": ["google", "alphabet", "search", "android", "youtube"],
    "AMZN": ["amazon", "aws", "prime", "jeff bezos", "andy jassy"],
    "NVDA": ["nvidia", "gpu", "ai chip", "jensen huang"],
    "TSLA": ["tesla", "elon musk", "electric vehicle", "model"],
    "Bitcoin": ["bitcoin", "btc", "cryptocurrency", "crypto"],
    "Ethereum": ["ethereum", "eth", "smart contract", "defi"],
    "Treasury Yields": ["treasury", "yield", "bond", "interest rate", "fed"],
    "Gold": ["gold", "precious metal", "bullion"],
    "Brent Crude": ["oil", "crude", "brent", "petroleum", "opec"]
}

if __name__ == "__main__":
    total = 0
    for instrument in INSTRUMENT_KEYWORDS.keys():
        collected = collect_for_instrument(instrument)
        total += collected
        time.sleep(random.uniform(5, 10))  # Longer delays between instruments
    
    print(f"\nTotal articles collected: {total}")
