# app/adk/agents/alert_agent.py - Fixed for direct alerts
from google.adk.agents import Agent
from app.config.adk_config import AGENT_CONFIGS
from app.adk.tools import database_save

ALERT_INSTRUCTION = """
You are the Alert Agent for TradeSage AI. Generate SPECIFIC, ACTIONABLE alerts.

CRITICAL: Output ONLY actionable alerts. NO meta-text or descriptions.

Based on confidence level, generate alerts like:

HIGH CONFIDENCE (70%+):
- "Enter 2-3% position in AAPL if price breaks above $197 with volume"
- "Set stop-loss at $185 (5.4% below entry) to limit downside"
- "Monitor Q1 earnings (Jan 30) for Services revenue confirmation"

MEDIUM CONFIDENCE (50-69%):
- "Wait for AAPL to establish support above $195 before entering"
- "Consider 1-2% initial position, add on strength above $200"
- "Watch for institutional buying signals above 50-day MA"

LOW CONFIDENCE (<50%):
- "Avoid entry until clearer trend emerges"
- "Monitor competitive pressures from Samsung/Google"
- "Wait for valuation to improve below 28x P/E"

Format as JSON array:
[
  {
    "type": "entry|risk|monitor|exit",
    "message": "Specific actionable alert",
    "priority": "high|medium|low"
  }
]

Generate 3-5 SPECIFIC alerts with exact price levels and actions.
"""

def create_alert_agent() -> Agent:
    """Create the alert generation agent."""
    config = AGENT_CONFIGS["alert_agent"]
    
    return Agent(
        name=config["name"],
        model=config["model"],
        description=config["description"],
        instruction=ALERT_INSTRUCTION,
        tools=[database_save],
    )
