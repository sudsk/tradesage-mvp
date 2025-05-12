# app/tools/news_data_tool.py
import requests
from google.cloud import secretmanager
import json
from datetime import datetime, timedelta

def get_secret(secret_name, project_id):
    """Retrieve secret from Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error retrieving secret {secret_name}: {e}")
        return None

def news_data_tool(query, days=7, project_id="tradesage-mvp"):
    """Tool for retrieving financial news."""
    try:
        # Get news from Alpha Vantage News API
        api_key = get_secret("alpha-vantage-key", project_id)
        if not api_key:
            return {"error": "Alpha Vantage API key not found"}
            
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&topics={query}&apikey={api_key}"
        
        response = requests.get(url)
        response.raise_for_status()
        av_data = response.json()
        
        # Filter for recent news only
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        if 'feed' in av_data:
            filtered_news = [
                article for article in av_data['feed'] 
                if article.get('time_published', '') >= cutoff_date
            ]
            
            processed_news = []
            for article in filtered_news[:10]:  # Limit to 10 articles
                processed_news.append({
                    "title": article.get('title', ''),
                    "summary": article.get('summary', ''),
                    "source": article.get('source', ''),
                    "url": article.get('url', ''),
                    "published": article.get('time_published', ''),
                    "sentiment": article.get('overall_sentiment_score', 0)
                })
            
            return {
                "query": query,
                "days": days,
                "articles": processed_news,
                "status": "success"
            }
        else:
            return {"error": "No news data found", "status": "error"}
        
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "status": "error"
        }
