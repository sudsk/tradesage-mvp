# 5_multi_source_technical_collector_complete.py
import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import time
import random
import requests

# Define instruments with proper Yahoo Finance tickers
INSTRUMENTS = {
    "AAPL": "AAPL",
    "MSFT": "MSFT", 
    "GOOGL": "GOOGL",
    "AMZN": "AMZN",
    "NVDA": "NVDA", 
    "TSLA": "TSLA",
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
    "Gold": "GC=F",      # Gold futures
    "Brent Crude": "BZ=F", # Brent crude futures
    "Treasury": "^TNX"   # 10-year Treasury yield
}

# Add headers to avoid being blocked
def get_session():
    """Create a session with proper headers"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    return session

def fetch_from_alpha_vantage(symbol, api_key=None):
    """Fetch from Alpha Vantage as backup"""
    if not api_key:
        return None
    
    print(f" Trying symbol:{symbol}")
    url = f"https://www.alphavantage.co/query"
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': api_key,
        'outputsize': 'compact'
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        if 'Time Series (Daily)' in data:
            # Convert to pandas DataFrame
            time_series = data['Time Series (Daily)']
            
            df_data = []
            for date, values in time_series.items():
                df_data.append({
                    'Open': float(values['1. open']),
                    'High': float(values['2. high']),
                    'Low': float(values['3. low']),
                    'Close': float(values['4. close']),
                    'Volume': int(values['5. volume'])
                })
            
            df = pd.DataFrame(df_data)
            df.index = pd.to_datetime(list(time_series.keys()))
            df.sort_index(inplace=True)
            
            return df
        elif 'Note' in data:
            print(f"    ⚠️  Alpha Vantage API limit reached")
            return None
        elif 'Error Message' in data:
            print(f"    ❌ Alpha Vantage error: {data['Error Message']}")
            return None
            
    except Exception as e:
        print(f"    Alpha Vantage error: {str(e)}")
        return None

def map_ticker_for_alpha_vantage(ticker):
    """Map Yahoo Finance tickers to Alpha Vantage compatible symbols"""
    mapping = {
        'BTC-USD': 'BTC',  # Crypto not available in Alpha Vantage stock API
        'ETH-USD': 'ETH',  # Crypto not available in Alpha Vantage stock API
        'GC=F': 'GLD',     # Use Gold ETF instead of futures
        'BZ=F': 'USO',     # Use Oil ETF instead of Brent futures
        '^TNX': 'TNX'      # Treasury yield
    }
    return mapping.get(ticker, ticker)

def fetch_mock_data(ticker):
    """Generate mock data as last resort for demo purposes"""
    print(f"    Generating mock data for {ticker}...")
    
    # Generate 100 days of mock data
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    
    # Start with a reasonable base price
    if 'BTC' in ticker:
        base_price = 45000
    elif 'ETH' in ticker:
        base_price = 2500
    elif ticker in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA']:
        base_price = 150
    elif 'GC' in ticker:  # Gold
        base_price = 2000
    elif 'BZ' in ticker or 'CL' in ticker:  # Oil
        base_price = 75
    else:
        base_price = 100
    
    # Generate price data with random walk
    np.random.seed(hash(ticker) % 2**32)  # Consistent seed based on ticker
    returns = np.random.normal(0.001, 0.02, len(dates))  # Daily returns
    prices = [base_price]
    
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    # Create OHLCV data
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        volatility = abs(np.random.normal(0, 0.015))
        high = close * (1 + volatility)
        low = close * (1 - volatility)
        open_price = prices[i-1] if i > 0 else close
        volume = int(np.random.normal(1000000, 300000))
        
        data.append({
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close,
            'Volume': max(volume, 100000)  # Minimum volume
        })
    
    df = pd.DataFrame(data, index=dates)
    print(f"    Generated {len(df)} days of mock data")
    return df

def fetch_historical_data(ticker, period="6mo", max_retries=2):
    """Fetch data with retry logic and better error handling"""
    
    for attempt in range(max_retries):
        try:
            print(f"    Yahoo Finance attempt {attempt + 1}...")
            
            # Create a session with headers
            session = get_session()
            
            # Create ticker object with session
            stock = yf.Ticker(ticker, session=session)
            
            data = stock.history(period=period, timeout=30)
            
            if not data.empty and len(data) > 20:  # Need at least 20 data points
                print(f"    ✅ Yahoo Finance success: {len(data)} data points")
                return data
            else:
                print(f"    ⚠️  Empty or insufficient data for period {period}")
                        
        except Exception as e:
            print(f"    ❌ Yahoo Finance attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(3)
    
    return None

def fetch_data_with_fallbacks(ticker, name):
    """Try multiple data sources with fallbacks"""
    
    print(f"  Fetching data for {name} ({ticker})...")
    
    # Method 1: Yahoo Finance with retries
    historical_data = fetch_historical_data(ticker)
    
    if historical_data is not None and not historical_data.empty:
        return historical_data, "yahoo_finance"
    
    # Method 2: Alpha Vantage (if you have API key)
    alpha_vantage_key = "YOUR_ALPHA_VANTAGE_API_KEY"  # Replace with your actual key
    if alpha_vantage_key and alpha_vantage_key != "YOUR_ALPHA_VANTAGE_API_KEY":
        print(f"    Trying Alpha Vantage...")
        av_symbol = map_ticker_for_alpha_vantage(ticker)
        data = fetch_from_alpha_vantage(av_symbol, alpha_vantage_key)
        if data is not None and not data.empty:
            print(f"    ✅ Alpha Vantage success: {len(data)} data points")
            return data, "alpha_vantage"
    
    # Method 3: Mock data for demo
    print(f"    All real data sources failed, generating mock data...")
    data = fetch_mock_data(ticker)
    return data, "mock_data"

# ========== TECHNICAL ANALYSIS FUNCTIONS ==========

def calculate_sma(data, window):
    """Simple Moving Average"""
    return data.rolling(window=window).mean()

def calculate_ema(data, window):
    """Exponential Moving Average"""
    return data.ewm(span=window).mean()

def calculate_rsi(data, window=14):
    """Relative Strength Index"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data, fast=12, slow=26, signal=9):
    """MACD Indicator"""
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(data, window=20, num_std=2):
    """Bollinger Bands"""
    sma = calculate_sma(data, window)
    std = data.rolling(window=window).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    return upper_band, sma, lower_band

