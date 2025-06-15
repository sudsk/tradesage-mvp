# app/adk/agents/research_agent.py - Fixed imports
from google.adk.agents import Agent
from app.config.adk_config import AGENT_CONFIGS
from app.adk.tools import market_data_search, news_search  # Import functions directly

RESEARCH_INSTRUCTION = """
You are the Research Agent for TradeSage AI. You conduct comprehensive market research.

Your responsibilities:
1. Gather market data for relevant financial instruments
2. Search for recent news and analysis
3. Combine all data sources into comprehensive research

Use the available tools to:
- market_data_search: Get current prices, volumes, and basic fundamentals
- news_search: Find recent news articles and analysis

Always provide:
1. Current market data summary
2. Recent news highlights
3. Data quality assessment
4. Research confidence level

Focus on the specific asset and timeframe mentioned in the hypothesis.
"""

def create_research_agent() -> Agent:
    """Create the market research agent."""
    config = AGENT_CONFIGS["research_agent"]
    
    return Agent(
        name=config["name"],
        model=config["model"],
        description=config["description"], 
        instruction=RESEARCH_INSTRUCTION,
        tools=[market_data_search, news_search],  # Functions directly
    )
