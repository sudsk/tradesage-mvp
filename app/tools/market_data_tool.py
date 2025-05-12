# app/tools/market_data_tool.py
import yfinance as yf
import requests
from google.cloud import secretmanager
import json
import pandas as pd

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

def market_data_tool(instrument, source="yahoo", project_id="tradesage-mvp"):
    """Tool for retrieving market data from various sources."""
    try:
        if source == 'yahoo':
            # Get data from Yahoo Finance
            stock = yf.Ticker(instrument)
            info = stock.info
            history = stock.history(period="1d")
            
            if not history.empty:
                data = {
                    "symbol": instrument,
                    "info": {
                        "name": info.get("longName", instrument),
                        "sector": info.get("sector", "N/A"),
                        "marketCap": info.get("marketCap", 0),
                        "currentPrice": info.get("currentPrice", history.iloc[-1]['Close']),
                        "previousClose": info.get("previousClose", history.iloc[-1]['Close']),
                        "dayChange": history.iloc[-1]['Close'] - history.iloc[-1]['Open'],
                        "dayChangePercent": ((history.iloc[-1]['Close'] - history.iloc[-1]['Open']) / history.iloc[-1]['Open']) * 100
                    },
                    "recent_price": float(history.iloc[-1]['Close']),
                    "price_history": history.tail(30)['Close'].to_dict()
                }
            else:
                data = {"error": f"No data found for {instrument}"}
                
        elif source == 'alphavantage':
            # Get data from Alpha Vantage
            api_key = get_secret("alpha-vantage-key", project_id)
            if not api_key:
                return {"error": "Alpha Vantage API key not found"}
                
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={instrument}&apikey={api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
        elif source == 'fmp':
            # Get data from Financial Modeling Prep
            api_key = get_secret("fmp-api-key", project_id)
            if not api_key:
                return {"error": "FMP API key not found"}
                
            url = f"https://financialmodelingprep.com/api/v3/profile/{instrument}?apikey={api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
        else:
            return {"error": f"Unsupported data source: {source}"}
        
        return {
            "instrument": instrument,
            "source": source,
            "data": data,
            "status": "success"
        }
        
    except Exception as e:
        return {
            "instrument": instrument,
            "source": source,
            "error": str(e),
            "status": "error"
        }