def calculate_stochastic(high, low, close, k_window=14, d_window=3):
    """Stochastic Oscillator"""
    lowest_low = low.rolling(window=k_window).min()
    highest_high = high.rolling(window=k_window).max()
    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d_percent = k_percent.rolling(window=d_window).mean()
    return k_percent, d_percent

def calculate_technical_indicators(data):
    """Calculate all technical indicators"""
    if data is None or len(data) < 50:
        return None
    
    # Copy the data to avoid SettingWithCopyWarning
    df = data.copy()
    
    try:
        # Moving averages
        df['SMA_20'] = calculate_sma(df['Close'], 20)
        df['SMA_50'] = calculate_sma(df['Close'], 50)
        df['SMA_200'] = calculate_sma(df['Close'], 200)
        df['EMA_12'] = calculate_ema(df['Close'], 12)
        df['EMA_26'] = calculate_ema(df['Close'], 26)
        
        # RSI
        df['RSI'] = calculate_rsi(df['Close'], 14)
        
        # MACD
        df['MACD'], df['MACD_signal'], df['MACD_hist'] = calculate_macd(df['Close'])
        
        # Bollinger Bands
        df['BB_upper'], df['BB_middle'], df['BB_lower'] = calculate_bollinger_bands(df['Close'])
        
        # Stochastic
        df['Stoch_K'], df['Stoch_D'] = calculate_stochastic(df['High'], df['Low'], df['Close'])
        
        # Volume indicators
        if 'Volume' in df.columns:
            df['Volume_SMA'] = calculate_sma(df['Volume'], 20)
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        else:
            df['Volume_SMA'] = 1000000  # Default volume
            df['Volume_Ratio'] = 1.0
        
        # Price momentum
        df['Price_Change_1d'] = df['Close'].pct_change(1) * 100
        df['Price_Change_5d'] = df['Close'].pct_change(5) * 100
        df['Price_Change_20d'] = df['Close'].pct_change(20) * 100
        
        # Volatility (using standard deviation)
        df['Volatility_20d'] = df['Close'].rolling(window=20).std()
        
        return df
        
    except Exception as e:
        print(f"Error calculating indicators: {str(e)}")
        return None

