# news_collector_gnews_only.py
import requests
import json
import os
from datetime import datetime, timedelta
import time

# GNews configuration with expanded content
GNEWS_CONFIG = {
    "name": "gnews",
    "url": "https://gnews.io/api/v4/search",
    "api_key": "<api key>",  # Replace with your actual API key
    "limit": 100,  # Essential plan allows up to 100 articles per request
    "max_requests_per_day": 1000,  # Essential plan limit
    "expand_content": True  # Get full article content
}

# Enhanced instrument mapping with better search queries
INSTRUMENTS = {
    "AAPL": {
        "queries": ["Apple Inc", "AAPL stock", "iPhone sales", "Tim Cook Apple", "Apple earnings"],
        "category": "business"
    },
    "MSFT": {
        "queries": ["Microsoft Corporation", "MSFT stock", "Azure cloud", "Satya Nadella", "Microsoft earnings"],
        "category": "business"
    },
    "GOOGL": {
        "queries": ["Alphabet Google", "GOOGL stock", "Google search", "Sundar Pichai", "Google earnings"],
        "category": "business"
    },
    "AMZN": {
        "queries": ["Amazon Inc", "AMZN stock", "AWS cloud", "Jeff Bezos Amazon", "Amazon earnings"],
        "category": "business"
    },
    "NVDA": {
        "queries": ["NVIDIA Corporation", "NVDA stock", "AI chips", "Jensen Huang NVIDIA", "GPU sales"],
        "category": "business"
    },
    "TSLA": {
        "queries": ["Tesla Inc", "TSLA stock", "electric vehicles", "Elon Musk Tesla", "Tesla earnings"],
        "category": "business"
    },
    "Bitcoin": {
        "queries": ["Bitcoin price", "BTC cryptocurrency", "Bitcoin news", "Bitcoin regulation", "Bitcoin ETF"],
        "category": "business"
    },
    "Ethereum": {
        "queries": ["Ethereum price", "ETH cryptocurrency", "Ethereum upgrade", "smart contracts", "DeFi Ethereum"],
        "category": "business"
    },
    "Treasury Yields": {
        "queries": ["Treasury yields", "bond rates", "Federal Reserve rates", "10-year Treasury", "interest rates"],
        "category": "business"
    },
    "Gold": {
        "queries": ["gold price", "gold investment", "precious metals", "gold futures", "gold market"],
        "category": "business"
    },
    "Brent Crude": {
        "queries": ["Brent crude oil", "oil prices", "petroleum market", "OPEC oil", "crude oil futures"],
        "category": "business"
    }
}

