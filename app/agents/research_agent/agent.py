# app/agents/research_agent/agent.py - Updated to handle cryptocurrencies
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
from app.tools.market_data_tool import market_data_tool
from app.tools.news_data_tool import news_data_tool
import json
import re

class ResearchAgent:
    def __init__(self):
        try:
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            self.model = GenerativeModel(
                model_name=MODEL_NAME,
                generation_config=GENERATION_CONFIG,
                system_instruction=SYSTEM_INSTRUCTION
            )
        except Exception as e:
            print(f"Error initializing Research Agent: {e}")
            self.model = None
    
    def process(self, input_data):
        """Conduct research based on the hypothesis."""
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("hypothesis", "")
        processed_hypothesis = input_data.get("processed_hypothesis", hypothesis)
        
        # Extract instruments/symbols from hypothesis with better cryptocurrency support
        instruments = self._extract_instruments(processed_hypothesis)
        print(f"Extracted instruments: {instruments}")
        
        # Gather market data
        market_data = {}
        for i, instrument in enumerate(instruments[:2]):  # Limit to 2 instruments
            print(f"Fetching data for instrument {i+1}/{min(2, len(instruments))}: {instrument}")
            market_data[instrument] = market_data_tool(instrument, "auto", PROJECT_ID)
        
        # Gather news data
        news_query = self._create_news_query(processed_hypothesis)
        news_data = news_data_tool(news_query, 7, PROJECT_ID)
        
        # Create research summary prompt
        prompt = f"""
        Research Summary for Hypothesis: {processed_hypothesis}
        
        Market Data: {json.dumps(market_data, indent=2)}
        
        News Data: {json.dumps(news_data, indent=2)}
        
        Please provide:
        1. Summary of market data findings
        2. Key news and developments
        3. Relevant metrics and indicators
        4. Current market context
        
        Focus on factual information without analysis.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "research_data": {
                    "market_data": market_data,
                    "news_data": news_data,
                    "summary": response.text
                },
                "status": "success"
            }
        except Exception as e:
            print(f"Research agent error: {str(e)}")
            return {
                "research_data": {
                    "market_data": market_data,
                    "news_data": news_data,
                    "summary": f"Basic research completed for hypothesis regarding {', '.join(instruments)}."
                },
                "status": "success"
            }
    
    def _extract_instruments(self, text):
        """Extract symbols from text with improved cryptocurrency and ticker detection."""
        instruments = []
        
        # 1. Look for cryptocurrency patterns
        crypto_patterns = [
            # Bitcoin patterns
            r'(?:bitcoin|btc)[-\s]*(?:usd)?',
            # Ethereum patterns
            r'(?:ethereum|eth)[-\s]*(?:usd)?',
            # Other major cryptos
            r'(?:cardano|ada)[-\s]*(?:usd)?',
            r'(?:solana|sol)[-\s]*(?:usd)?',
            r'(?:xrp|ripple)[-\s]*(?:usd)?',
            r'(?:dogecoin|doge)[-\s]*(?:usd)?',
            # General crypto ticker pattern
            r'(?:[A-Z]{3,5})[-\s]*(?:usd)?'
        ]
        
        for pattern in crypto_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                # Map common cryptocurrency names to their tickers
                if 'bitcoin' in match or 'btc' in match:
                    instruments.append('BTC-USD')
                elif 'ethereum' in match or 'eth' in match:
                    instruments.append('ETH-USD')
                elif 'cardano' in match or 'ada' in match:
                    instruments.append('ADA-USD')
                elif 'solana' in match or 'sol' in match:
                    instruments.append('SOL-USD')
                elif 'ripple' in match or 'xrp' in match:
                    instruments.append('XRP-USD')
                elif 'dogecoin' in match or 'doge' in match:
                    instruments.append('DOGE-USD')
        
        # 2. Look for stock market ETFs or indices
        etf_patterns = [
            r'\b(SPY|QQQ|IWM|VTI|DIA)\b',  # Common ETFs
            r'\b(S&P 500|NASDAQ|Dow Jones|Russell 2000)\b'  # Common indices
        ]
        
        for pattern in etf_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                match_upper = match.upper()
                # Map indices to ETFs
                if match_upper == 'S&P 500':
                    instruments.append('SPY')
                elif match_upper == 'NASDAQ':
                    instruments.append('QQQ')
                elif match_upper == 'DOW JONES':
                    instruments.append('DIA')
                elif match_upper == 'RUSSELL 2000':
                    instruments.append('IWM')
                else:
                    instruments.append(match_upper)
        
        # 3. Look for regular stock tickers with $ prefix
        stock_patterns = [
            r'\$([A-Z]{1,5})',  # $AAPL style
            r'\b([A-Z]{3,5})\b'  # AAPL style (only for 3-5 letter tickers)
        ]
        
        for pattern in stock_patterns:
            matches = re.findall(pattern, text)
            instruments.extend([m for m in matches if len(m) >= 2])
        
        # Remove duplicates and filter common words
        instruments = list(set(instruments))
        exclude = {'THE', 'AND', 'FOR', 'ARE', 'WILL', 'USD', 'HAS', 'NOT', 'BY', 'END', 'INC'}
        instruments = [i for i in instruments if i not in exclude]
        
        # If no instruments found, use default based on context
        if not instruments:
            if 'bitcoin' in text.lower() or 'btc' in text.lower() or 'crypto' in text.lower():
                instruments = ['BTC-USD']
            elif 'stock' in text.lower() or 'market' in text.lower() or 'index' in text.lower():
                instruments = ['SPY']
            else:
                instruments = ['SPY']  # Default to S&P 500
        
        return instruments[:2]  # Limit to 2 instruments to avoid rate limiting
    
    def _create_news_query(self, hypothesis):
        """Create a more targeted news search query."""
        # Check for cryptocurrencies
        if re.search(r'bitcoin|btc|ethereum|eth|crypto|cryptocurrency', hypothesis.lower()):
            return 'cryptocurrency bitcoin ethereum market'
        
        # Extract key financial terms
        important_terms = re.findall(r'\b(?:stock|market|etf|index|bond|rate|inflation|recession|growth)\w*\b', 
                                   hypothesis.lower())
        
        # If financial terms found, use them
        if important_terms:
            return ' '.join(important_terms[:3])
        
        # Fallback to extracting nouns
        words = re.findall(r'\b[A-Za-z]{4,}\b', hypothesis)
        if words:
            return ' '.join(words[:3])
        
        # Last resort
        return 'financial market news'

def create():
    """Create and return a research agent instance."""
    return ResearchAgent()
