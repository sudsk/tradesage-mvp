# comprehensive_gnews_collector.py
import requests
import json
import os
from datetime import datetime, timedelta
import time

class ComprehensiveGNewsCollector:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://gnews.io/api/v4/search"
        
    def fetch_articles(self, query, max_results=20, days_back=30, category=None):
        """Generic article fetching method"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            "q": query,
            "token": self.api_key,
            "lang": "en",
            "max": max_results,
            "expand": "content",
            "from": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sortby": "relevance"
        }
        
        if category:
            params["category"] = category
            
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get("articles", [])
        except Exception as e:
            print(f"Error fetching articles: {str(e)}")
        
        return []
    
    def collect_news_articles(self, instrument, queries):
        """Collect regular news articles"""
        print(f"  Collecting news articles for {instrument}...")
        articles = []
        
        for query in queries:
            results = self.fetch_articles(query, max_results=30, days_back=14)
            articles.extend(results)
            time.sleep(1)
        
        self.save_documents(articles, instrument, "news")
        return len(articles)
    
    def collect_analysis_reports(self, instrument, queries):
        """Collect analysis and opinion pieces"""
        print(f"  Collecting analysis reports for {instrument}...")
        articles = []
        
        for query in queries:
            analysis_query = f"{query} analysis OR forecast OR prediction OR target OR outlook"
            results = self.fetch_articles(analysis_query, max_results=20, days_back=60)
            articles.extend(results)
            time.sleep(1)
        
        self.save_documents(articles, instrument, "analysis")
        return len(articles)
    
    def collect_earnings_reports(self, instrument, queries):
        """Collect earnings and financial results"""
        print(f"  Collecting earnings reports for {instrument}...")
        articles = []
        
        for query in queries:
            earnings_query = f"{query} earnings OR results OR revenue OR quarterly OR guidance"
            results = self.fetch_articles(earnings_query, max_results=15, days_back=90)
            articles.extend(results)
            time.sleep(1)
        
        self.save_documents(articles, instrument, "earnings")
        return len(articles)
    
    def collect_technical_analysis(self, instrument, queries):
        """Collect technical analysis content"""
        print(f"  Collecting technical analysis for {instrument}...")
        articles = []
        
        for query in queries:
            tech_query = f"{query} technical analysis OR chart pattern OR trend OR support OR resistance"
            results = self.fetch_articles(tech_query, max_results=10, days_back=30)
            articles.extend(results)
            time.sleep(1)
        
        self.save_documents(articles, instrument, "technical_analysis")
        return len(articles)
    
    def save_documents(self, articles, instrument, doc_type):
        """Save documents with type classification"""
        if not articles:
            return
            
        # Remove duplicates
        unique_articles = {}
        for article in articles:
            url = article.get("url", "")
            if url and url not in unique_articles:
                unique_articles[url] = article
        
        final_articles = list(unique_articles.values())
        
        # Create directory
        output_dir = f"{doc_type}/{instrument}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save with metadata
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/gnews_{timestamp}.json"
        
        output_data = {
            "metadata": {
                "instrument": instrument,
                "document_type": doc_type,
                "collection_date": datetime.now().isoformat(),
                "article_count": len(final_articles),
                "total_word_count": sum(len(article.get("content", "").split()) for article in final_articles)
            },
            "articles": final_articles
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"    Saved {len(final_articles)} {doc_type} documents to {filename}")

# Usage example
def main():
    collector = ComprehensiveGNewsCollector("<api-key>")
    
    instruments = {
        "MSFT": ["Microsoft Corporation", "MSFT stock", "Azure cloud", "Satya Nadella", "Microsoft earnings"],
        "GOOGL": ["Alphabet Google", "GOOGL stock", "Google search", "Sundar Pichai", "Google earnings"],
        "AMZN": ["Amazon Inc", "AMZN stock", "AWS cloud", "Jeff Bezos Amazon", "Amazon earnings"],
        "NVDA": ["NVIDIA Corporation", "NVDA stock", "AI chips", "Jensen Huang NVIDIA", "GPU sales"],
        "TSLA": ["Tesla Inc", "TSLA stock", "electric vehicles", "Elon Musk Tesla", "Tesla earnings"],
        "Ethereum": ["Ethereum", "ETH", "smart contracts", "DeFi Ethereum", "Ethereum upgrade"],
        "Treasury Yields": ["Treasury yields", "bond rates", "Federal Reserve rates", "10-year Treasury", "interest rates"],
        "Gold": ["gold price", "gold investment", "precious metals", "gold futures", "gold market"]
    }
    
    for instrument, queries in instruments.items():
        print(f"\nProcessing {instrument}...")
        
        # Collect different types of documents
        news_count = collector.collect_news_articles(instrument, queries)
        analysis_count = collector.collect_analysis_reports(instrument, queries)
        earnings_count = collector.collect_earnings_reports(instrument, queries)
        technical_count = collector.collect_technical_analysis(instrument, queries)
        
        total = news_count + analysis_count + earnings_count + technical_count
        print(f"  Total documents for {instrument}: {total}")
        
        time.sleep(5)  # Pause between instruments

if __name__ == "__main__":
    main()
