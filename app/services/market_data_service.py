# app/services/market_data_service.py - Multi-API implementation
import requests
import os
import time
import random
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum

class DataProvider(Enum):
    ALPHA_VANTAGE = "alpha_vantage"
    FMP = "fmp"
    IEX_CLOUD = "iex_cloud"
    POLYGON = "polygon"
    TWELVE_DATA = "twelve_data"
    YAHOO_FALLBACK = "yahoo"

@dataclass
class ApiConfig:
    name: str
    daily_limit: int
    per_minute_limit: int
    requires_key: bool
    base_url: str

class MultiApiMarketData:
    def __init__(self):
        self.api_configs = {
            DataProvider.ALPHA_VANTAGE: ApiConfig(
                name="Alpha Vantage",
                daily_limit=500,
                per_minute_limit=5,
                requires_key=True,
                base_url="https://www.alphavantage.co/query"
            ),
            DataProvider.FMP: ApiConfig(
                name="Financial Modeling Prep",
                daily_limit=250,
                per_minute_limit=10,
                requires_key=True,
                base_url="https://financialmodelingprep.com/api/v3"
            ),
            DataProvider.IEX_CLOUD: ApiConfig(
                name="IEX Cloud",
                daily_limit=500000,  # Messages
                per_minute_limit=100,
                requires_key=True,
                base_url="https://cloud.iexapis.com/stable"
            ),
            DataProvider.POLYGON: ApiConfig(
                name="Polygon.io",
                daily_limit=None,
                per_minute_limit=5,
                requires_key=True,
                base_url="https://api.polygon.io"
            ),
            DataProvider.TWELVE_DATA: ApiConfig(
                name="Twelve Data",
                daily_limit=800,
                per_minute_limit=8,
                requires_key=True,
                base_url="https://api.twelvedata.com"
            )
        }
        
        # API Keys from environment
        self.api_keys = {
            DataProvider.ALPHA_VANTAGE: os.getenv("ALPHA_VANTAGE_API_KEY"),
            DataProvider.FMP: os.getenv("FMP_API_KEY"),
            DataProvider.IEX_CLOUD: os.getenv("IEX_CLOUD_TOKEN"),
            DataProvider.POLYGON: os.getenv("POLYGON_API_KEY"),
            DataProvider.TWELVE_DATA: os.getenv("TWELVE_DATA_API_KEY")
        }
        
        # Priority order for APIs (most reliable first)
        self.api_priority = [
            DataProvider.IEX_CLOUD,
            DataProvider.ALPHA_VANTAGE,
            DataProvider.FMP,
            DataProvider.TWELVE_DATA,
            DataProvider.POLYGON,
            DataProvider.YAHOO_FALLBACK
        ]
        
        # Simple in-memory usage tracking
        self.usage_tracker = {}
    
    def get_stock_data(self, symbol: str, retries: int = 3) -> Optional[Dict]:
        """Get stock data with automatic failover between APIs"""
        
        for provider in self.api_priority:
            if not self._can_use_api(provider):
                continue
                
            try:
                print(f"Trying {provider.value} for {symbol}")
                data = self._fetch_from_provider(provider, symbol)
                
                if data and data.get('status') == 'success':
                    self._track_usage(provider)
                    return self._normalize_data(data, provider)
                    
            except Exception as e:
                print(f"Error with {provider.value}: {str(e)}")
                continue
                
        # If all APIs fail, return mock data
        print(f"All APIs failed for {symbol}, returning mock data")
        return self._get_mock_data(symbol)
    
    def _can_use_api(self, provider: DataProvider) -> bool:
        """Check if we can use this API (has key, within limits)"""
        if provider == DataProvider.YAHOO_FALLBACK:
            return True
            
        # Check if we have API key
        if not self.api_keys.get(provider):
            return False
            
        # Check daily limits (simplified)
        config = self.api_configs[provider]
        if config.daily_limit and self._get_daily_usage(provider) >= config.daily_limit:
            return False
            
        return True
    
    def _fetch_from_provider(self, provider: DataProvider, symbol: str) -> Dict:
        """Fetch data from specific provider"""
        
        if provider == DataProvider.ALPHA_VANTAGE:
            return self._fetch_alpha_vantage(symbol)
        elif provider == DataProvider.FMP:
            return self._fetch_fmp(symbol)
        elif provider == DataProvider.IEX_CLOUD:
            return self._fetch_iex_cloud(symbol)
        elif provider == DataProvider.POLYGON:
            return self._fetch_polygon(symbol)
        elif provider == DataProvider.TWELVE_DATA:
            return self._fetch_twelve_data(symbol)
        elif provider == DataProvider.YAHOO_FALLBACK:
            return self._fetch_yahoo_fallback(symbol)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def _fetch_alpha_vantage(self, symbol: str) -> Dict:
        """Fetch from Alpha Vantage API"""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_keys[DataProvider.ALPHA_VANTAGE]
        }
        
        response = requests.get(self.api_configs[DataProvider.ALPHA_VANTAGE].base_url, 
                              params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API error
        if 'Error Message' in data:
            raise Exception(data['Error Message'])
            
        if 'Global Quote' not in data:
            raise Exception("No data in response")
            
        quote = data['Global Quote']
        
        return {
            'status': 'success',
            'provider': 'alpha_vantage',
            'symbol': symbol,
            'price': float(quote.get('05. price', 0)),
            'change': float(quote.get('09. change', 0)),
            'change_percent': quote.get('10. change percent', '0.00%').replace('%', ''),
            'volume': int(quote.get('06. volume', 0)),
            'previous_close': float(quote.get('08. previous close', 0)),
            'open': float(quote.get('02. open', 0)),
            'high': float(quote.get('03. high', 0)),
            'low': float(quote.get('04. low', 0))
        }
    
    def _fetch_fmp(self, symbol: str) -> Dict:
        """Fetch from Financial Modeling Prep API"""
        url = f"{self.api_configs[DataProvider.FMP].base_url}/quote/{symbol}"
        params = {'apikey': self.api_keys[DataProvider.FMP]}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or len(data) == 0:
            raise Exception("No data received")
            
        quote = data[0]
        
        return {
            'status': 'success',
            'provider': 'fmp',
            'symbol': symbol,
            'price': quote.get('price', 0),
            'change': quote.get('change', 0),
            'change_percent': quote.get('changesPercentage', 0),
            'volume': quote.get('volume', 0),
            'previous_close': quote.get('previousClose', 0),
            'open': quote.get('open', 0),
            'high': quote.get('dayHigh', 0),
            'low': quote.get('dayLow', 0)
        }
    
    def _fetch_iex_cloud(self, symbol: str) -> Dict:
        """Fetch from IEX Cloud API"""
        url = f"{self.api_configs[DataProvider.IEX_CLOUD].base_url}/stock/{symbol}/quote"
        params = {'token': self.api_keys[DataProvider.IEX_CLOUD]}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            'status': 'success',
            'provider': 'iex_cloud',
            'symbol': symbol,
            'price': data.get('latestPrice', 0),
            'change': data.get('change', 0),
            'change_percent': data.get('changePercent', 0) * 100,
            'volume': data.get('latestVolume', 0),
            'previous_close': data.get('previousClose', 0),
            'open': data.get('open', 0),
            'high': data.get('high', 0),
            'low': data.get('low', 0)
        }
    
    def _fetch_polygon(self, symbol: str) -> Dict:
        """Fetch from Polygon.io API"""
        url = f"{self.api_configs[DataProvider.POLYGON].base_url}/v2/aggs/ticker/{symbol}/prev"
        params = {'apikey': self.api_keys[DataProvider.POLYGON]}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('results') or len(data['results']) == 0:
            raise Exception("No data received")
            
        result = data['results'][0]
        
        # Calculate change (Polygon doesn't provide it directly)
        current_price = result.get('c', 0)
        previous_close = result.get('o', current_price)  # Using open as proxy
        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close != 0 else 0
        
        return {
            'status': 'success',
            'provider': 'polygon',
            'symbol': symbol,
            'price': current_price,
            'change': change,
            'change_percent': change_percent,
            'volume': result.get('v', 0),
            'previous_close': previous_close,
            'open': result.get('o', 0),
            'high': result.get('h', 0),
            'low': result.get('l', 0)
        }
    
    def _fetch_twelve_data(self, symbol: str) -> Dict:
        """Fetch from Twelve Data API"""
        url = f"{self.api_configs[DataProvider.TWELVE_DATA].base_url}/quote"
        params = {
            'symbol': symbol,
            'apikey': self.api_keys[DataProvider.TWELVE_DATA]
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'error':
            raise Exception(data.get('message', 'API Error'))
        
        return {
            'status': 'success',
            'provider': 'twelve_data',
            'symbol': symbol,
            'price': float(data.get('close', 0)),
            'change': float(data.get('change', 0)),
            'change_percent': float(data.get('percent_change', 0)),
            'volume': int(data.get('volume', 0)),
            'previous_close': float(data.get('previous_close', 0)),
            'open': float(data.get('open', 0)),
            'high': float(data.get('high', 0)),
            'low': float(data.get('low', 0))
        }
    
    def _fetch_yahoo_fallback(self, symbol: str) -> Dict:
        """Fallback to yfinance with rate limiting"""
        import yfinance as yf
        time.sleep(2)  # Rate limiting
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")
        
        if hist.empty:
            raise Exception("No data from Yahoo Finance")
        
        current_price = hist['Close'].iloc[-1]
        previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        
        return {
            'status': 'success',
            'provider': 'yahoo_fallback',
            'symbol': symbol,
            'price': float(current_price),
            'change': float(current_price - previous_close),
            'change_percent': float((current_price - previous_close) / previous_close * 100),
            'volume': int(hist['Volume'].iloc[-1]),
            'previous_close': float(previous_close),
            'open': float(hist['Open'].iloc[-1]),
            'high': float(hist['High'].iloc[-1]),
            'low': float(hist['Low'].iloc[-1])
        }
    
    def _normalize_data(self, data: Dict, provider: DataProvider) -> Dict:
        """Normalize data from different providers to standard format"""
        return {
            'instrument': data['symbol'],
            'source': data['provider'],
            'data': {
                'symbol': data['symbol'],
                'info': {
                    'name': data['symbol'],
                    'currentPrice': data['price'],
                    'previousClose': data['previous_close'],
                    'dayChange': data['change'],
                    'dayChangePercent': float(str(data['change_percent']).replace('%', '')),
                    'volume': data['volume'],
                    'open': data['open'],
                    'high': data['high'],
                    'low': data['low']
                },
                'recent_price': data['price']
            },
            'status': 'success'
        }
    
    def _get_mock_data(self, symbol: str) -> Dict:
        """Generate mock data as last resort"""
        base_price = random.uniform(50, 200)
        change = random.uniform(-5, 5)
        
        return {
            'instrument': symbol,
            'source': 'mock',
            'data': {
                'symbol': symbol,
                'info': {
                    'name': f"{symbol} Mock Data",
                    'currentPrice': round(base_price, 2),
                    'previousClose': round(base_price - change, 2),
                    'dayChange': round(change, 2),
                    'dayChangePercent': round((change / base_price) * 100, 2),
                    'volume': random.randint(1000000, 10000000),
                    'open': round(base_price + random.uniform(-2, 2), 2),
                    'high': round(base_price + random.uniform(0, 5), 2),
                    'low': round(base_price - random.uniform(0, 5), 2)
                },
                'recent_price': round(base_price, 2)
            },
            'status': 'success_mock'
        }
    
    def _track_usage(self, provider: DataProvider):
        """Track API usage"""
        today = time.strftime("%Y-%m-%d")
        key = f"{provider.value}_{today}"
        self.usage_tracker[key] = self.usage_tracker.get(key, 0) + 1
    
    def _get_daily_usage(self, provider: DataProvider) -> int:
        """Get today's usage for a provider"""
        today = time.strftime("%Y-%m-%d")
        key = f"{provider.value}_{today}"
        return self.usage_tracker.get(key, 0)

# Usage example
market_data_service = MultiApiMarketData()

def enhanced_market_data_tool(instrument, source="auto", project_id="tradesage-mvp"):
    """Enhanced market data tool with multiple API fallbacks"""
    try:
        return market_data_service.get_stock_data(instrument)
    except Exception as e:
        print(f"Error fetching data for {instrument}: {str(e)}")
        return market_data_service._get_mock_data(instrument)
