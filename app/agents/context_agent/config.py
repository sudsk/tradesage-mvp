# app/agents/context_agent/config.py
import vertexai
from vertexai.generative_models import GenerationConfig

AGENT_NAME = "context_agent"
AGENT_DESCRIPTION = "Analyzes and provides intelligent context for trading hypotheses"

MODEL_NAME = "gemini-2.0-flash"
GENERATION_CONFIG = GenerationConfig(
    temperature=0.1,  # Low temperature for consistent, factual analysis
    top_p=0.95,
    top_k=40,
    max_output_tokens=4096,
)

PROJECT_ID = "tradesage-mvp"
LOCATION = "us-central1"
