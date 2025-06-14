# app/config/adk_config.py
import os
from typing import Dict, Any

# ADK Configuration
ADK_CONFIG = {
    "project_id": os.getenv("PROJECT_ID", "tradesage-mvp"),
    "location": os.getenv("REGION", "us-central1"),
    "model": "gemini-2.0-flash",
    "use_vertex_ai": True,
}

# Agent Configuration
AGENT_CONFIGS = {
    "hypothesis_agent": {
        "name": "hypothesis_processor",
        "description": "Processes and structures trading hypotheses",
        "model": "gemini-2.0-flash",
        "temperature": 0.2,
    },
    "context_agent": {
        "name": "context_analyzer", 
        "description": "Analyzes trading hypotheses for context and asset information",
        "model": "gemini-2.0-flash",
        "temperature": 0.1,
    },
    "research_agent": {
        "name": "market_researcher",
        "description": "Conducts market research using hybrid RAG and real-time data",
        "model": "gemini-2.0-flash", 
        "temperature": 0.1,
    },
    "contradiction_agent": {
        "name": "risk_analyzer",
        "description": "Identifies contradictions and risk factors in investment thesis",
        "model": "gemini-2.0-flash",
        "temperature": 0.3,
    },
    "synthesis_agent": {
        "name": "analysis_synthesizer",
        "description": "Synthesizes research and creates investment analysis",
        "model": "gemini-2.0-flash",
        "temperature": 0.2,
    },
    "alert_agent": {
        "name": "alert_generator",
        "description": "Generates actionable alerts and recommendations",
        "model": "gemini-2.0-flash",
        "temperature": 0.1,
    }
}
