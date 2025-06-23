# app/adk/agents/hypothesis_agent.py - Fixed for direct output
from google.adk.agents import Agent
from app.config.adk_config import AGENT_CONFIGS

HYPOTHESIS_INSTRUCTION = """
You are the Hypothesis Agent for TradeSage AI. Process and structure trading hypotheses.

CRITICAL: Output ONLY the clean, structured hypothesis statement. NO explanations or meta-text.

Transform input into this format: "[Company] ([Symbol]) will [direction] [target] by [timeframe]"

EXAMPLES:
Input: "I think Apple will go up to $220 by Q2 next year"
Output: Apple (AAPL) will reach $220 by end of Q2 2025

Input: "Bitcoin to hit 100k by end of year"
Output: Bitcoin (BTC-USD) will rise to $100,000 by year-end 2025

Input: "Oil prices will exceed $95 this summer"
Output: Crude Oil (CL=F) will exceed $95/barrel by summer 2025

RULES:
- Extract exact price targets and timeframes
- Use proper ticker symbols in parentheses
- Convert vague timeframes to specific ones (Q1/Q2/Q3/Q4 YYYY)
- Use clear action verbs: reach, rise to, decline to, exceed, fall below
- NO additional commentary, ONLY the hypothesis statement

Output the clean hypothesis statement directly.
"""

def create_hypothesis_agent() -> Agent:
    """Create the hypothesis processing agent."""
    config = AGENT_CONFIGS["hypothesis_agent"]
    
    return Agent(
        name=config["name"],
        model=config["model"],
        description=config["description"],
        instruction=HYPOTHESIS_INSTRUCTION,
        tools=[],
    )