def generate_technical_analysis(data, ticker):
    """Generate comprehensive technical analysis"""
    if data is None:
        return None
    
    # Get the most recent data points
    latest = data.iloc[-1]
    prev = data.iloc[-2] if len(data) > 1 else latest
    
    # Basic trend analysis
    trend = "Uptrend" if latest['Close'] > latest['SMA_50'] > latest['SMA_200'] else \
            "Downtrend" if latest['Close'] < latest['SMA_50'] < latest['SMA_200'] else \
            "Sideways"
    
    # RSI analysis
    rsi_status = "Overbought" if latest['RSI'] > 70 else \
                 "Oversold" if latest['RSI'] < 30 else \
                 "Neutral"
    
    # MACD analysis
    macd_signal = "Bullish" if latest['MACD'] > latest['MACD_signal'] else "Bearish"
    
    # Bollinger Bands analysis
    bb_status = "Upper Band" if latest['Close'] >= latest['BB_upper'] * 0.98 else \
                "Lower Band" if latest['Close'] <= latest['BB_lower'] * 1.02 else \
                "Middle Range"
    
    # Support and resistance levels
    recent_data = data.tail(60)
    support = np.percentile(recent_data['Low'], 10)
    resistance = np.percentile(recent_data['High'], 90)
    
    # Volume analysis
    volume_trend = "Above Average" if latest['Volume_Ratio'] > 1.2 else \
                   "Below Average" if latest['Volume_Ratio'] < 0.8 else \
                   "Average"
    
    # Generate overall signal
    bullish_signals = 0
    bearish_signals = 0
    
    # Count bullish signals
    if trend == "Uptrend":
        bullish_signals += 1
    if rsi_status != "Overbought" and latest['RSI'] > 50:
        bullish_signals += 1
    if macd_signal == "Bullish":
        bullish_signals += 1
    if latest['Close'] > latest['SMA_20']:
        bullish_signals += 1
    
    # Count bearish signals
    if trend == "Downtrend":
        bearish_signals += 1
    if rsi_status != "Oversold" and latest['RSI'] < 50:
        bearish_signals += 1
    if macd_signal == "Bearish":
        bearish_signals += 1
    if latest['Close'] < latest['SMA_20']:
        bearish_signals += 1
    
    overall_signal = "Buy" if bullish_signals > bearish_signals + 1 else \
                     "Sell" if bearish_signals > bullish_signals + 1 else \
                     "Hold"
    
    # Generate analysis text
    analysis = {
        "symbol": ticker,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "current_price": round(float(latest['Close']), 2),
        "trend": trend,
        "indicators": {
            "rsi": {
                "value": round(float(latest['RSI']), 2),
                "interpretation": rsi_status
            },
            "macd": {
                "value": round(float(latest['MACD']), 4),
                "signal": round(float(latest['MACD_signal']), 4),
                "interpretation": macd_signal
            },
            "bollinger_bands": {
                "upper": round(float(latest['BB_upper']), 2),
                "middle": round(float(latest['BB_middle']), 2),
                "lower": round(float(latest['BB_lower']), 2),
                "status": bb_status
            },
            "moving_averages": {
                "sma_20": round(float(latest['SMA_20']), 2),
                "sma_50": round(float(latest['SMA_50']), 2),
                "sma_200": round(float(latest['SMA_200']), 2)
            }
        },
        "support_resistance": {
            "support": round(float(support), 2),
            "resistance": round(float(resistance), 2)
        },
        "volume_analysis": {
            "trend": volume_trend,
            "ratio": round(float(latest['Volume_Ratio']), 2)
        },
        "momentum": {
            "1_day": round(float(latest['Price_Change_1d']), 2),
            "5_day": round(float(latest['Price_Change_5d']), 2),
            "20_day": round(float(latest['Price_Change_20d']), 2)
        },
        "volatility": round(float(latest['Volatility_20d']), 2),
        "overall_signal": overall_signal,
        "signal_strength": {
            "bullish_signals": bullish_signals,
            "bearish_signals": bearish_signals
        },
        "analysis_text": f"""
Technical Analysis for {ticker}:

Current Price: ${round(float(latest['Close']), 2)}
Trend: {trend}

Key Indicators:
- RSI: {round(float(latest['RSI']), 2)} ({rsi_status})
- MACD: {macd_signal} momentum
- Bollinger Bands: Price near {bb_status.lower()}
- Volume: {volume_trend.lower()} compared to 20-day average

Support Level: ${round(float(support), 2)}
Resistance Level: ${round(float(resistance), 2)}

Recent Performance:
- 1-day change: {round(float(latest['Price_Change_1d']), 2)}%
- 5-day change: {round(float(latest['Price_Change_5d']), 2)}%
- 20-day change: {round(float(latest['Price_Change_20d']), 2)}%

Overall Technical Signal: {overall_signal}
Signal Strength: {bullish_signals} bullish vs {bearish_signals} bearish indicators
        """
    }
    
    return analysis

