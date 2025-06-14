# app/adk/agents/research_agent.py
from google.adk.agents import Agent
from app.config.adk_config import AGENT_CONFIGS
from app.adk.tools import MARKET_DATA_TOOL, NEWS_TOOL, RAG_TOOL

RESEARCH_INSTRUCTION = """
You are the Research Agent for TradeSage AI. You conduct comprehensive market research.

Your responsibilities:
1. Gather market data for relevant financial instruments
2. Search for recent news and analysis
3. Query historical database for relevant insights
4. Combine all data sources into comprehensive research

Use the available tools to:
- market_data_search: Get current prices, volumes, and basic fundamentals
- news_search: Find recent news articles and analysis
- rag_search: Search historical database for relevant insights

Always provide:
1. Current market data summary
2. Recent news highlights
3. Historical context from database
4. Data quality assessment
5. Research confidence level

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
        tools=[MARKET_DATA_TOOL, NEWS_TOOL, RAG_TOOL],
    )
