# app/agents/alert_agent/config.py
import vertexai
from vertexai.generative_models import GenerationConfig

AGENT_NAME = "alert_agent"
AGENT_DESCRIPTION = "Generates alerts and actionable recommendations"

MODEL_NAME = "gemini-2.0-flash"
GENERATION_CONFIG = GenerationConfig(
    temperature=0.1,
    top_p=0.95,
    top_k=40,
    max_output_tokens=8192,
)

PROJECT_ID = "tradesage-mvp"
LOCATION = "us-central1"