def save_technical_analysis(analysis, instrument):
    """Save technical analysis to JSON file"""
    # Create directory if it doesn't exist
    output_dir = f"technical_analysis/{instrument}"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{output_dir}/{instrument}_technical_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"    Saved technical analysis to {filename}")

def main():
    """Main collection function"""
    print("Multi-Source Technical Analysis Collector")
    print("=" * 50)
    
    results = {}
    
    for name, ticker in INSTRUMENTS.items():
        print(f"\nProcessing {name}...")
        
        try:
            historical_data, source = fetch_data_with_fallbacks(ticker, name)
            
            if historical_data is not None and not historical_data.empty:
                data_with_indicators = calculate_technical_indicators(historical_data)
                
                if data_with_indicators is not None:
                    analysis = generate_technical_analysis(data_with_indicators, ticker)
                    
                    if analysis:
                        # Add source information to analysis
                        analysis['data_source'] = source
                        analysis['data_points'] = len(historical_data)
                        
                        save_technical_analysis(analysis, name)
                        results[name] = f"✅ Success ({source})"
                        print(f"  ✅ Completed {name} using {source}")
                    else:
                        results[name] = "❌ Analysis generation failed"
                else:
                    results[name] = "❌ Indicator calculation failed"
            else:
                results[name] = "❌ No data available"
                
        except Exception as e:
            results[name] = f"❌ Error: {str(e)}"
            print(f"  ❌ Error processing {name}: {str(e)}")
        
        # Delay between instruments
        time.sleep(random.uniform(3, 6))
    
    # Print summary
    print(f"\n" + "="*50)
    print("COLLECTION SUMMARY")
    print("="*50)
    for name, result in results.items():
        print(f"{name:15} | {result}")
    
    successful = sum(1 for r in results.values() if r.startswith("✅"))
    print(f"\nTotal successful: {successful}/{len(INSTRUMENTS)}")

if __name__ == "__main__":
    main()
