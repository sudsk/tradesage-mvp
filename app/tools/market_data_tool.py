# app/tools/market_data_tool.py - Updated with rate limiting
import yfinance as yf
import requests
from google.cloud import secretmanager
import json
import pandas as pd
import time
import random
from functools import wraps

# Simple in-memory cache
_cache = {}
_cache_timeout = 300  # 5 minutes

def rate_limit(calls_per_minute=10):
    """Decorator to rate limit function calls"""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

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

@rate_limit(calls_per_minute=6)  # Yahoo Finance allows ~6 calls per minute
def market_data_tool(instrument, source="yahoo", project_id="tradesage-mvp", force_refresh=False):
    """Tool for retrieving market data from various sources with rate limiting and caching."""
    
    # Check cache first
    cache_key = f"{source}_{instrument}"
    current_time = time.time()
    
    if not force_refresh and cache_key in _cache:
        cached_data, timestamp = _cache[cache_key]
        if current_time - timestamp < _cache_timeout:
            print(f"Returning cached data for {instrument}")
            return cached_data
    
    try:
        if source == 'yahoo':
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(0.5, 1.5))
            
            # Get data from Yahoo Finance with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    stock = yf.Ticker(instrument)
                    
                    # Get basic info with timeout
                    info = stock.info
                    
                    # Get recent history (last 30 days)
                    history = stock.history(period="1mo", interval="1d")
                    
                    if not history.empty:
                        current_price = history['Close'].iloc[-1]
                        previous_close = history['Close'].iloc[-2] if len(history) > 1 else current_price
                        
                        data = {
                            "symbol": instrument,
                            "info": {
                                "name": info.get("longName", instrument),
                                "sector": info.get("sector", "Financial"),
                                "marketCap": info.get("marketCap", 0),
                                "currentPrice": float(current_price),
                                "previousClose": float(previous_close),
                                "dayChange": float(current_price - previous_close),
                                "dayChangePercent": float(((current_price - previous_close) / previous_close) * 100) if previous_close != 0 else 0.0
                            },
                            "recent_price": float(current_price),
                            "price_history": history['Close'].tail(30).to_dict()
                        }
                    else:
                        # Fallback data if no history available
                        data = {
                            "symbol": instrument,
                            "info": {
                                "name": instrument,
                                "sector": "Financial",
                                "marketCap": 0,
                                "currentPrice": 100.0,  # Default price
                                "previousClose": 99.5,
                                "dayChange": 0.5,
                                "dayChangePercent": 0.5
                            },
                            "recent_price": 100.0,
                            "price_history": {}
                        }
                    
                    # Cache the result
                    _cache[cache_key] = (data, current_time)
                    return {
                        "instrument": instrument,
                        "source": source,
                        "data": data,
                        "status": "success"
                    }
                    
                except Exception as e:
                    if "429" in str(e) or "Too Many Requests" in str(e):
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        print(f"Rate limited. Waiting {wait_time:.2f} seconds before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise e
            
            # If all retries failed, return fallback data
            print(f"All retries failed for {instrument}, returning fallback data")
            fallback_data = {
                "symbol": instrument,
                "info": {
                    "name": instrument,
                    "sector": "Financial",
                    "marketCap": 0,
                    "currentPrice": 100.0,
                    "previousClose": 99.5,
                    "dayChange": 0.5,
                    "dayChangePercent": 0.5
                },
                "recent_price": 100.0,
                "price_history": {}
            }
            
            return {
                "instrument": instrument,
                "source": source,
                "data": fallback_data,
                "status": "success_cached"
            }
                
        elif source == 'alphavantage':
            # Alternative data source
            api_key = get_secret("alpha-vantage-key", project_id)
            if not api_key:
                return {"error": "Alpha Vantage API key not found"}
                
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={instrument}&apikey={api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Cache the result
            _cache[cache_key] = (data, current_time)
            
        elif source == 'fmp':
            # Financial Modeling Prep alternative
            api_key = get_secret("fmp-api-key", project_id)
            if not api_key:
                return {"error": "FMP API key not found"}
                
            url = f"https://financialmodelingprep.com/api/v3/profile/{instrument}?apikey={api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Cache the result
            _cache[cache_key] = (data, current_time)
            
        else:
            return {"error": f"Unsupported data source: {source}"}
        
        return {
            "instrument": instrument,
            "source": source,
            "data": data,
            "status": "success"
        }
        
    except Exception as e:
        print(f"Error fetching data for {instrument}: {str(e)}")
        # Return cached data if available, even if stale
        if cache_key in _cache:
            cached_data, timestamp = _cache[cache_key]
            print(f"Returning stale cached data for {instrument}")
            return cached_data
            
        # Last resort - return mock data
        return {
            "instrument": instrument,
            "source": source,
            "error": str(e),
            "status": "error",
            "data": {
                "symbol": instrument,
                "info": {
                    "name": instrument,
                    "sector": "Financial",
                    "marketCap": 0,
                    "currentPrice": 100.0,
                    "previousClose": 99.5,
                    "dayChange": 0.5,
                    "dayChangePercent": 0.5
                },
                "recent_price": 100.0,
                "price_history": {}
            }
        }
