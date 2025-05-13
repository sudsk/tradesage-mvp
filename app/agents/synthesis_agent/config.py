# app/agents/synthesis_agent/config.py
import vertexai
from vertexai.generative_models import GenerationConfig

AGENT_NAME = "synthesis_agent"
AGENT_DESCRIPTION = "Synthesizes research and contradictions into cohesive analysis"

MODEL_NAME = "gemini-1.5-pro"
GENERATION_CONFIG = GenerationConfig(
    temperature=0.2,
    top_p=0.95,
    top_k=40,
    max_output_tokens=8192,
)

PROJECT_ID = "tradesage-mvp"
LOCATION = "us-central1"

