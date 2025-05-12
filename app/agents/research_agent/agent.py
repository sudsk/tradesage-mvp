# app/agents/research_agent/agent.py
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
        
        # Extract instruments/symbols from hypothesis
        instruments = self._extract_instruments(processed_hypothesis)
        
        # Gather market data
        market_data = {}
        for instrument in instruments:
            market_data[instrument] = market_data_tool(instrument, "yahoo", PROJECT_ID)
        
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
            return {
                "error": str(e),
                "status": "error"
            }
    
    def _extract_instruments(self, text):
        """Extract stock symbols and instruments from text."""
        # Simple pattern matching for common stock symbols
        symbols = re.findall(r'\b[A-Z]{1,5}\b', text)
        # Filter out common words that aren't symbols
        exclude = {'AI', 'THE', 'AND', 'OR', 'NOT', 'FOR', 'IN', 'ON', 'AT', 'TO', 'BY'}
        symbols = [s for s in symbols if s not in exclude]
        
        # If no symbols found, extract sector/industry terms
        if not symbols:
            # Look for common sector/ETF terms
            sectors = ['SPY', 'XLF', 'XLE', 'XLK', 'QQQ', 'IWM']  # Common ETFs
            symbols = sectors[:2]  # Default to a couple of major ETFs
        
        return symbols[:3]  # Limit to 3 symbols to avoid too many API calls
    
    def _create_news_query(self, hypothesis):
        """Create a news search query from the hypothesis."""
        # Extract key terms for news search
        words = hypothesis.split()
        key_terms = [word for word in words if len(word) > 3 and word.isalpha()]
        return ' '.join(key_terms[:3])  # Use top 3 key terms

def create():
    """Create and return a research agent instance."""
    return ResearchAgent()

