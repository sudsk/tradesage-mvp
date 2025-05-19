# app/services/market_data_service.py - Simplified for reliability

import requests
import os
import time
import random
import json
from datetime import datetime, timedelta

class MarketDataService:
    def __init__(self):
        # Load API keys from environment
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.fmp_key = os.getenv("FMP_API_KEY")
        
        # Cache to prevent redundant calls
        self._cache = {}
        self._cache_duration = 300  # 5 minutes
        
        print("Market data service initialized with:")
        print(f"- Alpha Vantage API key: {'Available' if self.alpha_vantage_key else 'Not found'}")
        print(f"- FMP API key: {'Available' if self.fmp_key else 'Not found'}")
    
    def get_stock_data(self, symbol):
        """Main method to fetch stock data with fallbacks"""
        # Check cache first
        if symbol in self._cache:
            cache_time, cache_data = self._cache[symbol]
            if time.time() - cache_time < self._cache_duration:
                print(f"Using cached data for {symbol}")
                return cache_data
        
        # Try Alpha Vantage first (if key is available)
        if self.alpha_vantage_key:
            try:
                print(f"Trying Alpha Vantage for {symbol}")
                data = self._fetch_alpha_vantage(symbol)
                self._cache[symbol] = (time.time(), data)
                return data
            except Exception as e:
                print(f"Alpha Vantage failed: {str(e)}")
        
        # Try FMP next (if key is available)
        if self.fmp_key:
            try:
                print(f"Trying Financial Modeling Prep for {symbol}")
                data = self._fetch_fmp(symbol)
                self._cache[symbol] = (time.time(), data)
                return data
            except Exception as e:
                print(f"FMP failed: {str(e)}")
        
        # Try Yahoo Finance as last resort
        try:
            print(f"Trying Yahoo Finance for {symbol}")
            data = self._fetch_yahoo(symbol)
            self._cache[symbol] = (time.time(), data)
            return data
        except Exception as e:
            print(f"Yahoo Finance failed: {str(e)}")
        
        # If all APIs fail, return mock data
        print(f"All APIs failed for {symbol}, returning mock data")
        mock_data = self._generate_mock_data(symbol)
        self._cache[symbol] = (time.time(), mock_data)
        return mock_data
    
    def _fetch_alpha_vantage(self, symbol):
        """Fetch data from Alpha Vantage"""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.alpha_vantage_key
        }
        
        url = "https://www.alphavantage.co/query"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API error
        if 'Error Message' in data:
            raise Exception(data['Error Message'])
            
        if 'Global Quote' not in data or not data['Global Quote']:
            raise Exception("No data in Alpha Vantage response")
            
        quote = data['Global Quote']
        price = float(quote.get('05. price', 0))
        
        if price <= 0:
            raise Exception("Invalid price data")
        
        return {
            'instrument': symbol,
            'source': 'alpha_vantage',
            'data': {
                'symbol': symbol,
                'info': {
                    'name': symbol,
                    'sector': 'Technology',  # Placeholder
                    'marketCap': 0,  # Placeholder
                    'currentPrice': price,
                    'previousClose': float(quote.get('08. previous close', 0)),
                    'dayChange': float(quote.get('09. change', 0)),
                    'dayChangePercent': float(quote.get('10. change percent', '0.0%').replace('%', ''))
                },
                'recent_price': price,
                'price_history': {}  # Would need additional API call
            },
            'status': 'success'
        }
    
    def _fetch_fmp(self, symbol):
        """Fetch data from Financial Modeling Prep"""
        url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}"
        params = {'apikey': self.fmp_key}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or len(data) == 0:
            raise Exception("No data received from FMP")
            
        quote = data[0]
        price = quote.get('price', 0)
        
        if price <= 0:
            raise Exception("Invalid price data from FMP")
        
        return {
            'instrument': symbol,
            'source': 'fmp',
            'data': {
                'symbol': symbol,
                'info': {
                    'name': quote.get('name', symbol),
                    'sector': quote.get('sector', 'Unknown'),
                    'marketCap': quote.get('marketCap', 0),
                    'currentPrice': price,
                    'previousClose': quote.get('previousClose', 0),
                    'dayChange': quote.get('change', 0),
                    'dayChangePercent': quote.get('changesPercentage', 0)
                },
                'recent_price': price,
                'price_history': {}
            },
            'status': 'success'
        }
    
    def _fetch_yahoo(self, symbol):
        """Fetch data directly from Yahoo Finance website"""
        # Use direct HTML scraping as a backup approach
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            url = f"https://finance.yahoo.com/quote/{symbol}"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get current price
            price_element = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'})
            if not price_element:
                raise Exception("Price element not found")
                
            price = float(price_element.get('value', 0))
            
            # Get previous close
            prev_close_element = None
            table_rows = soup.find_all('tr')
            for row in table_rows:
                if row.find('td') and 'Previous Close' in row.find('td').get_text():
                    prev_close_element = row.find_all('td')[1]
                    break
            
            prev_close = float(prev_close_element.get_text().replace(',', '')) if prev_close_element else price
            change = price - prev_close
            change_percent = (change / prev_close * 100) if prev_close != 0 else 0
            
            return {
                'instrument': symbol,
                'source': 'yahoo_scraped',
                'data': {
                    'symbol': symbol,
                    'info': {
                        'name': soup.find('h1').get_text() if soup.find('h1') else symbol,
                        'sector': 'Unknown',  # Not easily scraped
                        'marketCap': 0,  # Not easily scraped
                        'currentPrice': price,
                        'previousClose': prev_close,
                        'dayChange': change,
                        'dayChangePercent': change_percent
                    },
                    'recent_price': price,
                    'price_history': {}
                },
                'status': 'success'
            }
            
        except Exception as e:
            print(f"Error scraping Yahoo Finance: {str(e)}")
            
            # Try a different Yahoo page as backup
            try:
                url = f"https://finance.yahoo.com/quote/{symbol}/history"
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for price in historical data
                price_rows = soup.find_all('tr', {'class': 'BdT Bdc($seperatorColor)'})
                if price_rows and len(price_rows) > 0:
                    cells = price_rows[0].find_all('td')
                    if len(cells) >= 5:
                        price = float(cells[4].get_text().replace(',', ''))
                        return {
                            'instrument': symbol,
                            'source': 'yahoo_history',
                            'data': {
                                'symbol': symbol,
                                'info': {
                                    'name': symbol,
                                    'sector': 'Unknown',
                                    'marketCap': 0,
                                    'currentPrice': price,
                                    'previousClose': price,  # We don't have this
                                    'dayChange': 0,  # We don't have this
                                    'dayChangePercent': 0  # We don't have this
                                },
                                'recent_price': price,
                                'price_history': {}
                            },
                            'status': 'success'
                        }
            except:
                pass  # Let it fall through to the original error
            
            raise Exception(f"Failed to scrape Yahoo Finance: {str(e)}")
    
    def _generate_mock_data(self, symbol):
        """Generate realistic mock data based on the symbol"""
        # Use different price ranges for different symbols
        symbol_first_letter = symbol[0].upper()
        
        # Assign price range based on first letter (just for variety)
        if symbol_first_letter in 'ABCDE':
            base_price = random.uniform(50, 150)
        elif symbol_first_letter in 'FGHIJ':
            base_price = random.uniform(100, 300)
        elif symbol_first_letter in 'KLMNO':
            base_price = random.uniform(150, 400)
        elif symbol_first_letter in 'PQRST':
            base_price = random.uniform(75, 250)
        else:
            base_price = random.uniform(25, 200)
            
        # Generate change
        change_percent = random.uniform(-3, 3)
        change = base_price * change_percent / 100
        prev_close = base_price - change
        
        # Mock price history (last 7 days)
        price_history = {}
        now = datetime.now()
        
        for i in range(7, 0, -1):
            day = now - timedelta(days=i)
            day_str = day.strftime('%Y-%m-%d')
            day_price = base_price * (1 + random.uniform(-0.05, 0.05))
            price_history[day_str] = round(day_price, 2)
        
        return {
            'instrument': symbol,
            'source': 'mock',
            'data': {
                'symbol': symbol,
                'info': {
                    'name': f"{symbol} Stock",
                    'sector': random.choice(['Technology', 'Healthcare', 'Financial', 'Consumer', 'Industrial']),
                    'marketCap': round(base_price * random.uniform(1000000, 1000000000), 0),
                    'currentPrice': round(base_price, 2),
                    'previousClose': round(prev_close, 2),
                    'dayChange': round(change, 2),
                    'dayChangePercent': round(change_percent, 2),
                    'volume': random.randint(100000, 10000000)
                },
                'recent_price': round(base_price, 2),
                'price_history': price_history
            },
            'status': 'success_mock'
        }

# Create a singleton instance
market_data_service = MarketDataService()

def get_market_data(symbol):
    """Helper function to get market data"""
    return market_data_service.get_stock_data(symbol)
