# app/agents/contradiction_agent/config.py
import vertexai
from vertexai.generative_models import GenerationConfig

AGENT_NAME = "contradiction_agent"
AGENT_DESCRIPTION = "Identifies contradictions and challenges hypotheses"

MODEL_NAME = "gemini-1.5-pro"
GENERATION_CONFIG = GenerationConfig(
    temperature=0.3,
    top_p=0.95,
    top_k=40,
    max_output_tokens=8192,
)

PROJECT_ID = "tradesage-mvp"
LOCATION = "us-central1"

