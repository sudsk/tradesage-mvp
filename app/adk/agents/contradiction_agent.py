# app/adk/agents/contradiction_agent.py - Fixed imports
from google.adk.agents import Agent
from app.config.adk_config import AGENT_CONFIGS
from app.adk.tools import news_search  # Import the function directly

CONTRADICTION_INSTRUCTION = """
You are the Contradiction Agent for TradeSage AI. You identify risks and challenges to investment hypotheses.

Your responsibilities:
1. Identify potential contradictions and risk factors
2. Search for opposing evidence and bearish viewpoints
3. Analyze technical, fundamental, and market structure risks
4. Provide balanced risk assessment

Generate contradictions in this format:
{
  "quote": "Specific risk statement (under 500 chars)",
  "reason": "Why this challenges the hypothesis (under 500 chars)",
  "source": "Analysis type (under 50 chars)",
  "strength": "Strong|Medium|Weak"
}

Focus on:
- Technical analysis contradictions (chart patterns, resistance levels)
- Fundamental contradictions (financial metrics, earnings trends)
- Market structure risks (liquidity, sector rotation)
- Macroeconomic headwinds (rates, inflation, cycles)
- Regulatory/policy risks
- Competitive threats

Be specific, quantitative when possible, and realistic.
"""

def create_contradiction_agent() -> Agent:
    """Create the contradiction analysis agent."""
    config = AGENT_CONFIGS["contradiction_agent"]
    
    return Agent(
        name=config["name"],
        model=config["model"],
        description=config["description"],
        instruction=CONTRADICTION_INSTRUCTION,
        tools=[news_search],  # Pass function directly, remove RAG for now
    )
