# app/services/market_data_service.py - Real data only, no mock fallbacks

import requests
import os
import time
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
        
        if not self.alpha_vantage_key and not self.fmp_key:
            print("⚠️  WARNING: No API keys found. Market data will be limited to Yahoo Finance scraping.")
    
    def get_stock_data(self, symbol):
        """Main method to fetch stock data - real data only, no mocks"""
        
        # Validate symbol
        if not symbol or len(symbol.strip()) == 0:
            return {
                'instrument': symbol,
                'error': 'Invalid symbol provided',
                'status': 'error'
            }
        
        symbol = symbol.upper().strip()
        
        # Check cache first
        cache_key = f"{symbol}_{int(time.time() // self._cache_duration)}"
        if cache_key in self._cache:
            print(f"✅ Using cached data for {symbol}")
            return self._cache[cache_key]
        
        errors = []
        
        # Try Alpha Vantage first (if key is available)
        if self.alpha_vantage_key:
            try:
                print(f"🔍 Fetching {symbol} from Alpha Vantage...")
                data = self._fetch_alpha_vantage(symbol)
                self._cache[cache_key] = data
                print(f"✅ Successfully fetched {symbol} from Alpha Vantage: ${data['data']['info']['currentPrice']}")
                return data
            except Exception as e:
                error_msg = f"Alpha Vantage failed: {str(e)}"
                print(f"❌ {error_msg}")
                errors.append(error_msg)
        
        # Try FMP next (if key is available)
        if self.fmp_key:
            try:
                print(f"🔍 Fetching {symbol} from Financial Modeling Prep...")
                data = self._fetch_fmp(symbol)
                self._cache[cache_key] = data
                print(f"✅ Successfully fetched {symbol} from FMP: ${data['data']['info']['currentPrice']}")
                return data
            except Exception as e:
                error_msg = f"FMP failed: {str(e)}"
                print(f"❌ {error_msg}")
                errors.append(error_msg)
        
        # Try Yahoo Finance as last resort
        try:
            print(f"🔍 Fetching {symbol} from Yahoo Finance (scraping)...")
            data = self._fetch_yahoo(symbol)
            self._cache[cache_key] = data
            print(f"✅ Successfully fetched {symbol} from Yahoo Finance: ${data['data']['info']['currentPrice']}")
            return data
        except Exception as e:
            error_msg = f"Yahoo Finance failed: {str(e)}"
            print(f"❌ {error_msg}")
            errors.append(error_msg)
        
        # If all methods fail, return error
        all_errors = "; ".join(errors)
        error_response = {
            'instrument': symbol,
            'error': f'Unable to fetch real market data for {symbol}. All sources failed: {all_errors}',
            'errors_detail': errors,
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'suggestions': [
                'Check if the symbol is correct (e.g., AAPL for Apple)',
                'Verify API keys are properly configured',
                'Try again in a few minutes (rate limits may apply)',
                'Check if the market is open (some APIs have limited weekend data)'
            ]
        }
        
        print(f"❌ Failed to fetch data for {symbol}: {all_errors}")
        return error_response
    
    def _fetch_alpha_vantage(self, symbol):
        """Fetch data from Alpha Vantage API"""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.alpha_vantage_key
        }
        
        url = "https://www.alphavantage.co/query"
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            raise Exception(f"API Error: {data['Error Message']}")
            
        if 'Note' in data:
            raise Exception("API rate limit exceeded. Please try again later.")
            
        if 'Global Quote' not in data or not data['Global Quote']:
            raise Exception("No quote data returned. Symbol may be invalid.")
            
        quote = data['Global Quote']
        
        # Validate price data
        try:
            price = float(quote.get('05. price', 0))
            prev_close = float(quote.get('08. previous close', 0))
            change = float(quote.get('09. change', 0))
            change_percent_str = quote.get('10. change percent', '0.0%')
            change_percent = float(change_percent_str.replace('%', ''))
        except (ValueError, TypeError):
            raise Exception("Invalid price data format from Alpha Vantage")
        
        if price <= 0:
            raise Exception(f"Invalid price data: ${price}")
        
        return {
            'instrument': symbol,
            'source': 'alpha_vantage',
            'data': {
                'symbol': symbol,
                'info': {
                    'name': f"{symbol} Stock",
                    'sector': 'Unknown',  # Alpha Vantage quote doesn't include sector
                    'marketCap': 0,  # Not available in quote endpoint
                    'currentPrice': round(price, 2),
                    'previousClose': round(prev_close, 2),
                    'dayChange': round(change, 2),
                    'dayChangePercent': round(change_percent, 2),
                    'volume': int(quote.get('06. volume', 0)),
                    'lastUpdated': quote.get('07. latest trading day', datetime.now().strftime('%Y-%m-%d'))
                },
                'recent_price': round(price, 2),
                'price_history': {}  # Would need additional API call
            },
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        }
    
    def _fetch_fmp(self, symbol):
        """Fetch data from Financial Modeling Prep API"""
        url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}"
        params = {'apikey': self.fmp_key}
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or len(data) == 0:
            raise Exception("No data returned. Symbol may be invalid.")
            
        if isinstance(data, dict) and 'Error Message' in data:
            raise Exception(f"API Error: {data['Error Message']}")
            
        quote = data[0]
        
        # Validate price data
        try:
            price = float(quote.get('price', 0))
            prev_close = float(quote.get('previousClose', 0))
            change = float(quote.get('change', 0))
            change_percent = float(quote.get('changesPercentage', 0))
            volume = int(quote.get('volume', 0))
            market_cap = int(quote.get('marketCap', 0))
        except (ValueError, TypeError):
            raise Exception("Invalid price data format from FMP")
        
        if price <= 0:
            raise Exception(f"Invalid price data: ${price}")
        
        return {
            'instrument': symbol,
            'source': 'fmp',
            'data': {
                'symbol': symbol,
                'info': {
                    'name': quote.get('name', f"{symbol} Stock"),
                    'sector': quote.get('sector', 'Unknown'),
                    'marketCap': market_cap,
                    'currentPrice': round(price, 2),
                    'previousClose': round(prev_close, 2),
                    'dayChange': round(change, 2),
                    'dayChangePercent': round(change_percent, 2),
                    'volume': volume,
                    'lastUpdated': datetime.now().strftime('%Y-%m-%d')
                },
                'recent_price': round(price, 2),
                'price_history': {}
            },
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        }
    
    def _fetch_yahoo(self, symbol):
        """Fetch data from Yahoo Finance via web scraping"""
        
        # Handle different symbol formats
        yahoo_symbol = symbol
        if '-' not in symbol and symbol not in ['BTC-USD', 'ETH-USD', 'SOL-USD']:
            # Regular stock symbol
            yahoo_symbol = symbol
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        try:
            url = f"https://finance.yahoo.com/quote/{yahoo_symbol}"
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Check if page indicates invalid symbol
            if "Symbol Lookup" in response.text or "doesn't exist" in response.text:
                raise Exception(f"Symbol {symbol} not found on Yahoo Finance")
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract current price
            price_element = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'})
            if not price_element:
                # Try alternative price element
                price_element = soup.find('span', {'data-reactid': '50'})
                if not price_element:
                    raise Exception("Price element not found on Yahoo Finance page")
            
            try:
                price_value = price_element.get('value') or price_element.get_text()
                price = float(price_value.replace(',', '').replace('$', ''))
            except (ValueError, AttributeError):
                raise Exception("Could not parse price from Yahoo Finance")
            
            if price <= 0:
                raise Exception(f"Invalid price found: ${price}")
            
            # Extract additional data
            name = yahoo_symbol
            try:
                name_element = soup.find('h1', {'data-reactid': '7'})
                if name_element:
                    name = name_element.get_text().split('(')[0].strip()
            except:
                pass
            
            # Extract previous close and calculate change
            prev_close = price  # Default fallback
            change = 0
            change_percent = 0
            
            try:
                # Look for previous close in summary table
                summary_table = soup.find('div', {'data-test': 'quote-statistics'}) or soup.find('div', {'data-test': 'summary-table'})
                if summary_table:
                    rows = summary_table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            label = cells[0].get_text().strip()
                            if 'Previous Close' in label:
                                prev_close = float(cells[1].get_text().replace(',', '').replace('$', ''))
                                change = price - prev_close
                                change_percent = (change / prev_close * 100) if prev_close != 0 else 0
                                break
            except:
                pass  # Use defaults
            
            # Determine sector (simplified)
            sector = "Unknown"
            if any(crypto in yahoo_symbol for crypto in ['BTC', 'ETH', 'SOL', 'ADA']):
                sector = "Cryptocurrency"
            
            return {
                'instrument': symbol,
                'source': 'yahoo_scraped',
                'data': {
                    'symbol': symbol,
                    'info': {
                        'name': name,
                        'sector': sector,
                        'marketCap': 0,  # Not easily scraped
                        'currentPrice': round(price, 2),
                        'previousClose': round(prev_close, 2),
                        'dayChange': round(change, 2),
                        'dayChangePercent': round(change_percent, 2),
                        'volume': 0,  # Not easily scraped
                        'lastUpdated': datetime.now().strftime('%Y-%m-%d')
                    },
                    'recent_price': round(price, 2),
                    'price_history': {}
                },
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }
            
        except requests.RequestException as e:
            raise Exception(f"Network error accessing Yahoo Finance: {str(e)}")
        except Exception as e:
            raise Exception(f"Error scraping Yahoo Finance: {str(e)}")
    
    def get_crypto_data(self, crypto_symbol):
        """Specific method for cryptocurrency data"""
        # Ensure proper format for crypto symbols
        if not crypto_symbol.endswith('-USD'):
            if crypto_symbol.upper() in ['BTC', 'BITCOIN']:
                crypto_symbol = 'BTC-USD'
            elif crypto_symbol.upper() in ['ETH', 'ETHEREUM']:
                crypto_symbol = 'ETH-USD'
            elif crypto_symbol.upper() in ['SOL', 'SOLANA']:
                crypto_symbol = 'SOL-USD'
            elif crypto_symbol.upper() in ['ADA', 'CARDANO']:
                crypto_symbol = 'ADA-USD'
            else:
                crypto_symbol = f"{crypto_symbol.upper()}-USD"
        
        return self.get_stock_data(crypto_symbol)
    
    def get_multiple_quotes(self, symbols):
        """Fetch data for multiple symbols"""
        results = {}
        
        for symbol in symbols:
            try:
                data = self.get_stock_data(symbol)
                results[symbol] = data
                
                # Add small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                results[symbol] = {
                    'instrument': symbol,
                    'error': str(e),
                    'status': 'error'
                }
        
        return results
    
    def clear_cache(self):
        """Clear the cache - useful for testing"""
        self._cache.clear()
        print("Market data cache cleared")
    
    def get_cache_info(self):
        """Get information about cached data"""
        return {
            'cached_symbols': list(self._cache.keys()),
            'cache_size': len(self._cache),
            'cache_duration_seconds': self._cache_duration
        }

# Create a singleton instance
market_data_service = MarketDataService()

def get_market_data(symbol):
    """Helper function to get market data"""
    return market_data_service.get_stock_data(symbol)

def get_crypto_data(crypto_symbol):
    """Helper function to get cryptocurrency data"""
    return market_data_service.get_crypto_data(crypto_symbol)
