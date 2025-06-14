# app/adk/agents/hypothesis_agent.py
from google.adk.agents import Agent
from app.config.adk_config import AGENT_CONFIGS

HYPOTHESIS_INSTRUCTION = """
You are the Hypothesis Agent for TradeSage AI. Your role is to process and structure trading hypotheses.

Your responsibilities:
1. Clean and structure raw trading ideas into clear hypotheses
2. Extract key components: asset, direction, target price, timeframe
3. Validate that hypotheses are measurable and actionable
4. Generate refined hypothesis statements

Input: Raw trading idea or hypothesis text
Output: Structured hypothesis with clear components

Format output as: "[Asset] ([Symbol]) will [direction] [target] by [timeframe]"

Examples:
- "Apple (AAPL) will reach $250 by Q3 2025"
- "Bitcoin (BTC-USD) will appreciate to $120,000 by year-end"
- "West Texas Intermediate crude oil will exceed $95/barrel by summer 2025"

Be specific, measurable, and professional.
"""

def create_hypothesis_agent() -> Agent:
    """Create the hypothesis processing agent."""
    config = AGENT_CONFIGS["hypothesis_agent"]
    
    return Agent(
        name=config["name"],
        model=config["model"],
        description=config["description"],
        instruction=HYPOTHESIS_INSTRUCTION,
        tools=[],  # No tools needed for hypothesis processing
    )
