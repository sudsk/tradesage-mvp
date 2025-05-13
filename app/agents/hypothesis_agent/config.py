# app/agents/hypothesis_agent/config.py
import vertexai
from vertexai.generative_models import GenerationConfig

AGENT_NAME = "hypothesis_agent"
AGENT_DESCRIPTION = "Generates, refines, and structures trading hypotheses"

MODEL_NAME = "gemini-2.0-flash"
GENERATION_CONFIG = GenerationConfig(
    temperature=0.2,
    top_p=0.95,
    top_k=40,
    max_output_tokens=8192,
)

PROJECT_ID = "tradesage-mvp"
LOCATION = "us-central1"

# Initialize Vertex AI
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
except Exception as e:
    print(f"Warning: Could not initialize Vertex AI: {e}")

