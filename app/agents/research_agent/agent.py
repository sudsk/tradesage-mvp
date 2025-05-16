# app/agents/research_agent/agent.py - Updated to reduce API calls
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
        """Conduct research based on the hypothesis with reduced API calls."""
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("hypothesis", "")
        processed_hypothesis = input_data.get("processed_hypothesis", hypothesis)
        
        # Extract instruments/symbols from hypothesis (limit to 1-2 instruments)
        instruments = self._extract_instruments(processed_hypothesis)
        
        # Gather market data (only for main instruments to avoid rate limiting)
        market_data = {}
        for i, instrument in enumerate(instruments[:2]):  # Limit to 2 instruments
            print(f"Fetching data for instrument {i+1}/{min(2, len(instruments))}: {instrument}")
            market_data[instrument] = market_data_tool(instrument, "yahoo", PROJECT_ID)
        
        # Gather news data (reduced frequency)
        news_query = self._create_news_query(processed_hypothesis)
        news_data = news_data_tool(news_query, 7, PROJECT_ID)
        
        # Create research summary prompt
        prompt = f"""
        Research Summary for Hypothesis: {processed_hypothesis[:200]}...
        
        Market Data: {json.dumps(market_data, indent=2)[:1000]}...
        
        News Data: {json.dumps(news_data, indent=2)[:1000]}...
        
        Please provide:
        1. Summary of market data findings
        2. Key news and developments
        3. Relevant metrics and indicators
        4. Current market context
        
        Focus on factual information without analysis.
        Keep the summary concise and relevant to the hypothesis.
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
            # Return fallback data if research fails
            return {
                "research_data": {
                    "market_data": market_data,
                    "news_data": {"articles": [], "status": "limited"},
                    "summary": f"Basic research completed for: {processed_hypothesis[:100]}..."
                },
                "status": "success"
            }
    
    def _extract_instruments(self, text):
        """Extract stock symbols and instruments from text with better filtering."""
        # Common ETF and stock patterns
        etf_patterns = [
            r'\b([A-Z]{3,5})\s+ETF',
            r'\bETF[:\s]+([A-Z]{3,5})',
            r'\b([A-Z]{3,5})\s+(?:fund|index)',
        ]
        
        # Extract ETFs first
        instruments = []
        for pattern in etf_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            instruments.extend(matches)
        
        # If no ETFs found, look for regular symbols
        if not instruments:
            symbols = re.findall(r'\b([A-Z]{3,5})\b', text)
            # Filter out common words
            exclude = {
                'THE', 'AND', 'OR', 'NOT', 'FOR', 'IN', 'ON', 'AT', 'TO', 'BY',
                'ETF', 'USD', 'API', 'GDP', 'CPI', 'FED', 'CEO', 'CFO', 'SEC'
            }
            instruments = [s for s in symbols if s not in exclude and len(s) >= 3]
        
        # If still no instruments, use defaults based on hypothesis content
        if not instruments:
            if 'oil' in text.lower() or 'energy' in text.lower():
                instruments = ['XLE', 'USO']
            elif 'tech' in text.lower() or 'ai' in text.lower():
                instruments = ['QQQ', 'XLK']
            elif 'bank' in text.lower() or 'financial' in text.lower():
                instruments = ['XLF', 'KRE']
            elif 'inflation' in text.lower():
                instruments = ['TIP', 'SCHP']
            else:
                instruments = ['SPY']  # Default to S&P 500
        
        # Return only the first 2 instruments to avoid rate limiting
        return instruments[:2]
    
    def _create_news_query(self, hypothesis):
        """Create a more targeted news search query."""
        # Extract key financial terms
        important_terms = re.findall(r'\b(?:oil|energy|bank|tech|inflation|fed|gdp|etf|stock|price|market)\w*\b', 
                                    hypothesis.lower())
        
        # Use only the most relevant terms
        if important_terms:
            return ' '.join(important_terms[:3])
        else:
            # Fallback to general market terms
            return 'market analysis financial'

def create():
    """Create and return a research agent instance."""
    return ResearchAgent()
