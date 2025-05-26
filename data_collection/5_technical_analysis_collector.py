# technical_analysis_collector.py
import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import talib

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

def fetch_historical_data(ticker, period="1y"):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return None

def calculate_technical_indicators(data):
    if data is None or len(data) < 30:
        return None
    
    # Copy the data to avoid SettingWithCopyWarning
    df = data.copy()
    
    # Calculate common technical indicators
    try:
        # Moving averages
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        # Bollinger Bands
        df['BB_middle'] = df['SMA_20']
        df['BB_upper'] = df['BB_middle'] + 2 * df['Close'].rolling(window=20).std()
        df['BB_lower'] = df['BB_middle'] - 2 * df['Close'].rolling(window=20).std()
        
        # Relative Strength Index
        df['RSI'] = talib.RSI(df['Close'].values, timeperiod=14)
        
        # MACD
        macd, macd_signal, macd_hist = talib.MACD(
            df['Close'].values, fastperiod=12, slowperiod=26, signalperiod=9
        )
        df['MACD'] = macd
        df['MACD_signal'] = macd_signal
        df['MACD_hist'] = macd_hist
        
        # Stochastic oscillator
        df['slowk'], df['slowd'] = talib.STOCH(
            df['High'].values, df['Low'].values, df['Close'].values,
            fastk_period=14, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0
        )
        
        # Average Directional Index
        df['ADX'] = talib.ADX(
            df['High'].values, df['Low'].values, df['Close'].values, timeperiod=14
        )
        
        # Fill NaN values for indicators that require calculation windows
        df = df.fillna(method='bfill')
        
        return df
    except Exception as e:
        print(f"Error calculating indicators: {str(e)}")
        return None

def generate_technical_analysis(data, ticker):
    if data is None:
        return None
    
    # Get the most recent data points
    latest = data.iloc[-1]
    prev = data.iloc[-2]
    
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
    bb_status = "Upper Band Touch" if latest['Close'] >= latest['BB_upper'] else \
                "Lower Band Touch" if latest['Close'] <= latest['BB_lower'] else \
                "Middle Band"
    
    # Support and resistance levels
    recent_data = data.tail(60)
    support = np.percentile(recent_data['Low'], 10)
    resistance = np.percentile(recent_data['High'], 90)
    
    # Generate analysis text
    analysis = {
        "symbol": ticker,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "current_price": round(latest['Close'], 2),
        "trend": trend,
        "indicators": {
            "rsi": {
                "value": round(latest['RSI'], 2),
                "interpretation": rsi_status
            },
            "macd": {
                "value": round(latest['MACD'], 4),
                "signal": round(latest['MACD_signal'], 4),
                "interpretation": macd_signal
            },
            "bollinger_bands": {
                "upper": round(latest['BB_upper'], 2),
                "middle": round(latest['BB_middle'], 2),
                "lower": round(latest['BB_lower'], 2),
                "status": bb_status
            }
        },
        "support_resistance": {
            "support": round(support, 2),
            "resistance": round(resistance, 2)
        },
        "overall_signal": "Buy" if (
            trend == "Uptrend" and 
            rsi_status != "Overbought" and 
            macd_signal == "Bullish"
        ) else "Sell" if (
            trend == "Downtrend" and 
            rsi_status != "Oversold" and 
            macd_signal == "Bearish"
        ) else "Neutral",
        "analysis_text": f"""
Technical Analysis for {ticker}:

{ticker} is currently in a {trend.lower()} with the price at ${round(latest['Close'], 2)}. 

RSI is at {round(latest['RSI'], 2)} indicating {rsi_status.lower()} conditions.

The MACD line is {'above' if latest['MACD'] > latest['MACD_signal'] else 'below'} the signal line, suggesting {macd_signal.lower()} momentum.

Bollinger Bands show the price is {'near the upper band' if latest['Close'] >= latest['BB_upper'] * 0.95 else 'near the lower band' if latest['Close'] <= latest['BB_lower'] * 1.05 else 'between bands'}.

Support level: ${round(support, 2)}
Resistance level: ${round(resistance, 2)}

Overall Technical Signal: {
    "Buy" if (trend == "Uptrend" and rsi_status != "Overbought" and macd_signal == "Bullish") 
    else "Sell" if (trend == "Downtrend" and rsi_status != "Oversold" and macd_signal == "Bearish") 
    else "Neutral"
}
        """
    }
    
    return analysis

def save_technical_analysis(analysis, instrument):
    # Create directory if it doesn't exist
    output_dir = f"technical_analysis/{instrument}"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{output_dir}/{instrument}_technical_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"Saved technical analysis to {filename}")

# Collect technical analysis for each instrument
for name, ticker in INSTRUMENTS.items():
    print(f"Generating technical analysis for {name} ({ticker})...")
    
    historical_data = fetch_historical_data(ticker)
    
    if historical_data is not None and not historical_data.empty:
        data_with_indicators = calculate_technical_indicators(historical_data)
        
        if data_with_indicators is not None:
            analysis = generate_technical_analysis(data_with_indicators, ticker)
            
            if analysis:
                save_technical_analysis(analysis, name)
    
    print(f"Completed {name}\n")
