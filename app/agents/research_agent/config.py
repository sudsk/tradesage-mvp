# app/agents/research_agent/config.py
import vertexai
from vertexai.generative_models import GenerationConfig

AGENT_NAME = "research_agent"
AGENT_DESCRIPTION = "Conducts market research and data gathering"

MODEL_NAME = "gemini-1.5-pro"
GENERATION_CONFIG = GenerationConfig(
    temperature=0.1,  # Lower temperature for factual responses
    top_p=0.95,
    top_k=40,
    max_output_tokens=8192,
)

PROJECT_ID = "tradesage-mvp"
LOCATION = "us-central1"

