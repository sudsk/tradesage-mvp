# rss_collector.py
import feedparser
import json
import os
from datetime import datetime

# RSS feeds for financial news
FEEDS = [
    {"name": "yahoo_finance", "url": "https://finance.yahoo.com/news/rssindex"},
    {"name": "seeking_alpha", "url": "https://seekingalpha.com/feed.xml"},
    {"name": "investing_com", "url": "https://www.investing.com/rss/news.rss"},
    {"name": "marketwatch", "url": "http://feeds.marketwatch.com/marketwatch/topstories/"},
    {"name": "cnbc", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
    {"name": "cryptocurrency", "url": "https://cointelegraph.com/rss"}
]

INSTRUMENTS = ["Apple", "Microsoft", "Google", "Amazon", "Nvidia", "Tesla", 
               "Bitcoin", "Ethereum", "Treasury", "Gold", "Oil", "Brent"]

def fetch_rss(feed_url):
    feed = feedparser.parse(feed_url)
    return feed.entries

def filter_articles_by_keyword(articles, keyword):
    return [
        article for article in articles 
        if keyword.lower() in article.title.lower() or 
           (hasattr(article, 'summary') and keyword.lower() in article.summary.lower())
    ]

def save_articles(articles, instrument, source_name):
    # Create directory if it doesn't exist
    output_dir = f"news/{instrument}"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/{source_name}_{timestamp}.json"
    
    # Convert feedparser objects to dictionaries
    articles_json = []
    for article in articles:
        article_dict = {
            "title": article.title,
            "link": article.link,
            "published": article.get("published", ""),
            "summary": article.get("summary", ""),
            "source": source_name
        }
        articles_json.append(article_dict)
    
    with open(filename, 'w') as f:
        json.dump(articles_json, f, indent=2)
    
    print(f"Saved {len(articles_json)} articles to {filename}")

# Collect articles
for feed in FEEDS:
    print(f"Fetching from {feed['name']}...")
    articles = fetch_rss(feed['url'])
    
    # Filter and save articles for each instrument
    for instrument in INSTRUMENTS:
        relevant_articles = filter_articles_by_keyword(articles, instrument)
        if relevant_articles:
            save_articles(relevant_articles, instrument, feed['name'])
            print(f"  Found {len(relevant_articles)} articles for {instrument}")
