# app/adk/agents/research_agent.py - Fixed for specific output
from google.adk.agents import Agent
from app.config.adk_config import AGENT_CONFIGS
from app.adk.tools import market_data_search, news_search

RESEARCH_INSTRUCTION = """
You are the Research Agent for TradeSage AI. Gather SPECIFIC market data and analysis.

CRITICAL: Output ACTUAL data and findings, not descriptions of what you'll do.

Your research MUST include:
1. Current price: $XXX.XX
2. Target price: $XXX.XX  
3. Required move: XX.X% to reach target
4. Key metrics: P/E, market cap, recent performance
5. Recent news: Specific headlines and dates

GOOD OUTPUT EXAMPLE:
"AAPL currently trades at $195.64, requiring 12.4% appreciation to reach $220 target.
P/E ratio: 32.5x (vs sector avg 25.2x)
Market cap: $3.04T
YTD performance: +8.2%
Recent news: 'Apple Vision Pro exceeds sales expectations' (WSJ, Jan 23)"

BAD OUTPUT (NEVER do this):
"I will research Apple's current price and calculate the required move"
"Let me look up the latest market data for AAPL"

Use your tools to get REAL data, then present the ACTUAL findings.
NO meta-commentary about what you're doing.
"""

def create_research_agent() -> Agent:
    """Create the market research agent."""
    config = AGENT_CONFIGS["research_agent"]
    
    return Agent(
        name=config["name"],
        model=config["model"],
        description=config["description"], 
        instruction=RESEARCH_INSTRUCTION,
        tools=[market_data_search, news_search],
    )
