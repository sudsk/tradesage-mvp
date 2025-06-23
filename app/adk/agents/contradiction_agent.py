# app/adk/agents/contradiction_agent.py - FIXED VERSION
from google.adk.agents import Agent
from app.config.adk_config import AGENT_CONFIGS
from app.adk.tools import news_search

# FIXED: More direct, output-focused instruction
CONTRADICTION_INSTRUCTION = """
You are the Contradiction Agent for TradeSage AI. Find and present SPECIFIC market risks and contradictions.

CRITICAL: Generate ACTUAL market contradictions, NOT meta-analysis or instructions.

For each contradiction, provide:
1. A SPECIFIC market fact or trend that challenges the hypothesis
2. Real concerns like valuation, competition, regulation, or market conditions
3. Concrete risks that investors should consider

GOOD EXAMPLES for "Apple will reach $220 by Q2 2025":
✅ "Apple's Services growth may decelerate due to increased regulatory scrutiny on the App Store"
✅ "iPhone demand showing signs of saturation in key markets with upgrade cycles lengthening"
✅ "Rising competition from Chinese manufacturers pressuring Apple's market share in Asia"

BAD EXAMPLES (NEVER generate these):
❌ "I will analyze the provided information and generate contradictions"
❌ "Okay, I will look for risks related to Apple's revenue streams"
❌ "I will investigate potential challenges from competitors"

Format your response as a JSON array of contradictions:
[
  {
    "quote": "Specific market risk or negative trend",
    "reason": "Why this challenges the investment thesis",
    "source": "Market Analysis",
    "strength": "Strong|Medium|Weak"
  }
]

Generate 3-5 SPECIFIC, REALISTIC contradictions based on actual market conditions.
"""

def create_contradiction_agent() -> Agent:
    """Create the contradiction agent with fixed instructions."""
    config = AGENT_CONFIGS["contradiction_agent"]
    
    return Agent(
        name=config["name"],
        model=config["model"],
        description=config["description"],
        instruction=CONTRADICTION_INSTRUCTION,
        tools=[news_search],
    )