def fetch_gnews_articles(query, category="business", days_back=7, max_results=100):
    """Fetch articles from GNews API with full content"""
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Format dates for GNews API (ISO format)
    from_date = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_date = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Construct API parameters
    params = {
        "q": query,
        "token": GNEWS_CONFIG["api_key"],
        "lang": "en",
        "country": "us",
        "max": min(max_results, GNEWS_CONFIG["limit"]),
        "from": from_date,
        "to": to_date,
        "sortby": "relevance",
        "expand": "content"  # This gets the full article content!
    }
    
    # Add category if specified
    if category:
        params["category"] = category
    
    try:
        print(f"    Fetching: {query} (last {days_back} days, max {max_results} articles)")
        response = requests.get(GNEWS_CONFIG["url"], params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if "articles" in data:
                articles = data["articles"]
                print(f"    Success: Found {len(articles)} articles")
                
                # Enhanced article processing
                processed_articles = []
                for article in articles:
                    processed_article = {
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "content": article.get("content", ""),  # Full article content!
                        "url": article.get("url", ""),
                        "source": {
                            "name": article.get("source", {}).get("name", "Unknown"),
                            "url": article.get("source", {}).get("url", "")
                        },
                        "publishedAt": article.get("publishedAt", ""),
                        "query_used": query,
                        "collected_at": datetime.now().isoformat(),
                        "word_count": len(article.get("content", "").split()) if article.get("content") else 0
                    }
                    processed_articles.append(processed_article)
                
                return processed_articles
            else:
                print(f"    No articles found in response")
                return []
                
        elif response.status_code == 403:
            print(f"    Error: API key invalid or quota exceeded")
            return []
        elif response.status_code == 429:
            print(f"    Error: Rate limit exceeded - waiting...")
            time.sleep(60)  # Wait 1 minute before continuing
            return []
        else:
            print(f"    Error: HTTP {response.status_code}")
            return []
            
    except requests.exceptions.Timeout:
        print(f"    Error: Request timeout")
        return []
    except Exception as e:
        print(f"    Error: {str(e)}")
        return []

def collect_news_for_instrument(instrument_name, instrument_config, articles_per_query=20):
    """Collect news for a specific instrument using multiple queries"""
    print(f"\nCollecting news for {instrument_name}...")
    
    all_articles = []
    queries = instrument_config["queries"]
    category = instrument_config.get("category", "business")
    
    for i, query in enumerate(queries):
        print(f"  Query {i+1}/{len(queries)}: {query}")
        
        # Fetch articles for this query
        articles = fetch_gnews_articles(
            query=query,
            category=category,
            days_back=14,  # Look back 2 weeks for more content
            max_results=articles_per_query
        )
        
        if articles:
            all_articles.extend(articles)
            print(f"    Added {len(articles)} articles (Total: {len(all_articles)})")
        
        # Be respectful of API limits - wait between queries
        time.sleep(2)
    
    # Remove duplicates based on URL
    unique_articles = {}
    for article in all_articles:
        url = article.get("url", "")
        if url and url not in unique_articles:
            unique_articles[url] = article
    
    final_articles = list(unique_articles.values())
    print(f"  After deduplication: {len(final_articles)} unique articles")
    
    # Save articles
    if final_articles:
        save_articles(final_articles, instrument_name, "gnews_expanded")
        
        # Print some stats
        total_words = sum(article.get("word_count", 0) for article in final_articles)
        avg_words = total_words / len(final_articles) if final_articles else 0
        
        print(f"  Saved {len(final_articles)} articles")
        print(f"  Average article length: {avg_words:.0f} words")
        print(f"  Total content: {total_words:,} words")
    
    return len(final_articles)

def save_articles(articles, instrument, source_name):
    """Save articles to JSON file with enhanced metadata"""
    # Create directory if it doesn't exist
    output_dir = f"news/{instrument}"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/{source_name}_{timestamp}.json"
    
    # Create metadata
    metadata = {
        "instrument": instrument,
        "source": source_name,
        "collection_date": datetime.now().isoformat(),
        "article_count": len(articles),
        "total_word_count": sum(article.get("word_count", 0) for article in articles),
        "date_range": {
            "earliest": min(article.get("publishedAt", "") for article in articles if article.get("publishedAt")),
            "latest": max(article.get("publishedAt", "") for article in articles if article.get("publishedAt"))
        },
        "sources": list(set(article.get("source", {}).get("name", "Unknown") for article in articles))
    }
    
    # Save with metadata
    output_data = {
        "metadata": metadata,
        "articles": articles
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"    Saved to {filename}")
    
    # Also save a summary file
    summary_filename = f"{output_dir}/summary_{timestamp}.txt"
    with open(summary_filename, 'w', encoding='utf-8') as f:
        f.write(f"Collection Summary for {instrument}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total Articles: {len(articles)}\n")
        f.write(f"Total Words: {metadata['total_word_count']:,}\n")
        f.write(f"Collection Date: {metadata['collection_date']}\n")
        f.write(f"Date Range: {metadata['date_range']['earliest']} to {metadata['date_range']['latest']}\n\n")
        f.write("Sources:\n")
        for source in metadata['sources']:
            f.write(f"  - {source}\n")
        f.write("\nTop 10 Headlines:\n")
        for i, article in enumerate(articles[:10]):
            f.write(f"{i+1:2d}. {article.get('title', 'No title')}\n")

def main():
    """Main collection function"""
    print("GNews Enhanced Collection for TradeSage")
    print("=" * 50)
    print(f"API Key configured: {'Yes' if GNEWS_CONFIG['api_key'] != 'YOUR_GNEWS_API_KEY' else 'No - Please update API key!'}")
    
    if GNEWS_CONFIG['api_key'] == 'YOUR_GNEWS_API_KEY':
        print("Please update your GNews API key in the script!")
        return
    
    total_articles = 0
    total_requests = 0
    
    for instrument_name, instrument_config in INSTRUMENTS.items():
        collected = collect_news_for_instrument(instrument_name, instrument_config, articles_per_query=30)
        total_articles += collected
        total_requests += len(instrument_config["queries"])
        
        print(f"  Completed {instrument_name}: {collected} articles")
        
        # Monitor API usage
        print(f"  API requests used so far: {total_requests}")
        
        # Wait between instruments to be respectful
        time.sleep(5)
    
    print(f"\nCollection Summary:")
    print(f"Total articles collected: {total_articles}")
    print(f"Total API requests made: {total_requests}")
    print(f"Estimated remaining requests today: {GNEWS_CONFIG['max_requests_per_day'] - total_requests}")

def test_api_key():
    """Test if the API key is working"""
    print("Testing GNews API key...")
    
    test_params = {
        "q": "Apple",
        "token": GNEWS_CONFIG["api_key"],
        "lang": "en",
        "max": 1,
        "expand": "content"
    }
    
    try:
        response = requests.get(GNEWS_CONFIG["url"], params=test_params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "articles" in data and len(data["articles"]) > 0:
                article = data["articles"][0]
                print("✅ API key is working!")
                print(f"Sample article title: {article.get('title', 'N/A')}")
                print(f"Content length: {len(article.get('content', ''))} characters")
                return True
            else:
                print("❌ API key works but no articles returned")
                return False
        elif response.status_code == 403:
            print("❌ API key is invalid or expired")
            return False
        elif response.status_code == 429:
            print("❌ API rate limit exceeded")
            return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {str(e)}")
        return False

if __name__ == "__main__":
    # First test the API key
    if test_api_key():
        print("\nStarting collection...\n")
        main()
    else:
        print("Please check your API key and try again.")
